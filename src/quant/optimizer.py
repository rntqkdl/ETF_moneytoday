"""
src/quant/optimizer.py
머니투데이 ETF 투자왕 [연금형] 1등 우승을 위한 동적 직교성 비대칭 퀀트 자산배분기
(Dynamic Orthogonal Convexity Optimizer: 40/30/20/10 + 상관관계 분산 가드레일 탑재)
"""

from typing import Dict, Any, List
from src.database.models import QuantDecisionOutput, ClusterViewItem
from src.quant.harness import ComplianceHarness

class PortfolioOptimizer:
    """대회 우승을 위한 동적 직교성 비대칭 자산배분 엔진"""

    def __init__(self, harness: ComplianceHarness):
        self.harness = harness

    def calculate_weights(self, decision: QuantDecisionOutput) -> Dict[str, float]:
        """
        AI 거시 확신도(Confidence) 및 클러스터 간 상관관계(Orthogonality)를 반영한 최적 비중 산출
        """
        views = decision.cluster_views
        conf = decision.confidence_score

        if not views:
            # 기본 중립 배분
            raw_weights = {
                "KODEX 코리아밸류업": 0.30,
                "ACE 미국빅테크TOP7 Plus": 0.30,
                "TIGER CD금리투자KIS(합성)": 0.20,
                "ACE 미국달러SOFR금리(합성)": 0.20
            }
            return self.harness.validate_allocation(raw_weights)

        # 1. 클러스터별 중복 방지 (서로 다른 3대 독립 클러스터 추출)
        selected_views: List[ClusterViewItem] = []
        seen_clusters = set()

        # 기대수익률 높은 순 정렬
        sorted_views = sorted(views, key=lambda v: (v.expected_return * v.confidence), reverse=True)
        for v in sorted_views:
            if v.cluster_id not in seen_clusters:
                selected_views.append(v)
                seen_clusters.add(v.cluster_id)
            if len(selected_views) >= 3:
                break

        # 2. 거시 확신도에 따른 3단 동적 비대칭 배분
        raw_weights: Dict[str, float] = {}

        if conf >= 0.85:
            # 🔥 [1단계: 1등 탈환 공격 모드] (40% / 30% / 20% / 10%)
            # 1위 대장주 (40%), 2위 독립 섹터 (30%), 3위 서브 섹터 (20%), 안전 파킹 (10%)
            alloc_ratios = [0.40, 0.30, 0.20]
            for i, v in enumerate(selected_views):
                target_ratio = alloc_ratios[i] if i < len(alloc_ratios) else 0.10
                raw_weights[v.top_pick] = target_ratio
            
            # 현금/안전 파킹 10% 배정
            raw_weights["TIGER CD금리투자KIS(합성)"] = 0.05
            raw_weights["ACE 미국달러SOFR금리(합성)"] = 0.05

        elif conf >= 0.65:
            # ⚖️ [2단계: 중립 박스권 분산 모드] (25% / 25% / 25% / 25%)
            for v in selected_views:
                raw_weights[v.top_pick] = 0.25
            raw_weights["TIGER CD금리투자KIS(합성)"] = 0.125
            raw_weights["ACE 미국달러SOFR금리(합성)"] = 0.125

        else:
            # 🛡️ [3단계: 긴급 하방 방어 모드] (안전자산 65% + 방어주 35%)
            if selected_views:
                raw_weights[selected_views[0].top_pick] = 0.35
            raw_weights["ACE KRX금현물"] = 0.20
            raw_weights["TIGER CD금리투자KIS(합성)"] = 0.225
            raw_weights["ACE 미국달러SOFR금리(합성)"] = 0.225

        # 3. 비중 정규화 (합계 1.0)
        total_w = sum(raw_weights.values())
        if total_w > 0:
            for k in list(raw_weights.keys()):
                raw_weights[k] = round(raw_weights[k] / total_w, 4)

        # 4. 컴플라이언스 하네스 검증 (단일 종목 최대 40% 캡 및 연금 적격 ETF 확인)
        return self.harness.validate_allocation(raw_weights)
