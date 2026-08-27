"""
src/database/data_collector.py
한국거래소(KRX) 및 글로벌 매크로 시계열 데이터 자동 수집기
8대 클러스터 대표 ETF 최근 1~3년 치 대규모 과거 시계열 데이터 및 실시간 장중 하락/상승 틱 가격 동기화
"""

import datetime
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from src.database.db_manager import DatabaseManager

# 8대 클러스터 핵심 대표 종목 및 KRX 표준 단축코드
REPRESENTATIVE_ETFS = {
    # 1. AI 반도체
    "091160": "KODEX 반도체",
    "390390": "TIGER 반도체TOP10",
    "465580": "KODEX 미국AI반도체TOP3플러스",
    "475380": "SOL AI반도체소부장",
    "381180": "TIGER 미국필라델피아반도체나스닥",
    # 2. 전력인프라 & 원자력 SMR
    "481180": "TIGER 미국AI전력SMR",
    "472150": "KODEX 원자력SMR",
    "481060": "ACE 미국SMR원자력TOP10",
    # 3. K-방산 & 글로벌 방산
    "462900": "ACE K방산TOP5+",
    "449450": "PLUS K방산",
    "487440": "HANARO 유럽방산",
    # 4. 밸류업 & 금융고배당
    "446770": "SOL 금융지주플러스고배당",
    "488660": "KODEX 코리아밸류업",
    "102780": "KODEX 삼성그룹",
    "139280": "TIGER 200 금융",
    # 5. 미국 메가캡 빅테크
    "360750": "TIGER 미국나스닥100",
    "379800": "KODEX 미국S&P500",
    "448290": "ACE 미국빅테크TOP7 Plus",
    # 6. 월배당 & 커버드콜
    "441680": "SOL 미국배당다우존스",
    "458730": "ACE 미국배당다우존스",
    # 7. 실물 금현물 & 원자재
    "411060": "ACE KRX금현물",
    # 8. 초단기 금리 / SOFR
    "453850": "TIGER CD금리투자KIS(합성)",
    "465520": "ACE 미국달러SOFR금리(합성)",
    "069500": "KODEX 200"
}

class FinancialDataCollector:
    """시세 및 매크로 지표 대규모 과거 시계열 자동 수집기"""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def collect_multi_year_history(self, years: int = 2):
        """대표 ETF 최근 years년(약 500~750 거래일) 과거 일봉 시계열 전면 수집"""
        try:
            import FinanceDataReader as fdr
            print(f"📥 [Data Collector] 8대 클러스터 {len(REPRESENTATIVE_ETFS)}개 ETF 최근 {years}년({years*365}일) 시계열 다운로드 중...")
            
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=years * 365 + 30)

            total_records = 0
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
                            total_records += 1
                except Exception as e:
                    print(f"⚠️ {name}({code}) 시세 스킵 ({e})")

            print(f"✅ {len(REPRESENTATIVE_ETFS)}개 대표 ETF 과거 {years}년치 총 {total_records:,}건 시계열 데이터베이스 적재 완료!")
        except Exception as e:
            print(f"❌ 시계열 수집 오류 ({e})")

    def sync_live_intraday_prices(self):
        """
        [장중 실시간 시세 동기화]
        - 상승/하락 가격 변동을 실시간으로 etf_daily_prices DB에 갱신
        """
        try:
            import FinanceDataReader as fdr
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            updated_count = 0

            for code in REPRESENTATIVE_ETFS.keys():
                try:
                    df = fdr.DataReader(code)
                    if df is not None and not df.empty:
                        last_row = df.iloc[-1]
                        close_p = float(last_row.get("Close", 10000))
                        vol = int(last_row.get("Volume", 0))
                        
                        self.db.execute_query("""
                        INSERT OR REPLACE INTO etf_daily_prices (
                            ticker, trade_date, open_price, high_price, low_price, close_price, volume, inav
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (code, today_str, close_p, close_p, close_p, close_p, vol, close_p))
                        updated_count += 1
                except Exception:
                    continue

            return updated_count
        except Exception as e:
            print(f"⚠️ 장중 실시간 시세 갱신 오류: {e}")
            return 0

    def calculate_empirical_covariance_and_momentum(self) -> Tuple[pd.DataFrame, pd.Series]:
        """과거 시계열 데이터를 기반으로 공분산 행렬(Sigma) 및 20일 모멘텀 산출"""
        rows = self.db.execute_query("""
        SELECT ticker, trade_date, close_price FROM etf_daily_prices
        ORDER BY trade_date ASC
        """)
        if not rows:
            return pd.DataFrame(), pd.Series()

        df = pd.DataFrame(rows)
        pivot_df = df.pivot(index="trade_date", columns="ticker", values="close_price").dropna(axis=1, thresh=30)
        
        returns_df = pivot_df.pct_change().dropna()
        cov_matrix = returns_df.cov() * 252.0
        momentum_20d = (pivot_df.iloc[-1] - pivot_df.iloc[-20]) / pivot_df.iloc[-20] if len(pivot_df) >= 20 else pd.Series()
        
        return cov_matrix, momentum_20d

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
                data = yf.Ticker(y_sym).history(period="30d")
                if not data.empty:
                    last_row = data.iloc[-1]
                    val = float(last_row["Close"])
                    
                    self.db.execute_query("""
                    INSERT OR REPLACE INTO portfolio_allocation_log (
                        regime_detected, qwen_confidence_score, target_weights, execution_status, notes
                    ) VALUES (?, ?, ?, ?, ?)
                    """, (f"MACRO_{ind_code}", val, "{}", "LOGGED", f"{cat} index: {val:.2f}"))
            print("✅ 매크로 지표 (환율/10년물 국채/VIX) 수집 완료!")
        except Exception as e:
            print(f"⚠️ 매크로 지표 수집 스킵 ({e})")
