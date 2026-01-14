from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .models import User, Portfolio
from .exceptions import (
    AuthenticationError, InsufficientFundsError, CurrencyNotFoundError, ValidationError
)
from ..infra.database import db
from ..infra.settings import settings
from ..decorators import log_action


@dataclass
class Session:
    user_id: int
    username: str
    login_time: datetime
    last_activity: datetime


class UseCases:
    def __init__(self):
        self.current_session: Optional[Session] = None
        self._load_session()
    
    @property
    def is_authenticated(self) -> bool:
        return self.current_session is not None
    
    def get_current_user_id(self) -> Optional[int]:
        return self.current_session.user_id if self.current_session else None
    
    def _save_session(self):
        import json
        from pathlib import Path
        
        if self.current_session:
            session_file = Path("session.json")
            session_data = {
                "user_id": self.current_session.user_id,
                "username": self.current_session.username,
                "login_time": self.current_session.login_time.isoformat(),
                "last_activity": self.current_session.last_activity.isoformat()
            }
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
    
    def _load_session(self):
        import json
        from pathlib import Path
        
        session_file = Path("session.json")
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                self.current_session = Session(
                    user_id=session_data["user_id"],
                    username=session_data["username"],
                    login_time=datetime.fromisoformat(session_data["login_time"]),
                    last_activity=datetime.fromisoformat(session_data["last_activity"])
                )
            except (json.JSONDecodeError, KeyError):
                self.current_session = None
                if session_file.exists():
                    session_file.unlink()
    
    def logout(self) -> None:
        if self.current_session:
            self.current_session = None
        
        import os
        if os.path.exists("session.json"):
            os.remove("session.json")
    
    def check_authentication(self) -> None:
        if not self.is_authenticated:
            raise AuthenticationError("Сначала выполните вход в систему")
    
    @log_action(verbose=True)
    def register_user(self, username: str, password: str) -> User:
        if not username or not username.strip():
            raise ValidationError("username", "Имя пользователя не может быть пустым")
        
        if len(password) < settings.password_min_length:
            raise ValidationError(
                "password", 
                f"Пароль должен быть не короче {settings.password_min_length} символов"
            )
        
        if db.username_exists(username):
            raise ValidationError("username", f"Имя пользователя '{username}' уже занято")
        
        user_id = db.get_next_user_id()
        
        user = User(
            user_id=user_id,
            username=username,
            password=password
        )
        
        db.save_user(user)
        
        portfolio = Portfolio(user_id=user_id)
        db.save_portfolio(portfolio)
        
        return user
    
    @log_action(verbose=True)
    def login(self, username: str, password: str) -> Session:
        user = db.get_user_by_username(username)
        if not user:
            raise AuthenticationError(f"Пользователь '{username}' не найден")
        
        if not user.verify_password(password):
            raise AuthenticationError("Неверный пароль")
        
        now = datetime.now()
        self.current_session = Session(
            user_id=user.user_id,
            username=user.username,
            login_time=now,
            last_activity=now
        )
        
        self._save_session()
        return self.current_session
    
    @log_action()
    def get_user_portfolio(self, user_id: Optional[int] = None) -> Portfolio:
        if user_id is None:
            self.check_authentication()
            user_id = self.current_session.user_id
        
        return db.get_portfolio(user_id)
    
    @log_action(verbose=True)
    def get_portfolio_info(self, base_currency: str = "USD") -> str:
        self.check_authentication()
        
        portfolio = db.get_portfolio(self.current_session.user_id)
        return portfolio.get_portfolio_info(base_currency)
    
    @log_action()
    def get_wallet_balance(self, currency_code: str) -> float:
        self.check_authentication()
        
        portfolio = db.get_portfolio(self.current_session.user_id)
        wallet = portfolio.get_wallet(currency_code)
        
        if wallet:
            return wallet.balance
        return 0.0
    
    @log_action(verbose=True)
    def buy_currency(self, currency_code: str, amount: float) -> Dict[str, Any]:
        self.check_authentication()
        
        if amount <= 0:
            raise ValidationError("amount", "Количество должно быть положительным")
        
        currency_code = currency_code.upper()
        
        portfolio = db.get_portfolio(self.current_session.user_id)
        
        rate = settings.get_default_exchange_rate(currency_code, "USD")
        if not rate:
            reverse_rate = settings.get_default_exchange_rate("USD", currency_code)
            if reverse_rate:
                rate = 1 / reverse_rate
            else:
                raise CurrencyNotFoundError(currency_code)
        
        cost_usd = amount * rate if currency_code != "USD" else amount
        
        if currency_code != "USD":
            usd_wallet = portfolio.get_wallet("USD")
            if not usd_wallet or usd_wallet.balance < cost_usd:
                available = usd_wallet.balance if usd_wallet else 0.0
                raise InsufficientFundsError(
                    available=available,
                    required=cost_usd,
                    code="USD"
                )
            
            usd_wallet.withdraw(cost_usd)
        
        wallet = portfolio.add_currency(currency_code)
        wallet.deposit(amount)
        
        db.save_portfolio(portfolio)
        
        return {
            "success": True,
            "currency": currency_code,
            "amount": amount,
            "rate": rate,
            "cost_usd": cost_usd,
            "new_balance": wallet.balance,
            "message": f"Покупка выполнена: {amount:.4f} {currency_code} за {cost_usd:.2f} USD"
        }
    
    @log_action(verbose=True)
    def sell_currency(self, currency_code: str, amount: float) -> Dict[str, Any]:
        self.check_authentication()
        
        if amount <= 0:
            raise ValidationError("amount", "Количество должно быть положительным")
        
        currency_code = currency_code.upper()
        
        portfolio = db.get_portfolio(self.current_session.user_id)
        
        wallet = portfolio.get_wallet(currency_code)
        if not wallet:
            raise CurrencyNotFoundError(
                f"У вас нет кошелька '{currency_code}'. "
                f"Добавьте валюту: она создаётся автоматически при первой покупке."
            )
        
        if wallet.balance < amount:
            raise InsufficientFundsError(
                available=wallet.balance,
                required=amount,
                code=currency_code
            )
        
        rate = settings.get_default_exchange_rate(currency_code, "USD")
        if not rate:
            reverse_rate = settings.get_default_exchange_rate("USD", currency_code)
            if reverse_rate:
                rate = 1 / reverse_rate
            else:
                raise CurrencyNotFoundError(currency_code)
        
        revenue_usd = amount * rate if currency_code != "USD" else amount
        
        wallet.withdraw(amount)
        
        if currency_code != "USD":
            usd_wallet = portfolio.add_currency("USD")
            usd_wallet.deposit(revenue_usd)
        
        db.save_portfolio(portfolio)
        
        return {
            "success": True,
            "currency": currency_code,
            "amount": amount,
            "rate": rate,
            "revenue_usd": revenue_usd,
            "new_balance": wallet.balance,
            "message": f"Продажа выполнена: {amount:.4f} {currency_code} за {revenue_usd:.2f} USD"
        }
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Dict[str, Any]:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Пытаемся получить курс из базы
        rate = db.get_exchange_rate(from_currency, to_currency)
        
        # Если курс не найден или устарел
        if rate is None or not db.is_rate_fresh():
            # Пытаемся получить обратный курс
            reverse_rate = db.get_exchange_rate(to_currency, from_currency)
            if reverse_rate and reverse_rate != 0:
                rate = 1 / reverse_rate
                source = "reverse_calculation"
            else:
                # Используем дефолтные курсы
                rate = settings.get_default_exchange_rate(from_currency, to_currency)
                if not rate:
                    raise CurrencyNotFoundError(f"{from_currency} или {to_currency}")
                source = "default"
            
            timestamp = datetime.now().isoformat()
        else:
            # Берем данные из кеша
            rates = db.get_exchange_rates()
            pair_key = f"{from_currency}_{to_currency}"
            pair_data = rates["pairs"].get(pair_key, {})
            source = pair_data.get("source", "cache")
            timestamp = pair_data.get("updated_at", "unknown")
        
        return {
            "from": from_currency,
            "to": to_currency,
            "rate": rate,
            "source": source,
            "updated_at": timestamp
        }
    
    def validate_currency_code(self, currency_code: str) -> bool:
        return settings.is_currency_supported(currency_code)
    
    def get_supported_currencies(self) -> list:
        return settings.get("supported_currencies", [])


use_cases = UseCases()
