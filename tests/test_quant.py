"""
tests/test_quant.py
컴플라이언스 하네스, 포트폴리오 최적화기, TWAP 분할기 및 스트레스 테스터 통합 테스트
"""

import unittest
from src.database.db_manager import DatabaseManager
from src.database.models import QuantDecisionOutput, ClusterViewItem
from src.quant.harness import ComplianceHarness
from src.quant.optimizer import PortfolioOptimizer
from src.quant.execution_twap import TWAPExecutionEngine
from src.quant.stress_tester import PortfolioStressTester

class TestQuant(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()
        self.harness = ComplianceHarness(db=self.db)
        self.optimizer = PortfolioOptimizer(harness=self.harness)
        self.stress_tester = PortfolioStressTester(db=self.db)

    def test_harness_single_asset_cap(self):
        decision = QuantDecisionOutput(
            regime="Bull_Tech",
            confidence_score=0.90,
            cluster_views=[
                ClusterViewItem(cluster_id="C1_AI_SEMI", expected_return=0.08, confidence=0.95, top_pick="KODEX 미국AI반도체TOP3플러스"),
                ClusterViewItem(cluster_id="C2_AI_POWER", expected_return=0.06, confidence=0.90, top_pick="TIGER 미국AI전력SMR"),
                ClusterViewItem(cluster_id="C3_US_TECH", expected_return=0.05, confidence=0.88, top_pick="ACE 미국빅테크TOP7 Plus")
            ],
            cash_park_ratio=0.10,
            reasoning="강세장"
        )
        weights = self.optimizer.calculate_weights(decision)
        
        # 총합 1.0 검증
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=2)
        # 1위 대장주 최대 40% 비중 캡 검증
        self.assertLessEqual(weights["KODEX 미국AI반도체TOP3플러스"], 0.40)
        self.assertGreaterEqual(weights["KODEX 미국AI반도체TOP3플러스"], 0.35)

    def test_twap_execution_slicing(self):
        weights = {
            "KODEX 미국AI반도체TOP3플러스": 0.40,
            "TIGER 미국AI전력SMR": 0.30,
            "ACE 미국빅테크TOP7 Plus": 0.20,
            "TIGER CD금리투자KIS(합성)": 0.05,
            "ACE 미국달러SOFR금리(합성)": 0.05
        }
        plan = TWAPExecutionEngine.generate_twap_plan(
            target_weights=weights,
            current_holdings={},
            prices={},
            total_nav=1_000_000_000.0
        )
        self.assertEqual(plan.num_slices, 6)
        self.assertGreater(len(plan.slices), 0)
        self.assertGreater(plan.expected_slippage_savings_krw, 0.0)

    def test_stress_tester_runs(self):
        weights = {
            "KODEX 미국AI반도체TOP3플러스": 0.40,
            "TIGER 미국AI전력SMR": 0.30,
            "TIGER CD금리투자KIS(합성)": 0.15,
            "ACE 미국달러SOFR금리(합성)": 0.15
        }
        res = self.stress_tester.run_stress_test(current_weights=weights, total_nav=1_000_000_000.0)
        self.assertIn("2020_COVID_CRASH", res)
        self.assertIn("2022_INFLATION_TIGHTENING", res)
        self.assertGreater(res["2020_COVID_CRASH"]["defense_alpha_pct"], 0.0)

if __name__ == "__main__":
    unittest.main()
