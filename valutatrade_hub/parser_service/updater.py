from typing import List, Dict, Any
from datetime import datetime
from ..logging_config import logger
from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .storage import RatesStorage
from .config import config


class RatesUpdater:
    def __init__(self):
        self.clients = [
            CoinGeckoClient(),
            ExchangeRateApiClient()
        ]
        self.storage = RatesStorage()
    
    def run_update(self) -> Dict[str, Any]:
        logger.info("Starting rates update")
        
        all_rates = []
        errors = []
        
        for client in self.clients:
            try:
                rates_data = client.fetch_rates()
                if rates_data["success"]:
                    all_rates.append(rates_data)
                    logger.info(f"Got rates from {client.__class__.__name__}")
                else:
                    errors.append(f"{client.__class__.__name__}: No data")
            except Exception as e:
                errors.append(f"{client.__class__.__name__}: {str(e)}")
                logger.error(f"Error from {client.__class__.__name__}: {e}")
        
        if all_rates:
            merged = self.storage.merge_rates(all_rates)
            self.storage.save_rates(merged)
            
            return {
                "success": True,
                "message": f"Updated {len(merged['pairs'])} rates",
                "pairs_count": len(merged['pairs']),
                "timestamp": merged['last_refresh'],
                "errors": errors if errors else None
            }
        else:
            return {
                "success": False,
                "message": "Failed to get rates from any source",
                "errors": errors
            }
