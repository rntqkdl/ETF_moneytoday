"""
src/quant/krx_market_guard.py
한국거래소(KRX) ETF 시장 고유의 제도적 맹점 방어 및 연금형 특화 가드레일 엔진
1. 09:00~09:05 LP 호가 부재 타임락 & iNAV 0.5% 괴리율 필터
2. 일평균 10억 미만 / 스프레드 20bp 초과 슬리피지 회피 필터
3. 원/달러 1,380원대 환헤지(H) vs 환노출(UH) 동적 스위칭
4. 연금계좌 15.4% 배당세 비과세 100% DRIP 복리 엔진
5. 한국 밸류업 vs 글로벌 AI 듀얼 모멘텀 순환매 틸팅
"""

import math
import datetime
from typing import Dict, Any, Tuple, List
from src.database.db_manager import DatabaseManager

class KRXMarketGuard:
    """한국거래소(KRX) ETF 특화 가드레일 및 알파 창출 엔진"""

    def __init__(self, db: DatabaseManager = None):
        self.db = db or DatabaseManager()

    def check_time_lock_and_disparity(
        self, 
        current_time_str: str, 
        market_price: float, 
        inav: float
    ) -> Tuple[bool, str]:
        """
        [가드 1] 09:00~09:05 LP 호가 부재 시간대 거래 차단 및 iNAV 괴리율 0.5% 초과 차단
        """
        # 1. 09:00 ~ 09:05 타임락
        if "09:00:00" <= current_time_str < "09:05:00":
            return False, "🚨 [REJECT] 09:00~09:05 LP 호가 제출 의무 면제 시간대: 시장가 진입 금지"

        # 2. 괴리율 0.5% 초과 차단
        if inav > 0:
            disparity = abs((market_price - inav) / inav)
            if disparity > 0.005:  # 0.5% 초과
                return False, f"⚠️ [REJECT] iNAV 괴리율({disparity*100:.2f}%) 허용 한도(0.5%) 초과 과열 상태"

        return True, "✅ [APPROVED] LP 호가 정상 및 괴리율 안전권"

    def check_liquidity_safety(
        self, 
        adv_20d_krw: float, 
        spread_bps: float
    ) -> Tuple[bool, str]:
        """
        [가드 2] 일평균 거래대금 10억 미만 또는 호가 스프레드 20bp(0.2%) 초과 슬리피지 회피
        """
        if adv_20d_krw < 1_000_000_000:
            return False, f"⚠️ [FILTER] 일평균 거래대금({adv_20d_krw/100000000:.1f}억) 10억 원 미만으로 유동성 부족 제외"
        if spread_bps > 20.0:
            return False, f"⚠️ [FILTER] 호가 스프레드({spread_bps:.1f} bp) 20bp 초과로 슬리피지 위험 제외"

        return True, "✅ [APPROVED] 유동성 및 호가 스프레드 적격"

    def determine_fx_hedge_allocation(
        self, 
        usd_krw_rate: float, 
        sma_20: float = 1385.0, 
        sma_60: float = 1370.0
    ) -> Dict[str, float]:
        """
        [가드 3] 원/달러 환율 1,380원대 고점 논란 시 환헤지(H) vs 환노출(UH) 동적 스위칭
        - 환율 하락 추세(SMA20 < SMA60) 또는 1,380원 이상 고점 시: 환헤지(H) 비중 확대
        """
        if usd_krw_rate >= 1380.0 or sma_20 < sma_60:
            return {"UH_weight": 0.30, "H_weight": 0.70, "reason": "환율 1,380원대 상단 도달 -> 환헤지(H) 70% 방어 틸팅"}
        else:
            return {"UH_weight": 1.00, "H_weight": 0.00, "reason": "환율 안정 상승 추세 -> 환노출(UH) 100% 알파 수취"}

    def calculate_pension_drip_reinvestment(
        self, 
        dps_krw: float, 
        shares_owned: int, 
        opening_price: float
    ) -> Dict[str, Any]:
        """
        [가드 4] 연금계좌 15.4% 배당세 비과세 100% DRIP(배당 재투자) 수량 계산
        """
        if opening_price <= 0:
            return {"reinvest_shares": 0, "cash_left_krw": 0.0}

        total_cash_inflow = dps_krw * shares_owned  # 15.4% 세금 0원 적용
        reinvest_shares = math.floor(total_cash_inflow / opening_price)
        cash_left = total_cash_inflow - (reinvest_shares * opening_price)

        return {
            "tax_rate_applied": 0.0,
            "total_dividend_inflow_krw": total_cash_inflow,
            "reinvest_shares": reinvest_shares,
            "cash_left_krw": cash_left
        }

    def calculate_valueup_vs_ai_rotation(
        self, 
        valueup_ret_20d: float, 
        ai_tech_ret_20d: float
    ) -> Dict[str, Any]:
        """
        [가드 5] 한국형 밸류업(금융/지주) vs 글로벌 AI 20일 듀얼 모멘텀 순환매 틸팅
        """
        if valueup_ret_20d > ai_tech_ret_20d:
            return {
                "leader": "KOREA_VALUE_UP",
                "weights": {"ValueUp": 0.70, "GlobalAI": 0.30},
                "spread_bps": round((valueup_ret_20d - ai_tech_ret_20d) * 10000, 1),
                "reason": f"한국 밸류업 20일 모멘텀({valueup_ret_20d*100:+.1f}%)이 글로벌 AI({ai_tech_ret_20d*100:+.1f}%)를 앞섬 -> 밸류업 70% 틸팅"
            }
        else:
            return {
                "leader": "GLOBAL_AI_TECH",
                "weights": {"ValueUp": 0.30, "GlobalAI": 0.70},
                "spread_bps": round((ai_tech_ret_20d - valueup_ret_20d) * 10000, 1),
                "reason": f"글로벌 AI 20일 모멘텀({ai_tech_ret_20d*100:+.1f}%)이 밸류업({valueup_ret_20d*100:+.1f}%)을 앞섬 -> AI 70% 틸팅"
            }
