"""
db_manager.py
머니투데이 ETF 투자왕 대회 [연금형] 데이터베이스 매니저
PostgreSQL (pgvector) 및 로컬 환경 지원을 위한 하이브리드 커넥터 (Standard Library Native)
"""

import os
import sqlite3
import json
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """PostgreSQL 및 로컬 DB 연결 및 트랜잭션 관리자"""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///pension_etf.db")
        self.is_postgres = self.db_url.startswith("postgresql")
        self._init_db()

    def _init_db(self):
        """데이터베이스 초기화 및 테이블 생성"""
        if self.is_postgres:
            try:
                import psycopg2
                from psycopg2.extras import execute_values
                self.conn = psycopg2.connect(self.db_url)
                self.conn.autocommit = True
                schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
                with open(schema_path, "r", encoding="utf-8") as f:
                    with self.conn.cursor() as cur:
                        cur.execute(f.read())
                print("✅ PostgreSQL (pgvector) 연결 및 스키마 초기화 완료!")
                return
            except Exception as e:
                print(f"⚠️ PostgreSQL 연결 실패 ({e}). SQLite 로컬 모드로 자동 전환합니다.")
                self.is_postgres = False

        # SQLite 로컬 파일 기반 DB 초기화
        db_path = self.db_url.replace("sqlite:///", "")
        if not db_path.startswith("/"):
            db_path = os.path.join(os.path.dirname(__file__), db_path)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_sqlite_tables()
        print(f"✅ SQLite 로컬 DB 초기화 완료: {db_path}")

    def _create_sqlite_tables(self):
        """SQLite 환경용 스키마 생성"""
        cur = self.conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS etf_master (
            ticker TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            issuer TEXT NOT NULL,
            brand TEXT NOT NULL,
            cluster_id TEXT NOT NULL,
            cluster_name TEXT NOT NULL,
            is_fx_hedged INTEGER DEFAULT 0,
            is_synthetic INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0,
            is_covered_call INTEGER DEFAULT 0,
            is_pension_eligible INTEGER DEFAULT 1,
            description TEXT,
            key_themes TEXT,
            expense_ratio REAL DEFAULT 0.0045,
            aum_billion_krw REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS etf_rag_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            document_type TEXT,
            title TEXT,
            content TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker) REFERENCES etf_master(ticker)
        );

        CREATE TABLE IF NOT EXISTS etf_daily_prices (
            ticker TEXT,
            trade_date TEXT,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume INTEGER,
            trading_value_krw INTEGER,
            inav REAL,
            disparity_ratio REAL,
            PRIMARY KEY (ticker, trade_date)
        );

        CREATE TABLE IF NOT EXISTS portfolio_allocation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            regime_detected TEXT,
            qwen_confidence_score REAL,
            target_weights TEXT,
            portfolio_cvar REAL,
            execution_status TEXT DEFAULT 'PENDING',
            notes TEXT
        );
        """)
        self.conn.commit()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """쿼리 실행 후 딕셔너리 리스트 반환"""
        if self.is_postgres:
            import psycopg2.extras
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params or ())
                if cur.description:
                    return [dict(row) for row in cur.fetchall()]
                return []
        else:
            self.conn.row_factory = sqlite3.Row
            cur = self.conn.cursor()
            cur.execute(query, params or ())
            if cur.description:
                return [dict(row) for row in cur.fetchall()]
            self.conn.commit()
            return []

    def insert_etf_master(self, records: List[Dict[str, Any]]):
        """ETF 마스터 데이터 일괄 삽입"""
        if self.is_postgres:
            import psycopg2.extras
            query = """
            INSERT INTO etf_master (
                ticker, name, issuer, brand, cluster_id, cluster_name,
                is_fx_hedged, is_synthetic, is_active, is_covered_call,
                is_pension_eligible, description, key_themes, expense_ratio, aum_billion_krw
            ) VALUES %s
            ON CONFLICT (ticker) DO UPDATE SET
                name = EXCLUDED.name,
                cluster_id = EXCLUDED.cluster_id,
                description = EXCLUDED.description;
            """
            values = [
                (
                    r["ticker"], r["name"], r["issuer"], r["brand"], r["cluster_id"], r["cluster_name"],
                    r["is_fx_hedged"], r["is_synthetic"], r["is_active"], r["is_covered_call"],
                    r["is_pension_eligible"], r["description"], r["key_themes"], r["expense_ratio"], r["aum_billion_krw"]
                )
                for r in records
            ]
            with self.conn.cursor() as cur:
                psycopg2.extras.execute_values(cur, query, values)
            self.conn.commit()
        else:
            cur = self.conn.cursor()
            for r in records:
                cur.execute("""
                INSERT OR REPLACE INTO etf_master (
                    ticker, name, issuer, brand, cluster_id, cluster_name,
                    is_fx_hedged, is_synthetic, is_active, is_covered_call,
                    is_pension_eligible, description, key_themes, expense_ratio, aum_billion_krw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r["ticker"], r["name"], r["issuer"], r["brand"], r["cluster_id"], r["cluster_name"],
                    1 if r["is_fx_hedged"] else 0, 1 if r["is_synthetic"] else 0,
                    1 if r["is_active"] else 0, 1 if r["is_covered_call"] else 0,
                    1 if r["is_pension_eligible"] else 0, r["description"],
                    ",".join(r["key_themes"]) if isinstance(r["key_themes"], list) else r["key_themes"],
                    r["expense_ratio"], r["aum_billion_krw"]
                ))
            self.conn.commit()
        print(f"💾 {len(records)}개 ETF 마스터 레코드 저장 완료!")

    def insert_rag_document(self, ticker: str, doc_type: str, title: str, content: str, metadata: dict = None):
        """RAG 지식 문서 저장"""
        if self.is_postgres:
            query = """
            INSERT INTO etf_rag_documents (ticker, document_type, title, content, metadata)
            VALUES (%s, %s, %s, %s, %s)
            """
            with self.conn.cursor() as cur:
                cur.execute(query, (ticker, doc_type, title, content, json.dumps(metadata or {})))
            self.conn.commit()
        else:
            cur = self.conn.cursor()
            cur.execute("""
            INSERT INTO etf_rag_documents (ticker, document_type, title, content, metadata)
            VALUES (?, ?, ?, ?, ?)
            """, (ticker, doc_type, title, content, json.dumps(metadata or {})))
            self.conn.commit()
