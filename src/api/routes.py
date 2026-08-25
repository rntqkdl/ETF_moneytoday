"""
src/api/routes.py
FastAPI 엔드포인트 라우터 정의 (웹 대시보드 및 실시간 데이터 API 지원)
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
import time
import json

from src.database.db_manager import DatabaseManager
from src.rag.hybrid_search import HybridETFRAGEngine
from src.ai.inference_engine import QuantInferenceEngine
from src.quant.harness import ComplianceHarness
from src.quant.optimizer import PortfolioOptimizer
from src.quant.paper_trader import PaperTradingAccount

router = APIRouter()

db = DatabaseManager()
rag = HybridETFRAGEngine(db=db)
harness = ComplianceHarness(db=db)
optimizer = PortfolioOptimizer(harness=harness)
account = PaperTradingAccount(db=db)
ai_engine = None

def get_ai_engine():
    global ai_engine
    if ai_engine is None:
        ai_engine = QuantInferenceEngine(rag=rag)
    return ai_engine

class NewsRequest(BaseModel):
    headline: str
    content: Optional[str] = ""

@router.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "indexed_etfs": len(rag.docs),
        "engine": "Apple Silicon M5 Metal GPU"
    }

@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """반응형 실시간 웹 대시보드 UI 서빙"""
    template_path = Path(__file__).parent / "templates" / "dashboard.html"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>대시보드 템플릿을 찾을 수 없습니다.</h1>", status_code=404)

@router.get("/api/dashboard/data")
async def get_dashboard_data():
    """대시보드 실시간 렌더링용 JSON 데이터 반환"""
    state = account.get_status()
    return state

@router.post("/api/macro/evaluate")
async def evaluate_macro(req: NewsRequest):
    start = time.perf_counter()
    engine = get_ai_engine()
    decision = engine.evaluate_news(req.headline, req.content)
    weights = optimizer.calculate_weights(decision)
    latency = (time.perf_counter() - start) * 1000.0

    action = "EXECUTE_AGGRESSIVE_TILTING" if decision.confidence_score >= 0.80 else "EXECUTE_BALANCED"

    # DB 기록
    db.execute_query("""
    INSERT INTO portfolio_allocation_log (regime_detected, qwen_confidence_score, target_weights, execution_status, notes)
    VALUES (?, ?, ?, ?, ?)
    """, (
        decision.regime,
        decision.confidence_score,
        json.dumps(weights, ensure_ascii=False),
        action,
        decision.reasoning
    ))

    return {
        "regime": decision.regime,
        "confidence_score": decision.confidence_score,
        "cash_park_ratio": decision.cash_park_ratio,
        "cluster_views": [v.model_dump() for v in decision.cluster_views],
        "recommended_weights": weights,
        "execution_action": action,
        "reasoning": decision.reasoning,
        "latency_ms": round(latency, 2)
    }
