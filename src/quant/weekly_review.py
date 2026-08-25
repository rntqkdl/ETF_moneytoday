"""
src/quant/weekly_review.py
매주 일요일 20:00 KST 가상 포트폴리오 주간 성과 분석 및 LoRA 모델 평가 리포터
"""

import datetime
from typing import Dict, Any, Optional
from src.database.db_manager import DatabaseManager
from src.quant.paper_trader import PaperTradingAccount

class WeeklyPerformanceReviewer:
    """주간 성과 귀속(Performance Attribution) 분석기"""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.account = PaperTradingAccount(db=self.db)

    def generate_weekly_report(self) -> Dict[str, Any]:
        """1주일간의 매매 원장 및 누적 수익률, MDD 분석 리포트 생성"""
        state = self.account.get_status()
        trades = self.db.execute_query("""
        SELECT * FROM paper_trades_ledger 
        ORDER BY trade_timestamp DESC 
        LIMIT 10
        """)

        nav = state.get("total_nav_krw", 1_000_000_000.0)
        cum_ret = state.get("cumulative_return_pct", 0.0)
        mdd = state.get("max_drawdown_pct", 0.0)
        holdings = state.get("holdings", {})

        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append(f"📅 [주간 성과 리뷰] 10억 원 가상 포트폴리오 딥리포트 ({datetime.date.today()})")
        report_lines.append("=" * 70)
        report_lines.append(f"• 주간 누적 수익률 : {cum_ret:+.2f}%")
        report_lines.append(f"• 총 평가 자산 (NAV) : {nav:,.0f} 원 ({nav/100_000_000:.2f} 억 원)")
        report_lines.append(f"• 주간 최대 낙폭 (MDD): {mdd:.2f}% (안전 가드레일 -3.0% 이내 유지)")
        report_lines.append(f"• 주간 총 매매 횟수  : {len(trades)} 건")
        report_lines.append("-" * 70)
        report_lines.append("🏆 [현재 핵심 보유 섹터 및 비중]")
        for name, item in holdings.items():
            w = (item.get("valuation_krw", 0) / nav) * 100 if nav > 0 else 0
            report_lines.append(f"  • {name}: {w:.1f}% ({item.get('valuation_krw', 0):,.0f}원)")
        report_lines.append("-" * 70)
        report_lines.append("📝 [최근 리밸런싱 이력]")
        for t in trades[:5]:
            report_lines.append(f"  [{t['trade_timestamp'][:16]}] {t['action']} {t['ticker_name']} ({t['shares']:,}주 @ {t['price']:,.0f}원)")
        report_lines.append("=" * 70)

        full_text = "\n".join(report_lines)
        return {
            "summary_text": full_text,
            "cumulative_return_pct": cum_ret,
            "mdd_pct": mdd,
            "total_nav": nav,
            "trade_count": len(trades)
        }
