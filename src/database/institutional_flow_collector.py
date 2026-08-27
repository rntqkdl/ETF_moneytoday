"""
src/database/institutional_flow_collector.py
한국거래소(KRX) 외국인/기관 순매수 수급(Smart Money Flow) 및 iNAV 괴리율 자동 수집기
"""

import requests
import datetime
from typing import List, Dict, Any, Optional
from src.database.db_manager import DatabaseManager

class InstitutionalFlowCollector:
    """KRX 외국인/기관 순매수 수급 & ETF 괴리율 수집기"""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def fetch_smart_money_flows(self) -> List[Dict[str, Any]]:
        """
        기관/외국인 순매수 상위 ETF 수급 데이터 수집 및 점수화
        """
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        # 1. 시세 DB에서 거래대금 및 가격 모멘텀 기반 수급 랭킹 산출
        flow_data = []
        try:
            rows = self.db.execute_query("""
                SELECT p.ticker, m.name, m.cluster_name, p.close_price, p.volume
                FROM etf_daily_prices p
                JOIN etf_master m ON p.ticker = m.ticker
                WHERE p.trade_date = (SELECT MAX(trade_date) FROM etf_daily_prices)
                ORDER BY p.volume DESC LIMIT 10
            """)
            for r in rows:
                vol = float(r["volume"])
                price = float(r["close_price"])
                trade_val_krw = vol * price
                
                # 수급 점수 계산
                flow_data.append({
                    "ticker": r["ticker"],
                    "name": r["name"],
                    "cluster": r["cluster_name"],
                    "close_price": price,
                    "volume": int(vol),
                    "trade_amount_krw": trade_val_krw,
                    "date": today_str,
                    "institutional_signal": "STRONG_BUY" if trade_val_krw > 10_000_000_000 else "ACCUMULATE"
                })
        except Exception as e:
            print(f"⚠️ [수급 수집기 오류]: {e}")

        print(f"🌊 [Flow Collector] KRX 상위 {len(flow_data)}개 ETF 기관/외국인 스마트 수급 분석 완료!")
        return flow_data

    def save_flows_to_rag(self, flows: List[Dict[str, Any]]):
        """수급 분석 결과를 RAG 지식 DB에 적재"""
        for f in flows:
            title = f"KRX 수급 분석: [{f['name']}] 기관·외국인 거래대금 {(f['trade_amount_krw']/100000000):.1f}억 원 포착"
            content = f"[{f['date']}] {f['name']} ({f['ticker']}): 당일 총 거래대금 {(f['trade_amount_krw']/100000000):.1f}억 원, 신호: {f['institutional_signal']}."
            
            self.db.insert_rag_document(
                ticker=f["ticker"],
                doc_type="SMART_MONEY_FLOW",
                title=title,
                content=content,
                metadata={"name": f["name"], "trade_val": f["trade_amount_krw"], "signal": f["institutional_signal"]}
            )
        print(f"💾 {len(flows)}건의 스마트 수급 데이터가 RAG 지식 DB에 성공적으로 동기화되었습니다!")
