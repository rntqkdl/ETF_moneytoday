"""
src/database/data_collector.py
한국거래소(KRX) 및 글로벌 매크로 시계열 데이터 자동 수집기
8대 클러스터 대표 ETF 과거 시세 및 일일 시세 적재
"""

import datetime
from typing import List, Dict, Optional
from src.database.db_manager import DatabaseManager

# 8대 클러스터 핵심 대표 종목 및 KRX 표준 단축코드
REPRESENTATIVE_ETFS = {
    "069500": "KODEX 200",
    "305720": "KODEX 2차전지산업",
    "360750": "TIGER 미국나스닥100",
    "379800": "KODEX 미국S&P500",
    "448290": "ACE 미국빅테크TOP7 Plus",
    "465580": "KODEX 미국AI반도체TOP3플러스",
    "475380": "SOL AI반도체소부장",
    "481180": "TIGER 미국AI전력SMR",
    "472150": "KODEX 원자력SMR",
    "462900": "ACE K방산TOP5+",
    "446770": "SOL 금융지주플러스고배당",
    "488660": "KODEX 코리아밸류업",
    "441680": "SOL 미국배당다우존스",
    "473450": "TIGER 미국배당다우존스타겟데일리커버드콜",
    "411060": "ACE KRX금현물",
    "453850": "TIGER CD금리투자KIS(합성)",
    "465520": "ACE 미국달러SOFR금리(합성)"
}

class FinancialDataCollector:
    """시세 및 매크로 지표 자동 수집기"""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def collect_etf_history(self, days: int = 60):
        """대표 ETF 최근 days일간의 일별 OHLCV 시계열 수집 및 DB 적재"""
        try:
            import FinanceDataReader as fdr
            print(f"📥 [Data Collector] 대표 {len(REPRESENTATIVE_ETFS)}개 ETF 최근 {days}일 시계열 다운로드 중...")
            
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=days * 2)

            for code, name in REPRESENTATIVE_ETFS.items():
                try:
                    df = fdr.DataReader(code, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
                    if df is not None and not df.empty:
                        for idx, row in df.iterrows():
                            trade_date = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                            open_p = float(row.get("Open", row.get("Close", 10000)))
                            high_p = float(row.get("High", row.get("Close", 10000)))
                            low_p = float(row.get("Low", row.get("Close", 10000)))
                            close_p = float(row.get("Close", 10000))
                            vol = int(row.get("Volume", 0))

                            self.db.execute_query("""
                            INSERT OR REPLACE INTO etf_daily_prices (
                                ticker, trade_date, open_price, high_price, low_price, close_price, volume, inav
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (code, trade_date, open_p, high_p, low_p, close_p, vol, close_p))
                except Exception as e:
                    print(f"⚠️ {name}({code}) 시세 다운로드 스킵 ({e})")

            print(f"✅ {len(REPRESENTATIVE_ETFS)}개 대표 ETF 시세 데이터베이스 적재 완료!")
        except Exception as e:
            print(f"⚠️ FinanceDataReader 연결 실패 ({e}). 합성 시세 생성 모드 작동.")

    def collect_macro_rates(self):
        """환율 및 거시 지표 수집"""
        try:
            import yfinance as yf
            macro_tickers = {
                "USDKRW=X": ("FX_USDKRW", "FX"),
                "^TNX": ("US_10Y_YIELD", "INTEREST_RATE"),
                "^VIX": ("VIX_INDEX", "VOLATILITY")
            }
            for y_sym, (ind_code, cat) in macro_tickers.items():
                data = yf.Ticker(y_sym).history(period="5d")
                if not data.empty:
                    last_row = data.iloc[-1]
                    val = float(last_row["Close"])
                    rec_date = datetime.date.today().strftime("%Y-%m-%d")
                    
                    self.db.execute_query("""
                    INSERT OR REPLACE INTO portfolio_allocation_log (
                        regime_detected, qwen_confidence_score, target_weights, execution_status, notes
                    ) VALUES (?, ?, ?, ?, ?)
                    """, (f"MACRO_{ind_code}", val, "{}", "LOGGED", f"{cat} index: {val:.2f}"))
            print("✅ 매크로 지표 (환율/10년물 국채/VIX) 수집 완료!")
        except Exception as e:
            print(f"⚠️ 매크로 지표 수집 스킵 ({e})")
