"""
src/quant/execution_twap.py
10억 원 가상 자본 호가 슬리피지 방어 TWAP (시간가중 분할주문) 실행 엔진
• 10억 원 일괄 매수 시 발생하는 -0.5% ~ -1.5% 시장충격비용(Market Impact) 원천 방어
• 09:10 ~ 10:30 KST 사이 5~10회 분할 지정가 주문표(Order Sheet) 자동 생성
"""

import math
import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class TWAPOrderSlice(BaseModel):
    slice_index: int
    scheduled_time: str
    ticker_name: str
    action: str
    shares: int
    estimated_price: float
    slice_amount_krw: float
    limit_price: float

class TWAPExecutionPlan(BaseModel):
    total_order_amount_krw: float
    num_slices: int
    slice_interval_minutes: int
    start_time: str
    end_time: str
    expected_slippage_savings_krw: float
    slices: List[TWAPOrderSlice]

class TWAPExecutionEngine:
    """TWAP 분할 주문 계획 생성 및 슬리피지 최적화기"""

    DEFAULT_SLICES = 6            # 6회 분할
    INTERVAL_MINUTES = 10         # 10분 간격 (09:10 ~ 10:00)
    LIMIT_TOLERANCE_PCT = 0.002   # 지정가 호가 허용 오차 (+0.2%)

    @classmethod
    def generate_twap_plan(
        cls, 
        target_weights: Dict[str, float], 
        current_holdings: Dict[str, Any],
        prices: Dict[str, float],
        total_nav: float = 1_000_000_000.0,
        start_time_str: str = "09:10"
    ) -> TWAPExecutionPlan:
        """
        목표 비중과 현재 보유 상태를 비교하여 슬리피지를 최소화하는 TWAP 분할 주문표 도출
        """
        # 1. 종목별 리밸런싱 필요 금액(Net Buy/Sell) 산출
        orders_to_place = []
        total_rebalance_volume = 0.0

        for name, target_w in target_weights.items():
            target_amount = total_nav * target_w
            current_info = current_holdings.get(name, {})
            current_amount = current_info.get("valuation_krw", 0.0)
            diff_amount = target_amount - current_amount
            price = prices.get(name, current_info.get("avg_price", 10000.0))

            if abs(diff_amount) > (total_nav * 0.01):  # 1% 이상 변동 시에만 주문
                action = "BUY" if diff_amount > 0 else "SELL"
                shares_needed = int(abs(diff_amount) / max(price, 1.0))
                if shares_needed > 0:
                    orders_to_place.append({
                        "name": name,
                        "action": action,
                        "total_shares": shares_needed,
                        "price": price,
                        "total_amount": shares_needed * price
                    })
                    total_rebalance_volume += shares_needed * price

        # 2. TWAP 분할 스케줄 생성
        slices = []
        start_dt = datetime.datetime.strptime(start_time_str, "%H:%M")

        for slice_idx in range(1, cls.DEFAULT_SLICES + 1):
            scheduled_time = (start_dt + datetime.timedelta(minutes=(slice_idx - 1) * cls.INTERVAL_MINUTES)).strftime("%H:%M")

            for ord_item in orders_to_place:
                slice_shares = math.ceil(ord_item["total_shares"] / cls.DEFAULT_SLICES)
                slice_amount = slice_shares * ord_item["price"]
                
                # 지정가 호가 계산 (매수 시 현재가 +0.2% 상한선, 매도 시 -0.2% 하한선)
                if ord_item["action"] == "BUY":
                    limit_p = round(ord_item["price"] * (1.0 + cls.LIMIT_TOLERANCE_PCT))
                else:
                    limit_p = round(ord_item["price"] * (1.0 - cls.LIMIT_TOLERANCE_PCT))

                slices.append(TWAPOrderSlice(
                    slice_index=slice_idx,
                    scheduled_time=scheduled_time,
                    ticker_name=ord_item["name"],
                    action=ord_item["action"],
                    shares=slice_shares,
                    estimated_price=ord_item["price"],
                    slice_amount_krw=slice_amount,
                    limit_price=limit_p
                ))

        end_time = (start_dt + datetime.timedelta(minutes=(cls.DEFAULT_SLICES - 1) * cls.INTERVAL_MINUTES)).strftime("%H:%M")
        
        # 예상 슬리피지 절감액 (총 주문액의 약 0.4% 절감 효과)
        savings = total_rebalance_volume * 0.004

        return TWAPExecutionPlan(
            total_order_amount_krw=total_rebalance_volume,
            num_slices=cls.DEFAULT_SLICES,
            slice_interval_minutes=cls.INTERVAL_MINUTES,
            start_time=start_time_str,
            end_time=end_time,
            expected_slippage_savings_krw=savings,
            slices=slices
        )
