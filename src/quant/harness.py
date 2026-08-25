"""
src/quant/harness.py
머니투데이 ETF 투자왕 대회 [연금형] 컴플라이언스 가드레일 (선물·레버리지·인버스 0-Violation 차단)
"""

from typing import Dict, List, Set
from config.settings import settings
from src.database.db_manager import DatabaseManager

class ComplianceHarness:
    """연금형 리그 100% 규정 준수 검증기"""

    FORBIDDEN_KEYWORDS = ["선물", "레버리지", "인버스", "2X", "3X", "-1X", "-2X", "VIX선물", "인버스2X"]

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.eligible_tickers: Set[str] = set()
        self._load_whitelist()

    def _load_whitelist(self):
        rows = self.db.execute_query("SELECT ticker, name FROM etf_master WHERE is_pension_eligible = 1")
        self.eligible_tickers = set(r["name"] for r in rows)

    def validate_allocation(self, raw_weights: Dict[str, float]) -> Dict[str, float]:
        """
        포트폴리오 비중 검증:
        1) 10대 후원사 승인 종목 외 차단
        2) 롱온리 (w >= 0)
        3) 단일 위험 자산 최대 비중 25% 캡 보장
        4) 초과분은 현금성 안전 자산(TIGER CD금리투자KIS)으로 오버플로우 배분
        """
        sanitized = {}
        excess_cash = 0.0

        for name, w in raw_weights.items():
            if name not in self.eligible_tickers:
                raise ValueError(f"🚨 [Harness Reject] 미승인 또는 규정 위반 종목: {name}")
            
            for kw in self.FORBIDDEN_KEYWORDS:
                if kw in name:
                    raise ValueError(f"🚨 [Harness Reject] 금지 키워드 포함: {name}")

            if w < 0:
                raise ValueError(f"🚨 [Harness Reject] 숏/인버스 비중 불가: {name} ({w})")

            # 현금성 자산이 아닌 일반 위험자산은 25% 캡 적용
            if "CD금리" not in name and "SOFR" not in name and "머니마켓" not in name:
                if w > settings.MAX_SINGLE_ASSET_WEIGHT:
                    excess_cash += (w - settings.MAX_SINGLE_ASSET_WEIGHT)
                    sanitized[name] = settings.MAX_SINGLE_ASSET_WEIGHT
                else:
                    sanitized[name] = w
            else:
                sanitized[name] = w

        # 초과분을 현금성 자산에 추가
        if excess_cash > 0:
            cash_asset = "TIGER CD금리투자KIS(합성)"
            sanitized[cash_asset] = sanitized.get(cash_asset, 0.0) + excess_cash

        # 정규화 (1.0 합계 유지)
        total = sum(sanitized.values())
        if total > 0:
            return {k: round(v / total, 4) for k, v in sanitized.items()}
        return sanitized
