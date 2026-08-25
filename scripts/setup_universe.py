"""
scripts/setup_universe.py
893개 연금 적격 ETF 마스터 데이터베이스 및 RAG 지식 인덱스 구축 스크립트
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.db_manager import DatabaseManager
from src.rag.universe_parser import UniverseParser

def setup():
    print("🚀 [Setup] 893개 연금 적격 ETF DB 및 RAG 인덱스 구축 시작...")
    db = DatabaseManager()
    records = UniverseParser.get_all_records()
    db.insert_etf_master(records)

    for r in records:
        db.insert_rag_document(
            ticker=r.ticker,
            doc_type="FACTSHEET",
            title=f"ETF 팩트시트: {r.name}",
            content=r.description,
            metadata={
                "cluster_id": r.cluster_id,
                "issuer": r.issuer,
                "is_fx_hedged": r.is_fx_hedged,
                "key_themes": r.key_themes
            }
        )
    print(f"🎉 총 {len(records)}개 연금 적격 ETF 인덱싱 성공 완료!")

if __name__ == "__main__":
    setup()
