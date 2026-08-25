"""
tests/test_api.py
FastAPI 서버, 실시간 웹 대시보드 및 데이터 API 엔드포인트 무결성 테스트
"""

import unittest
from fastapi.testclient import TestClient
from src.api.server import app

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertGreater(data["indexed_etfs"], 0)

    def test_dashboard_html_serve(self):
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn("머니투데이 ETF 투자왕", res.text)
        self.assertIn("allocationChart", res.text)

    def test_dashboard_data_json(self):
        res = self.client.get("/api/dashboard/data")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_nav_krw", data)
        self.assertIn("cumulative_return_pct", data)
        self.assertIn("holdings", data)

if __name__ == "__main__":
    unittest.main()
