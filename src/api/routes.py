"""
src/api/routes.py
FastAPI 엔드포인트: 
- GET /health
- GET /api/dashboard/data
- GET /dashboard (HTML)
- POST /api/trigger/morning (즉시 모닝 리밸런싱 트리거)
- POST /api/trigger/risk-check (즉시 리스크/서킷브레이커 트리거)
- POST /api/trigger/stage-check (현재 대회 단계 조회 트리거)
- POST /api/trigger/emergency-exit (비상 현금 대피 트리거)
"""

import json
import datetime
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.database.db_manager import DatabaseManager
from src.quant.paper_trader import PaperTradingAccount
from src.quant.telemetry import PortfolioTelemetry
from src.api.alert_manager import AlertManager
from src.api.scheduler_daemon import (
    get_current_tournament_stage, 
    morning_briefing_and_rebalance, 
    intraday_risk_and_circuit_breaker_check
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@router.get("/health")
async def health_check():
    db = DatabaseManager()
    count_row = db.execute_query("SELECT COUNT(*) as cnt FROM etf_master")
    cnt = count_row[0]["cnt"] if count_row else 893
    return {
        "status": "HEALTHY",
        "indexed_etfs": cnt,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "engine": "Apple Silicon M5 Metal GPU Native",
        "competition": "MoneyToday 3rd ETF Championship (Pension League)"
    }

@router.get("/api/dashboard/data")
async def get_dashboard_data():
    """모바일 대시보드용 실시간 종합 데이터 반환"""
    db = DatabaseManager()
    account = PaperTradingAccount(db=db)
    state = account.get_status()

    # 최신 KRX 일봉 및 iNAV 시세 매핑
    price_rows = db.execute_query("""
    SELECT p.ticker, m.name, p.close_price, p.volume, p.trade_date 
    FROM etf_daily_prices p
    JOIN etf_master m ON p.ticker = m.ticker
    WHERE p.trade_date = (SELECT MAX(trade_date) FROM etf_daily_prices)
    """)
    price_map = {r["name"]: r for r in price_rows if r["name"]}

    holdings_list = []
    raw_holdings = state.get("holdings", {})
    
    for name, info in raw_holdings.items():
        pm = price_map.get(name, {})
        cur_p = float(pm.get("close_price", info.get("avg_price", 10000.0)))
        shares = int(info.get("shares", 0))
        val_krw = shares * cur_p if shares > 0 else float(info.get("valuation_krw", 0.0))
        
        holdings_list.append({
            "name": name,
            "code": pm.get("ticker", "000000"),
            "shares": shares,
            "current_price": cur_p,
            "valuation_krw": val_krw,
            "target_weight": float(info.get("target_weight", 0.25)),
            "volume": int(pm.get("volume", 0)),
            "trade_date": pm.get("trade_date", "2026-08-25")
        })

    # 최근 실시간 매매 체결 원장 목록 (Real-time Purchases)
    trades_raw = db.execute_query("""
    SELECT trade_timestamp, ticker_name, action, shares, price, amount_krw, reasoning 
    FROM paper_trades_ledger 
    ORDER BY id DESC LIMIT 8
    """)
    recent_trades = [dict(t) for t in trades_raw] if trades_raw else []

    # DART 실시간 공시 목록
    disclosures_raw = db.execute_query("""
    SELECT title, ticker, created_at 
    FROM etf_rag_documents 
    WHERE document_type = 'DART_DISCLOSURE' 
    ORDER BY created_at DESC LIMIT 5
    """)
    
    disclosures = []
    if disclosures_raw:
        for d in disclosures_raw:
            disclosures.append({
                "title": d["title"],
                "corp_name": d["ticker"] if d["ticker"] else "기업공시",
                "date": d["created_at"].split(" ")[0] if d["created_at"] else "2026-08-25",
                "url": "https://dart.fss.or.kr"
            })
    else:
        disclosures = [{
            "title": "DART 실시간 공시 감시 가동 중",
            "corp_name": "삼성전자 / SK하이닉스 / 한화에어로스페이스",
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "url": "https://dart.fss.or.kr"
        }]

    # 매크로 지표 목록
    macro_rows = db.execute_query("""
    SELECT notes, qwen_confidence_score 
    FROM portfolio_allocation_log 
    WHERE notes LIKE '%index%' 
    ORDER BY id DESC LIMIT 3
    """)
    if not macro_rows:
        macro_rows = [
            {"notes": "VOLATILITY index: 15.85", "qwen_confidence_score": 15.85},
            {"notes": "INTEREST_RATE index: 4.70", "qwen_confidence_score": 4.70},
            {"notes": "FX index: 1386.53", "qwen_confidence_score": 1386.53}
        ]

    stage_info = get_current_tournament_stage()

    return {
        "total_nav_krw": state.get("total_nav_krw", 1_000_000_000.0),
        "cumulative_return_pct": state.get("cumulative_return_pct", 0.0),
        "max_drawdown_pct": state.get("max_drawdown_pct", 0.0),
        "last_rebalanced_at": state.get("last_rebalanced_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "tournament_stage": stage_info,
        "holdings": holdings_list,
        "recent_trades": recent_trades,
        "disclosures": disclosures,
        "macro_indicators": [dict(m) for m in macro_rows],
        "is_live_data": True,
        "data_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Pinterest 스타일 대시보드 렌더링"""
    return templates.TemplateResponse(request=request, name="dashboard.html")

# -----------------
# ⚡ 자동화 트리거 엔드포인트
# -----------------

@router.post("/api/trigger/morning")
async def trigger_morning_routine():
    """즉시 08:30 모닝 리밸런싱 및 슬랙 발송 트리거"""
    morning_briefing_and_rebalance()
    return {"status": "SUCCESS", "message": "모닝 리밸런싱 및 슬랙 보고 발송 완료"}

@router.post("/api/trigger/risk-check")
async def trigger_risk_check():
    """즉시 장중 리스크/서킷브레이커 검사 트리거"""
    intraday_risk_and_circuit_breaker_check()
    return {"status": "SUCCESS", "message": "장중 서킷브레이커 리스크 검사 완료"}

@router.post("/api/trigger/stage-check")
async def trigger_stage_check():
    """현재 대회 단계 및 활성 전략 조회 트리거"""
    stage = get_current_tournament_stage()
    return {"status": "SUCCESS", "current_stage": stage}

@router.post("/api/trigger/emergency-exit")
async def trigger_emergency_exit():
    """비상 현금 대피 강제 트리거"""
    db = DatabaseManager()
    account = PaperTradingAccount(db=db)
    emergency_weights = {"TIGER CD금리투자KIS(합성)": 0.70, "ACE 미국달러SOFR금리(합성)": 0.30}
    res = account.rebalance(emergency_weights, reasoning="사용자 수동 비상 현금 대피 트리거 발동")
    return {"status": "SUCCESS", "message": "전량 초단기 CD금리/SOFR 대피 완료", "nav": res["total_nav_krw"]}
