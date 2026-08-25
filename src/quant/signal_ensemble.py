"""
src/quant/signal_ensemble.py
지수 가중 변동성(EWMA) 및 수치 안정화(Epsilon) 기반 샤프 모멘텀(Sharpe-Momentum) 듀얼 알파 엔진
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from src.database.db_manager import DatabaseManager

class DualAlphaEnsembleEngine:
    """EWMA 변동성 보정 샤프 모멘텀 및 클러스터 직교성 랭킹 엔진"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def calculate_ewma_volatility(self, returns_series: pd.Series, span: int = 10) -> float:
        """최근 이상 징후를 빠르게 반영하는 지수 가중 이동평균(EWMA) 연환산 변동성"""
        if len(returns_series) < 5:
            return 0.20
        ewma_var = returns_series.ewm(span=span).var().iloc[-1]
        return float(np.sqrt(ewma_var * 252.0))

    def calculate_robust_sharpe_momentum(self, prices_series: pd.Series) -> float:
        """
        수치 안정화(Epsilon=0.01) 적용 샤프 모멘텀 스코어:
        Score = Momentum_20D / (EWMA_Vol + 0.01)
        """
        if len(prices_series) < 20:
            return 0.0
        
        # 20일 모멘텀
        p_now = prices_series.iloc[-1]
        p_prev = prices_series.iloc[-20]
        mom_20d = (p_now - p_prev) / p_prev if p_prev > 0 else 0.0

        # EWMA 변동성
        daily_ret = prices_series.pct_change().dropna()
        ewma_vol = self.calculate_ewma_volatility(daily_ret, span=10)

        # 안정화된 샤프 모멘텀 스코어
        return float(mom_20d / (ewma_vol + 0.01))

    def rank_universe_etfs(self) -> List[Dict[str, Any]]:
        """전체 ETF 유니버스에 대한 샤프 모멘텀 랭킹 산출"""
        rows = self.db.execute_query("""
        SELECT ticker, trade_date, close_price 
        FROM etf_daily_prices 
        ORDER BY trade_date ASC
        """)
        if not rows:
            return []

        df = pd.DataFrame(rows)
        pivot = df.pivot(index="trade_date", columns="ticker", values="close_price").dropna(axis=1, thresh=30)

        scores = []
        for ticker in pivot.columns:
            series = pivot[ticker].dropna()
            score = self.calculate_robust_sharpe_momentum(series)
            last_p = float(series.iloc[-1])
            scores.append({
                "ticker": ticker,
                "sharpe_momentum_score": round(score, 4),
                "close_price": last_p
            })

        return sorted(scores, key=lambda x: x["sharpe_momentum_score"], reverse=True)
