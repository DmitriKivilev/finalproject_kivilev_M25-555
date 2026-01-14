import hashlib
import secrets
from datetime import datetime
from typing import Optional


class User:
    """Класс пользователя системы."""
    
    def __init__(
        self, 
        user_id: int, 
        username: str, 
        password: str,
        salt: Optional[str] = None,
        registration_date: Optional[datetime] = None
    ):
        self._user_id = user_id
        self.username = username
        self._salt = salt or secrets.token_hex(8)
        self._hashed_password = self._hash_password(password, self._salt)
        self._registration_date = registration_date or datetime.now()
    
    @property
    def user_id(self) -> int:
        return self._user_id
    
    @property
    def username(self) -> str:
        return self._username
    
    @username.setter
    def username(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()
    
    @property
    def hashed_password(self) -> str:
        return self._hashed_password
    
    @property
    def salt(self) -> str:
        return self._salt
    
    @property
    def registration_date(self) -> datetime:
        return self._registration_date
    
    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        return self._hash_password(password, self._salt) == self._hashed_password
    
    def change_password(self, new_password: str) -> None:
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(new_password, self._salt)
    
    def get_user_info(self) -> str:
        return (f"ID: {self._user_id}, "
                f"Имя: {self._username}, "
                f"Зарегистрирован: {self._registration_date.strftime('%Y-%m-%d %H:%M')}")
    
    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        user = cls(
            user_id=data["user_id"],
            username=data["username"],
            password="",
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"])
        )
        user._hashed_password = data["hashed_password"]
        return user
    
    def __str__(self) -> str:
        return self.get_user_info()
    
    def __repr__(self) -> str:
        return f"User(id={self._user_id}, username='{self._username}')"


class Wallet:
    """Класс кошелька для одной конкретной валюты."""
    
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self.balance = balance
    
    @property
    def currency_code(self) -> str:
        return self._currency_code
    
    @currency_code.setter
    def currency_code(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Код валюты не может быть пустым")
        self._currency_code = value.strip().upper()
    
    @property
    def balance(self) -> float:
        return self._balance
    
    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)
    
    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance += amount
    
    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        
        if amount > self.balance:
            from .exceptions import InsufficientFundsError
            raise InsufficientFundsError(
                available=self.balance,
                required=amount,
                code=self.currency_code
            )
        
        self.balance -= amount
    
    def get_balance_info(self) -> str:
        return f"Кошелёк {self.currency_code}: {self.balance:.2f}"
    
    def to_dict(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self.balance
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )
    
    def __str__(self) -> str:
        return self.get_balance_info()
    
    def __repr__(self) -> str:
        return f"Wallet(currency='{self.currency_code}', balance={self.balance})"


class Portfolio:
    """Класс портфеля пользователя (управление всеми кошельками)."""
    
    def __init__(self, user_id: int, wallets: Optional[dict[str, Wallet]] = None):
        self._user_id = user_id
        self._wallets = wallets or {}
    
    @property
    def user_id(self) -> int:
        return self._user_id
    
    @property
    def wallets(self) -> dict[str, Wallet]:
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> Wallet:
        currency_code = currency_code.upper()
        
        if currency_code in self._wallets:
            return self._wallets[currency_code]
        
        wallet = Wallet(currency_code, initial_balance)
        self._wallets[currency_code] = wallet
        return wallet
    
    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        return self._wallets.get(currency_code.upper())
    
    def remove_currency(self, currency_code: str) -> bool:
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            del self._wallets[currency_code]
            return True
        return False
    
    def get_total_value(self, base_currency: str = "USD") -> float:
        exchange_rates = {
            "BTC_USD": 59337.21,
            "EUR_USD": 1.0786,
            "RUB_USD": 0.01016,
            "ETH_USD": 3720.00,
            "USD_USD": 1.0,
        }
        
        total_value = 0.0
        
        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total_value += wallet.balance
            else:
                rate_key = f"{currency_code}_{base_currency}"
                if rate_key in exchange_rates:
                    total_value += wallet.balance * exchange_rates[rate_key]
        
        return total_value
    
    def get_portfolio_info(self, base_currency: str = "USD") -> str:
        if not self._wallets:
            return f"Портфель пользователя {self._user_id} пуст"
        
        info_lines = [f"Портфель пользователя ID: {self._user_id}"]
        info_lines.append(f"Базовая валюта: {base_currency}")
        info_lines.append("-" * 40)
        
        total_value = 0.0
        exchange_rates = {
            "BTC_USD": 59337.21,
            "EUR_USD": 1.0786,
            "RUB_USD": 0.01016,
            "ETH_USD": 3720.00,
            "USD_USD": 1.0,
        }
        
        for currency_code, wallet in sorted(self._wallets.items()):
            wallet_value = wallet.balance
            
            if currency_code != base_currency:
                rate_key = f"{currency_code}_{base_currency}"
                if rate_key in exchange_rates:
                    wallet_value = wallet.balance * exchange_rates[rate_key]
                else:
                    wallet_value = 0.0
            
            total_value += wallet_value
            
            if currency_code == base_currency:
                info_lines.append(
                    f"{currency_code}: {wallet.balance:.2f} → {wallet_value:.2f} {base_currency}"
                )
            else:
                rate = exchange_rates.get(f"{currency_code}_{base_currency}", "N/A")
                info_lines.append(
                    f"{currency_code}: {wallet.balance:.2f} (курс: {rate}) → {wallet_value:.2f} {base_currency}"
                )
        
        info_lines.append("-" * 40)
        info_lines.append(f"ИТОГО: {total_value:.2f} {base_currency}")
        
        return "\n".join(info_lines)
    
    def to_dict(self) -> dict:
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()
        
        return {
            "user_id": self._user_id,
            "wallets": wallets_dict
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        wallets = {}
        for currency_code, wallet_data in data.get("wallets", {}).items():
            wallets[currency_code] = Wallet.from_dict(wallet_data)
        
        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )
    
    def __str__(self) -> str:
        return f"Portfolio(user_id={self._user_id}, wallets={len(self._wallets)})"
    
    def __repr__(self) -> str:
        return f"Portfolio(user_id={self._user_id}, wallets={list(self._wallets.keys())})"
