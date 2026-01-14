import requests
from typing import Dict, Any
from datetime import datetime
from ..core.exceptions import ApiRequestError
from .config import config


class BaseApiClient:
    def fetch_rates(self) -> Dict[str, Any]:
        raise NotImplementedError
    
    def _make_request(self, url: str, params: dict = None) -> Dict[str, Any]:
        try:
            print(f"DEBUG: Request to {url}")
            response = requests.get(
                url, 
                params=params, 
                timeout=config.REQUEST_TIMEOUT,
                headers={
                    "User-Agent": "ValutatradeHub/1.0",
                    "Accept": "application/json"
                }
            )
            print(f"DEBUG: Status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"DEBUG: Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return data
            
        except requests.exceptions.Timeout:
            print("DEBUG: Timeout error")
            raise ApiRequestError("Таймаут запроса")
        except requests.exceptions.HTTPError as e:
            print(f"DEBUG: HTTP error: {e.response.status_code}")
            print(f"DEBUG: Response text: {e.response.text[:200]}")
            raise ApiRequestError(f"HTTP ошибка {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"DEBUG: Request error: {str(e)}")
            raise ApiRequestError(f"Ошибка запроса: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON decode error: {str(e)}")
            raise ApiRequestError(f"Ошибка парсинга JSON")

class CoinGeckoClient(BaseApiClient):
    def fetch_rates(self) -> Dict[str, Any]:
        url = config.COINGECKO_API_URL
        ids = ",".join(config.CRYPTO_ID_MAP.values())
        
        try:
            data = self._make_request(url, {
                "ids": ids,
                "vs_currencies": "usd"
            })
            
            rates = {}
            timestamp = datetime.now().isoformat()
            
            for crypto_code, gecko_id in config.CRYPTO_ID_MAP.items():
                if gecko_id in data:
                    usd_rate = data[gecko_id].get("usd")
                    if usd_rate:
                        pair_key = f"{crypto_code}_USD"
                        rates[pair_key] = {
                            "rate": usd_rate,
                            "updated_at": timestamp,
                            "source": "coingecko"
                        }
            
            return {
                "success": len(rates) > 0,
                "rates": rates,
                "timestamp": timestamp,
                "source": "coingecko"
            }
        except ApiRequestError as e:
            raise
        except Exception as e:
            raise ApiRequestError(f"CoinGecko: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    def fetch_rates(self) -> Dict[str, Any]:
        url = f"{config.EXCHANGERATE_API_URL}/{config.EXCHANGERATE_API_KEY}/latest/{config.BASE_CURRENCY}"

        try:
            data = self._make_request(url)

            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown")
                raise ApiRequestError(f"ExchangeRate-API: {error_type}")

            rates = {}
            timestamp = datetime.now().isoformat()

            # API возвращает: 1 BASE_CURRENCY = X target_currency
            # Например: 1 USD = 78.829 RUB
            exchange_rates = data.get("conversion_rates", {})

            for target_currency, rate in exchange_rates.items():
                # Формат: USD_RUB (1 USD = X RUB)
                pair_key = f"{config.BASE_CURRENCY}_{target_currency}"
                rates[pair_key] = {
                    "rate": rate,  # 1 USD = X target_currency
                    "updated_at": timestamp,
                    "source": "exchangerate-api",
                    "from": config.BASE_CURRENCY,
                    "to": target_currency
                }
                
                # Обратный курс: RUB_USD (1 RUB = X USD)
                if rate != 0:
                    reverse_pair_key = f"{target_currency}_{config.BASE_CURRENCY}"
                    rates[reverse_pair_key] = {
                        "rate": 1 / rate,  # 1 target_currency = X USD
                        "updated_at": timestamp,
                        "source": "exchangerate-api",
                        "from": target_currency,
                        "to": config.BASE_CURRENCY
                    }

            return {
                "success": len(rates) > 0,
                "rates": rates,
                "timestamp": timestamp,
                "source": "exchangerate-api",
                "base_currency": config.BASE_CURRENCY
            }

        except Exception as e:
            raise ApiRequestError(f"ExchangeRate-API: {str(e)}")
