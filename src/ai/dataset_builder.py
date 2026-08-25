"""
src/ai/dataset_builder.py
8대 전 전략 클러스터(방산, 밸류업, 금융, 배당, 금현물, 전력SMR, 반도체, 빅테크) 100% 포괄 정밀 LoRA 학습 데이터셋 생성기
"""

import json
import os
import random
from config.settings import settings

SYSTEM_PROMPT = (
    "당신은 머니투데이 제3회 ETF 투자왕 대회(연금형 부문, 10억 원 모의투자)의 수석 퀀트 AI 에이전트입니다. "
    "선물, 레버리지, 인버스 ETF는 절대 매매할 수 없으며 오직 10대 후원사의 연금 적격 현물 ETF 8대 클러스터("
    "C1_AI_SEMI, C2_AI_POWER, C3_US_TECH, C4_DEFENSE, C5_VALUE_UP, C6_DIVIDEND, C7_COMMODITY, C8_CASH_PARK)에 대해 "
    "거시 국면(regime), 투자 확신도(confidence_score 0.0~1.0), 클러스터별 기대수익률 및 공식 탑픽 ETF, 현금보유비율(cash_park_ratio), "
    "판단 근거(reasoning)를 순수 JSON 형식으로 정확히 출력하십시오."
)

SCENARIOS = [
    # 1. AI 반도체 & 슈퍼사이클
    {
        "user": "[시황 속보] 엔비디아 어닝 서프라이즈 및 차세대 블랙웰 가속기 주문량 폭증. SK하이닉스 5세대 HBM3E 공급 확대 공시. 필라델피아 반도체 지수 급등.",
        "assistant": {
            "regime": "AI_Hardware_Supercycle",
            "confidence_score": 0.95,
            "cluster_views": [
                {"cluster_id": "C1_AI_SEMI", "expected_return": 0.068, "confidence": 0.97, "top_pick": "KODEX 미국AI반도체TOP3플러스"},
                {"cluster_id": "C1_AI_SEMI", "expected_return": 0.058, "confidence": 0.94, "top_pick": "SOL AI반도체소부장"},
                {"cluster_id": "C3_US_TECH", "expected_return": 0.045, "confidence": 0.91, "top_pick": "ACE 미국빅테크TOP7 Plus"}
            ],
            "cash_park_ratio": 0.05,
            "reasoning": "AI 가속기 및 HBM 하드웨어 실적이 주도하는 초강세장 국면. 반도체 및 빅테크 클러스터에 최대 롱 틸팅."
        }
    },
    # 2. AI 전력인프라 & SMR 원자력
    {
        "user": "[산업 공시] 마이크로소프트와 아마존이 대규모 AI 데이터센터 가동을 위해 소형모듈원전(SMR) 및 원전 기업과 20년 장기 전력구매계약 체결. 변압기 수주잔고 사상 최대.",
        "assistant": {
            "regime": "AI_Power_Infrastructure_Bottleneck",
            "confidence_score": 0.93,
            "cluster_views": [
                {"cluster_id": "C2_AI_POWER", "expected_return": 0.062, "confidence": 0.96, "top_pick": "TIGER 미국AI전력SMR"},
                {"cluster_id": "C2_AI_POWER", "expected_return": 0.058, "confidence": 0.94, "top_pick": "KODEX 원자력SMR"},
                {"cluster_id": "C2_AI_POWER", "expected_return": 0.050, "confidence": 0.90, "top_pick": "RISE AI전력인프라"}
            ],
            "cash_park_ratio": 0.06,
            "reasoning": "AI 데이터센터의 핵심 병목인 전력/에너지 테마의 구조적 상승 모멘텀. 원자력 및 전력인프라 ETF 최우선 배분."
        }
    },
    # 3. K-방산 & 글로벌 안보 / 로봇
    {
        "user": "[방산 속보] 폴란드 K2 전차 및 K9 자주포 2차 본계약 10조원 체결, 루마니아 장갑차 수출 낭보. 유럽 NATO 회원국 국방비 GDP 2.5%로 상향 합의.",
        "assistant": {
            "regime": "Global_Defense_Spending_Boom",
            "confidence_score": 0.92,
            "cluster_views": [
                {"cluster_id": "C4_DEFENSE", "expected_return": 0.058, "confidence": 0.95, "top_pick": "ACE K방산TOP5+"},
                {"cluster_id": "C4_DEFENSE", "expected_return": 0.052, "confidence": 0.93, "top_pick": "PLUS K방산"},
                {"cluster_id": "C4_DEFENSE", "expected_return": 0.046, "confidence": 0.89, "top_pick": "HANARO 유럽방산"}
            ],
            "cash_park_ratio": 0.08,
            "reasoning": "글로벌 지정학적 리스크 확산 및 K-방산 수출 수주잔고 사상 최대치 갱신에 따른 방산 섹터 집중 매수."
        }
    },
    # 4. 국내 밸류업 & 금융고배당 (주주환원)
    {
        "user": "[정책 속보] 정부 밸류업 세제개편안(배당소득 분리과세 및 자사주 소각 법인세 감면) 국회 본회의 통과. 4대 금융지주 1조원 규모 자사주 매입 소각 공시.",
        "assistant": {
            "regime": "Korea_ValueUp_Rerating",
            "confidence_score": 0.94,
            "cluster_views": [
                {"cluster_id": "C5_VALUE_UP", "expected_return": 0.055, "confidence": 0.96, "top_pick": "SOL 금융지주플러스고배당"},
                {"cluster_id": "C5_VALUE_UP", "expected_return": 0.050, "confidence": 0.93, "top_pick": "KODEX 코리아밸류업"},
                {"cluster_id": "C5_VALUE_UP", "expected_return": 0.045, "confidence": 0.90, "top_pick": "RISE 코리아금융고배당"}
            ],
            "cash_park_ratio": 0.05,
            "reasoning": "코리아 디스카운트 해소 세제 혜택과 주주환원율(자사주 소각) 급증 수혜 저PBR 금융 및 밸류업 ETF 집중 배분."
        }
    },
    # 5. 월배당 & 타겟 데일리 커버드콜 (안정적 현금흐름 장세)
    {
        "user": "[시장 분석] 미국 박스권 횡보 장세 지속, 월분배 인컴 수요 급증. 다우존스 배당성장주 및 일일 옵션 프리미엄 수요 확대.",
        "assistant": {
            "regime": "High_Dividend_Income_Focus",
            "confidence_score": 0.88,
            "cluster_views": [
                {"cluster_id": "C6_DIVIDEND", "expected_return": 0.040, "confidence": 0.93, "top_pick": "SOL 미국배당다우존스"},
                {"cluster_id": "C6_DIVIDEND", "expected_return": 0.038, "confidence": 0.91, "top_pick": "TIGER 미국배당다우존스타겟데일리커버드콜"},
                {"cluster_id": "C5_VALUE_UP", "expected_return": 0.035, "confidence": 0.88, "top_pick": "ACE 고배당주"}
            ],
            "cash_park_ratio": 0.10,
            "reasoning": "박스권 횡보장에서 월분배금 캐시플로우 창출 및 커버드콜 옵션 프리미엄을 통한 하방 변동성 방어."
        }
    },
    # 6. 위기 대응 및 금현물 / 현금 파킹 (Risk-Off)
    {
        "user": "[위험 경보] 중동 분쟁 격화로 국제유가 급등, 미국 CPI 예상치 상회로 연준 금리 인상론 재부각. VIX 35 돌파, 글로벌 증시 전면 급락.",
        "assistant": {
            "regime": "Stagflation_Risk_Off",
            "confidence_score": 0.96,
            "cluster_views": [
                {"cluster_id": "C7_COMMODITY", "expected_return": 0.045, "confidence": 0.94, "top_pick": "ACE KRX금현물"},
                {"cluster_id": "C8_CASH_PARK", "expected_return": 0.015, "confidence": 0.98, "top_pick": "TIGER CD금리투자KIS(합성)"},
                {"cluster_id": "C8_CASH_PARK", "expected_return": 0.018, "confidence": 0.97, "top_pick": "ACE 미국달러SOFR금리(합성)"}
            ],
            "cash_park_ratio": 0.70,
            "reasoning": "급격한 위험회피(Risk-off) 및 인플레이션 재발 장세. 주식 비중을 최소화하고 실물 금현물과 원화 CD/달러 SOFR로 자본 보존."
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
        noise = random.uniform(-0.02, 0.02)
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
