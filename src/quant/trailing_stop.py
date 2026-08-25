"""
src/quant/trailing_stop.py
대회 1등 수성을 위한 계단식 래칫 익절(Stepwise Ratchet Profit Lock-in) 및 비상 서킷브레이커 탈출 엔진
"""

from typing import Dict, Any, List, Tuple
from src.database.db_manager import DatabaseManager

class TrailingProfitLockEngine:
    """계단식 이익 보존 및 급락 비상 탈출 방어기"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.hard_stop_loss_pct = -4.0   # 개별 종목 -4% 도달 시 2주 홀딩 무시하고 비상 탈출
        self.peak_drawdown_limit = -3.0  # 고점 대비 -3% 되돌림 시 발동

    def evaluate_holdings_for_profit_lock(
        self, 
        current_holdings: Dict[str, Dict[str, Any]], 
        current_prices: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        보유 종목별 비상 탈출 및 계단식 래칫(Ratchet) 익절 조치 권고 산출
        """
        actions = []

        for name, info in current_holdings.items():
            avg_p = float(info.get("avg_price", 10000.0))
            cur_p = current_prices.get(name, avg_p)
            gain_pct = ((cur_p - avg_p) / avg_p) * 100.0

            # 1. 🚨 [비상 서킷브레이커 손절] (-4.0% 급락 시 즉시 탈출)
            if gain_pct <= self.hard_stop_loss_pct:
                actions.append({
                    "name": name,
                    "gain_pct": round(gain_pct, 2),
                    "action": "EMERGENCY_CIRCUIT_BREAKER_EXIT",
                    "lock_ratio": 1.0,  # 100% 전량 매도
                    "reason": f"🚨 진입가 대비 {gain_pct:.1f}% 급락 감지! 2주 룰 무시 즉시 전량 매도 후 초단기 CD금리 대피"
                })
                continue

            # 2. 🔒 [계단식 래칫(Ratchet) 이익 락인]
            if gain_pct >= 20.0:
                # 3단계: +20% 이상 폭등 시 70% 비중 현금 락인 (1위 확정)
                actions.append({
                    "name": name,
                    "gain_pct": round(gain_pct, 2),
                    "action": "RATCHET_TIER_3_LOCK_70PCT",
                    "lock_ratio": 0.70,
                    "reason": f"🎉 누적 수익률 +{gain_pct:.1f}% 대폭등! 이익금 70%를 CD금리/SOFR로 락인하여 1위 수성"
                })
            elif gain_pct >= 15.0:
                # 2단계: +15% 이상 상승 시 50% 비중 현금 락인
                actions.append({
                    "name": name,
                    "gain_pct": round(gain_pct, 2),
                    "action": "RATCHET_TIER_2_LOCK_50PCT",
                    "lock_ratio": 0.50,
                    "reason": f"📈 누적 수익률 +{gain_pct:.1f}% 달성. 고점 대비 되돌림 방어를 위해 50% 비중 익절 락인"
                })
            elif gain_pct >= 10.0:
                # 1단계: +10% 이상 상승 시 30% 비중 현금 락인
                actions.append({
                    "name": name,
                    "gain_pct": round(gain_pct, 2),
                    "action": "RATCHET_TIER_1_LOCK_30PCT",
                    "lock_ratio": 0.30,
                    "reason": f"✨ 누적 수익률 +{gain_pct:.1f}% 돌파. 초기 수익 보존을 위해 30% 부분 익절"
                })

        return actions
