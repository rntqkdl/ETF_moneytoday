"""
src/database/dart_collector.py
금융감독원 전자공시시스템(DART) Open API 실시간 공시 수집기
주요 대형주(삼성전자, SK하이닉스, 금융지주, 원전/방산 등)의 실적, 수주, 자사주 소각 공시 실시간 수집
"""

import requests
import datetime
from typing import List, Dict, Any, Optional
from config.settings import settings
from src.database.db_manager import DatabaseManager

class DARTDisclosureCollector:
    """DART 전자공시 Open API 수집기"""

    BASE_URL = "https://opendart.fss.or.kr/api/list.json"

    # ETF 핵심 편입 상위 종목 코드 (고유번호 매핑)
    CORE_COMPANIES = {
        "삼성전자": "005930",
        "SK하이닉스": "000660",
        "현대차": "005380",
        "KB금융": "105560",
        "신한지주": "055550",
        "한화에어로스페이스": "012450",
        "두산에너빌리티": "034020",
        "HD현대일렉트릭": "267260",
        "효성중공업": "298040",
        "포스코홀딩스": "005490"
    }

    def __init__(self, api_key: Optional[str] = None, db: Optional[DatabaseManager] = None):
        self.api_key = api_key or settings.DART_API_KEY
        self.db = db or DatabaseManager()

    def fetch_recent_disclosures(self, days: int = 3) -> List[Dict[str, Any]]:
        """최근 days일간의 주요 기업 공시 수집"""
        if not self.api_key:
            print("⚠️ [DART Collector] DART API 키가 설정되지 않았습니다.")
            return []

        end_date = datetime.date.today().strftime("%Y%m%d")
        start_date = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y%m%d")

        params = {
            "crtfc_key": self.api_key,
            "bgn_de": start_date,
            "end_de": end_date,
            "page_no": 1,
            "page_count": 50
        }

        try:
            res = requests.get(self.BASE_URL, params=params, timeout=10)
            data = res.json()

            if data.get("status") != "000":
                print(f"⚠️ [DART API 응답]: {data.get('message')}")
                return []

            disclosures = data.get("list", [])
            print(f"📥 [DART Collector] 최근 {days}일간 {len(disclosures)}건의 전체 공시 수집 성공!")

            filtered = []
            for item in disclosures:
                corp_name = item.get("corp_name", "")
                report_nm = item.get("report_nm", "")
                rcept_dt = item.get("rcept_dt", "")
                rcept_no = item.get("rcept_no", "")

                # 주요 ETF 연관 기업이거나 핵심 키워드 포함 시 필터링
                is_core = any(comp in corp_name for comp in self.CORE_COMPANIES.keys())
                has_key_event = any(k in report_nm for k in ["공급계약", "수주", "자사주", "소각", "영업실적", "잠정실적", "유상증자", "무상증자"])

                if is_core or has_key_event:
                    title_text = f"[{corp_name}] {report_nm}"
                    filtered.append({
                        "title": title_text,
                        "corp_name": corp_name,
                        "report_name": report_nm,
                        "date": rcept_dt,
                        "receipt_no": rcept_no,
                        "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
                    })

            print(f"🎯 [DART Filter] ETF 투자에 유의미한 핵심 공시 {len(filtered)}건 추출 완료!")
            return filtered

        except Exception as e:
            print(f"❌ [DART Collector 오류]: {e}")
            return []

    def save_disclosures_to_rag(self, disclosures: List[Dict[str, Any]]):
        """수집된 공시를 RAG 지식 DB에 적재"""
        for disc in disclosures:
            title = disc.get("title", f"DART 공시: [{disc['corp_name']}] {disc['report_name']}")
            content = f"[{disc['date']}] {disc['corp_name']} 공시 발표: {disc['report_name']}. 공시 상세 링크: {disc['url']}"
            
            self.db.insert_rag_document(
                ticker="A_DART",
                doc_type="DART_DISCLOSURE",
                title=title,
                content=content,
                metadata={"corp_name": disc["corp_name"], "date": disc["date"], "url": disc["url"]}
            )
        print(f"💾 {len(disclosures)}건의 DART 공시가 RAG 지식 DB에 성공적으로 동기화되었습니다!")
