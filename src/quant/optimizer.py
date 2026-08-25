"""
src/quant/optimizer.py
Qwen LoRA 퀀트 뷰와 결합된 자산배분 및 리밸런싱 최적화기
"""

from typing import Dict, Any, List
from config.settings import settings
from src.database.models import QuantDecisionOutput
from src.quant.harness import ComplianceHarness

class PortfolioOptimizer:
    """확신도 가중 및 제약식 기반 포트폴리오 최적화기"""

    def __init__(self, harness: ComplianceHarness):
        self.harness = harness

    def calculate_weights(self, decision: QuantDecisionOutput) -> Dict[str, float]:
        """LoRA Decision 객체를 받아 하네스 검증을 통과한 최종 목표 비중 벡터 도출"""
        views = decision.cluster_views
        cash_ratio = max(decision.cash_park_ratio, settings.MIN_CASH_PARK_RATIO)
        equity_budget = max(0.0, 1.0 - cash_ratio)

        raw_weights = {}
        if views:
            per_stock_budget = equity_budget / len(views)
            for v in views:
                raw_weights[v.top_pick] = min(per_stock_budget, settings.MAX_SINGLE_ASSET_WEIGHT)

        allocated_equity = sum(raw_weights.values())
        rem_cash = max(0.0, 1.0 - allocated_equity)

        # 현금성 자산 (원화 CD 50% + 달러 SOFR 50%)
        raw_weights["TIGER CD금리투자KIS(합성)"] = rem_cash * 0.5
        raw_weights["ACE 미국달러SOFR금리(합성)"] = rem_cash * 0.5

        # 하네스 가드레일 최종 검증
        return self.harness.validate_allocation(raw_weights)
