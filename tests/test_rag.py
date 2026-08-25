"""
tests/test_rag.py
하이브리드 RAG 검색 엔진 및 레이턴시 테스트
"""

import unittest
import time
from src.rag.hybrid_search import HybridETFRAGEngine

class TestRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rag = HybridETFRAGEngine()

    def test_rag_latency_and_accuracy(self):
        start = time.perf_counter()
        results = self.rag.search("원자력 SMR 및 전력 인프라 쇼티지", top_k=3)
        latency_ms = (time.perf_counter() - start) * 1000.0

        self.assertLess(latency_ms, 5.0)  # 5ms 이하 보장
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].cluster_id, "C2_AI_POWER")

if __name__ == "__main__":
    unittest.main()
