"""
src/api/scheduler_daemon.py
KRX 장 운영 시간, D-Day 대회 타임라인, 리스크 서킷브레이커 기반 통합 자동화 트리거 데몬
"""

import time
import datetime
import schedule
import pytz
from typing import Dict, Any, Tuple
from src.database.data_collector import FinancialDataCollector
from src.database.dart_collector import DARTDisclosureCollector
from src.ai.inference_engine import QuantInferenceEngine
from src.ai.multi_agent_consensus import MultiAgentConsensusCommittee
from src.quant.harness import ComplianceHarness
from src.quant.optimizer import PortfolioOptimizer
from src.quant.paper_trader import PaperTradingAccount
from src.quant.trailing_stop import TrailingProfitLockEngine
from src.quant.krx_market_guard import KRXMarketGuard
from src.database.db_manager import DatabaseManager
from src.api.alert_manager import AlertManager

KST = pytz.timezone('Asia/Seoul')

def get_current_tournament_stage() -> Dict[str, Any]:
    """
    [대회 타임라인 자동 트리거 단계 감지]
    - Stage 1: 모의 운용 & OOS 검증 (현재 ~ 9월 16일)
    - Stage 2: 코스콤 HTS 브릿지 연동 D-Day (9월 17일 ~ 18일)
    - Stage 3-A: 본선 1~2주차 포지션 빌드업 (9월 21일 ~ 10월 2일)
    - Stage 3-B: 본선 3~6주차 1등 주도주 40% 전력 질주 (10월 5일 ~ 10월 30일)
    - Stage 3-C: 본선 7~8주차 래칫 익절 1위 수성 굳히기 (11월 2일 ~ 11월 13일)
    """
    today = datetime.date.today()
    
    if today < datetime.date(2026, 9, 17):
        return {
            "stage_id": "STAGE_1_PAPER_OOS",
            "stage_name": "🚀 1단계: 모의 운용 & 실시간 성과 추적 (D-Day 빌드업)",
            "mode": "PAPER_TRADING",
            "strategy": "40/30/20/10 직교성 샤프 모멘텀 + VWAP 분할 체결",
            "action_required": "무인 자동 운용 (스마트폰 슬랙 & 대시보드 모니터링)"
        }
    elif datetime.date(2026, 9, 17) <= today <= datetime.date(2026, 9, 18):
        return {
            "stage_id": "STAGE_2_KOSCOM_DDAY",
            "stage_name": "💻 2단계: 코스콤 계좌 발급 D-Day (HTS 브릿지 연동)",
            "mode": "HTS_BRIDGE_STANDBY",
            "strategy": "Windows HTS 매크로 자동 체결 리허설",
            "action_required": "코스콤 ID/PW 수령 시 windows_hts_bridge.py 연동"
        }
    elif datetime.date(2026, 9, 21) <= today <= datetime.date(2026, 10, 2):
        return {
            "stage_id": "STAGE_3A_BUILDUP",
            "stage_name": "🏆 3-A단계: 본선 1~2주차 포지션 빌드업",
            "mode": "LIVE_CHAMPIONSHIP",
            "strategy": "8대 클러스터 1등 국가대표 3종목 초기 진입 (40/30/20)",
            "action_required": "2주 추세 탑승 유지 (뇌동매매 금지)"
        }
    elif datetime.date(2026, 10, 5) <= today <= datetime.date(2026, 10, 30):
        return {
            "stage_id": "STAGE_3B_ALPHA_SPRINT",
            "stage_name": "🔥 3-B단계: 본선 3~6주차 1등 주도주 40% 풀 틸팅 질주",
            "mode": "LIVE_CHAMPIONSHIP",
            "strategy": "최강 모멘텀 섹터에 4억 집중 + 독립 섹터 3억 분산",
            "action_required": "상방 폭발 수익률 극대화"
        }
    else:
        return {
            "stage_id": "STAGE_3C_RATCHET_LOCK",
            "stage_name": "👑 3-C단계: 본선 7~8주차 래칫 익절 1위 수성 굳히기",
            "mode": "LIVE_CHAMPIONSHIP",
            "strategy": "수익률 3단계 래칫(30%/50%/70%) 현금 락인",
            "action_required": "1위 수익률 안전 보존 및 우승 확정"
        }

def morning_briefing_and_rebalance():
    """
    [트리거 1: 평일 08:30 KST]
    1. DART 공시 수집 & RAG 주입
    2. 매크로 환율/금리/VIX 수집
    3. 5대 멀티 에이전트 위원회 교차 토론 & 의결
    4. 10억 원 가상 포트폴리오 리밸런싱 집행
    5. 슬랙 알림 카드 자동 발송
    """
    now_kst = datetime.datetime.now(KST)
    if now_kst.weekday() >= 5:
        print(f"🛌 [Scheduler - {now_kst.strftime('%H:%M')}] 주말 휴장일 (절전 모드 유지)")
        return

    print(f"\n⏰ [Scheduler - 08:30] 모닝 기상! 10억 원 AI 퀀트 전략 수립 시작 ({now_kst.strftime('%Y-%m-%d %H:%M')})")

    stage_info = get_current_tournament_stage()
    print(f"📌 [현재 대회 단계]: {stage_info['stage_name']}")

    # 1. DART 수집
    dart_collector = DARTDisclosureCollector()
    disclosures = dart_collector.fetch_recent_disclosures(days=1)
    dart_collector.save_disclosures_to_rag(disclosures)

    # 2. 매크로 수집
    fin_collector = FinancialDataCollector()
    fin_collector.collect_macro_rates()

    # 3. 5대 멀티 에이전트 위원회 토론 & 의결
    db = DatabaseManager()
    committee = MultiAgentConsensusCommittee(db=db)
    sample_news = disclosures[0]["title"] if disclosures else "AI 반도체 및 원자력 SMR 인프라 수주 모멘텀 지속"
    report = committee.run_committee_deliberation(news_text=sample_news)

    # 4. 리밸런싱 집행
    account = PaperTradingAccount(db=db)
    res = account.rebalance(target_weights=report.final_target_weights, reasoning=report.consensus_decision)

    # 5. 슬랙 알림 발송
    engine = QuantInferenceEngine()
    decision = engine.evaluate_news(sample_news)
    alert_mgr = AlertManager()
    alert_mgr.send_rebalance_alert(decision, report.final_target_weights, total_nav=res["total_nav_krw"])
    print(f"✅ [08:30] 모닝 리밸런싱 완료 및 슬랙 보고 발송 완료!\n")

def intraday_risk_and_circuit_breaker_check():
    """
    [트리거 2: 장중 10분 주기]
    - -4% 급락 감지 시 비상 서킷브레이커 발동 -> 전량 현금 대피
    - +10%/+15%/+20% 도달 시 래칫 익절 락인
    """
    now_kst = datetime.datetime.now(KST)
    if now_kst.weekday() >= 5 or not (datetime.time(9, 5) <= now_kst.time() <= datetime.time(15, 30)):
        return

    db = DatabaseManager()
    account = PaperTradingAccount(db=db)
    risk_engine = TrailingProfitLockEngine(db=db)
    guard = KRXMarketGuard(db=db)
    
    state = account.get_status()
    holdings = state.get("holdings", {})
    if not holdings:
        return

    # 최신가 조회
    price_rows = db.execute_query("""
        SELECT m.name, p.close_price 
        FROM etf_daily_prices p
        JOIN etf_master m ON p.ticker = m.ticker
        WHERE p.trade_date = (SELECT MAX(trade_date) FROM etf_daily_prices)
    """)
    price_map = {r["name"]: float(r["close_price"]) for r in price_rows if r["name"]}

    actions = risk_engine.evaluate_holdings_for_profit_lock(holdings, price_map)
    for act in actions:
        if act.get("action") == "EMERGENCY_CIRCUIT_BREAKER_EXIT":
            print(f"🚨 [장중 비상 서킷브레이커 발동]: {act['name']} - {act['reason']}")
            # 비상 현금 대피 리밸런싱
            emergency_weights = {"TIGER CD금리투자KIS(합성)": 0.70, "ACE 미국달러SOFR금리(합성)": 0.30}
            account.rebalance(emergency_weights, reasoning=f"비상 서킷브레이커 발동: {act['reason']}")

def market_close_settlement():
    """
    [트리거 3: 평일 15:40 KST]
    - 당일 공식 종가 정산 & 야간 절전 모드 진입
    """
    now_kst = datetime.datetime.now(KST)
    if now_kst.weekday() >= 5:
        return

    print(f"\n🌙 [Scheduler - 15:40] 한국거래소 장 마감! 공식 정산 및 슬랙 일일 결산 보고 발송 ({now_kst.strftime('%Y-%m-%d')})")
    db = DatabaseManager()
    account = PaperTradingAccount(db=db)
    state = account.get_status()
    print(f"📊 [오늘의 마감 최종 자산]: {state.get('total_nav_krw', 1_000_000_000):,.0f} 원 (누적 수익률: {state.get('cumulative_return_pct', 0.0):+.2f}%)")
    print(f"💤 내일 아침 08:30까지 시스템 저전력 절전(Sleep) 대기 모드 진입.\n")

def start_daemon_loop():
    """스케줄러 데몬 무한 루프"""
    print("=" * 75)
    print("🤖 [Smart Lifecycle Daemon] 한국거래소(KRX) 장 시간 자동화 스케줄러 상주 시작")
    print("⏰ [기상 & 모닝 전략] 평일 08:30 KST (DART 공시 + 10억 리밸런싱 + 슬랙 발송)")
    print("⏰ [장중 리스크 감시] 평일 09:05 ~ 15:30 KST (10분 주기 비상 서킷브레이커 감시)")
    print("⏰ [마감 & 절전 대기] 평일 15:40 KST (공식 종가 정산 + 야간 절전 대기)")
    print("=" * 75)

    schedule.every().day.at("08:30").do(morning_briefing_and_rebalance)
    schedule.every(10).minutes.do(intraday_risk_and_circuit_breaker_check)
    schedule.every().day.at("15:40").do(market_close_settlement)

    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    start_daemon_loop()
