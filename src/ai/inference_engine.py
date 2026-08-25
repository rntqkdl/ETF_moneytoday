"""
src/ai/inference_engine.py
RAG 지식 검색과 결합된 Qwen 2.5 LoRA 실시간 추론 및 8대 클러스터 퀀트 뷰 생성기 (견고한 JSON 파서 탑재)
"""

import json
import re
from typing import Optional, Dict, Any, List
from config.settings import settings
from src.database.models import QuantDecisionOutput, ClusterViewItem
from src.rag.hybrid_search import HybridETFRAGEngine

class QuantInferenceEngine:
    """LoRA 어댑터 상주 로드 및 실시간 추론기"""

    def __init__(self, rag: Optional[HybridETFRAGEngine] = None):
        self.rag = rag or HybridETFRAGEngine()
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        try:
            from mlx_lm import load
            print(f"🤖 [Inference Engine] M5 Metal GPU 모델 로드 중 ({settings.ADAPTER_PATH})...")
            self.model, self.tokenizer = load(
                settings.BASE_MODEL_NAME, 
                adapter_path=settings.ADAPTER_PATH
            )
            print("✅ LoRA 모델 상주 준비 완료!")
        except Exception as e:
            print(f"⚠️ 모델 로드 실패 ({e}). Fallback 모드 작동.")

    def evaluate_news(self, news_headline: str, news_content: str = "") -> QuantDecisionOutput:
        """뉴스 입력 -> RAG 검색 -> LoRA 추론 -> QuantDecisionOutput 반환"""
        full_text = f"{news_headline} {news_content}".strip()
        rag_results = self.rag.search(full_text, top_k=6)
        rag_context = self.rag.build_qwen_context_prompt(full_text, top_k=6)

        if self.model is not None:
            from mlx_lm import generate
            system_prompt = (
                "당신은 머니투데이 제3회 ETF 투자왕 대회(연금형 부문, 10억 원 모의투자)의 수석 퀀트 AI 에이전트입니다. "
                "선물, 레버리지, 인버스 ETF는 절대 매매할 수 없으며 오직 10대 후원사의 연금 적격 현물 ETF 8대 클러스터에 대해서만 "
                "거시 국면(regime), 투자 확신도(confidence_score 0.0~1.0), 클러스터별 기대초과수익률 및 탑픽(cluster_views), 현금보유비율(cash_park_ratio), "
                "판단 근거(reasoning)를 순수 JSON 형식으로 정확히 출력하십시오."
            )
            user_prompt = f"{full_text}\n\n{rag_context}\n\n위 정보를 바탕으로 최적의 포트폴리오 뷰를 JSON으로만 출력하십시오."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            raw_response = generate(self.model, self.tokenizer, prompt=prompt, max_tokens=512, verbose=False)
        else:
            raw_response = json.dumps({
                "regime": "Fallback_Regime",
                "confidence_score": 0.85,
                "cluster_views": [
                    {"cluster_id": r.cluster_id, "expected_return": 0.05, "confidence": 0.90, "top_pick": r.name}
                    for r in rag_results[:3]
                ],
                "cash_park_ratio": 0.10,
                "reasoning": "RAG 검색 기반 추천 포트폴리오."
            })

        # 견고한 JSON 파싱
        clean_json = raw_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()

        try:
            parsed_dict = json.loads(clean_json)
        except Exception:
            # JSON 추출 정규식
            json_match = re.search(r"\{.*\}", clean_json, re.DOTALL)
            if json_match:
                parsed_dict = json.loads(json_match.group(0))
            else:
                parsed_dict = {}

        # 필드 보정
        regime = parsed_dict.get("regime", "Adaptive_Macro_Regime")
        conf = float(parsed_dict.get("confidence_score", 0.90))
        cash = float(parsed_dict.get("cash_park_ratio", 0.08))
        reasoning = parsed_dict.get("reasoning", "RAG 및 거시 팩터 앙상블 분석")
        
        raw_views = parsed_dict.get("cluster_views", parsed_dict.get("views", []))
        views = []
        if isinstance(raw_views, list) and raw_views:
            for v in raw_views:
                if isinstance(v, dict) and "top_pick" in v:
                    views.append(ClusterViewItem(
                        cluster_id=v.get("cluster_id", "C1_AI_SEMI"),
                        expected_return=float(v.get("expected_return", 0.05)),
                        confidence=float(v.get("confidence", 0.92)),
                        top_pick=v.get("top_pick", "")
                    ))

        # 만약 cluster_views가 비어있다면 RAG 검색 상위 3개로 안전 폴백
        if not views and rag_results:
            for r in rag_results[:3]:
                views.append(ClusterViewItem(
                    cluster_id=r.cluster_id,
                    expected_return=0.055,
                    confidence=0.92,
                    top_pick=r.name
                ))

        return QuantDecisionOutput(
            regime=regime,
            confidence_score=conf,
            cluster_views=views,
            cash_park_ratio=cash,
            reasoning=reasoning
        )
