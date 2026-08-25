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

    # paper-status
    subparsers.add_parser("paper-status", help="가상 10억 원 포트폴리오 실시간 성과 대시보드 출력")

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
        collector.collect_etf_history(days=60)
        collector.collect_macro_rates()
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
            "TIGER 미국AI반도체팹리스": 0.25,
            "KODEX 원자력SMR": 0.25,
            "ACE 미국빅테크TOP7 Plus": 0.25,
            "TIGER CD금리투자KIS(합성)": 0.125,
            "ACE 미국달러SOFR금리(합성)": 0.125
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
