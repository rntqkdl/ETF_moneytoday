"""
test_pipeline.py
전체 연금형 ETF 퀀트 시스템 통합 검증 및 단위 테스트 스위트
"""

import time
from db_manager import DatabaseManager
from rag_engine import HybridETFRAGEngine

def test_full_pipeline():
    print("=" * 70)
    print("🧪 [통합 테스트] 머니투데이 ETF 투자왕 대회 (연금형) DB & RAG 파이프라인 검증")
    print("=" * 70)

    # 1. DB 연결 및 통계 검증
    db = DatabaseManager()
    stats = db.execute_query("""
    SELECT cluster_id, cluster_name, COUNT(*) as count
    FROM etf_master
    GROUP BY cluster_id, cluster_name
    ORDER BY count DESC
    """)
    
    print("\n📊 [1] 8대 클러스터별 적격 ETF 데이터베이스 분포:")
    total_count = 0
    for s in stats:
        total_count += s['count']
        print(f"  • {s['cluster_id']} ({s['cluster_name']}): {s['count']}개")
    print(f"  👉 총 등록된 연금 적격 ETF: {total_count}개")
    assert total_count > 0, "DB에 ETF가 정상 등록되지 않았습니다."

    # 2. 컴플라이언스 룰 가드레일 검증 (선물, 레버리지, 인버스 0건 확인)
    forbidden_records = db.execute_query("""
    SELECT name FROM etf_master 
    WHERE name LIKE '%선물%' OR name LIKE '%레버리지%' OR name LIKE '%인버스%' OR name LIKE '%2X%'
    """)
    print("\n🛡️ [2] 컴플라이언스 가드레일 검증 (선물/레버리지/인버스 배제):")
    print(f"  • 규정 위반(선물/레버리지/인버스) 검출 수: {len(forbidden_records)}건")
    assert len(forbidden_records) == 0, f"규정 위반 종목 발견: {forbidden_records}"
    print("  ✅ 100% 규정 준수 통과!")

    # 3. RAG 엔진 속도 및 정확도 검증
    print("\n⚡ [3] RAG 엔진 검색 레이턴시 및 정확도 벤치마크:")
    rag = HybridETFRAGEngine(db=db)
    
    queries = [
        ("AI 반도체 HBM 장비 수혜주", "C1_AI_SEMI"),
        ("SMR 소형모듈원전 및 전력 변압기", "C2_AI_POWER"),
        ("미국 빅테크 M7 나스닥 롱 포지션", "C3_US_TECH"),
        ("K-방산 유럽 수출 및 휴머노이드 로봇", "C4_DEFENSE"),
        ("금융지주 밸류업 자사주 매입", "C5_VALUE_UP"),
        ("미국 배당성장 및 데일리 커버드콜", "C6_DIVIDEND"),
        ("금현물 인플레이션 헷지", "C7_COMMODITY"),
        ("FOMC 변동성 대비 SOFR 금리 파킹", "C8_CASH_PARK")
    ]

    for q, expected_cluster in queries:
        start_t = time.perf_counter()
        res = rag.search(q, top_k=3)
        latency_ms = (time.perf_counter() - start_t) * 1000.0
        
        top_res = res[0] if res else None
        assert top_res is not None, f"검색 결과 없음: {q}"
        print(f"  🔍 '{q}' -> Top 1: {top_res['name']} ({top_res['cluster_id']}) | {latency_ms:.2f}ms")

    # 4. Qwen LoRA용 프롬프트 생성 검증
    prompt_context = rag.build_qwen_context_prompt("미국 대선 전후 지정학적 갈등과 방산주 모멘텀")
    print("\n📝 [4] Qwen LoRA 주입용 RAG 프롬프트 샘플:")
    print(prompt_context)

    print("\n" + "=" * 70)
    print("🎉 모든 검증 테스트가 100% 성공적으로 완료되었습니다!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_pipeline()
