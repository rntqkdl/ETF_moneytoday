"""
tests/test_quant.py
컴플라이언스 하네스 및 포트폴리오 최적화기 테스트
"""

import unittest
from src.database.db_manager import DatabaseManager
from src.database.models import QuantDecisionOutput, ClusterViewItem
from src.quant.harness import ComplianceHarness
from src.quant.optimizer import PortfolioOptimizer

class TestQuant(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()
        self.harness = ComplianceHarness(db=self.db)
        self.optimizer = PortfolioOptimizer(harness=self.harness)

    def test_harness_single_asset_cap(self):
        decision = QuantDecisionOutput(
            regime="Bull_Tech",
            confidence_score=0.90,
            cluster_views=[
                ClusterViewItem(cluster_id="C1_AI_SEMI", expected_return=0.06, confidence=0.95, top_pick="KODEX 미국AI반도체TOP3플러스")
            ],
            cash_park_ratio=0.10,
            reasoning="강세장"
        )
        weights = self.optimizer.calculate_weights(decision)
        
        # 총합 1.0 검증
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=2)
        # 단일 종목 최대 25% 비중 캡 검증
        self.assertLessEqual(weights["KODEX 미국AI반도체TOP3플러스"], 0.25)

if __name__ == "__main__":
    unittest.main()
