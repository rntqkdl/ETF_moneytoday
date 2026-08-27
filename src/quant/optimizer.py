"""
src/quant/optimizer.py
머니투데이 ETF 투자왕 [연금형] 1등 우승을 위한 실시간 20일 샤프 모멘텀 동적 유니버스 퀀트 최적화기
(Dynamic Cross-Sectional Sharpe-Momentum Optimizer: 896개 전종목 실시간 랭킹 + 직교 분산)
"""

from typing import Dict, Any, List, Optional
import pandas as pd
from src.database.models import QuantDecisionOutput, ClusterViewItem
from src.quant.harness import ComplianceHarness
from src.database.db_manager import DatabaseManager

class PortfolioOptimizer:
    """전종목 시계열 실측 샤프 모멘텀 기반 동적 40/30/20/10 자산배분 엔진"""

    def __init__(self, harness: ComplianceHarness, db: Optional[DatabaseManager] = None):
        self.harness = harness
        self.db = db or DatabaseManager()

    def get_dynamic_momentum_leaders(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        896개 전종목의 최근 20영업일 실측 데이터를 분석하여 샤프 모멘텀 상위 1등~5등 종목을 동적 추출
        """
        try:
            rows = self.db.execute_query("""
                SELECT p.ticker, m.name, m.cluster_name, p.trade_date, p.close_price, p.volume
                FROM etf_daily_prices p
                JOIN etf_master m ON p.ticker = m.ticker
                WHERE m.name NOT LIKE '%선물%' 
                  AND m.name NOT LIKE '%레버리지%' 
                  AND m.name NOT LIKE '%인버스%'
                ORDER BY p.ticker, p.trade_date
            """)
            if not rows:
                return []

            df = pd.DataFrame(rows)
            df['close_price'] = df['close_price'].astype(float)
            df['volume'] = df['volume'].astype(float)
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            ranked = []
            for ticker, grp in df.groupby('ticker'):
                grp = grp.sort_values('trade_date')
                if len(grp) >= 20:
                    name = grp['name'].iloc[-1]
                    cname = grp['cluster_name'].iloc[-1]
                    p_latest = grp['close_price'].iloc[-1]
                    p_20d_ago = grp['close_price'].iloc[-20]
                    avg_vol = grp['volume'].tail(5).mean()

                    ret_20d = (p_latest - p_20d_ago) / p_20d_ago
                    daily_ret = grp['close_price'].pct_change().dropna()
                    vol_ann = daily_ret.std() * (252**0.5)
                    sharpe = (daily_ret.mean() * 252 - 0.035) / (vol_ann + 0.01)

                    ranked.append({
                        "ticker": ticker,
                        "name": name,
                        "cluster": cname,
                        "ret_20d": ret_20d,
                        "volatility": vol_ann,
                        "sharpe": sharpe,
                        "latest_price": p_latest,
                        "avg_volume": avg_vol
                    })

            ranked_df = pd.DataFrame(ranked).sort_values("sharpe", ascending=False)
            
            unique_leaders = []
            seen_clusters = set()
            for _, row in ranked_df.iterrows():
                if "CD금리" in row["name"] or "SOFR" in row["name"]:
                    continue
                if row["cluster"] not in seen_clusters:
                    unique_leaders.append(row.to_dict())
                    seen_clusters.add(row["cluster"])
                if len(unique_leaders) >= top_n:
                    break

            return unique_leaders

        except Exception as e:
            print(f"⚠️ [동적 모멘텀 랭킹 실패]: {e}")
            return []

    def calculate_weights(self, decision: QuantDecisionOutput) -> Dict[str, float]:
        """
        AI 거시 뷰 + 896개 전종목 실측 시계열 모멘텀을 결합한 40/30/20/10 최적 포트폴리오 산출
        """
        leaders = self.get_dynamic_momentum_leaders(top_n=4)
        conf = decision.confidence_score

        # 1. 탑픽 선정 (AI가 명시한 뷰 우선, 없으면 실측 모멘텀 랭킹 1~3위 자동 적용)
        if decision.cluster_views and len(decision.cluster_views) >= 3:
            p1 = decision.cluster_views[0].top_pick
            p2 = decision.cluster_views[1].top_pick
            p3 = decision.cluster_views[2].top_pick
        elif len(leaders) >= 3:
            p1 = leaders[0]["name"]
            p2 = leaders[1]["name"]
            p3 = leaders[2]["name"]
        else:
            p1 = "SOL 금융지주플러스고배당"
            p2 = "KODEX 반도체"
            p3 = "ACE KRX금현물"

        cash = "TIGER CD금리투자KIS(합성)"
        raw_weights: Dict[str, float] = {}

        # 2. 확신도에 따른 40/30/20/10 틸팅
        if conf >= 0.85:
            # 🔥 [1등 탈환 공격 모드] 1위(40%), 2위(30%), 3위(20%), 안전 현금(10%)
            raw_weights[p1] = 0.40
            raw_weights[p2] = 0.30
            raw_weights[p3] = 0.20
            raw_weights[cash] = 0.10
        elif conf >= 0.65:
            # ⚖️ [중립 분산 모드] 25% / 25% / 25% / 25%
            raw_weights[p1] = 0.25
            raw_weights[p2] = 0.25
            raw_weights[p3] = 0.25
            raw_weights[cash] = 0.25
        else:
            # 🛡️ [하방 방어 모드] 안전자산 65% + 방어주 35%
            raw_weights[p1] = 0.35
            raw_weights["ACE KRX금현물"] = 0.20
            raw_weights[cash] = 0.45

        # 정규화
        total_w = sum(raw_weights.values())
        if total_w > 0:
            for k in list(raw_weights.keys()):
                raw_weights[k] = round(raw_weights[k] / total_w, 4)

        return self.harness.validate_allocation(raw_weights)
