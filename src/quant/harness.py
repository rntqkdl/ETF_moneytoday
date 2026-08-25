"""
src/quant/harness.py
머니투데이 ETF 투자왕 대회 [연금형] 컴플라이언스 가드레일 (선물·레버리지·인버스 0-Violation 차단 및 오타 보정기)
"""

import difflib
from typing import Dict, List, Set, Optional
from config.settings import settings
from src.database.db_manager import DatabaseManager

class ComplianceHarness:
    """연금형 리그 100% 규정 준수 검증 및 ETF 명칭 자동 정규화기"""

    FORBIDDEN_KEYWORDS = ["선물", "레버리지", "인버스", "2X", "3X", "-1X", "-2X", "VIX선물", "인버스2X"]

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.eligible_tickers: Set[str] = set()
        self.eligible_list: List[str] = []
        self._load_whitelist()

    def _load_whitelist(self):
        rows = self.db.execute_query("SELECT ticker, name FROM etf_master WHERE is_pension_eligible = 1")
        self.eligible_list = [r["name"] for r in rows]
        self.eligible_tickers = set(self.eligible_list)

    def resolve_valid_etf_name(self, raw_name: str) -> Optional[str]:
        """정확 일치하지 않을 경우 가장 유사한 공식 연금 적격 ETF명으로 자동 매핑"""
        if raw_name in self.eligible_tickers:
            return raw_name
        
        # 유사도 기반 최근접 공식 종목명 탐색 (Fuzzy Match)
        matches = difflib.get_close_matches(raw_name, self.eligible_list, n=1, cutoff=0.5)
        if matches:
            print(f"🔧 [Harness Auto-Fix] '{raw_name}' -> 공식명 '{matches[0]}' 자동 매핑")
            return matches[0]
        return None

    def validate_allocation(self, raw_weights: Dict[str, float]) -> Dict[str, float]:
        """
        포트폴리오 비중 검증:
        1) 10대 후원사 승인 종목 자동 정규화 및 규정 위반 차단
        2) 롱온리 (w >= 0)
        3) 단일 위험 자산 최대 비중 25% 캡 보장
        4) 초과분은 현금성 안전 자산(TIGER CD금리투자KIS)으로 오버플로우 배분
        """
        sanitized = {}
        excess_cash = 0.0

        for name, w in raw_weights.items():
            valid_name = self.resolve_valid_etf_name(name)
            if not valid_name:
                print(f"⚠️ [Harness Drop] 미승인 종목 제외: {name}")
                excess_cash += w
                continue
            
            for kw in self.FORBIDDEN_KEYWORDS:
                if kw in valid_name:
                    raise ValueError(f"🚨 [Harness Reject] 금지 키워드 포함: {valid_name}")

            if w < 0:
                raise ValueError(f"🚨 [Harness Reject] 숏/인버스 비중 불가: {valid_name} ({w})")

            # 현금성 자산이 아닌 일반 위험자산은 25% 캡 적용
            if "CD금리" not in valid_name and "SOFR" not in valid_name and "머니마켓" not in valid_name:
                if w > settings.MAX_SINGLE_ASSET_WEIGHT:
                    excess_cash += (w - settings.MAX_SINGLE_ASSET_WEIGHT)
                    sanitized[valid_name] = settings.MAX_SINGLE_ASSET_WEIGHT
                else:
                    sanitized[valid_name] = w
            else:
                sanitized[valid_name] = w

        # 초과분을 현금성 자산에 추가
        if excess_cash > 0:
            cash_asset = "TIGER CD금리투자KIS(합성)"
            sanitized[cash_asset] = sanitized.get(cash_asset, 0.0) + excess_cash

        # 정규화 (1.0 합계 유지)
        total = sum(sanitized.values())
        if total > 0:
            return {k: round(v / total, 4) for k, v in sanitized.items()}
        return sanitized
