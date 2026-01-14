import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .settings import settings
from ..core.models import User, Wallet, Portfolio


class DatabaseManager:
    """Singleton менеджер для работы с JSON-хранилищем."""
    
    _instance: Optional['DatabaseManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.RLock()
        self._initialized = True
    
    def _read_json_file(self, file_path: Path) -> Any:
        with self._lock:
            try:
                if not file_path.exists():
                    return []
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
            except json.JSONDecodeError as e:
                backup_path = file_path.with_suffix('.json.bak')
                if file_path.exists():
                    file_path.rename(backup_path)
                return []
    
    def _write_json_file(self, file_path: Path, data: Any) -> None:
        with self._lock:
            file_path.parent.mkdir(exist_ok=True)
            
            temp_path = file_path.with_suffix('.json.tmp')
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=self._json_serializer)
                
                temp_path.replace(file_path)
                
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise
    
    def _json_serializer(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def save_user(self, user: User) -> None:
        users_file = settings.get_users_file_path()
        users = self._read_json_file(users_file)
        
        user_dict = user.to_dict()
        user_found = False
        
        for i, existing_user in enumerate(users):
            if existing_user.get('user_id') == user.user_id:
                users[i] = user_dict
                user_found = True
                break
        
        if not user_found:
            users.append(user_dict)
        
        self._write_json_file(users_file, users)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        users_file = settings.get_users_file_path()
        users = self._read_json_file(users_file)
        
        for user_data in users:
            if user_data.get('user_id') == user_id:
                return User.from_dict(user_data)
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        users_file = settings.get_users_file_path()
        users = self._read_json_file(users_file)
        
        for user_data in users:
            if user_data.get('username') == username:
                return User.from_dict(user_data)
        
        return None
    
    def username_exists(self, username: str) -> bool:
        return self.get_user_by_username(username) is not None
    
    def get_all_users(self) -> List[User]:
        users_file = settings.get_users_file_path()
        users_data = self._read_json_file(users_file)
        
        return [User.from_dict(user_data) for user_data in users_data]
    
    def get_next_user_id(self) -> int:
        users = self.get_all_users()
        if not users:
            return 1
        
        max_id = max(user.user_id for user in users)
        return max_id + 1
    
    def save_portfolio(self, portfolio: Portfolio) -> None:
        portfolios_file = settings.get_portfolios_file_path()
        portfolios = self._read_json_file(portfolios_file)
        
        portfolio_dict = portfolio.to_dict()
        portfolio_found = False
        
        for i, existing_portfolio in enumerate(portfolios):
            if existing_portfolio.get('user_id') == portfolio.user_id:
                portfolios[i] = portfolio_dict
                portfolio_found = True
                break
        
        if not portfolio_found:
            portfolios.append(portfolio_dict)
        
        self._write_json_file(portfolios_file, portfolios)
    
    def get_portfolio(self, user_id: int) -> Portfolio:
        portfolios_file = settings.get_portfolios_file_path()
        portfolios = self._read_json_file(portfolios_file)
        
        for portfolio_data in portfolios:
            if portfolio_data.get('user_id') == user_id:
                return Portfolio.from_dict(portfolio_data)
        
        return Portfolio(user_id=user_id)
    
    def delete_portfolio(self, user_id: int) -> bool:
        portfolios_file = settings.get_portfolios_file_path()
        portfolios = self._read_json_file(portfolios_file)
        
        initial_length = len(portfolios)
        portfolios = [p for p in portfolios if p.get('user_id') != user_id]
        
        if len(portfolios) < initial_length:
            self._write_json_file(portfolios_file, portfolios)
            return True
        
        return False
    
    def save_exchange_rates(self, rates_data: Dict[str, Any]) -> None:
        rates_file = settings.get_rates_file_path()
        self._write_json_file(rates_file, rates_data)
    
    def get_exchange_rates(self) -> Dict[str, Any]:
        rates_file = settings.get_rates_file_path()
        rates = self._read_json_file(rates_file)
        
        if not rates:
            return {
                "last_refresh": datetime.now().isoformat(),
                "pairs": {},
                "source": "default"
            }
        
        return rates
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        rates = self.get_exchange_rates()
        pairs = rates.get("pairs", {})
        
        pair_key = f"{from_currency}_{to_currency}"
        pair_data = pairs.get(pair_key)
        
        if pair_data:
            return pair_data.get("rate")
        
        return None
    
    def is_rate_fresh(self, max_age_seconds: Optional[int] = None) -> bool:
        if max_age_seconds is None:
            max_age_seconds = settings.rates_ttl
        
        rates = self.get_exchange_rates()
        last_refresh_str = rates.get("last_refresh")
        
        if not last_refresh_str:
            return False
        
        try:
            last_refresh = datetime.fromisoformat(last_refresh_str)
            age_seconds = (datetime.now() - last_refresh).total_seconds()
            return age_seconds <= max_age_seconds
        except (ValueError, TypeError):
            return False
    
    def initialize_database(self) -> None:
        files_to_init = [
            settings.get_users_file_path(),
            settings.get_portfolios_file_path(),
            settings.get_rates_file_path(),
            settings.get_exchange_rates_file_path(),
        ]
        
        for file_path in files_to_init:
            if not file_path.exists():
                if "users" in file_path.name:
                    self._write_json_file(file_path, [])
                elif "portfolios" in file_path.name:
                    self._write_json_file(file_path, [])
                elif "rates" in file_path.name:
                    self._write_json_file(file_path, {
                        "last_refresh": datetime.now().isoformat(),
                        "pairs": {},
                        "source": "system"
                    })
                elif "exchange_rates" in file_path.name:
                    self._write_json_file(file_path, [])
    
    def backup_database(self) -> Path:
        import shutil
        
        backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        files_to_backup = [
            settings.get_users_file_path(),
            settings.get_portfolios_file_path(),
            settings.get_rates_file_path(),
            settings.get_exchange_rates_file_path(),
        ]
        
        for src_file in files_to_backup:
            if src_file.exists():
                dst_file = backup_dir / src_file.name
                shutil.copy2(src_file, dst_file)
        
        return backup_dir


db = DatabaseManager()
