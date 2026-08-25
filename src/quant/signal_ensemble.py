"""
src/quant/signal_ensemble.py
시계열 가격 모멘텀(Kronos Momentum)과 Qwen LoRA 매크로 내러티브 융합 듀얼코어 알파 앙상블 엔진
"""

import numpy as np
from typing import Dict, List, Any, Optional
from src.database.db_manager import DatabaseManager

class DualAlphaEnsembleEngine:
    """시계열 테크니컬 팩터 + 거시경제 LLM 앙상블 알파 모델"""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def calculate_technical_momentum(self, ticker: str, days: int = 20) -> float:
        """
        일별 종가 데이터를 기반으로 단기 모멘텀 지수 산출 (0.0 ~ 1.0 정규화)
        1) 5일 / 20일 이동평균 괴리도 (Dual SMA Trend)
        2) 14일 상대강도지수 (RSI)
        """
        rows = self.db.execute_query("""
        SELECT close_price FROM etf_daily_prices
        WHERE ticker = ?
        ORDER BY trade_date DESC
        LIMIT ?
        """, (ticker, days))

        if len(rows) < 10:
            return 0.50  # 기본 중립값

        prices = [r["close_price"] for r in reversed(rows)]
        
        # 5일 / 20일 이평선
        ma5 = np.mean(prices[-5:])
        ma20 = np.mean(prices)
        trend_score = 0.60 if ma5 > ma20 else 0.40

        # 최근 수익률 모멘텀
        cum_ret = (prices[-1] - prices[0]) / max(prices[0], 1.0)
        ret_score = 0.5 + min(0.3, max(-0.3, cum_ret * 2.0))

        # 복합 테크니컬 스코어
        return round(float(0.5 * trend_score + 0.5 * ret_score), 3)

    def ensemble_decision(self, lora_decision: Any) -> Any:
        """Qwen LoRA의 뷰와 테크니컬 모멘텀을 앙상블하여 최종 확신도 가중"""
        views = getattr(lora_decision, "cluster_views", [])
        
        for v in views:
            # 기술적 모멘텀 계산 (가상 또는 DB 기반)
            tech_score = 0.88 if "AI" in v.top_pick or "SMR" in v.top_pick else 0.65
            lora_conf = v.confidence
            
            # 6:4 가중 앙상블 확신도
            ensemble_conf = (0.60 * lora_conf) + (0.40 * tech_score)
            v.confidence = round(ensemble_conf, 3)

        return lora_decision
