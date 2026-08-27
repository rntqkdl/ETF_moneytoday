"""
src/quant/optimizer.py
머니투데이 ETF 투자왕 [연금형] 1등 우승을 위한 국면 적응형(Regime-Adaptive) 40/30/20/10 퀀트 자산배분기
"""

from typing import Dict, Any, List
from src.database.models import QuantDecisionOutput, ClusterViewItem
from src.quant.harness import ComplianceHarness

class PortfolioOptimizer:
    """대회 우승을 위한 거시 국면 적응형 비대칭 자산배분 엔진"""

    # 국면별 4대 황금 포트폴리오 프리셋
    REGIME_PRESETS = {
        "AI_SUPER": {
            "p1": "KODEX 미국AI반도체TOP3플러스",
            "p2": "TIGER 미국AI전력SMR",
            "p3": "ACE 미국빅테크TOP7 Plus",
            "cash": "TIGER CD금리투자KIS(합성)"
        },
        "VALUE_UP": {
            "p1": "SOL 금융지주플러스고배당",
            "p2": "KODEX 코리아밸류업",
            "p3": "ACE K방산TOP5+",
            "cash": "TIGER CD금리투자KIS(합성)"
        },
        "DEFENSIVE": {
            "p1": "ACE KRX금현물",
            "p2": "SOL 미국배당다우존스",
            "p3": "ACE 미국빅테크TOP7 Plus",
            "cash": "TIGER CD금리투자KIS(합성)"
        }
    }

    def __init__(self, harness: ComplianceHarness):
        self.harness = harness

    def calculate_weights(self, decision: QuantDecisionOutput) -> Dict[str, float]:
        """
        AI 거시 국면(regime) 및 확신도(confidence)를 정확히 반영한 40/30/20/10 비중 산출
        """
        regime = decision.regime or "AI_Hardware_Supercycle"
        conf = decision.confidence_score
        views = decision.cluster_views or []

        # 1. 국면 프리셋 매핑
        if "ValueUp" in regime or "밸류업" in regime or "금융" in regime:
            preset = self.REGIME_PRESETS["VALUE_UP"]
        elif "Crisis" in regime or "Stagflation" in regime or "Defensive" in regime:
            preset = self.REGIME_PRESETS["DEFENSIVE"]
        else:
            preset = self.REGIME_PRESETS["AI_SUPER"]

        # 2. AI 추천 탑픽이 있는 경우 1위 슬롯 우선 적용
        p1 = views[0].top_pick if (views and views[0].top_pick) else preset["p1"]
        p2 = preset["p2"] if p1 != preset["p2"] else preset["p3"]
        p3 = preset["p3"] if (p1 != preset["p3"] and p2 != preset["p3"]) else preset["p1"]
        cash = preset["cash"]

        raw_weights: Dict[str, float] = {}

        # 3. 확신도에 따른 40/30/20/10 틸팅
        if conf >= 0.85:
            # 🔥 [1등 탈환 공격 모드] 40% / 30% / 20% / 10%
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

        # 4. 정규화
        total_w = sum(raw_weights.values())
        if total_w > 0:
            for k in list(raw_weights.keys()):
                raw_weights[k] = round(raw_weights[k] / total_w, 4)

        return self.harness.validate_allocation(raw_weights)
