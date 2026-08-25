"""
src/quant/telemetry.py
가상 포트폴리오 성과 텔레메트리 및 시각화 대시보드 리포터
"""

from typing import Dict, Any
from src.quant.paper_trader import PaperTradingAccount

class PortfolioTelemetry:
    """성과 보고서 및 대시보드 생성기"""

    @classmethod
    def render_dashboard(cls, account: PaperTradingAccount) -> str:
        state = account.get_status()
        if not state:
            return "⚠️ 가상 계좌 데이터를 찾을 수 없습니다."

        nav = state["total_nav_krw"]
        cash = state["cash_krw"]
        ret = state["cumulative_return_pct"]
        mdd = state["max_drawdown_pct"]
        last_update = state.get("last_rebalanced_at", "N/A")
        holdings = state.get("holdings", {})

        report = []
        report.append("=" * 70)
        report.append("📊 [머니투데이 ETF 투자왕] 10억 원 가상 포트폴리오 실시간 현황")
        report.append("=" * 70)
        report.append(f"• 총 평가 자산 (NAV)  : {nav:,.0f} 원 ({nav/100_000_000:.2f} 억 원)")
        report.append(f"• 보유 현금 (Cash)     : {cash:,.0f} 원 ({cash/nav*100:.1f}%)")
        report.append(f"• 누적 수익률          : {ret:+.2f}%")
        report.append(f"• 최대 낙폭 (MDD)      : {mdd:.2f}%")
        report.append(f"• 최근 리밸런싱 일시   : {last_update}")
        report.append("-" * 70)
        report.append("📌 [현재 보유 ETF 포지션]")

        if not holdings:
            report.append("  (보유 포지션 없음 - 100% 현금 대기 중)")
        else:
            for idx, (name, item) in enumerate(holdings.items(), 1):
                val = item.get("valuation_krw", 0)
                shares = item.get("shares", 0)
                w = (val / nav) * 100 if nav > 0 else 0
                report.append(f"  {idx}. [{name}]")
                report.append(f"     • 수량: {shares:,} 주 | 평가액: {val:,.0f} 원 | 비중: {w:.1f}%")
        report.append("=" * 70)
        return "\n".join(report)
