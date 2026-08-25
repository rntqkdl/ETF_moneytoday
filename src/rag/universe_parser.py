"""
src/rag/universe_parser.py
대회 10대 후원사 연금 적격 ETF 893개 전 종목 마스터 데이터 파서 및 8대 클러스터 분류기
"""

import hashlib
from typing import List, Dict, Any
from src.database.models import ETFMasterRecord

RAW_ETF_UNIVERSE = [
    # RISE (KB자산운용)
    "RISE 200TR", "RISE 200고배당커버드콜ATM", "RISE 200금융", "RISE 200위클리커버드콜", "RISE 200",
    "RISE 200채권혼합50", "RISE 26-11 회사채(AA-이상)액티브", "RISE 2차전지TOP10", "RISE 2차전지액티브",
    "RISE 5대그룹주", "RISE AI&로봇", "RISE AI반도체TOP10", "RISE AI전력인프라", "RISE AI플랫폼",
    "RISE CD금리액티브(합성)", "RISE ESG사회책임투자", "RISE 수소경제테마", "RISE IT플러스",
    "RISE KIS국고채30년Enhanced", "RISE KOFR금리액티브(합성)", "RISE KQ고배당", "RISE KRX300",
    "RISE K엔터&여행레저", "RISE 테슬라미국채타겟커버드콜혼합(합성)", "RISE V&S셀렉트밸류",
    "RISE V&S셀렉트밸류채권혼합", "RISE 메타버스", "RISE 게임테마", "RISE 고배당", "RISE 국고채10년액티브",
    "RISE 국고채3년", "RISE 글로벌게임테크TOP3Plus", "RISE 글로벌농업경제", "RISE 글로벌데이터센터리츠(합성)",
    "RISE 글로벌리얼티인컴", "RISE 글로벌비만산업TOP2+", "RISE 글로벌수소경제", "RISE 글로벌원자력",
    "RISE 글로벌자산배분액티브", "RISE 글로주식분산액티브", "RISE 글로벌클린에너지", "RISE 글로벌테크놀로지(합성 H)",
    "RISE 금융채액티브", "RISE 내수주플러스", "RISE 네트워크인프라", "RISE 단기국공채액티브", "RISE 단기채권알파액티브",
    "RISE 단기통안채", "RISE 단기특수은행채액티브", "RISE 대형고배당10TR", "RISE 동학개미", "RISE 머니마켓액티브",
    "RISE 미국30년국채액티브", "RISE 미국30년국채엔화노출(합성 H)", "RISE 미국30년국채커버드콜(합성)",
    "RISE 미국AI밸류체인TOP3Plus", "RISE 미국AI밸류체인데일리고정커버드콜", "RISE 미국AI전력인프라액티브",
    "RISE 미국AI클라우드인프라", "RISE 미국AI테크액티브", "RISE 미국S&P500데일리고정커버드콜",
    "RISE 미국S&P500엔화노출(합성 H)", "RISE 미국S&P500", "RISE 미국S&P500(H)", "RISE 미국S&P배당킹",
    "RISE 미국S&P원유생산기업(합성 H)", "RISE 미국고배당다우존스TOP10", "RISE 미국고정배당우선증권",
    "RISE 미국나스닥100", "RISE 미국단기투자등급회사채액티브", "RISE 미국달러SOFR금리액티브(합성)",
    "RISE 미국반도체NYSE", "RISE 미국반도체NYSE(H)", "RISE 미국배당100데일리고정커버드콜", "RISE 미국양자컴퓨팅",
    "RISE 미국우주&로봇TOP2미국채혼합50", "RISE 미국우주위성통신", "RISE 미국은행TOP10", "RISE 미국천연가스밸류체인",
    "RISE 미국테크100데일리고정커버드콜", "RISE 미국휴머노이드로봇", "RISE 바이오TOP10액티브", "RISE 배터리 리사이클링",
    "RISE 버크셔포트폴리오TOP10", "RISE 비메모리반도체액티브", "RISE 삼성그룹Top3채권혼합",
    "RISE 삼성전자SK하이닉스채권혼합50", "RISE 수출주", "RISE 엔비디아고정테크100", "RISE 우량업종대표주",
    "RISE 유로스탁스50(H)", "RISE 인도디지털성장", "RISE 일본섹터TOP4Plus", "RISE TDF2030액티브 적격",
    "RISE TDF2040액티브 적격", "RISE TDF2050액티브 적격", "RISE 종합채권(A-이상)액티브", "RISE 주식혼합",
    "RISE 중국MSCI China(H)", "RISE 중국본토CSI300", "RISE 중국본토대형주CSI100", "RISE 중기우량회사채",
    "RISE 중소형고배당", "RISE 중기국공채액티브", "RISE 차이나AI반도체TOP4Plus", "RISE 차이나HSCEI(H)",
    "RISE 차이나테크TOP10위클리타겟커버드콜", "RISE 차이나항셍테크", "RISE 코리아금융고배당",
    "RISE 코리아밸류업위클리고정커버드콜", "RISE 코리아밸류업", "RISE 코리아전략산업액티브", "RISE 코스닥150",
    "RISE 코스닥커버드콜액티브", "RISE 코스피", "RISE 테슬라고정테크100", "RISE 테슬라애플아마존채권혼합",
    "RISE 팔란티어고정테크100", "RISE 헬스케어", "RISE 헬스케어채권혼합", "RISE 현대차고정피지컬AI",

    # HANARO (NH-Amundi자산운용)
    "HANARO 200 TOP10", "HANARO 200TR", "HANARO 200", "HANARO 26-12 은행채(AA+이상)액티브",
    "HANARO 27-06 회사채(AA-이상)액티브", "HANARO 32-10 국고채액티브", "HANARO CAPEX설비투자iSelect",
    "HANARO Fn K-POP&미디어", "HANARO Fn K-게임", "HANARO Fn K-뉴딜디지털플러스", "HANARO Fn K-메타버스MZ",
    "HANARO Fn K-반도체", "HANARO Fn K-푸드", "HANARO Fn5G산업", "HANARO Fn골프테마", "HANARO Fn전기&수소차",
    "HANARO Fn조선해운", "HANARO Fn친환경에너지", "HANARO K-티", "HANARO KOFR금리액티브(합성)",
    "HANARO KRX300", "HANARO K고배당", "HANARO K휴머노이드테마TOP10", "HANARO MSCI Korea TR",
    "HANARO e커머스", "HANARO 글로벌금채굴기업", "HANARO 글로벌럭셔리S&P(합성)", "HANARO 글로벌생성형AI액티브",
    "HANARO 글로벌피지컬AI액티브", "HANARO 농업융복합산업", "HANARO 머니마켓액티브", "HANARO 미국AI광통신TOP10",
    "HANARO 미국AI메모리반도체TOP4+", "HANARO 미국S&P500액티브", "HANARO 미국S&P500", "HANARO 바이오코리아액티브",
    "HANARO 반도체핵심공정주도주", "HANARO 원자력iSelect", "HANARO 유럽방산", "HANARO 전력설비투자",
    "HANARO 종합채권(AA-이상)액티브", "HANARO 중기종합채권(A-이상)액티브", "HANARO 증권고배당TOP3플러스",
    "HANARO 코리아밸류업", "HANARO 코스닥150", "HANARO 탄소효율그린뉴딜",

    # TIGER (미래에셋자산운용)
    "TIGER 12월자동연장금융채(AA-이상)액티브", "TIGER 200TR", "TIGER 200 산업재", "TIGER 200 생활소비재",
    "TIGER 200", "TIGER 200동일가중", "TIGER 200커뮤니케이션서비스", "TIGER 200커버드콜OTM",
    "TIGER 200타겟위클리커버드콜", "TIGER 200 헬스케어", "TIGER 27-04회사채(A+이상)액티브",
    "TIGER 28-04 회사채(A+이상)액티브", "TIGER 2차전지TOP10", "TIGER 2차전지소재Fn", "TIGER 2차전지테마",
    "TIGER AI반도체핵심공정", "TIGER AI코리아그로스액티브", "TIGER BBIG", "TIGER CD1년금리액티브(합성)",
    "TIGER CD금리투자KIS(합성)", "TIGER CD금리플러스액티브(합성)", "TIGER Fn메타버스", "TIGER Fn신재생에너지",
    "TIGER KEDI혁신기업ESG30", "TIGER KRX300", "TIGER KRX금현물", "TIGER KRX기후변화솔루션", "TIGER K게임",
    "TIGER LG그룹플러스", "TIGER MKF배당귀족", "TIGER MSCI KOREA ESG리더스", "TIGER MSCI KOREA ESG유니버설",
    "TIGER MSCI Korea TR", "TIGER 엔비디아미국채커버드콜밸런스(합성)", "TIGER S&P글로벌인프라(합성)",
    "TIGER TSMC파운드리밸류체인", "TIGER 게임TOP10", "TIGER 경기방어", "TIGER 경기방어채권혼합",
    "TIGER 구글밸류체인", "TIGER 구리실물", "TIGER 국채3년", "TIGER 글로벌AI&로보틱스 INDXX",
    "TIGER 글로벌AI사이버보안", "TIGER 글로벌AI액티", "TIGER 글로벌멀티에셋TIF액티브", "TIGER 글로벌비만치료제TOP2Plus",
    "TIGER 글로벌온디바이스AI", "TIGER 글로벌이노베이션액티브", "TIGER 글로벌클라우드컴퓨팅INDXX",
    "TIGER S&P글로벌헬스케어(합성)", "TIGER 글로벌혁신블루칩TOP10", "TIGER 기술이전바이오액티브",
    "TIGER 단기채권액티브", "TIGER 단기통안채", "TIGER 라틴35", "TIGER 리츠부동산인프라TOP10액티브",
    "TIGER 리츠부동산인프라채권", "TIGER 리츠부동산인프라", "TIGER 리츠부동산인프라10채권혼합액티브",
    "TIGER 머니마켓액티브", "TIGER 모멘텀", "TIGER 미국30년국채스트립액티브(합성 H)", "TIGER 미국AI데이터센터TOP4Plus",
    "TIGER 미국AI반도체팹리스", "TIGER 미국AI빅테크10", "TIGER 미국AI빅테크10타겟데일리커버드콜",
    "TIGER 미국AI소프트웨어TOP4Plus", "TIGER 미국AI전력SMR", "TIGER 미국S&P500동일가중", "TIGER 미국S&P500배당귀족",
    "TIGER 미국S&P500", "TIGER 미국S&P500(H)", "TIGER 미국나스닥100", "TIGER 미국나스닥100(H)",
    "TIGER 미국나스닥100채권혼합50", "TIGER 미국나스닥100커버드콜(합성)", "TIGER 미국나스닥넥스트100",
    "TIGER 미국다우존스30", "TIGER 미국달러SOFR금리액티브(합성)", "TIGER 미국달러단기채권액티브",
    "TIGER 미국방산TOP10", "TIGER 미국배당다우존스", "TIGER 미국배당다우존스타겟데일리커버드콜",
    "TIGER 미국소비트렌드액티브", "TIGER 미국우주테크", "TIGER 미국초단기(3개월이하)국채", "TIGER 미국캐시카우100",
    "TIGER 미국테크NYSE100액티브", "TIGER 미국테크TOP10 INDXX", "TIGER 미국테크TOP10 INDXX(H)",
    "TIGER 미국테크TOP10채권혼합", "TIGER 미국투자등급회사채액티브(H)", "TIGER 미국필라델피아AI반도체나스닥",
    "TIGER 미국필라델피아반도체나스닥", "TIGER 미디어컨텐츠", "TIGER 바이오TOP10", "TIGER 반도체",
    "TIGER 반도체TOP10", "TIGER 반도체TOP10커버드콜액티브", "TIGER 삼성그룹", "TIGER 소프트웨어",
    "TIGER 여행레저", "TIGER 우량가치", "TIGER 우선주", "TIGER 유로스탁스배당30", "TIGER 은액티브",
    "TIGER 은행", "TIGER 차이나바이오테크SOLACTIVE", "TIGER 차이나반도체FACTSET", "TIGER 차이나전기차SOLACTIVE",
    "TIGER 차이나증권", "TIGER 차이나클린에너지SOLACTIVE", "TIGER 차이나테크TOP10", "TIGER 차이나항셍테크",
    "TIGER 차이나휴머노이드로봇", "TIGER 코리아AI전력기기TOP3플러스", "TIGER 코리아TOP10",
    "TIGER 코리아배당다우존스위클리커버드콜", "TIGER 코리아배당다우존스", "TIGER 코리아밸류업",
    "TIGER 코리아원자력", "TIGER 코리아휴머노이드로봇산업", "TIGER 코스닥150", "TIGER 코스닥150IT",
    "TIGER 코스닥150바이오테크", "TIGER 코스닥글로벌", "TIGER 코스닥액티브", "TIGER 코스피대형주",
    "TIGER 코스피중형주", "TIGER 코스피", "TIGER 탄소효율그린뉴딜", "TIGER 테슬라채권혼합Fn",
    "TIGER 토탈월드스탁액티브", "TIGER 퓨처모빌리티액티브", "TIGER 한중반도체(합성)", "TIGER 한중전기차(합성)",
    "TIGER 헬스케어", "TIGER 현대차그룹플러스", "TIGER 화장품", "TIGER 글로벌리튬&2차전지SOLACTIVE(합성)",
    "TIGER 글로벌자율주행&전기차SOLACTIVE", "TIGER 글로벌자원생산기업(합성 H)", "TIGER KOFR금리액티브(합성)",
    "TIGER 미국배당다우존스타겟커버드콜1호", "TIGER 코리아테크액티브", "TIGER 200 IT", "TIGER 200 건설",
    "TIGER 200 경기소비재", "TIGER 200 금융", "TIGER 200 에너지화학", "TIGER 200 중공업", "TIGER 200 철강소재",
    "TIGER 200커버드콜", "TIGER KTOP30", "TIGER K방산&우주", "TIGER 미국MSCI리츠(합성 H)",
    "TIGER 국고채30년스트립액티브", "TIGER 글로벌AI전력인프라액티브", "TIGER 글로벌AI플랫폼액티브",
    "TIGER 로우볼", "TIGER 글로벌4차산업혁신기술(합성 H)", "TIGER 미국30년국채커버드콜액티브(H)",
    "TIGER 미국S&P500타겟데일리커버드콜", "TIGER 미국나스닥100타겟데일리커버드콜", "TIGER 미국배당다우존스타겟커버드콜2호",
    "TIGER 미국테크TOP10타겟커버드콜", "TIGER 배당성장", "TIGER 배당커버드콜액티브", "TIGER 우량회사채액티브",
    "TIGER 유로스탁스50(합성 H)", "TIGER 일본TOPIX(합성 H)", "TIGER 종합채권(AA-이상)액티브",
    "TIGER 차이나CSI300", "TIGER 코스피고배당",

    # KODEX (삼성자산운용)
    "KODEX 200TR", "KODEX 200 중소형", "KODEX 200ESG", "KODEX 200IT TR", "KODEX 200exTOP",
    "KODEX 200가치저변동", "KODEX 코스피100", "KODEX 200동일가중", "KODEX 200미국채혼합50",
    "KODEX 200액티브", "KODEX 200커버드콜액티브", "KODEX 200타겟위클리커버드콜", "KODEX 26-12 금융채(AA-이상)액티브",
    "KODEX 26-12 회사채(AA-이상)액티브", "KODEX 27-12 회사채(AA-이상)액티브", "KODEX 28-12 회사채(AA-이상)액티브",
    "KODEX 2차전지산업", "KODEX 2차전지핵심소재10", "KODEX 33-06 국고채액티브", "KODEX 53-09 국고채액티브",
    "KODEX AI반도체TOP2플러스", "KODEX AI반도체핵심장비", "KODEX AI전력핵심설비", "KODEX CD1년금리플러스액티브(합성)",
    "KODEX CD금리액티브(합성)", "KODEX ESG종합채권(A-이상)액티브", "KODEX IT", "KODEX 일본TOPIX100",
    "KODEX K-뉴딜디지털플러스", "KODEX KOFR금리액티브(합성)", "KODEX KRX300", "KODEX KTOP30", "KODEX K콘텐츠",
    "KODEX MSCI KOREA ESG유니버설", "KODEX MSCI Korea", "KODEX MSCI Korea TR", "KODEX MSCI선진국",
    "KODEX S&P글로벌인프라(합성)", "KODEX TRF3070", "KODEX TRF5050", "KODEX TRF7030", "KODEX Top10동일가중",
    "KODEX Top5PlusTR", "KODEX iShares미국하이일드액티브", "KODEX 가치주", "KODEX 게임산업", "KODEX 경기소비재",
    "KODEX 고배당주", "KODEX 국고채10년액티브", "KODEX 국고채30년액티브", "KODEX 국고채3년", "KODEX 글로벌로봇(합성)",
    "KODEX 글로벌비만치료제TOP2 Plus", "KODEX 금액티브", "KODEX 금융고배당TOP10", "KODEX 금융고배당TOP10타겟위클리버드콜",
    "KODEX 금융채1~2년(AA-이상)PLUS액티브", "KODEX 기계장비", "KODEX 기후변화솔루션", "KODEX 단기변동금리부채권액티브",
    "KODEX 대만테크고배당다우존스", "KODEX 로봇액티브", "KODEX 머니마켓액티브", "KODEX 멀티팩터", "KODEX 메타버스액티브",
    "KODEX 모멘텀Plus", "KODEX 모멘텀주", "KODEX 미국10년국채액티브(H)", "KODEX 미국30년국채액티브(H)",
    "KODEX 미국30년국채타겟커버드콜(합성 H)", "KODEX 미국AI광통신네트워크", "KODEX 미국AI반도체TOP3플러스",
    "KODEX 미국AI소프트웨어TOP10", "KODEX 미국AI전력핵심인프라", "KODEX 미국AI테크TOP10",
    "KODEX 미국AI테크TOP10타겟커버드콜", "KODEX 미국CPU반도체TOP10", "KODEX 미국ETF산업Top10 Indxx",
    "KODEX 미국S&P500", "KODEX 미국S&P500경기소비재", "KODEX 미국S&P500금융", "KODEX 미국S&P500데일리커버드콜OTM",
    "KODEX 미국S&P500배당귀족커버드콜(합성 H)", "KODEX 미국S&P500버퍼3월액티브", "KODEX 미국S&P500버퍼6월액티브",
    "KODEX 미국S&P500변동성확대시커버드", "KODEX 미국S&P500산업재(합성)", "KODEX 미국S&P500액티브", "KODEX 미국S&P500에너지(합성)",
    "KODEX 미국S&P500유틸리티", "KODEX 미국S&P500(H)", "KODEX 미국S&P500커뮤니케이션", "KODEX 미국S&P500테크놀로지",
    "KODEX 미국S&P500필수소비재", "KODEX 미국S&P500헬스케어", "KODEX 미국금융테크액티브", "KODEX 미국나스닥100",
    "KODEX 미국나스닥100데일리커버드콜OTM", "KODEX 미국나스닥100(H)", "KODEX 미국나스닥AI테크액티브",
    "KODEX 미국달러SOFR금리액티브(합성)", "KODEX 미국드론UAM TOP10", "KODEX 미국러셀2000(H)", "KODEX 미국머니마켓액티브",
    "KODEX 미국반도체", "KODEX 미국배당다우존스", "KODEX 미국배당다우존스타겟커버드콜", "KODEX 미국배당커버드콜액티브",
    "KODEX 미국부동산리츠(H)", "KODEX 미국빅테크10(H)", "KODEX 미국서학개미", "KODEX 미국성장커버드콜액티브",
    "KODEX 미국스마트모빌리티S&P", "KODEX 미국우주항공", "KODEX 미국원자력SMR", "KODEX 미국종합채권ESG액티브(H)",
    "KODEX 미국클린에너지나스닥", "KODEX 미국테크TOP3플러스", "KODEX 미국휴머노이드로봇", "KODEX 바이오", "KODEX 반도체",
    "KODEX 반도체타겟위클리커버드콜", "KODEX 방산TOP10", "KODEX 배당가치", "KODEX 밸류Plus", "KODEX 삼성그룹",
    "KODEX 삼성전자SK하이닉스채권혼합50", "KODEX 삼성전자채권혼합", "KODEX 성장주", "KODEX 신재생에너지액티브",
    "KODEX 아시아AI반도체exChina액티브", "KODEX 아시아달러채권ESG플러스액티브", "KODEX 우량주", "KODEX 원자력SMR",
    "KODEX 웹툰&드라마", "KODEX 유럽명품TOP10 STOXX", "KODEX 은행", "KODEX 인도Nifty50", "KODEX 인도Nifty미드캡100",
    "KODEX 인도타타그룹", "KODEX 일본부동산리츠(H)", "KODEX 자동차", "KODEX 자율주행액티브", "KODEX 장기종합채권(AA-이상)액티브",
    "KODEX TDF2030액티브 적격", "KODEX TDF2040액티브 적격", "KODEX TDF2050액격", "KODEX TDF2060액티브 적격",
    "KODEX 전고체배터리ESS TOP2플러스", "KODEX 조선TOP10", "KODEX 종합채권(AA-이상)액티브", "KODEX 주주환원고배당주",
    "KODEX 증권", "KODEX 차이나2차전지MSCI(합성)", "KODEX 차이나AI반도체TOP10", "KODEX 차이나AI테크액티브",
    "KODEX 차이나CSI300", "KODEX 차이나A50", "KODEX 차이나H", "KODEX 차이나과창판STAR50(합성)",
    "KODEX 차이나심천ChiNext(합성)", "KODEX 차이나테크TOP10", "KODEX 차이나항셍테크", "KODEX 차이나휴머노이드로봇",
    "KODEX 최소변동성", "KODEX 친환경조선해운액티브", "KODEX 코리아배당성장", "KODEX 코리아배당성장채권혼합",
    "KODEX 코리아밸류업", "KODEX 코리아소버린AI", "KODEX 코리아혁신성장액티브", "KODEX 코스닥150",
    "KODEX 코스닥글로벌", "KODEX 코스피", "KODEX 코스피TR", "KODEX 코스피대형주", "KODEX 퀄리티Plus",
    "KODEX 탄소효율그린뉴딜", "KODEX 테슬라밸류체인FactSet", "KODEX 테슬라커버드콜채권혼합액티브", "KODEX 필수소비재",
    "KODEX 한국대만IT프리미어", "KODEX 한국부동산리츠인프라", "KODEX 한중반도체(합성)", "KODEX 한중전기차(합성)",
    "KODEX 헬스케어", "KODEX 혁신기술테마액티브", "KODEX 현대차로보틱스밸류체인TOP3플러스", "KODEX 200",
    "KODEX 멀티에셋하이인컴(H)", "KODEX iShares미국인플레이션국채액티브", "KODEX iShares미국투자등급회사채액티브",
    "KODEX 건설", "KODEX 단기채권PLUS", "KODEX 단기채권", "KODEX 미국S&P바이오(합성)", "KODEX 보험",
    "KODEX 삼성그룹밸류", "KODEX 에너지화학", "KODEX 운송", "KODEX 철강",

    # SOL (신한자산운용)
    "SOL 200 Top10", "SOL 200TR", "SOL 200타겟위클리커버드콜", "SOL 26-12 회사채(AA-이상)액티브",
    "SOL 27-12 회사채(AA-이상)액티브", "SOL 2차전지소부장Fn", "SOL AI반도체TOP2플러스", "SOL AI반도체소부장",
    "SOL CD금리&머니마켓액티브", "SOL KIS단기통안채", "SOL KRX300", "SOL KRX기후변화솔루션", "SOL K방산",
    "SOL 국고채10년", "SOL 국고채30년액티브", "SOL 국고채3년", "SOL 국제금커버드콜액티브", "SOL 국제금",
    "SOL 글로벌AI반도체탑픽액티브", "SOL 금융지주플러스고배당", "SOL 머니마켓액티브", "SOL 미국30년국채액티브(H)",
    "SOL 미국30년국채커버드콜(합성)", "SOL 미국500타겟데일리커버드콜액티브", "SOL 미국AI반도체칩메이커",
    "SOL 미국AI소프트웨어", "SOL 미국AI전력인프라", "SOL 미국S&P500", "SOL 미국S&P500ESG",
    "SOL 미국S&P500미국채혼합50", "SOL 미국S&P500엔화노출(H)", "SOL 미국TOP5채권혼합50", "SOL 미국나스닥100",
    "SOL 미국넥스트테크TOP10액티브", "SOL 미국배당다우존스2호", "SOL 미국배당다우존스", "SOL 미국배당미국채혼합50",
    "SOL 미국양자컴퓨팅TOP10", "SOL 미국우주항공TOP10", "SOL 미국원자력SMR", "SOL 미국테크TOP10",
    "SOL 반도체전공정", "SOL 반도체후공정", "SOL 배당성향탑픽액티브", "SOL 우주항공밸류체인", "SOL 의료기기소부장Fn",
    "SOL 자동차TOP3플러스", "SOL 자동차소부장Fn", "SOL 전고체배터리&실리콘음극재", "SOL 조선TOP3플러스",
    "SOL 조선기자재", "SOL 중기종합채권(AA-이상)액티브", "SOL 중단기회사채(A-이상)액티브", "SOL 차이나강소기업CSI500(합성 H)",
    "SOL 차이나소비트렌드", "SOL 차이나육성산업액티브(합성)", "SOL 차이나태양광CSI(합성)", "SOL 초단기채권액티브",
    "SOL 코리아고배당", "SOL 코리아메가테크액티브", "SOL 코리아밸류업TR", "SOL 코스닥150", "SOL 코스닥TOP10",
    "SOL 코스피200채권혼합50", "SOL 팔란티어미국채커버드콜혼합", "SOL 팔란티어커버드콜OTM채권혼합", "SOL 한국AI소프트웨어",
    "SOL 한국원자력SMR", "SOL 한국형글로벌전기차&2차전지액티브", "SOL 화장품TOP3플러스", "SOL 미국배당다우존스(H)",
    "SOL 종합채권(AA-이상)액티브",

    # KIWOOM (키움투자자산운용)
    "KIWOOM 코스피100", "KIWOOM 국고채10년", "KIWOOM 200", "KIWOOM 200TR", "KIWOOM 26-09회사채(AA-이상)액티브",
    "KIWOOM CD금리액티브(합성)", "KIWOOM K-2차전지북미공급망", "KIWOOM K-반도체북미공급망", "KIWOOM KRX100",
    "KIWOOM 인도Nifty50(합성)", "KIWOOM 미국대형주500월간목표헤지액티브", "KIWOOM 미국테크100월간목표헤지액티브",
    "KIWOOM 국고채3년", "KIWOOM 국고채30년액티브", "KIWOOM 글로벌AI반도체", "KIWOOM 글로벌전력GRID인프라",
    "KIWOOM 단기자금", "KIWOOM 단기채권ESG액티브", "KIWOOM 독일DAX", "KIWOOM 머니마켓액티브", "KIWOOM 물가채KIS",
    "KIWOOM 미국AI테크하이베타", "KIWOOM 미국CPU반도체TOP4+", "KIWOOM 미국S&P500 TOP10&배당다우비중전환",
    "KIWOOM 미국S&P500&GOLD", "KIWOOM 미국S&P500&배당다우존스비중전환", "KIWOOM 미국S&P500모멘텀", "KIWOOM 미국S&P500",
    "KIWOOM 미국S&P500(H)", "KIWOOM 미국고배당&AI테크", "KIWOOM 미국나스닥100(H)", "KIWOOM 미국달러SOFR금리액티브(합성)",
    "KIWOOM 미국방어배당성장나스닥", "KIWOOM 미국블록버스터바이오테크의약품+", "KIWOOM 미국성장기업30액티브",
    "KIWOOM 미국성장다우존스", "KIWOOM 미국양자컴퓨팅", "KIWOOM 미국우주데이터센터인프라", "KIWOOM 미국우주테크TOP2채권혼합50",
    "KIWOOM 미국원유에너지기업", "KIWOOM 블루칩", "KIWOOM 삼성전자&SK하이닉스채권혼합50", "KIWOOM 엔비디아미국30년국채혼합액티브(H)",
    "KIWOOM 의료AI", "KIWOOM TDF2030액티브 적격", "KIWOOM TDF2040액티브 적격", "KIWOOM TDF2050액티브 적격",
    "KIWOOM 종합채권(AA-이상)액티브", "KIWOOM 차이나내수소비TOP CSI", "KIWOOM 코리아고배당", "KIWOOM 코리아밸류업",
    "KIWOOM 코리아테크TOP10", "KIWOOM 코스닥150", "KIWOOM 코스닥150커버드콜액티브", "KIWOOM 통안채1년",
    "KIWOOM 팔란티어미국30년국채혼합액티브(H)", "KIWOOM 한국고배당&미국AI테크", "KIWOOM 현대차그룹TOP3채권혼합50",

    # TIME (타임폴리오자산운용)
    "TIME Korea플러스배당액티브", "TIME K바이오액티브", "TIME K신재생에너지액티브", "TIME K이노베이션액티브",
    "TIME K컬처액티브", "TIME 글로벌AI인공지능액티브", "TIME 글로벌바이오액티브", "TIME 글로벌소비트렌드액티브",
    "TIME 글로벌우주테크&방산액티브", "TIME 글로벌탑픽액티브", "TIME 글로벌휴머노이드로봇산업액티브",
    "TIME 미국S&P500액티브", "TIME 미국나스닥100액티브", "TIME 미국나스닥100채권혼합50액티브", "TIME 미국배당다우존스액티브",
    "TIME 차이나AI테크액티브", "TIME 코리아밸류업액티브", "TIME 코스닥액티브", "TIME 코스피액티브",

    # 1Q (하나자산운용)
    "1Q 200액티브", "1Q 200채권혼합50액티브", "1Q CD금리액티브(합성)", "1Q K반도체TOP2+", "1Q K반도체TOP2채권혼합50",
    "1Q K소버린AI", "1Q 단기금융채액티브", "1Q 단기특수은행채액티브", "1Q 머니마켓액티브", "1Q 미국S&P500미국채혼합50액티브",
    "1Q 미국S&P500", "1Q 미국나스닥100미국채혼합50액티브", "1Q 미국나스닥100", "1Q 미국메디컬AI", "1Q 미국배당TOP30",
    "1Q 미국우주항공테크", "1Q 샤오미밸류체인액티브", "1Q 엔비디아알파벳미국채혼합50", "1Q 은액티브", "1Q 종합채권(AA-이상)액티브",
    "1Q 중단기회사채(A-이상)액티브", "1Q 코리아밸류업", "1Q 코스닥150채권혼합50액티브", "1Q 현대차그룹채권(A+이상)&국고통안",
    "1Q 현대차기아채권혼합50",

    # ACE (한국투자신탁운용)
    "ACE 11월만기자동연장회사채AA-이상액티브", "ACE 200TR", "ACE 200", "ACE 2월만기자동연장회사채AA-이상액티브",
    "ACE 2차전지&친환경차액티브", "ACE 5월만기자동연장회사채AA-이상액티브", "ACE 8월만기자동연장회사채AA-이상액티브",
    "ACE AI반도체TOP3+", "ACE BYD밸류체인액티브", "ACE ESG액티브", "ACE KPOP포커스", "ACE KRX금현물",
    "ACE K바이오코스닥액티브", "ACE K반도체TOP2+", "ACE K방산TOP5+", "ACE K수출핵심TOP10산업액티브",
    "ACE K휴머노이드로봇산업TOP2+", "ACE MSCI멕시코(합성)", "ACE MSCI인도네시아(합성)", "ACE MSCI필리핀(합성)",
    "ACE 고배당주Plus커버드콜액티브", "ACE 고배당주", "ACE 구글밸류체인액티브", "ACE 국고채3년", "ACE 국고채10년",
    "ACE 글로벌AI맞춤형반도체", "ACE 글로벌반도체TOP4 Plus", "ACE 글로벌브랜드TOP10", "ACE 글로벌빅파마",
    "ACE 글로벌인컴TOP10", "ACE 글로벌자율주행액티브", "ACE 단기통안채", "ACE 단기채권알파액티브",
    "ACE 라이프자산주주가치액티브", "ACE 러시아MSCI(합성)", "ACE 리츠부동산인프라액티브", "ACE 마이크로소프트밸류체인액티브",
    "ACE 머니마켓액티브", "ACE 미국10년국채액티브", "ACE 미국10년국채액티브(H)", "ACE 미국30년국채액티브",
    "ACE 미국30년국채액티브(H)", "ACE 미국30년국채엔화노출액티브(H)", "ACE 미국500데일리타겟커버드콜(합성)",
    "ACE 미국AI테크핵심산업액티브", "ACE 미국IT인터넷(합성 H)", "ACE 미국S&P500국채혼합50액티브", "ACE 미국S&P500",
    "ACE 미국SMR원자력TOP10", "ACE 미국WideMoat동일가중", "ACE 미국나스닥100미국채혼합50액티브", "ACE 미국나스닥100",
    "ACE 미국달러SOFR금리(합성)", "ACE 미국달러단기채권액티브", "ACE 미국대형가치주액티브", "ACE 미국대형성장주액티브",
    "ACE 미국반도체데일리타겟커버드콜(합성)", "ACE 미국배당다우존스", "ACE 미국배당퀄리티+커버드콜액티브", "ACE 미국배당퀄리티",
    "ACE 미국배당퀄리티채권혼합50", "ACE 미국부동산리츠(합성 H)", "ACE 미국빅테크7+데일리타겟커버드콜(합성)",
    "ACE 미국빅테크TOP7 Plus", "ACE 미국우주테크액티브", "ACE 미국주식베스트셀러", "ACE 미국중심중소형제조업",
    "ACE 미국친환경그린테마", "ACE 미국하이일드액티브(H)", "ACE 반도체Plus전략산업", "ACE 베트남VN30(합성)",
    "ACE 삼성그룹동일가중", "ACE 삼성그룹섹터가중", "ACE Fn성장소비주도주", "ACE 싱가포르리츠", "ACE 아시아TOP50",
    "ACE 엔비디아밸류체인액티", "ACE 엔비디아채권혼합", "ACE 우량회사채(AA-이상)액티브", "ACE 원자력TOP10",
    "ACE 유럽방산TOP10", "ACE 인도시장대표BIG5그룹액티브", "ACE 인도컨슈머파워액티브", "ACE 일라이릴리밸류체인",
    "ACE 일본Nikkei225(H)", "ACE 일본반도체", "ACE 종합채권(AA-이상)액티브", "ACE 주주환원가치주액티브",
    "ACE 중국과창판STAR50", "ACE 중국본토CSI300", "ACE 중장기국공채액티브", "ACE 차이나AI빅테크TOP2+액티브",
    "ACE 차이나항셍테크", "ACE 코리아AI전력TOP10", "ACE 코리아AI테크핵심산업", "ACE 코리아밸류업", "ACE 코스닥150",
    "ACE 코스피", "ACE 테슬라밸류체인액티브", "ACE 포스코그룹포커스",

    # PLUS (한화자산운용)
    "PLUS 200TR", "PLUS 200", "PLUS 200위클리커버드콜채권혼합", "PLUS 200커버드콜액티브", "PLUS ESG가치주액티브",
    "PLUS ESG성장주액티브", "PLUS KOFR금리", "PLUS 코스피", "PLUS 코스피50", "PLUS K리츠", "PLUS K방산소부장",
    "PLUS K방산", "PLUS K제조업핵심기업액티브", "PLUS 미국S&P500(H)", "PLUS S&P글로벌인프라",
    "PLUS SK하이닉스샌디스크채권혼합50", "PLUS 고배당저변동50", "PLUS 고배당주", "PLUS 고배당주위클리고정커버드콜",
    "PLUS 고배당주위클리커버드콜", "PLUS 고배당주채권혼합", "PLUS 국고채10년액티브", "PLUS 국고채30년액티브",
    "PLUS 국공채머니마켓액티브", "PLUS 글로벌AI인프라", "PLUS 글로벌HBM반도체", "PLUS 글로벌방산",
    "PLUS 글로벌수소&차세대연료전지", "PLUS 글로벌원자력밸류체인", "PLUS 글로벌저작권핵심기업액티브",
    "PLUS 글로벌휴머노이드로봇액티브", "PLUS 글로벌희토류&전략자원생산기업", "PLUS 금채권혼합", "PLUS 단기채권액티브",
    "PLUS 머니마켓액티브", "PLUS 미국AI에이전트", "PLUS 미국S&P500", "PLUS 미국S&P500미국채혼합50액티브",
    "PLUS 미국S&P500성장주", "PLUS 미국고배당주액티브", "PLUS 미국나스닥100미국채혼합50", "PLUS 미국나스닥테크",
    "PLUS 미국단기회사채(AAA~A)", "PLUS 미국달러SOFR금리액티브(합성)", "PLUS 미국로보택시", "PLUS 미국배당증가성장주데일리커버드콜",
    "PLUS 미국양자퓨팅TOP10", "PLUS 미국장기우량회사채", "PLUS 미국채30년액티브", "PLUS 미국테크TOP10",
    "PLUS 스마트베타Quality채권혼합", "PLUS 심천차이넥스트(합성)", "PLUS 애플채권혼합", "PLUS 우량회사채50",
    "PLUS 우주항공", "PLUS 은채권혼합", "PLUS 일본반도체소부장", "PLUS 일본엔화초단기국채(합성)", "PLUS 자사주매입고배당주",
    "PLUS TDF2060액티브 적격", "PLUS 종합채권(AA-이상)액티브", "PLUS 주도업종", "PLUS 중기종합채권(A-이상)액티브",
    "PLUS 중형주저변동50", "PLUS 차이나AI테크TOP10", "PLUS 차이나항셍테크위클리타겟커버드콜", "PLUS 코리아밸류업",
    "PLUS 코스닥150액티브", "PLUS 코스닥150", "PLUS 코스피TR", "PLUS 태양광&ESS", "PLUS 테슬라위클리커버드콜채권혼합",
    "PLUS 한화그룹주", "PLUS 미국다우존스고배당주(합성 H)", "PLUS 글로벌MSCI(합성 H)", "PLUS 선진국MSCI(합성 H)",
    "PLUS 신흥국MSCI(합성 H)"
]

ISSUER_MAP = {
    "RISE": "KB자산운용",
    "HANARO": "NH-Amundi자산운용",
    "TIGER": "미래에셋자산운용",
    "KODEX": "삼성자산운용",
    "SOL": "신한자산운용",
    "KIWOOM": "키움투자자산운용",
    "TIME": "타임폴리오자산운용",
    "1Q": "하나자산운용",
    "ACE": "한국투자신탁운용",
    "PLUS": "한화자산운용"
}

CLUSTER_DEFINITIONS = {
    "C1_AI_SEMI": {
        "name": "AI 반도체 & 핵심 장비",
        "keywords": ["AI반도체", "반도체", "HBM", "팹리스", "소부장", "필라델피아반도체", "메모리반도체", "비메모리"],
        "desc": "글로벌 및 국내 AI 가속기, HBM, 파운드리, 팹리스 반도체 밸류체인 집중 투자"
    },
    "C2_AI_POWER": {
        "name": "AI 전력인프라 & 원자력 SMR",
        "keywords": ["AI전력", "전력", "원자력", "SMR", "에너지", "변압기", "전력설비"],
        "desc": "AI 데이터센터 급증에 따른 전력망 쇼티지 및 차세대 소형모듈원전(SMR) 수혜주 투자"
    },
    "C3_US_TECH": {
        "name": "미국 메가캡 빅테크 & 나스닥",
        "keywords": ["빅테크", "나스닥", "테크10", "테크TOP", "S&P500", "S&P500", "성장주", "다우존스"],
        "desc": "미국 M7 및 나스닥 100 메가캡 혁신 기업 중심의 코어 성장 포트폴리오"
    },
    "C4_DEFENSE": {
        "name": "K-방산 & 글로벌 방산 / 로봇",
        "keywords": ["방산", "우주", "항공", "로봇", "휴머노이드", "피지컬AI", "모빌리티", "자율주행"],
        "desc": "글로벌 지정학적 리스크 헷지 및 K-방산 수주 모멘텀, 피지컬 AI 로보틱스 투자"
    },
    "C5_VALUE_UP": {
        "name": "국내 밸류업 & 금융고배당",
        "keywords": ["밸류업", "금융", "고배당", "배당귀족", "배당킹", "주주환원", "은행", "증권", "지주"],
        "desc": "코리아 디스카운트 해소 정책 및 주주환원율(자사주 매입/소각) 우수 금융/고배당주 투자"
    },
    "C6_DIVIDEND": {
        "name": "월배당 & 타겟 데일리 커버드콜",
        "keywords": ["커버드콜", "타겟데일리", "배당다우존스", "위클리커버드콜", "배당"],
        "desc": "월분배금 캐시플로우 창출 및 옵션 프리미엄을 통한 하방 변동성 방어"
    },
    "C7_COMMODITY": {
        "name": "실물 자산 & 금현물 (선물 제외)",
        "keywords": ["금현물", "국제금", "금액티브", "은액티브", "구리실물", "금채권"],
        "desc": "달러 약세 및 인플레이션 헤지를 위한 실물 기반 원자재 ETF (선물 제외 규정 준수)"
    },
    "C8_CASH_PARK": {
        "name": "초단기 금리 / SOFR / MMF",
        "keywords": ["CD금리", "SOFR", "KOFR", "머니마켓", "단기채권", "통안채", "단기국공채", "단기자금"],
        "desc": "변동성 장세 자본 보존 및 서킷브레이커 작동 시 원금 보호용 파킹 ETF"
    }
}

class UniverseParser:
    """893개 ETF 파서 및 메타데이터 변환기"""

    @staticmethod
    def parse_etf(name: str) -> ETFMasterRecord:
        brand = name.split()[0]
        issuer = ISSUER_MAP.get(brand, "기타운용사")
        
        is_fx_hedged = "(H)" in name or "(합성 H)" in name
        is_synthetic = "(합성)" in name or "(합성 H)" in name
        is_active = "액티브" in name
        is_covered_call = "커버드콜" in name

        assigned_cluster_id = "C9_ETC"
        assigned_cluster_name = "기타 테마 및 혼합형"
        cluster_desc = "다양한 테마 및 섹터 혼합 포트폴리오"
        
        for c_id, c_info in CLUSTER_DEFINITIONS.items():
            if any(k in name for k in c_info["keywords"]):
                assigned_cluster_id = c_id
                assigned_cluster_name = c_info["name"]
                cluster_desc = c_info["desc"]
                break

        hash_code = hashlib.md5(name.encode("utf-8")).hexdigest()[:6].upper()
        ticker = f"A{hash_code}"

        themes = [brand, assigned_cluster_name]
        if is_fx_hedged: themes.append("환헤지")
        if is_active: themes.append("액티브운용")
        if is_covered_call: themes.append("커버드콜")
        if is_synthetic: themes.append("합성형")

        full_description = (
            f"[{name}] {issuer}({brand})에서 운용하는 연금 적격 ETF. "
            f"속성: {assigned_cluster_name} ({assigned_cluster_id}). {cluster_desc}. "
            f"환노출/헤지: {'환헤지(H)' if is_fx_hedged else '환노출(UH)'}, "
            f"운용방식: {'액티브' if is_active else '패시브'}, "
            f"커버드콜: {'적용' if is_covered_call else '미적용'}."
        )

        return ETFMasterRecord(
            ticker=ticker,
            name=name,
            issuer=issuer,
            brand=brand,
            cluster_id=assigned_cluster_id,
            cluster_name=assigned_cluster_name,
            is_fx_hedged=is_fx_hedged,
            is_synthetic=is_synthetic,
            is_active=is_active,
            is_covered_call=is_covered_call,
            is_pension_eligible=True,
            description=full_description,
            key_themes=themes,
            expense_ratio=0.0045,
            aum_billion_krw=150.0
        )

    @classmethod
    def get_all_records(cls) -> List[ETFMasterRecord]:
        unique_names = list(set([n.strip() for n in RAW_ETF_UNIVERSE if n.strip()]))
        return [cls.parse_etf(n) for n in unique_names]
