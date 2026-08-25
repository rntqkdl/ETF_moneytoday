"""
src/quant/paper_trader.py
10억 원 가상 포트폴리오 모의투자 샌드박스 및 일일 원장(Ledger) 추적기
대회 시작(9/21) 전 4주 동안 실전 데이터로 모의 포트폴리오를 사전 운용하여 성과 추적
"""

import json
import datetime
from typing import Dict, Any, List, Optional
from src.database.db_manager import DatabaseManager

class PaperTradingAccount:
    """10억 원 가상 포트폴리오 계좌 관리자"""

    INITIAL_CAPITAL = 1_000_000_000.0  # 10억 원

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self._init_tables()

    def _init_tables(self):
        """가상 포트폴리오 상태 및 매매 내역 테이블 생성"""
        self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS paper_portfolio_state (
            id INTEGER PRIMARY KEY DEFAULT 1,
            cash_krw REAL NOT NULL,
            holdings_json TEXT NOT NULL,       -- {"KODEX 미국AI반도체": {"shares": 10000, "avg_price": 12500}, ...}
            total_nav_krw REAL NOT NULL,
            peak_nav_krw REAL NOT NULL,
            cumulative_return_pct REAL NOT NULL,
            max_drawdown_pct REAL NOT NULL,
            last_rebalanced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        self.db.execute_query("""
        CREATE TABLE IF NOT EXISTS paper_trades_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ticker_name TEXT NOT NULL,
            action TEXT NOT NULL,             -- 'BUY', 'SELL'
            shares INTEGER NOT NULL,
            price REAL NOT NULL,
            amount_krw REAL NOT NULL,
            reasoning TEXT
        );
        """)

        # 초기 계좌 데이터 없으면 10억 원 세팅
        rows = self.db.execute_query("SELECT * FROM paper_portfolio_state WHERE id = 1")
        if not rows:
            self.db.execute_query("""
            INSERT INTO paper_portfolio_state (
                id, cash_krw, holdings_json, total_nav_krw, peak_nav_krw, cumulative_return_pct, max_drawdown_pct
            ) VALUES (1, ?, '{}', ?, ?, 0.0, 0.0)
            """, (self.INITIAL_CAPITAL, self.INITIAL_CAPITAL, self.INITIAL_CAPITAL))

    def get_status(self) -> Dict[str, Any]:
        """현재 계좌 상태 조회"""
        rows = self.db.execute_query("SELECT * FROM paper_portfolio_state WHERE id = 1")
        if not rows:
            return {}
        state = dict(rows[0])
        state["holdings"] = json.loads(state["holdings_json"])
        return state

    def rebalance(self, target_weights: Dict[str, float], estimated_prices: Optional[Dict[str, float]] = None, reasoning: str = "") -> Dict[str, Any]:
        """
        AI 목표 비중에 따른 가상 10억 원 포트폴리오 리밸런싱 실행
        """
        current_state = self.get_status()
        current_cash = current_state["cash_krw"]
        holdings = current_state["holdings"]
        
        # 기본 가격 추정치 (실제 시세 미제공 시 기본 10,000원)
        prices = estimated_prices or {}
        
        # 1. 현재 총 포트폴리오 평가액 (NAV) 계산
        current_nav = current_cash
        for name, info in holdings.items():
            price = prices.get(name, info.get("avg_price", 10000.0))
            current_nav += info["shares"] * price

        # 2. 목표 비중별 목표 금액 및 수량 계산
        new_holdings = {}
        trade_logs = []
        new_cash = current_nav

        for name, weight in target_weights.items():
            target_amount = current_nav * weight
            price = prices.get(name, 10000.0)
            target_shares = int(target_amount / max(price, 1.0))
            actual_amount = target_shares * price

            if target_shares > 0:
                new_holdings[name] = {
                    "shares": target_shares,
                    "avg_price": price,
                    "target_weight": weight,
                    "valuation_krw": actual_amount
                }
                new_cash -= actual_amount
                trade_logs.append((name, "BUY", target_shares, price, actual_amount, reasoning))

        # 3. 성과 지표 계산
        peak_nav = max(current_state["peak_nav_krw"], current_nav)
        cum_return = ((current_nav - self.INITIAL_CAPITAL) / self.INITIAL_CAPITAL) * 100.0
        mdd = ((current_nav - peak_nav) / peak_nav) * 100.0

        # 4. DB 상태 업데이트
        self.db.execute_query("""
        UPDATE paper_portfolio_state SET
            cash_krw = ?,
            holdings_json = ?,
            total_nav_krw = ?,
            peak_nav_krw = ?,
            cumulative_return_pct = ?,
            max_drawdown_pct = ?,
            last_rebalanced_at = CURRENT_TIMESTAMP
        WHERE id = 1
        """, (new_cash, json.dumps(new_holdings, ensure_ascii=False), current_nav, peak_nav, cum_return, mdd))

        # 5. 거래 원장 기록
        for log in trade_logs:
            self.db.execute_query("""
            INSERT INTO paper_trades_ledger (ticker_name, action, shares, price, amount_krw, reasoning)
            VALUES (?, ?, ?, ?, ?, ?)
            """, log)

        return {
            "total_nav_krw": current_nav,
            "cash_krw": new_cash,
            "cumulative_return_pct": cum_return,
            "max_drawdown_pct": mdd,
            "holdings_count": len(new_holdings),
            "holdings": new_holdings
        }
