import json
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsLoader:
    """Singleton класс для управления настройками приложения."""
    
    _instance: Optional['SettingsLoader'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'SettingsLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if SettingsLoader._initialized:
            return
        
        self._settings = {
            "data_dir": "data",
            "users_file": "users.json",
            "portfolios_file": "portfolios.json",
            "rates_file": "rates.json",
            "exchange_rates_file": "exchange_rates.json",
            "default_base_currency": "USD",
            "supported_currencies": ["USD", "EUR", "BTC", "ETH", "RUB"],
            "rates_ttl_seconds": 300,
            "default_exchange_rates": {
                "BTC_USD": 59337.21,
                "EUR_USD": 1.0786,
                "RUB_USD": 0.01016,
                "ETH_USD": 3720.00,
                "USD_USD": 1.0,
            },
            "password_min_length": 4,
            "session_timeout_minutes": 30,
            "log_dir": "logs",
            "log_level": "INFO",
            "coingecko_url": "https://api.coingecko.com/api/v3/simple/price",
            "exchangerate_api_url": "https://v6.exchangerate-api.com/v6",
            "request_timeout": 10,
        }
        
        self._load_external_config()
        SettingsLoader._initialized = True
    
    def _load_external_config(self) -> None:
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    external_config = json.load(f)
                    self._settings.update(external_config)
            except (json.JSONDecodeError, Exception):
                pass
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value
    
    def reload(self) -> None:
        self._load_external_config()
    
    def get_path(self, file_key: str) -> Path:
        data_dir = Path(self._settings["data_dir"])
        filename = self._settings.get(file_key)
        
        if not filename:
            raise KeyError(f"Ключ файла '{file_key}' не найден в настройках")
        
        data_dir.mkdir(exist_ok=True)
        return data_dir / filename
    
    def get_users_file_path(self) -> Path:
        return self.get_path("users_file")
    
    def get_portfolios_file_path(self) -> Path:
        return self.get_path("portfolios_file")
    
    def get_rates_file_path(self) -> Path:
        return self.get_path("rates_file")
    
    def get_exchange_rates_file_path(self) -> Path:
        return self.get_path("exchange_rates_file")
    
    def get_log_dir_path(self) -> Path:
        log_dir = Path(self._settings["log_dir"])
        log_dir.mkdir(exist_ok=True)
        return log_dir
    
    def is_currency_supported(self, currency_code: str) -> bool:
        supported = self._settings.get("supported_currencies", [])
        return currency_code.upper() in supported
    
    def get_default_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        rates = self._settings.get("default_exchange_rates", {})
        rate_key = f"{from_currency}_{to_currency}"
        return rates.get(rate_key)
    
    @property
    def rates_ttl(self) -> int:
        return self._settings.get("rates_ttl_seconds", 300)
    
    @property
    def default_base_currency(self) -> str:
        return self._settings.get("default_base_currency", "USD")
    
    @property
    def password_min_length(self) -> int:
        return self._settings.get("password_min_length", 4)
    
    @property
    def all_settings(self) -> Dict[str, Any]:
        return self._settings.copy()


settings = SettingsLoader()
