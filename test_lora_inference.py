"""
test_lora_inference.py
학습 완료된 Qwen 2.5 LoRA 어댑터 + RAG 융합 인퍼런스 및 퀀트 뷰 생성 테스트 (최신 MLX-LM 규격)
"""

import json
from pydantic import BaseModel, Field
from typing import List
from mlx_lm import load, generate
from rag_engine import HybridETFRAGEngine

class ClusterView(BaseModel):
    cluster_id: str
    expected_return: float
    confidence: float
    top_pick: str

class QuantDecisionOutput(BaseModel):
    regime: str
    confidence_score: float
    cluster_views: List[ClusterView]
    cash_park_ratio: float
    reasoning: str

def evaluate_lora_model(news_prompt: str):
    print("=" * 70)
    print("🧪 [Qwen 2.5 LoRA + RAG] 실시간 매크로 뷰 추론 및 검증")
    print("=" * 70)
    
    # 1. RAG 지식 검색
    rag = HybridETFRAGEngine()
    rag_context = rag.build_qwen_context_prompt(news_prompt)
    print(f"\n📰 [입력 뉴스]: {news_prompt}\n")
    print(rag_context)

    # 2. 파인튜닝된 Qwen LoRA 모델 로드
    model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    adapter_path = "./adapters/pension_qwen7b_lora"

    print(f"\n🤖 M5 Metal GPU로 LoRA 어댑터 로드 중 ({adapter_path})...")
    model, tokenizer = load(model_path, adapter_path=adapter_path)

    system_prompt = (
        "당신은 머니투데이 제3회 ETF 투자왕 대회(연금형 부문, 10억 원 모의투자)의 수석 퀀트 AI 에이전트입니다. "
        "선물, 레버리지, 인버스 ETF는 절대 매매할 수 없으며 오직 10대 후원사의 연금 적격 현물 ETF 8대 클러스터(AI반도체, AI전력/SMR, "
        "미국빅테크, K-방산/로봇, 밸류업/금융, 월배당/커버드콜, 실물금현물, 초단기금리/SOFR)에 대해서만 "
        "거시 국면(regime), 투자 확신도(confidence_score 0.0~1.0), 클러스터별 기대초과수익률 및 탑픽, 현금보유비율(cash_park_ratio), "
        "판단 근거(reasoning)를 순수 JSON 형식으로 정확히 출력하십시오."
    )

    full_user_content = f"{news_prompt}\n\n{rag_context}\n\n위 정보를 바탕으로 최적의 포트폴리오 뷰를 JSON으로만 출력하십시오."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_user_content}
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    print("⚡ Metal GPU 고속 생성 중...")
    response = generate(
        model, tokenizer,
        prompt=prompt,
        max_tokens=512,
        verbose=False
    )

    print("\n" + "=" * 70)
    print("📋 [Qwen 2.5 LoRA 최종 추론 결과 (Raw Output)]")
    print(response)
    print("=" * 70)

    # Pydantic JSON 파싱 검증
    try:
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed_obj = QuantDecisionOutput.model_validate_json(json_str)
        print("\n✅ Pydantic 검증 통과! 구조화된 퀀트 뷰 객체 변환 성공:")
        print(f"  • 국면(Regime): {parsed_obj.regime}")
        print(f"  • 종합 확신도(Confidence): {parsed_obj.confidence_score * 100:.1f}%")
        print(f"  • 현금 파킹 비율: {parsed_obj.cash_park_ratio * 100:.1f}%")
        print("  • 클러스터별 뷰:")
        for cv in parsed_obj.cluster_views:
            print(f"    - [{cv.cluster_id}] 기대수익률: {cv.expected_return*100:+.1f}% | 신뢰도: {cv.confidence} | 탑픽: {cv.top_pick}")
        print(f"  • 판단 근거: {parsed_obj.reasoning}")
    except Exception as e:
        print(f"\n⚠️ JSON 파싱 경고 ({e})")

if __name__ == "__main__":
    test_news = "[시황 속보] 엔비디아 2분기 어닝 서프라이즈 및 차세대 블랙웰 칩 주문량 3배 폭증. SK하이닉스 5세대 HBM3E 공급 확대 공시. 필라델피아 반도체 지수 4.8% 급등."
    evaluate_lora_model(test_news)
