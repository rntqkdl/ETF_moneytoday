"""
n8n_fastapi_bridge.py
n8n 워크플로우와 Apple M5 Metal GPU (Qwen LoRA, RAG, skfolio, DB)를 연결하는 초저지연 REST API 서버
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import json
import time
import os

from rag_engine import HybridETFRAGEngine
from db_manager import DatabaseManager

app = FastAPI(title="Pension ETF Quant Multi-Agent Bridge", version="2.0.0")

# 싱글톤 DB 및 RAG 엔진 인메모리 로드
db = DatabaseManager()
rag = HybridETFRAGEngine(db=db)

# Qwen LoRA 모델 로드 (지연 로딩 지원)
model = None
tokenizer = None
MODEL_PATH = "mlx-community/Qwen2.5-7B-Instruct-4bit"
ADAPTER_PATH = os.path.join(os.path.dirname(__file__), "adapters/pension_qwen7b_lora")

def get_model():
    global model, tokenizer
    if model is None:
        try:
            from mlx_lm import load
            print(f"🤖 [FastAPI Bridge] Apple Silicon M5 Metal GPU로 LoRA 어댑터 상주 로드 중 ({ADAPTER_PATH})...")
            model, tokenizer = load(MODEL_PATH, adapter_path=ADAPTER_PATH)
            print("✅ Qwen 2.5 LoRA 모델 메모리 상주 완료 (keep_alive 24h)")
        except Exception as e:
            print(f"⚠️ 모델 로드 경고 ({e}). 모의 추론 모드로 구동합니다.")
            model = "MOCK"
    return model, tokenizer

class NewsEvaluationRequest(BaseModel):
    headline: str
    content: Optional[str] = ""
    source: Optional[str] = "NEWS"

class ClusterViewItem(BaseModel):
    cluster_id: str
    expected_return: float
    confidence: float
    top_pick: str

class QuantDecisionResponse(BaseModel):
    regime: str
    confidence_score: float
    cluster_views: List[ClusterViewItem]
    cash_park_ratio: float
    reasoning: str
    recommended_weights: Dict[str, float]
    execution_action: str
    latency_ms: float

@app.get("/health")
async def health_check():
    return {"status": "HEALTHY", "engine": "Apple Silicon M5 Metal", "universe_count": len(rag.docs)}

@app.post("/api/macro/evaluate", response_model=QuantDecisionResponse)
async def evaluate_market_news(req: NewsEvaluationRequest):
    """뉴스/공시 입력 -> RAG 후보군 추출 -> Qwen LoRA 추론 -> 목표 비중 산출"""
    start_time = time.perf_counter()
    full_text = f"{req.headline} {req.content}".strip()

    # 1. RAG 후보군 검색
    rag_context = rag.build_qwen_context_prompt(full_text)

    # 2. Qwen LoRA 추론
    m, tok = get_model()
    if m != "MOCK":
        from mlx_lm import generate
        system_prompt = (
            "당신은 머니투데이 제3회 ETF 투자왕 대회(연금형 부문, 10억 원 모의투자)의 수석 퀀트 AI 에이전트입니다. "
            "선물, 레버리지, 인버스 ETF는 절대 매매할 수 없으며 오직 10대 후원사의 연금 적격 현물 ETF 8대 클러스터에 대해서만 "
            "거시 국면(regime), 투자 확신도(confidence_score 0.0~1.0), 클러스터별 기대초과수익률 및 탑픽, 현금보유비율(cash_park_ratio), "
            "판단 근거(reasoning)를 순수 JSON 형식으로 정확히 출력하십시오."
        )
        user_prompt = f"{full_text}\n\n{rag_context}\n\n위 정보를 바탕으로 최적의 포트폴리오 뷰를 JSON으로만 출력하십시오."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        raw_response = generate(m, tok, prompt=prompt, max_tokens=512, verbose=False)
    else:
        # Fallback Mock Logic
        raw_response = json.dumps({
            "regime": "Macro_Inflow_Cycle",
            "confidence_score": 0.88,
            "cluster_views": [
                {"cluster_id": "C1_AI_SEMI", "expected_return": 0.055, "confidence": 0.92, "top_pick": "KODEX 미국AI반도체TOP3플러스"},
                {"cluster_id": "C3_US_TECH", "expected_return": 0.045, "confidence": 0.89, "top_pick": "ACE 미국빅테크TOP7 Plus"}
            ],
            "cash_park_ratio": 0.10,
            "reasoning": "RAG 검색 기반 상위 수혜 섹터 도출 및 롱 틸팅."
        })

    # 3. JSON 파싱
    try:
        clean_json = raw_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
        
        decision_data = json.loads(clean_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM JSON 파싱 오류: {str(e)} | Raw: {raw_response}")

    # 4. 목표 비중 계산 (확신도 가중 배분)
    conf = decision_data.get("confidence_score", 0.5)
    cash_ratio = decision_data.get("cash_park_ratio", 0.10)
    views = decision_data.get("cluster_views", [])
    
    recommended_weights = {}
    if views:
        equity_budget = max(0.0, 1.0 - cash_ratio)
        per_asset_w = round(equity_budget / len(views), 4)
        for v in views:
            pick = v.get("top_pick", "KODEX 미국AI반도체TOP3플러스")
            recommended_weights[pick] = min(per_asset_w, 0.25) # 단일 종목 25% 캡

    # 잔여 비중은 현금성 자산(TIGER CD금리/ACE SOFR)에 배분
    allocated_sum = sum(recommended_weights.values())
    remaining_cash = round(max(0.0, 1.0 - allocated_sum), 4)
    recommended_weights["TIGER CD금리투자KIS(합성)"] = round(remaining_cash * 0.5, 4)
    recommended_weights["ACE 미국달러SOFR금리(합성)"] = round(remaining_cash * 0.5, 4)

    # 5. 실행 액션 결정
    if conf >= 0.80:
        action = "EXECUTE_AGGRESSIVE_TILTING"
    elif conf >= 0.50:
        action = "EXECUTE_BALANCED_REBALANCE"
    else:
        action = "TRIGGER_DEFENSIVE_PARKING"

    latency = (time.perf_counter() - start_time) * 1000.0

    # 6. DB 로깅
    db.execute_query("""
    INSERT INTO portfolio_allocation_log (regime_detected, qwen_confidence_score, target_weights, execution_status, notes)
    VALUES (?, ?, ?, ?, ?)
    """, (
        decision_data.get("regime", "Unknown"),
        conf,
        json.dumps(recommended_weights, ensure_ascii=False),
        action,
        decision_data.get("reasoning", "")
    ))

    return QuantDecisionResponse(
        regime=decision_data.get("regime", "Unknown"),
        confidence_score=conf,
        cluster_views=[ClusterViewItem(**v) for v in views],
        cash_park_ratio=cash_ratio,
        reasoning=decision_data.get("reasoning", ""),
        recommended_weights=recommended_weights,
        execution_action=action,
        latency_ms=round(latency, 2)
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
