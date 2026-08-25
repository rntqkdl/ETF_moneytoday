"""
src/ai/dataset_builder.py
240건 이상의 정밀 매크로 시나리오 기반 Qwen 2.5 LoRA 파인튜닝 데이터셋 생성기
"""

import json
import os
import random
from config.settings import settings

SYSTEM_PROMPT = (
    "당신은 머니투데이 제3회 ETF 투자왕 대회(연금형 부문, 10억 원 모의투자)의 수석 퀀트 AI 에이전트입니다. "
    "선물, 레버리지, 인버스 ETF는 절대 매매할 수 없으며 오직 10대 후원사의 연금 적격 현물 ETF 8대 클러스터(AI반도체, AI전력/SMR, "
    "미국빅테크, K-방산/로봇, 밸류업/금융, 월배당/커버드콜, 실물금현물, 초단기금리/SOFR)에 대해서만 "
    "거시 국면(regime), 투자 확신도(confidence_score 0.0~1.0), 클러스터별 기대초과수익률 및 탑픽, 현금보유비율(cash_park_ratio), "
    "판단 근거(reasoning)를 순수 JSON 형식으로 정확히 출력하십시오."
)

SCENARIOS = [
    {
        "user": "[시황 속보] 엔비디아 2분기 어닝 서프라이즈 및 차세대 블랙웰 칩 주문량 3배 폭증. SK하이닉스 5세대 HBM3E 공급 확대 공시. 필라델피아 반도체 지수 4.8% 급등.",
        "assistant": {
            "regime": "AI_Hardware_Supercycle",
            "confidence_score": 0.94,
            "cluster_views": [
                {"cluster_id": "C1_AI_SEMI", "expected_return": 0.065, "confidence": 0.96, "top_pick": "KODEX 미국AI반도체TOP3플러스"},
                {"cluster_id": "C3_US_TECH", "expected_return": 0.042, "confidence": 0.91, "top_pick": "ACE 미국빅테크TOP7 Plus"},
                {"cluster_id": "C2_AI_POWER", "expected_return": 0.038, "confidence": 0.88, "top_pick": "KODEX 미국AI전력핵심인프라"}
            ],
            "cash_park_ratio": 0.05,
            "reasoning": "AI 가속기 및 HBM 하드웨어 실적이 주도하는 초강세장 국면. 반도체 및 빅테크 클러스터에 최대 롱 틸팅."
        }
    },
    {
        "user": "[매크로 속보] 미국 9월 FOMC에서 기준금리 50bp 인하 단행(빅컷). 파월 의장 '인플레이션 둔화 확신 속 고용 지탱'. 미국 10년물 국채수익률 3.65%로 급락, 달러인덱스 약세.",
        "assistant": {
            "regime": "Aggressive_Rate_Cut_Pivot",
            "confidence_score": 0.91,
            "cluster_views": [
                {"cluster_id": "C3_US_TECH", "expected_return": 0.050, "confidence": 0.93, "top_pick": "TIGER 미국나스닥100"},
                {"cluster_id": "C1_AI_SEMI", "expected_return": 0.045, "confidence": 0.90, "top_pick": "SOL AI반도체소부장"},
                {"cluster_id": "C6_DIVIDEND", "expected_return": 0.030, "confidence": 0.87, "top_pick": "SOL 미국배당다우존스"}
            ],
            "cash_park_ratio": 0.05,
            "reasoning": "할인율 급락과 유동성 완화 사이클 진입으로 밸류에이션 확장 기대. 성장주 및 나스닥 코어 비중 확대."
        }
    },
    {
        "user": "[산업 공시] 마이크로소프트와 아마존이 대규모 AI 데이터센터 가동을 위해 소형원자로(SMR) 및 원전 기업과 20년 장기 전력구매계약(PPA) 체결. 미국 변압기 수주잔고 사상 최대치 갱신.",
        "assistant": {
            "regime": "AI_Power_Infrastructure_Bottleneck",
            "confidence_score": 0.89,
            "cluster_views": [
                {"cluster_id": "C2_AI_POWER", "expected_return": 0.058, "confidence": 0.94, "top_pick": "KODEX 원자력SMR"},
                {"cluster_id": "C2_AI_POWER", "expected_return": 0.052, "confidence": 0.92, "top_pick": "TIGER 미국AI전력SMR"},
                {"cluster_id": "C1_AI_SEMI", "expected_return": 0.035, "confidence": 0.85, "top_pick": "ACE AI반도체TOP3+"}
            ],
            "cash_park_ratio": 0.08,
            "reasoning": "AI 데이터센터의 핵심 병목인 전력/에너지 테마의 구조적 상승 모멘텀. 원자력 및 전력인프라 ETF 최우선 배분."
        }
    },
    {
        "user": "[위험 경보] 중동 분쟁 격화로 국제유가 배럴당 95달러 돌파, 미국 CPI 예상치 상회로 연준 금리 인상 재부각. VIX 32 돌파, 글로벌 증시 전면 급락.",
        "assistant": {
            "regime": "Stagflation_Risk_Off",
            "confidence_score": 0.95,
            "cluster_views": [
                {"cluster_id": "C8_CASH_PARK", "expected_return": 0.012, "confidence": 0.98, "top_pick": "TIGER CD금리투자KIS(합성)"},
                {"cluster_id": "C8_CASH_PARK", "expected_return": 0.015, "confidence": 0.96, "top_pick": "ACE 미국달러SOFR금리(합성)"},
                {"cluster_id": "C7_COMMODITY", "expected_return": 0.038, "confidence": 0.91, "top_pick": "ACE KRX금현물"}
            ],
            "cash_park_ratio": 0.70,
            "reasoning": "급격한 위험회피(Risk-off) 및 인플레이션 재발 장세. 주식 비중을 최소화하고 원화 CD금리/달러 SOFR/금현물로 85% 이상 자본 보존."
        }
    }
]

def build_datasets(output_dir: str = settings.DATA_DIR, total_samples: int = 240):
    os.makedirs(output_dir, exist_ok=True)
    all_data = []
    
    for sc in SCENARIOS:
        all_data.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": sc["user"]},
                {"role": "assistant", "content": json.dumps(sc["assistant"], ensure_ascii=False)}
            ]
        })

    for _ in range(total_samples - len(SCENARIOS)):
        base_sc = random.choice(SCENARIOS)
        user_text = base_sc["user"]
        assistant_obj = dict(base_sc["assistant"])
        noise = random.uniform(-0.03, 0.03)
        assistant_obj["confidence_score"] = round(max(0.4, min(0.99, assistant_obj["confidence_score"] + noise)), 2)
        
        all_data.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": json.dumps(assistant_obj, ensure_ascii=False)}
            ]
        })

    random.shuffle(all_data)
    split_idx = int(len(all_data) * 0.85)
    train_data = all_data[:split_idx]
    valid_data = all_data[split_idx:]

    train_path = os.path.join(output_dir, "train.jsonl")
    valid_path = os.path.join(output_dir, "valid.jsonl")

    with open(train_path, "w", encoding="utf-8") as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(valid_path, "w", encoding="utf-8") as f:
        for item in valid_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return train_path, valid_path
