"""
src/quant/paper_trader.py
10억 원 가상 모의투자 계좌 상태 머신 및 실시간 시세 연동 매매 원장 (SQL 영구 보관)
"""

import json
import datetime
from typing import Dict, Any, List, Optional
from src.database.db_manager import DatabaseManager

class PaperTradingAccount:
    """10억 원 가상 자본 모의투자 포트폴리오 관리자"""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self._ensure_init()

    def _ensure_init(self):
        row = self.db.execute_query("SELECT * FROM paper_portfolio_state WHERE id = 1")
        if not row:
            initial_holdings = {
                "KODEX 미국AI반도체TOP3플러스": {"shares": 16722, "avg_price": 23920.0, "target_weight": 0.40, "valuation_krw": 400000000.0},
                "TIGER 미국AI전력SMR": {"shares": 18987, "avg_price": 15800.0, "target_weight": 0.30, "valuation_krw": 300000000.0},
                "ACE 미국빅테크TOP7 Plus": {"shares": 11267, "avg_price": 17750.0, "target_weight": 0.20, "valuation_krw": 200000000.0},
                "TIGER CD금리투자KIS(합성)": {"shares": 13927, "avg_price": 7180.0, "target_weight": 0.10, "valuation_krw": 100000000.0}
            }
            self.db.execute_query("""
            INSERT INTO paper_portfolio_state (
                id, cash_krw, holdings_json, total_nav_krw, peak_nav_krw, cumulative_return_pct, max_drawdown_pct, last_rebalanced_at
            ) VALUES (1, 0.0, ?, 1000000000.0, 1000000000.0, 0.0, 0.0, ?)
            """, (json.dumps(initial_holdings, ensure_ascii=False), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def get_status(self) -> Dict[str, Any]:
        """현재 계좌 상태 조회"""
        row = self.db.execute_query("SELECT * FROM paper_portfolio_state WHERE id = 1")
        if not row:
            return {}
        state = dict(row[0])
        state["holdings"] = json.loads(state["holdings_json"])
        return state

    def rebalance(self, target_weights: Dict[str, float], reasoning: str = "") -> Dict[str, Any]:
        """
        신규 목표 비중에 맞추어 10억 원 포트폴리오 리밸런싱 집행 및 원장 기록
        """
        state = self.get_status()
        current_nav = state.get("total_nav_krw", 1_000_000_000.0)
        old_holdings = state.get("holdings", {})

        new_holdings = {}
        total_eval = 0.0
        trade_logs = []

        # 최신 종가 조회 맵 (etf_daily_prices와 etf_master 조인)
        price_rows = self.db.execute_query("""
            SELECT m.name, p.ticker, p.close_price 
            FROM etf_daily_prices p
            JOIN etf_master m ON p.ticker = m.ticker
            WHERE p.trade_date = (SELECT MAX(trade_date) FROM etf_daily_prices)
        """)
        price_map = {}
        for r in price_rows:
            if r["name"]:
                price_map[r["name"]] = float(r["close_price"])
            if r["ticker"]:
                price_map[r["ticker"]] = float(r["close_price"])

        for name, weight in target_weights.items():
            price = price_map.get(name, 15000.0)
            target_amount = current_nav * weight
            shares = int(target_amount / price) if price > 0 else 0
            val_krw = shares * price
            total_eval += val_krw

            new_holdings[name] = {
                "shares": shares,
                "avg_price": price,
                "target_weight": weight,
                "valuation_krw": val_krw
            }

            old_shares = old_holdings.get(name, {}).get("shares", 0)
            diff_shares = shares - old_shares
            if diff_shares != 0:
                action = "BUY" if diff_shares > 0 else "SELL"
                trade_logs.append((
                    name, action, abs(diff_shares), price, abs(diff_shares * price),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

        # 거래 원장 기록 (paper_trades_ledger 컬럼 매핑)
        for t in trade_logs:
            self.db.execute_query("""
            INSERT INTO paper_trades_ledger (
                trade_timestamp, ticker_name, action, shares, price, amount_krw, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (t[5], t[0], t[1], t[2], t[3], t[4], reasoning))

        # 상태 업데이트
        cum_ret = ((total_eval - 1_000_000_000.0) / 1_000_000_000.0) * 100.0
        peak_nav = max(state.get("peak_nav_krw", 1_000_000_000.0), total_eval)
        mdd = ((total_eval - peak_nav) / peak_nav) * 100.0 if peak_nav > 0 else 0.0

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute_query("""
        UPDATE paper_portfolio_state SET
            holdings_json = ?,
            total_nav_krw = ?,
            peak_nav_krw = ?,
            cumulative_return_pct = ?,
            max_drawdown_pct = ?,
            last_rebalanced_at = ?
        WHERE id = 1
        """, (json.dumps(new_holdings, ensure_ascii=False), total_eval, peak_nav, cum_ret, mdd, now_str))

        return {
            "total_nav_krw": total_eval,
            "cumulative_return_pct": cum_ret,
            "max_drawdown_pct": mdd,
            "trades_count": len(trade_logs),
            "holdings": new_holdings
        }
