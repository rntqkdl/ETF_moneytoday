"""
src/api/routes.py
FastAPI 엔드포인트 라우터 (RESTful DTO & Enterprise Service Controller 계층)
"""

import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.database.db_manager import DatabaseManager
from src.database.models import QuantDecisionOutput, PortfolioAllocationLog
from src.quant.harness import ComplianceHarness
from src.quant.optimizer import PortfolioOptimizer
from src.quant.execution_twap import TWAPExecutionEngine
from src.quant.paper_trader import PaperTradingAccount
from src.ai.inference_engine import QuantInferenceEngine
from src.api.scheduler_daemon import (
    get_current_tournament_stage,
    morning_briefing_and_rebalance,
    intraday_risk_and_circuit_breaker_check
)

router = APIRouter()

# DTO 요청/응답 모델
class RebalanceRequest(BaseModel):
    news_text: str = Field(..., description="매크로 뉴스 또는 산업 속보 텍스트")

class RebalanceResponse(BaseModel):
    status: str
    regime: str
    confidence: float
    target_weights: Dict[str, float]
    total_nav_krw: float
    reasoning: str
    timestamp: str

def get_db():
    return DatabaseManager()

# -----------------
# 📊 RESTful API 엔드포인트
# -----------------

@router.get("/health")
async def health_check(db: DatabaseManager = Depends(get_db)):
    """서버 상태 점검"""
    etf_count = db.execute_query("SELECT COUNT(*) as cnt FROM etf_master")[0]["cnt"]
    return {
        "status": "HEALTHY",
        "service": "Pension ETF AI Quant Engine",
        "version": "2.0.0",
        "indexed_etfs": etf_count
    }

@router.post("/api/v1/rebalance", response_model=RebalanceResponse)
async def trigger_rebalance(req: RebalanceRequest, db: DatabaseManager = Depends(get_db)):
    """실시간 뉴스 기반 AI 퀀트 리밸런싱 실행"""
    engine = QuantInferenceEngine()
    harness = ComplianceHarness(db=db)
    optimizer = PortfolioOptimizer(harness=harness)
    account = PaperTradingAccount(db=db)

    decision = engine.evaluate_news(req.news_text)
    weights = optimizer.calculate_weights(decision)
    res = account.rebalance(target_weights=weights, reasoning=decision.reasoning)

    return RebalanceResponse(
        status="SUCCESS",
        regime=decision.regime,
        confidence=decision.confidence_score,
        target_weights=weights,
        total_nav_krw=res["total_nav_krw"],
        reasoning=decision.reasoning,
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@router.get("/api/dashboard/data")
async def get_dashboard_data(db: DatabaseManager = Depends(get_db)):
    """실시간 웹 대시보드용 통합 JSON 데이터 제공"""
    account = PaperTradingAccount(db=db)
    state = account.get_status()
    stage_info = get_current_tournament_stage()

    holdings_list = []
    for name, info in state.get("holdings", {}).items():
        price_row = db.execute_query(
            "SELECT close_price, volume, trade_date FROM etf_daily_prices WHERE ticker = ? ORDER BY trade_date DESC LIMIT 1",
            (info.get("ticker", "000000"),)
        )
        cur_price = float(price_row[0]["close_price"]) if price_row else info.get("avg_price", 10000.0)
        cur_vol = int(price_row[0]["volume"]) if price_row else 0
        cur_date = price_row[0]["trade_date"] if price_row else "2026-08-27"

        holdings_list.append({
            "name": name,
            "code": info.get("ticker", "000000"),
            "shares": info.get("shares", 0),
            "current_price": cur_price,
            "valuation_krw": info.get("shares", 0) * cur_price,
            "target_weight": info.get("target_weight", 0.25),
            "volume": cur_vol,
            "trade_date": cur_date
        })

    trades_rows = db.execute_query("""
        SELECT id, trade_timestamp, ticker_name, action, shares, price, amount_krw, reasoning
        FROM paper_trades_ledger
        ORDER BY id DESC LIMIT 10
    """)
    recent_trades = [dict(r) for r in trades_rows] if trades_rows else []

    disclosures_rows = db.execute_query("""
        SELECT title, metadata, created_at 
        FROM etf_rag_documents 
        WHERE document_type IN ('DART_DISCLOSURE', 'INSTITUTIONAL_RESEARCH')
        ORDER BY id DESC LIMIT 8
    """)
    
    import json
    disclosures = []
    for d in disclosures_rows:
        meta = json.loads(d["metadata"]) if d.get("metadata") else {}
        disclosures.append({
            "corp_name": meta.get("corp_name") or meta.get("broker") or "기업공시",
            "title": d.get("title", ""),
            "date": meta.get("date") or d.get("created_at", "")[:10]
        })

    macro_rows = db.execute_query("""
        SELECT regime_detected, qwen_confidence_score, notes
        FROM portfolio_allocation_log
        WHERE regime_detected LIKE 'MACRO_%'
        ORDER BY id DESC LIMIT 3
    """)

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
    """Pinterest / Bloomberg 스타일 Enterprise Vue.js 3 대시보드 렌더링"""
    template_path = Path(__file__).parent / "templates" / "dashboard.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    return HTMLResponse(content="<h1>Dashboard Template Not Found</h1>", status_code=404)

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
    """장중 실시간 틱 동기화 및 서킷브레이커 검사 즉시 실행"""
    intraday_risk_and_circuit_breaker_check()
    return {"status": "SUCCESS", "message": "실시간 가격 갱신 및 리스크 점검 완료"}
