import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from ..infra.settings import settings


class RatesStorage:
    def __init__(self):
        self.rates_file = settings.get_rates_file_path()
        self.history_file = settings.get_exchange_rates_file_path()
    
    def save_rates(self, rates_data: Dict[str, Any]) -> None:
        # Атомарная запись через временный файл
        temp_fd, temp_path = tempfile.mkstemp(suffix='.json', dir=self.rates_file.parent)
        
        try:
            with open(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(rates_data, f, indent=2, ensure_ascii=False)
            
            Path(temp_path).replace(self.rates_file)
            
            # Добавляем в историю
            self._add_to_history(rates_data)
            
        except Exception:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise
    
    def _add_to_history(self, rates_data: Dict[str, Any]) -> None:
        try:
            history = self._read_json_file(self.history_file) or []
            
            history.append({
                "timestamp": datetime.now().isoformat(),
                "data": rates_data
            })
            
            # Ограничиваем историю
            if len(history) > 1000:
                history = history[-1000:]
            
            self._write_json_file(self.history_file, history)
        except Exception:
            pass  # История - вторичная функция
    
    def load_rates(self) -> Dict[str, Any]:
        data = self._read_json_file(self.rates_file)
        if data:
            return data
        
        return {
            "last_refresh": datetime.now().isoformat(),
            "pairs": {},
            "source": "system"
        }
    
    def merge_rates(self, sources_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        merged = {}
        
        for source_data in sources_data:
            if not source_data.get("success"):
                continue
                
            for pair_key, pair_info in source_data.get("rates", {}).items():
                merged[pair_key] = pair_info
        
        return {
            "last_refresh": datetime.now().isoformat(),
            "pairs": merged,
            "source": "merged"
        }
    
    def _read_json_file(self, file_path: Path) -> Any:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _write_json_file(self, file_path: Path, data: Any) -> None:
        file_path.parent.mkdir(exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
