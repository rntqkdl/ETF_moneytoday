"""
src/api/scheduler_daemon.py
한국거래소(KRX) 장 운영 시간 스마트 라이프사이클 데몬
(08:30 자동 기상 -> 09:00~15:30 장중 운용 -> 15:40 마감 정산 & 자동 절전 대기)
"""

import schedule
import time
import datetime
from src.database.db_manager import DatabaseManager
from src.database.data_collector import FinancialDataCollector
from src.database.dart_collector import DARTDisclosureCollector
from src.ai.inference_engine import QuantInferenceEngine
from src.quant.harness import ComplianceHarness
from src.quant.optimizer import PortfolioOptimizer
from src.quant.paper_trader import PaperTradingAccount
from src.api.alert_manager import AlertManager

db = DatabaseManager()
collector = FinancialDataCollector(db=db)
dart_collector = DARTDisclosureCollector(db=db)
harness = ComplianceHarness(db=db)
optimizer = PortfolioOptimizer(harness=harness)
account = PaperTradingAccount(db=db)
alert_mgr = AlertManager()
ai_engine = None

def get_engine():
    global ai_engine
    if ai_engine is None:
        ai_engine = QuantInferenceEngine()
    return ai_engine

def is_market_day() -> bool:
    """평일(월~금) 여부 확인"""
    today = datetime.date.today()
    return today.weekday() < 5

def morning_briefing_and_rebalance():
    """🌅 [08:30 KST] 모닝 전략 수립 및 리밸런싱 실행"""
    if not is_market_day():
        print(f"💤 [Scheduler] 주말/휴일 대기 중 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})")
        return

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n⏰ [Scheduler - 08:30] 모닝 기상! 10억 원 AI 퀀트 전략 수립 시작 ({now_str})")
    
    # 1. DART 전자공시 & 매크로 지표 수집
    dart_disclosures = dart_collector.fetch_recent_disclosures(days=1)
    dart_collector.save_disclosures_to_rag(dart_disclosures)
    collector.collect_macro_rates()

    # 2. AI 퀀트 뷰 추론 & 40/30/20/10 비대칭 최적화
    engine = get_engine()
    news_text = "미국 반도체 지수 강세 및 AI 전력 인프라 SMR 수주 지속, 밸류업 프로그램 추진"
    decision = engine.evaluate_news(news_text)
    weights = optimizer.calculate_weights(decision)

    # 3. 10억 원 가상 포트폴리오 리밸런싱 & 슬랙 발송
    res = account.rebalance(target_weights=weights, reasoning=decision.reasoning)
    alert_mgr.send_rebalance_alert(decision, weights, total_nav=res["total_nav_krw"])
    print(f"✅ [08:30] 모닝 리밸런싱 완료 및 슬랙 보고 발송 완료!")

def closing_settlement_and_sleep():
    """🌇 [15:40 KST] 장 마감 확정 시세 수집 & 일일 정산 후 자동 절전 대기"""
    if not is_market_day():
        return

    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"\n⏰ [Scheduler - 15:40] 장 마감 확정 정산 시작 ({now_str})")
    
    # 1. 당일 공식 확정 종가 DB 적재
    collector.collect_multi_year_history(years=1)
    
    # 2. 10억 원 가상 계좌 평가액 마크투마켓(Mark-to-Market)
    state = account.get_status()
    total_nav = state.get("total_nav_krw", 1_000_000_000.0)
    ret_pct = state.get("cumulative_return_pct", 0.0)
    
    print(f"💰 [15:40 장 마감 정산] 총 평가 자산: {total_nav:,.0f} 원 (누적 수익률: {ret_pct:+.2f}%)")
    print(f"🌙 [15:40] 마감 정산 완료! 내일 아침 08:30까지 백그라운드 절전 대기 모드 진입.")

def start_daemon_loop():
    """스마트 라이프사이클 스케줄러 메인 루프"""
    schedule.every().day.at("08:30").do(morning_briefing_and_rebalance)
    schedule.every().day.at("15:40").do(closing_settlement_and_sleep)

    print("=" * 75)
    print("🤖 [Smart Lifecycle Daemon] 한국거래소(KRX) 장 시간 자동화 스케줄러 상주 시작")
    print("⏰ [기상 & 모닝 전략] 평일 08:30 KST (DART 공시 + 10억 리밸런싱 + 슬랙 발송)")
    print("⏰ [마감 & 절전 대기] 평일 15:40 KST (공식 종가 정산 + 야간 절전 대기)")
    print("=" * 75)

    while True:
        schedule.run_pending()
        time.sleep(30)
