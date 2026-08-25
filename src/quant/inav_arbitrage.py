"""
src/quant/inav_arbitrage.py
연금형 ETF 1등 우승을 위한 iNAV(순자산가치) 괴리율 역발상 알파 & 월배당 스나이핑 엔진
(iNAV Disparity Arbitrage & Monthly Dividend Compounding Engine)
"""

import datetime
from typing import Dict, Any, List, Tuple
from src.database.db_manager import DatabaseManager

class INAVArbitrageEngine:
    """실시간 iNAV 괴리율 추적 및 저평가 차익 매수 가중치 산출기"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def calculate_disparity_score(self, current_price: float, inav: float) -> float:
        """
        괴리율 산출: ((현재가 - iNAV) / iNAV) * 100
        - 음수(디스카운트): 실제 가치보다 저평가 (매수 기회, 가산점)
        - 과도한 양수(+2% 이상 프리미엄): 과열 거품 (매수 자제, 감점)
        """
        if inav <= 0:
            return 0.0
        return ((current_price - inav) / inav) * 100.0

    def get_etf_arbitrage_ranking(self, candidate_tickers: List[str]) -> List[Dict[str, Any]]:
        """후보 ETF들의 최근 괴리율 및 유동성 점수 랭킹 산출"""
        ranked = []
        for ticker in candidate_tickers:
            row = self.db.execute_query("""
            SELECT ticker, close_price, inav, volume, trade_date 
            FROM etf_daily_prices 
            WHERE ticker = ? 
            ORDER BY trade_date DESC LIMIT 1
            """, (ticker,))
            
            if row:
                r = row[0]
                cp = float(r["close_price"])
                inav = float(r["inav"] if r["inav"] else cp)
                disparity = self.calculate_disparity_score(cp, inav)
                vol = int(r["volume"])

                # 저평가 보너스 스코어 (-1.5% 저평가 시 +1.5점, 과열 시 감점)
                arbitrage_alpha = -disparity if abs(disparity) <= 3.0 else 0.0
                
                ranked.append({
                    "ticker": ticker,
                    "close_price": cp,
                    "inav": inav,
                    "disparity_pct": round(disparity, 2),
                    "arbitrage_alpha": round(arbitrage_alpha, 2),
                    "volume": vol
                })

        return sorted(ranked, key=lambda x: x["arbitrage_alpha"], reverse=True)

    def is_dividend_reinvestment_day(self) -> Tuple[bool, str]:
        """월말 배당락 전후 월배당 스나이핑 타이밍 감지"""
        today = datetime.date.today()
        # 매월 마지막 3영업일 판별
        if today.day >= 25:
            return True, "월말 배당락 전후: 월배당(Covered Call/금융지주) ETF 분배금 자동 재투자(DRIP) 추천"
        return False, "일반 운용 국면"
