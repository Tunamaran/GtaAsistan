# history.py
"""Son görülen araçların geçmişini tutan modül."""
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class VehicleHistory:
    """RAM'de son görülen araçların geçmişini tutar (dosyaya yazmaz)."""
    
    MAX_HISTORY = 50
    
    def __init__(self):
        self._history: List[Dict] = []  # [{timestamp, name, data}, ...]
        self._daily_count = 0
        self._daily_date = datetime.now().date()
        self._seen_counts: Dict[str, int] = {}  # {name: count}
    
    def add(self, vehicle_name: str, vehicle_data: dict) -> None:
        """Yeni araç tespiti ekler."""
        now = datetime.now()
        
        # Gün değiştiyse sayacı sıfırla
        if now.date() != self._daily_date:
            self._daily_count = 0
            self._daily_date = now.date()
        
        # Aynı araç art arda eklenmesin
        if self._history and self._history[0]["name"] == vehicle_name:
            return
        
        entry = {
            "timestamp": now,
            "name": vehicle_name,
            "data": vehicle_data,
            "time_str": now.strftime("%H:%M:%S")
        }
        
        self._history.insert(0, entry)  # Başa ekle (en yeni ilk)
        self._daily_count += 1
        self._seen_counts[vehicle_name] = self._seen_counts.get(vehicle_name, 0) + 1
        
        # Limit aşılırsa en eskiyi sil
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop()
    
    def get_recent(self, limit: int = 20) -> List[Dict]:
        """Son N kaydı döndürür."""
        return self._history[:limit]
    
    def get_stats(self) -> Dict:
        """Geçmiş istatistiklerini döndürür."""
        if not self._history:
            return {
                "total": 0,
                "daily": 0,
                "unique": 0,
                "most_seen": None,
                "most_seen_count": 0
            }
        
        most_seen = max(self._seen_counts, key=self._seen_counts.get) if self._seen_counts else None
        most_seen_count = self._seen_counts.get(most_seen, 0) if most_seen else 0
        
        return {
            "total": len(self._history),
            "daily": self._daily_count,
            "unique": len(self._seen_counts),
            "most_seen": most_seen,
            "most_seen_count": most_seen_count
        }
    
    def clear(self) -> None:
        """Geçmişi temizler."""
        self._history.clear()
        self._seen_counts.clear()
        self._daily_count = 0
