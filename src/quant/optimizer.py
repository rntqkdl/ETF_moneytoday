"""
src/quant/optimizer.py
머니투데이 ETF 투자왕 [연금형] 1등 우승을 위한 동적 직교성 비대칭 퀀트 자산배분기
(Dynamic Orthogonal Convexity Optimizer: 40/30/20/10 + 직교 클러스터 자동 백필 탑재)
"""

from typing import Dict, Any, List
from src.database.models import QuantDecisionOutput, ClusterViewItem
from src.quant.harness import ComplianceHarness

class PortfolioOptimizer:
    """대회 우승을 위한 동적 직교성 비대칭 자산배분 엔진"""

    # 8대 클러스터별 1등 국가대표 기본 매핑
    BENCHMARK_LEADERS = {
        "C1_AI_SEMI": "KODEX 미국AI반도체TOP3플러스",
        "C2_AI_POWER": "TIGER 미국AI전력SMR",
        "C3_US_TECH": "ACE 미국빅테크TOP7 Plus",
        "C4_DEFENSE": "ACE K방산TOP5+",
        "C5_VALUE_UP": "SOL 금융지주플러스고배당",
        "C6_DIVIDEND": "SOL 미국배당다우존스",
        "C7_COMMODITY": "ACE KRX금현물",
        "C8_CASH_PARK": "TIGER CD금리투자KIS(합성)"
    }

    def __init__(self, harness: ComplianceHarness):
        self.harness = harness

    def calculate_weights(self, decision: QuantDecisionOutput) -> Dict[str, float]:
        """
        AI 거시 확신도(Confidence) 및 클러스터 간 상관관계(Orthogonality)를 반영한 최적 비중 산출
        """
        views = decision.cluster_views or []
        conf = decision.confidence_score

        # 1. 클러스터별 중복 방지 (서로 다른 3대 독립 클러스터 선별)
        selected_views: List[ClusterViewItem] = []
        seen_clusters = set()

        sorted_views = sorted(views, key=lambda v: (v.expected_return * v.confidence), reverse=True)
        for v in sorted_views:
            if v.cluster_id not in seen_clusters:
                selected_views.append(v)
                seen_clusters.add(v.cluster_id)
            if len(selected_views) >= 3:
                break

        # 부족한 슬롯을 독립적인 백마크 대표 ETF로 자동 백필 (상관관계 분산 보장)
        default_backup_clusters = ["C1_AI_SEMI", "C2_AI_POWER", "C3_US_TECH", "C4_DEFENSE", "C5_VALUE_UP"]
        for cid in default_backup_clusters:
            if len(selected_views) >= 3:
                break
            if cid not in seen_clusters:
                selected_views.append(ClusterViewItem(
                    cluster_id=cid,
                    expected_return=0.045,
                    confidence=0.85,
                    top_pick=self.BENCHMARK_LEADERS[cid]
                ))
                seen_clusters.add(cid)

        # 2. 거시 확신도에 따른 3단 동적 비대칭 배분
        raw_weights: Dict[str, float] = {}

        if conf >= 0.85:
            # 🔥 [1단계: 1등 탈환 공격 모드] (40% / 30% / 20% / 10%)
            raw_weights[selected_views[0].top_pick] = 0.40
            raw_weights[selected_views[1].top_pick] = 0.30
            raw_weights[selected_views[2].top_pick] = 0.20
            raw_weights["TIGER CD금리투자KIS(합성)"] = 0.10

        elif conf >= 0.65:
            # ⚖️ [2단계: 중립 박스권 분산 모드] (25% / 25% / 25% / 25%)
            raw_weights[selected_views[0].top_pick] = 0.25
            raw_weights[selected_views[1].top_pick] = 0.25
            raw_weights[selected_views[2].top_pick] = 0.25
            raw_weights["TIGER CD금리투자KIS(합성)"] = 0.25

        else:
            # 🛡️ [3단계: 긴급 하방 방어 모드] (안전자산 65% + 방어주 35%)
            raw_weights[selected_views[0].top_pick] = 0.35
            raw_weights["ACE KRX금현물"] = 0.20
            raw_weights["TIGER CD금리투자KIS(합성)"] = 0.45

        # 3. 비중 정규화 (합계 1.0)
        total_w = sum(raw_weights.values())
        if total_w > 0:
            for k in list(raw_weights.keys()):
                raw_weights[k] = round(raw_weights[k] / total_w, 4)

        # 4. 컴플라이언스 하네스 검증
        return self.harness.validate_allocation(raw_weights)
