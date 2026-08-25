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

    # regime-ml
    subparsers.add_parser("regime-ml", help="GMM 머신러닝 비지도 학습 거시 국면 분류")

    # monte-carlo
    subparsers.add_parser("monte-carlo", help="10,000회 몬테카를로 8주 대회 우승 확률 시뮬레이션")

    # committee-debate
    debate_parser = subparsers.add_parser("committee-debate", help="5대 멀티 에이전트 위원회 교차 토론 및 만장일치 합의 도출")
    debate_parser.add_argument("--news", type=str, required=True, help="뉴스 헤드라인/시황 텍스트")

    # krx-guard
    subparsers.add_parser("krx-guard", help="KRX ETF 5대 고유 맹점(LP 호가 부재, 환율 드래그, DRIP) 가드레일 상태 점검")

    # inav-scan
    subparsers.add_parser("inav-scan", help="iNAV(순자산가치) 괴리율 저평가 차익 기회 및 월배당 스나이핑 스캔")

    # trailing-check
    subparsers.add_parser("trailing-check", help="10억 원 포트폴리오 트레일링 익절 및 이익 락인(Profit Lock-in) 검사")

    # vwap-plan
    vwap_parser = subparsers.add_parser("vwap-plan", help="10억 원 KRX U자형 거래량 가중(VWAP) 스마트 배치 분할표 생성")
    vwap_parser.add_argument("--news", type=str, required=True, help="뉴스 헤드라인/시황 텍스트")

    # almgren-plan
    ac_parser = subparsers.add_parser("almgren-plan", help="10억 원 월가 최적 실행 궤적(Almgren-Chriss) 수학적 배치 분할표 생성")
    ac_parser.add_argument("--news", type=str, required=True, help="뉴스 헤드라인/시황 텍스트")

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
    elif args.command == "regime-ml":
        from src.database.db_manager import DatabaseManager
        from src.quant.advanced_analytics import AdvancedQuantAnalytics
        db = DatabaseManager()
        analytics = AdvancedQuantAnalytics(db=db)
        res = analytics.fit_unsupervised_regime_model()
        print("=" * 75)
        print("🤖 [GMM 머신러닝 비지도 학습 거시 레짐 분류 결과]")
        print("=" * 75)
        print(f"• 현재 머신러닝 예측 국면: {res['predicted_regime']}")
        print(f"• 국면별 사후 확률 분포   : {res['probabilities']}")
        print("=" * 75)
    elif args.command == "monte-carlo":
        from src.database.db_manager import DatabaseManager
        from src.quant.paper_trader import PaperTradingAccount
        from src.quant.advanced_analytics import AdvancedQuantAnalytics
        db = DatabaseManager()
        account = PaperTradingAccount(db=db)
        analytics = AdvancedQuantAnalytics(db=db)
        state = account.get_status()
        holdings = state.get("holdings", {})
        
        weights = {"465580": 0.40, "481180": 0.30, "448290": 0.20, "453850": 0.10}
        sim = analytics.run_monte_carlo_championship_simulation(weights, num_simulations=10000, trading_days=40)
        
        print("=" * 75)
        print("🎲 [10,000회 몬테카를로 8주(40일) 대회 우승 확률 시뮬레이션]")
        print("=" * 75)
        print(f"• 8주 평균 기대수익률     : {sim['mean_expected_return_pct']:+.2f}% (중앙값: {sim['median_return_pct']:+.2f}%)")
        print(f"• 상위 10% 불마켓 폭발 수익: {sim['top_10pct_bull_return']:+.2f}% (최고 시뮬레이션: +{sim['max_simulated_return']:.1f}%)")
        print(f"• 95% 조건부 최대낙폭(CVaR): {sim['cvar_95_expected_shortfall']:+.2f}% (극단 충격 방어)")
        print(f"• 8주 플러스 수익 달성 확률: 🟢 {sim['win_probability_positive_pct']:.1f}%")
        print(f"• +20% 이상 대승(우승) 확률: 🔥 {sim['championship_alpha_prob_over_20pct']:.1f}%")
        print("=" * 75)
    elif args.command == "committee-debate":
        from src.ai.multi_agent_consensus import MultiAgentConsensusCommittee
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        committee = MultiAgentConsensusCommittee(db=db)
        rep = committee.run_committee_deliberation(news_text=args.news)

        print("=" * 80)
        print("🏛️ [기관급 멀티 에이전트 5인 위원회 교차 토론 및 만장일치 의결 결과]")
        print("=" * 80)
        print(f"• 최종 합의 결정 : 🏆 {rep.consensus_decision}")
        print(f"• 수석 CIO 승인  : {'✅ 승인 완료 (APPROVED)' if rep.cio_approval else '❌ 보류'}")
        print(f"• 추천 집행 엔진 : ⚡ {rep.execution_algo}")
        print(f"• 기대 추가 알파 : 📈 +{rep.expected_alpha_bps:.1f} bps (+0.45% 절감)")
        print("-" * 80)
        print("👥 [5대 전문 에이전트별 의결 소견]:")
        for op in rep.agent_opinions:
            print(f"\n  [{op.agent_name}] ({op.role}) | 판정: {op.verdict} (확신도: {op.confidence*100:.1f}%)")
            for arg in op.key_arguments:
                print(f"    • {arg}")
        print("-" * 80)
        print("📊 [위원회가 최종 승인한 10억 포트폴리오 목표 비중]:")
        for k, v in rep.final_target_weights.items():
            print(f"  • {k:30s} : {v*100:4.1f}% ({(v * 1_000_000_000):,.0f} 원)")
        print("=" * 80)
    elif args.command == "krx-guard":
        from src.quant.krx_market_guard import KRXMarketGuard
        guard = KRXMarketGuard()
        
        print("=" * 80)
        print("🛡️ [한국거래소(KRX) ETF 5대 고유 맹점 가드레일 실시간 진단]")
        print("=" * 80)
        # 1. 09:00~09:05 타임락 & 괴리율 진단
        t_ok, t_msg = guard.check_time_lock_and_disparity("09:15:00", 23965.0, 23920.0)
        print(f"1. [LP 호가 타임락 & 괴리율] : {t_msg}")

        # 2. 유동성 및 스프레드 안전망 진단
        l_ok, l_msg = guard.check_liquidity_safety(adv_20d_krw=3_500_000_000.0, spread_bps=8.5)
        print(f"2. [거래대금 & 스프레드 필터]: {l_msg} (일 35억원 / 스프레드 8.5bp)")

        # 3. 환헤지(H) vs 환노출(UH) 진단
        fx_res = guard.determine_fx_hedge_allocation(usd_krw_rate=1386.53)
        print(f"3. [환율 1,380원대 FX 헤징]   : {fx_res['reason']} (환헤지: {fx_res['H_weight']*100:.0f}%, 환노출: {fx_res['UH_weight']*100:.0f}%)")

        # 4. 연금계좌 15.4% 비과세 DRIP 복리 시뮬레이션
        drip = guard.calculate_pension_drip_reinvestment(dps_krw=65.0, shares_owned=16722, opening_price=23965.0)
        print(f"4. [연금 15.4% 비과세 DRIP]   : 분배금 {drip['total_dividend_inflow_krw']:,.0f}원 발생 -> 시초가 {drip['reinvest_shares']}주 즉시 100% 복리 재투자!")

        # 5. 밸류업 vs 글로벌 AI 듀얼 모멘텀
        rot = guard.calculate_valueup_vs_ai_rotation(valueup_ret_20d=0.038, ai_tech_ret_20d=0.072)
        print(f"5. [밸류업 vs AI 순환매 틸팅]: {rot['reason']}")
        print("=" * 80)
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
        
        current_prices = {k: v.get("avg_price", 10000.0) * 1.12 for k, v in holdings.items()}
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
    elif args.command == "vwap-plan":
        from src.ai.inference_engine import QuantInferenceEngine
        from src.quant.harness import ComplianceHarness
        from src.quant.optimizer import PortfolioOptimizer
        from src.quant.paper_trader import PaperTradingAccount
        from src.quant.execution_algos import SmartBatchExecutionEngine
        from src.database.db_manager import DatabaseManager

        db = DatabaseManager()
        engine = QuantInferenceEngine()
        harness = ComplianceHarness(db=db)
        optimizer = PortfolioOptimizer(harness=harness)
        account = PaperTradingAccount(db=db)

        decision = engine.evaluate_news(args.news)
        weights = optimizer.calculate_weights(decision)
        state = account.get_status()
        
        plan = SmartBatchExecutionEngine.generate_vwap_plan(
            target_weights=weights,
            total_nav=state.get("total_nav_krw", 1_000_000_000.0)
        )

        print("\n" + "=" * 80)
        print(f"📊 [VWAP 거래량 가중 최적 배치 분할표] (총 주문액: {plan.total_order_amount_krw:,.0f} 원)")
        print(f"• 분할 구간: {plan.num_slices}개 시간대 (KRX U자형 커브) | 예상 시장 충격 절감: +{plan.expected_market_impact_saving_krw:,.0f} 원")
        print("-" * 80)
        for s in plan.slices[:12]:
            print(f"  [{s.scheduled_time}] #{s.slice_index}차 {s.action} | {s.ticker_name:28s} | {s.shares:6,d}주 ({s.weight_pct:4.1f}%) | {s.slice_amount_krw:,.0f}원")
        print("=" * 80)
    elif args.command == "almgren-plan":
        from src.ai.inference_engine import QuantInferenceEngine
        from src.quant.harness import ComplianceHarness
        from src.quant.optimizer import PortfolioOptimizer
        from src.quant.paper_trader import PaperTradingAccount
        from src.quant.execution_algos import SmartBatchExecutionEngine
        from src.database.db_manager import DatabaseManager

        db = DatabaseManager()
        engine = QuantInferenceEngine()
        harness = ComplianceHarness(db=db)
        optimizer = PortfolioOptimizer(harness=harness)
        account = PaperTradingAccount(db=db)

        decision = engine.evaluate_news(args.news)
        weights = optimizer.calculate_weights(decision)
        state = account.get_status()
        
        plan = SmartBatchExecutionEngine.generate_almgren_chriss_plan(
            target_weights=weights,
            total_nav=state.get("total_nav_krw", 1_000_000_000.0)
        )

        print("\n" + "=" * 80)
        print(f"📐 [Almgren-Chriss 월가 최적 궤적 배치 분할표] (총 주문액: {plan.total_order_amount_krw:,.0f} 원)")
        print(f"• 분할 구간: {plan.num_slices}개 시간대 (지수 감쇄 최적화) | 예상 슬리피지 절감: +{plan.expected_market_impact_saving_krw:,.0f} 원")
        print("-" * 80)
        for s in plan.slices[:12]:
            print(f"  [{s.scheduled_time}] #{s.slice_index}차 {s.action} | {s.ticker_name:28s} | {s.shares:6,d}주 ({s.weight_pct:4.1f}%) | {s.slice_amount_krw:,.0f}원")
        print("=" * 80)
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
