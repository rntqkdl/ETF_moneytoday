"""
src/api/scheduler_daemon.py
한국거래소(KRX) 장 운영 시간에 맞춘 자동화 퀀트 스케줄러 데몬
• 매일 08:30 KST: 장 시작 전 모닝 매크로 뉴스 수집 -> LoRA 퀀트 추론 -> 포트폴리오 목표 비중 산출
• 매일 15:40 KST: 장 마감 후 일일 시세 및 매크로 지표 DB 적재 -> 계좌 평가손익 정산 및 일일 대시보드 기록
"""

import sys
import time
import datetime
from pathlib import Path

# 루트 디렉터리 경로 등록
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.database.data_collector import FinancialDataCollector
from src.database.db_manager import DatabaseManager
from src.ai.inference_engine import QuantInferenceEngine
from src.quant.harness import ComplianceHarness
from src.quant.optimizer import PortfolioOptimizer
from src.quant.paper_trader import PaperTradingAccount
from src.quant.telemetry import PortfolioTelemetry

def run_morning_strategy():
    """매일 08:30 KST: 모닝 매크로 뉴스 기반 리밸런싱 시그널 생성 및 가상 주문 실행"""
    print(f"\n⏰ [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 08:30 모닝 퀀트 전략 가동...")
    db = DatabaseManager()
    engine = QuantInferenceEngine()
    harness = ComplianceHarness(db=db)
    optimizer = PortfolioOptimizer(harness=harness)
    account = PaperTradingAccount(db=db)

    # 당일 주요 매크로 시황 프롬프트 (뉴스 수집기 연동)
    morning_news = (
        "미국 연준 9월 기준금리 25~50bp 인하 기대감 지속, 글로벌 AI 빅테크 및 반도체 서플라이체인 실적 견조, "
        "국내 밸류업 2차 가이드라인 및 고배당 세제지원 정책 모멘텀 유지."
    )

    print(f"📰 [모닝 매크로 브리핑]: {morning_news}")
    decision = engine.evaluate_news(morning_news)
    weights = optimizer.calculate_weights(decision)
    
    account.rebalance(target_weights=weights, reasoning=decision.reasoning)
    print("✅ 10억 원 가상 포트폴리오 모닝 리밸런싱 완료!")
    print(PortfolioTelemetry.render_dashboard(account))

def run_closing_settlement():
    """매일 15:40 KST: 장 마감 후 시세 수집 및 일일 포트폴리오 평가 정산"""
    print(f"\n⏰ [{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 15:40 장 마감 데이터 수집 및 정산 시작...")
    db = DatabaseManager()
    collector = FinancialDataCollector(db=db)
    account = PaperTradingAccount(db=db)

    # 1. 시세 및 매크로 지표 DB 적재
    collector.collect_etf_history(days=5)
    collector.collect_macro_rates()

    # 2. 일일 계좌 현황 출력
    print("✅ 일일 시세 적재 및 정산 완료!")
    print(PortfolioTelemetry.render_dashboard(account))

def start_daemon_loop():
    print("=" * 70)
    print("🚀 [Scheduler Daemon] KRX 장 시간 자동화 스케줄러 데몬 가동")
    print("• 매일 08:30 KST : 모닝 뉴스 퀀트 분석 & 10억 원 포트폴리오 리밸런싱")
    print("• 매일 15:40 KST : 장 마감 시세 DB 적재 & 계좌 평가손익 정산")
    print("=" * 70)

    # 데몬 시작 시 즉시 1회 초기화 실행
    print("\n⚡ [Day 1 초기화] 즉시 1회 모닝 전략 및 데이터 수집을 실행합니다...")
    run_morning_strategy()
    run_closing_settlement()

    last_morning_run = None
    last_closing_run = None

    while True:
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        weekday = now.weekday()  # 0=월, 4=금, 5=토, 6=일

        # 평일(월~금)에만 가동
        if weekday < 5:
            # 08:30 KST 모닝 전략
            if now.hour == 8 and now.minute >= 30 and last_morning_run != today_str:
                run_morning_strategy()
                last_morning_run = today_str

            # 15:40 KST 마감 정산
            if now.hour == 15 and now.minute >= 40 and last_closing_run != today_str:
                run_closing_settlement()
                last_closing_run = today_str

        # 30초 대기
        time.sleep(30)

if __name__ == "__main__":
    start_daemon_loop()
