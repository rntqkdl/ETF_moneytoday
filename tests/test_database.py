"""
tests/test_database.py
데이터베이스 연결 및 893개 ETF 무결성 테스트
"""

import unittest
from src.database.db_manager import DatabaseManager

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()

    def test_etf_master_count(self):
        rows = self.db.execute_query("SELECT COUNT(*) as count FROM etf_master")
        self.assertGreater(rows[0]["count"], 0)

    def test_compliance_zero_violation(self):
        forbidden = self.db.execute_query("""
        SELECT name FROM etf_master 
        WHERE name LIKE '%선물%' OR name LIKE '%레버리지%' OR name LIKE '%인버스%' OR name LIKE '%2X%'
        """)
        self.assertEqual(len(forbidden), 0)

if __name__ == "__main__":
    unittest.main()
