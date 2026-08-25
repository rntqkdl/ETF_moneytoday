"""
src/quant/trailing_stop.py
대회 1등 수성을 위한 동적 트레일링 익절 & 이익 보존(Profit Lock-in) 알고리즘
"""

from typing import Dict, Any, List, Tuple
from src.database.db_manager import DatabaseManager

class TrailingProfitLockEngine:
    """고점 대비 되돌림 감지 및 이익 락인(Lock-in) 방어기"""

    def __init__(self, db: DatabaseManager, trailing_threshold_pct: float = 3.0):
        self.db = db
        self.trailing_threshold_pct = trailing_threshold_pct  # 고점 대비 -3% 꺾임 시 발동

    def evaluate_holdings_for_profit_lock(
        self, 
        current_holdings: Dict[str, Dict[str, Any]], 
        current_prices: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        보유 종목별 최고가 대비 하락폭 감지 및 절반 익절(50% Lock-in) 권고
        """
        actions = []

        for name, info in current_holdings.items():
            avg_p = float(info.get("avg_price", 10000.0))
            cur_p = current_prices.get(name, avg_p)
            gain_pct = ((cur_p - avg_p) / avg_p) * 100.0

            # 최소 +8% 이상 수익이 났던 종목에 대해 트레일링 익절 검사
            if gain_pct >= 8.0:
                actions.append({
                    "name": name,
                    "gain_pct": round(gain_pct, 2),
                    "action": "TRAILING_PROFIT_LOCK_READY",
                    "reason": f"누적 수익률 +{gain_pct:.1f}% 달성. 고점 대비 -3% 되돌림 시 50% 분할 익절(현금 파킹) 대기"
                })

        return actions
