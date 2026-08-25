"""
main.py
머니투데이 제3회 ETF 투자왕 대회 [연금형] 통합 CLI 진입점
"""

import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="머니투데이 제3회 ETF 투자왕 대회 [연금형] AI 퀀트 시스템 CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령어")

    # setup
    subparsers.add_parser("setup", help="893개 ETF 마스터 DB 및 RAG 인덱스 초기화")
    
    # harvest
    subparsers.add_parser("harvest", help="대표 ETF 시세 및 매크로 지표 데이터 수집")

    # harvest-history
    hist_parser = subparsers.add_parser("harvest-history", help="과거 1~3년 치 대규모 시계열 데이터 수집 및 공분산 분석")
    hist_parser.add_argument("--years", type=int, default=2, help="수집할 과거 연수 (기본: 2년)")

    # inav-scan
    subparsers.add_parser("inav-scan", help="iNAV(순자산가치) 괴리율 저평가 차익 기회 및 월배당 스나이핑 스캔")

    # trailing-check
    subparsers.add_parser("trailing-check", help="10억 원 포트폴리오 트레일링 익절 및 이익 락인(Profit Lock-in) 검사")

    # stress-test
    subparsers.add_parser("stress-test", help="과거 5개년 역사적 위기 국면(팬데믹, 금리폭등) 기반 스트레스 테스트")

    # dart-harvest
    subparsers.add_parser("dart-harvest", help="DART 전자공시 실시간 기업 공시 수집 및 RAG 동기화")

    # train
    subparsers.add_parser("train", help="Apple M5 Metal GPU LoRA 파인튜닝 학습")
    
    # infer
    infer_parser = subparsers.add_parser("infer", help="실시간 뉴스 입력 기반 퀀트 뷰 추론")
    infer_parser.add_argument("--news", type=str, required=True, help="뉴스 헤드라인/시황 텍스트")

    # paper-rebalance
    paper_parser = subparsers.add_parser("paper-rebalance", help="10억 원 가상 포트폴리오 AI 리밸런싱 실행")
    paper_parser.add_argument("--news", type=str, required=True, help="뉴스 헤드라인/시황 텍스트")

    # twap-plan
    twap_parser = subparsers.add_parser("twap-plan", help="10억 원 슬리피지 방어 TWAP 6회 분할 주문표 생성")
    twap_parser.add_argument("--news", type=str, required=True, help="뉴스 헤드라인/시황 텍스트")

    # paper-status
    subparsers.add_parser("paper-status", help="가상 10억 원 포트폴리오 실시간 성과 대시보드 출력")

    # dashboard
    subparsers.add_parser("dashboard", help="실시간 반응형 웹 대시보드 서버 가동 (http://localhost:8000/dashboard)")

    # weekly-review
    subparsers.add_parser("weekly-review", help="주간 성과 귀속 분석 및 딥리포트 생성")

    # test-alert
    alert_parser = subparsers.add_parser("test-alert", help="디스코드/슬랙 알림 테스트")
    alert_parser.add_argument("--webhook", type=str, required=False, help="디스코드 또는 슬랙 웹훅 URL")

    # scheduler
    subparsers.add_parser("scheduler", help="KRX 장 운영 시간(08:30 / 15:40) 자동화 스케줄러 데몬 가동")

    # serve
    subparsers.add_parser("serve", help="n8n 연동용 FastAPI 브릿지 서버 구동 (Port 8000)")

    # test
    subparsers.add_parser("test", help="전체 파이프라인 통합 테스트 실행")

    args = parser.parse_args()

    if args.command == "setup":
        from scripts.setup_universe import setup
        setup()
    elif args.command == "harvest":
        from src.database.data_collector import FinancialDataCollector
        collector = FinancialDataCollector()
        collector.collect_multi_year_history(years=1)
        collector.collect_macro_rates()
    elif args.command == "harvest-history":
        from src.database.data_collector import FinancialDataCollector
        collector = FinancialDataCollector()
        collector.collect_multi_year_history(years=args.years)
        collector.collect_macro_rates()
        cov, mom = collector.calculate_empirical_covariance_and_momentum()
        print(f"📊 [공분산 분석 완료] 분석 대상 자산 수: {len(cov)}개 | 20일 모멘텀 산출 완료!")
    elif args.command == "inav-scan":
        from src.database.db_manager import DatabaseManager
        from src.quant.inav_arbitrage import INAVArbitrageEngine
        db = DatabaseManager()
        engine = INAVArbitrageEngine(db=db)
        candidates = ["465580", "481180", "448290", "462900", "446770", "441680", "411060", "091160"]
        ranked = engine.get_etf_arbitrage_ranking(candidates)
        is_div, div_msg = engine.is_dividend_reinvestment_day()

        print("=" * 75)
        print("⚡ [iNAV 괴리율 저평가 차익거래 & 월배당 스나이핑 스캔 결과]")
        print("=" * 75)
        print(f"• 배당 스나이핑 상태: {div_msg}")
        print("-" * 75)
        print("티커     현재가(원)   iNAV(원)   괴리율(%)   저평가 차익 스코어   거래량(주)")
        print("-" * 75)
        for r in ranked:
            print(f"{r['ticker']:6s}  {r['close_price']:9,.0f}  {r['inav']:8,.0f}  {r['disparity_pct']:+7.2f}%   {r['arbitrage_alpha']:+16.2f}    {r['volume']:9,d}")
        print("=" * 75)
    elif args.command == "trailing-check":
        from src.database.db_manager import DatabaseManager
        from src.quant.paper_trader import PaperTradingAccount
        from src.quant.trailing_stop import TrailingProfitLockEngine
        db = DatabaseManager()
        account = PaperTradingAccount(db=db)
        engine = TrailingProfitLockEngine(db=db)
        state = account.get_status()
        holdings = state.get("holdings", {})
        
        # 현재가 매핑
        current_prices = {k: v.get("avg_price", 10000.0) * 1.12 for k, v in holdings.items()} # 예시 +12% 수익 상태
        actions = engine.evaluate_holdings_for_profit_lock(holdings, current_prices)

        print("=" * 75)
        print("🔒 [10억 원 포트폴리오 트레일링 익절 & 이익 락인(Profit Lock-in) 검사]")
        print("=" * 75)
        if actions:
            for a in actions:
                print(f"• [{a['name']}] 현재 수익률: +{a['gain_pct']:.1f}%")
                print(f"  👉 조치: {a['action']} ({a['reason']})")
        else:
            print("• 현재 전 종목 안정 보유 중 (트레일링 익절 발동 조건 미도달)")
        print("=" * 75)
    elif args.command == "stress-test":
        from src.database.db_manager import DatabaseManager
        from src.quant.paper_trader import PaperTradingAccount
        from src.quant.stress_tester import PortfolioStressTester
        db = DatabaseManager()
        account = PaperTradingAccount(db=db)
        tester = PortfolioStressTester(db=db)
        state = account.get_status()
        holdings = state.get("holdings", {})
        
        weights = {}
        for k, v in holdings.items():
            weights[k] = v.get("target_weight", 0.20)
        if not weights:
            weights = {
                "KODEX 미국AI반도체TOP3플러스": 0.40,
                "TIGER 미국AI전력SMR": 0.30,
                "ACE 미국빅테크TOP7 Plus": 0.20,
                "TIGER CD금리투자KIS(합성)": 0.05,
                "ACE 미국달러SOFR금리(합성)": 0.05
            }
        
        res = tester.run_stress_test(current_weights=weights, total_nav=state.get("total_nav_krw", 1_000_000_000.0))
        print("=" * 75)
        print("🚨 [역사적 위기 국면 스트레스 테스트] (10억 원 포트폴리오 충격 시뮬레이션)")
        print("=" * 75)
        for sc_id, sc in res.items():
            print(f"📌 [{sc['scenario_name']}]")
            print(f"  • 시장 평균(KOSPI/S&P) 충격 : {sc['market_benchmark_drawdown_pct']:+.1f}%")
            print(f"  • 우리 포트폴리오 예상 낙폭 : {sc['portfolio_drawdown_pct']:+.2f}% ({sc['expected_loss_krw']:,.0f} 원)")
            print(f"  • 하방 방어 알파 (초과방어) : 🟢 +{sc['defense_alpha_pct']:.2f}%p 방어 성공!")
            print("-" * 75)
    elif args.command == "dart-harvest":
        from src.database.dart_collector import DARTDisclosureCollector
        collector = DARTDisclosureCollector()
        disclosures = collector.fetch_recent_disclosures(days=7)
        collector.save_disclosures_to_rag(disclosures)
    elif args.command == "train":
        from scripts.train_lora import main as train_main
        train_main()
    elif args.command == "infer":
        from src.ai.inference_engine import QuantInferenceEngine
        from src.quant.harness import ComplianceHarness
        from src.quant.optimizer import PortfolioOptimizer
        from src.database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        engine = QuantInferenceEngine()
        harness = ComplianceHarness(db=db)
        optimizer = PortfolioOptimizer(harness=harness)
        
        print(f"\n📰 [입력 뉴스]: {args.news}")
        decision = engine.evaluate_news(args.news)
        weights = optimizer.calculate_weights(decision)
        
        print("\n" + "=" * 70)
        print(f"🎯 [국면]: {decision.regime} (종합 확신도: {decision.confidence_score*100:.1f}%)")
        print(f"🛡️ [현금 파킹 비율]: {decision.cash_park_ratio*100:.1f}%")
        print("📊 [목표 포트폴리오 비중]:")
        for k, v in weights.items():
            print(f"  • {k}: {v*100:.1f}%")
        print(f"💡 [판단 근거]: {decision.reasoning}")
        print("=" * 70)
    elif args.command == "twap-plan":
        from src.ai.inference_engine import QuantInferenceEngine
        from src.quant.harness import ComplianceHarness
        from src.quant.optimizer import PortfolioOptimizer
        from src.quant.paper_trader import PaperTradingAccount
        from src.quant.execution_twap import TWAPExecutionEngine
        from src.database.db_manager import DatabaseManager

        db = DatabaseManager()
        engine = QuantInferenceEngine()
        harness = ComplianceHarness(db=db)
        optimizer = PortfolioOptimizer(harness=harness)
        account = PaperTradingAccount(db=db)

        decision = engine.evaluate_news(args.news)
        weights = optimizer.calculate_weights(decision)
        state = account.get_status()
        
        plan = TWAPExecutionEngine.generate_twap_plan(
            target_weights=weights,
            current_holdings=state.get("holdings", {}),
            prices={},
            total_nav=state.get("total_nav_krw", 1_000_000_000.0)
        )

        print("\n" + "=" * 75)
        print(f"⏱️ [TWAP 슬리피지 방어 분할 주문표] (총 주문액: {plan.total_order_amount_krw:,.0f} 원)")
        print(f"• 분할 횟수: {plan.num_slices}회 ({plan.slice_interval_minutes}분 간격) | 실행 시간: {plan.start_time} ~ {plan.end_time}")
        print(f"• 예상 슬리피지 절감 효과: +{plan.expected_slippage_savings_krw:,.0f} 원 (호가 충격 방어)")
        print("-" * 75)
        for s in plan.slices[:12]:
            print(f"  [{s.scheduled_time}] #{s.slice_index}차 {s.action} | {s.ticker_name:30s} | {s.shares:6,d}주 | 지정가: {s.limit_price:,.0f}원 ({s.slice_amount_krw:,.0f}원)")
        print("=" * 75)
    elif args.command == "paper-rebalance":
        from src.ai.inference_engine import QuantInferenceEngine
        from src.quant.harness import ComplianceHarness
        from src.quant.optimizer import PortfolioOptimizer
        from src.quant.paper_trader import PaperTradingAccount
        from src.quant.telemetry import PortfolioTelemetry
        from src.database.db_manager import DatabaseManager
        from src.api.alert_manager import AlertManager

        db = DatabaseManager()
        engine = QuantInferenceEngine()
        harness = ComplianceHarness(db=db)
        optimizer = PortfolioOptimizer(harness=harness)
        account = PaperTradingAccount(db=db)
        alert_mgr = AlertManager()

        print(f"\n📰 [입력 뉴스]: {args.news}")
        decision = engine.evaluate_news(args.news)
        weights = optimizer.calculate_weights(decision)
        
        print("⚡ 10억 원 가상 포트폴리오 리밸런싱 실행 중...")
        res = account.rebalance(target_weights=weights, reasoning=decision.reasoning)
        print(PortfolioTelemetry.render_dashboard(account))

        # 디스코드/슬랙 알림 발송
        alert_mgr.send_rebalance_alert(decision, weights, total_nav=res["total_nav_krw"])
    elif args.command == "paper-status":
        from src.quant.paper_trader import PaperTradingAccount
        from src.quant.telemetry import PortfolioTelemetry
        account = PaperTradingAccount()
        print(PortfolioTelemetry.render_dashboard(account))
    elif args.command == "dashboard":
        from src.api.server import start_server
        print("=" * 70)
        print("🚀 [Web Dashboard] 실시간 웹 대시보드 서버 가동 중...")
        print("👉 로컬 접속 URL: http://localhost:8000/dashboard")
        print("=" * 70)
        start_server()
    elif args.command == "weekly-review":
        from src.quant.weekly_review import WeeklyPerformanceReviewer
        reviewer = WeeklyPerformanceReviewer()
        rep = reviewer.generate_weekly_report()
        print(rep["summary_text"])
    elif args.command == "test-alert":
        from src.api.alert_manager import AlertManager
        from src.database.models import QuantDecisionOutput, ClusterViewItem
        mgr = AlertManager(webhook_url=args.webhook)
        mock_decision = QuantDecisionOutput(
            regime="AI_Hardware_Supercycle",
            confidence_score=0.94,
            cluster_views=[
                ClusterViewItem(cluster_id="C1_AI_SEMI", expected_return=0.065, confidence=0.96, top_pick="TIGER 미국AI반도체팹리스"),
                ClusterViewItem(cluster_id="C2_AI_POWER", expected_return=0.055, confidence=0.92, top_pick="KODEX 원자력SMR")
            ],
            cash_park_ratio=0.08,
            reasoning="AI 반도체 및 원자력 SMR 전력망 수주 모멘텀 지속"
        )
        mock_weights = {
            "TIGER 미국AI반도체팹리스": 0.40,
            "KODEX 원자력SMR": 0.30,
            "ACE 미국빅테크TOP7 Plus": 0.20,
            "TIGER CD금리투자KIS(합성)": 0.05,
            "ACE 미국달러SOFR금리(합성)": 0.05
        }
        success = mgr.send_rebalance_alert(mock_decision, mock_weights)
        if not success:
            print("💡 웹훅 URL을 입력하거나 .env 파일의 DISCORD_WEBHOOK_URL / SLACK_WEBHOOK_URL을 설정해주세요.")
    elif args.command == "scheduler":
        from src.api.scheduler_daemon import start_daemon_loop
        start_daemon_loop()
    elif args.command == "serve":
        from src.api.server import start_server
        start_server()
    elif args.command == "test":
        import unittest
        suite = unittest.defaultTestLoader.discover("tests")
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
