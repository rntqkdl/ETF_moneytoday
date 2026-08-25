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
    
    # train
    subparsers.add_parser("train", help="Apple M5 Metal GPU LoRA 파인튜닝 학습")
    
    # infer
    infer_parser = subparsers.add_parser("infer", help="실시간 뉴스 입력 기반 퀀트 뷰 추론")
    infer_parser.add_argument("--news", type=str, required=True, help="뉴스 헤드라인/시황 텍스트")

    # serve
    subparsers.add_parser("serve", help="n8n 연동용 FastAPI 브릿지 서버 구동 (Port 8000)")

    # test
    subparsers.add_parser("test", help="전체 파이프라인 통합 테스트 실행")

    args = parser.parse_args()

    if args.command == "setup":
        from scripts.setup_universe import setup
        setup()
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
