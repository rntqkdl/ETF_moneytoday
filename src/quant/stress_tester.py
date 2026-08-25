"""
src/quant/stress_tester.py
과거 5개년 역사적 위기 국면(2020 팬데믹, 2022 금리 인상 충격) 기반 10억 원 포트폴리오 스트레스 테스터
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.database.db_manager import DatabaseManager

HISTORICAL_CRISIS_SCENARIOS = {
    "2020_COVID_CRASH": {
        "name": "2020년 3월 팬데믹 글로벌 유동성 쇼크",
        "stock_shock_pct": -0.32,
        "sofr_cd_return_pct": +0.015,
        "gold_shock_pct": +0.08
    },
    "2022_INFLATION_TIGHTENING": {
        "name": "2022년 연준 급격한 금리인상(자이언트스텝) & 기술주 급락",
        "stock_shock_pct": -0.22,
        "sofr_cd_return_pct": +0.038,
        "gold_shock_pct": -0.04
    },
    "2024_SEMICONDUCTOR_FLASH_CRASH": {
        "name": "2024년 8월 글로벌 엔캐리 청산 & 반도체 일시 급락 (블랙 먼데이)",
        "stock_shock_pct": -0.12,
        "sofr_cd_return_pct": +0.008,
        "gold_shock_pct": +0.02
    }
}

class PortfolioStressTester:
    """역사적 위기 시나리오 스트레스 테스터"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def run_stress_test(self, current_weights: Dict[str, float], total_nav: float = 1_000_000_000.0) -> Dict[str, Any]:
        """현재 10억 원 포트폴리오에 역사적 위기 충격 가했을 때의 예상 손익 및 방어율 산출"""
        results = {}

        for sc_id, sc_info in HISTORICAL_CRISIS_SCENARIOS.items():
            expected_pnl = 0.0

            for name, w in current_weights.items():
                asset_amount = total_nav * w
                if "CD금리" in name or "SOFR" in name or "머니마켓" in name:
                    expected_pnl += asset_amount * sc_info["sofr_cd_return_pct"]
                elif "금현물" in name or "국제금" in name:
                    expected_pnl += asset_amount * sc_info["gold_shock_pct"]
                else:
                    expected_pnl += asset_amount * sc_info["stock_shock_pct"]

            est_nav = total_nav + expected_pnl
            est_return_pct = (expected_pnl / total_nav) * 100.0

            results[sc_id] = {
                "scenario_name": sc_info["name"],
                "initial_nav_krw": total_nav,
                "expected_loss_krw": expected_pnl,
                "stressed_nav_krw": est_nav,
                "portfolio_drawdown_pct": round(est_return_pct, 2),
                "market_benchmark_drawdown_pct": round(sc_info["stock_shock_pct"] * 100.0, 2),
                "defense_alpha_pct": round(est_return_pct - (sc_info["stock_shock_pct"] * 100.0), 2)
            }

        return results
