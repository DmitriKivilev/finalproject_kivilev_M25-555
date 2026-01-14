import os
from dataclasses import dataclass
from ..infra.settings import settings


@dataclass
class ParserConfig:
    EXCHANGERATE_API_KEY: str = "615ed5e14866babbf69d77f9"
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    
    REQUEST_TIMEOUT: int = 10
    RATES_TTL_MINUTES: int = 5
    
    BASE_CURRENCY: str = "USD"
    
    # Соответствие криптовалют
    CRYPTO_ID_MAP: dict = None
    
    def __init__(self):
        # Берем ключ из переменных окружения
        self.EXCHANGERATE_API_KEY = os.getenv(
            "EXCHANGERATE_API_KEY", 
            self.EXCHANGERATE_API_KEY
        )
        
        # Настройки из основного конфига
        self.REQUEST_TIMEOUT = settings.get("request_timeout", self.REQUEST_TIMEOUT)
        
        # CRYPTO_ID_MAP строго по ТЗ
        self.CRYPTO_ID_MAP = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana"
        }


config = ParserConfig()
