"""
build_lora_dataset.py
머니투데이 ETF 투자왕 대회 [연금형] 특화 Qwen 2.5 LoRA 파인튜닝 데이터셋 생성기
다양한 거시경제 국면(Regime), 뉴스 속보, 공시 시나리오 기반의 고품질 Q&A 데이터셋 (train.jsonl, valid.jsonl) 구축
"""

import json
import os
import random
from typing import List, Dict, Any

SYSTEM_PROMPT = (
    "당신은 머니투데이 제3회 ETF 투자왕 대회(연금형 부문, 10억 원 모의투자)의 수석 퀀트 AI 에이전트입니다. "
    "선물, 레버리지, 인버스 ETF는 절대 매매할 수 없으며 오직 10대 후원사의 연금 적격 현물 ETF 8대 클러스터(AI반도체, AI전력/SMR, "
    "미국빅테크, K-방산/로봇, 밸류업/금융, 월배당/커버드콜, 실물금현물, 초단기금리/SOFR)에 대해서만 "
    "거시 국면(regime), 투자 확신도(confidence_score 0.0~1.0), 클러스터별 기대초과수익률 및 탑픽, 현금보유비율(cash_park_ratio), "
    "판단 근거(reasoning)를 순수 JSON 형식으로 정확히 출력하십시오."
)

SCENARIOS: List[Dict[str, Any]] = [
    # 1. AI 반도체 & HBM 실적 서프라이즈
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
    # 2. 연준 50bp 빅컷 & 기술주 유동성 장세
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
    # 3. 데이터센터 전력망 쇼티지 & SMR 원자력 수주
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
    # 4. 국내 밸류업 세제지원 및 금융지주 자사주 소각
    {
        "user": "[정책 속보] 정부 코리아 밸류업 지수 공식 발표 및 배당소득 분리과세 법안 국회 상정. 주요 금융지주 자사주 5천억 원 소각 발표로 배당수익률 6% 돌파.",
        "assistant": {
            "regime": "Korea_ValueUp_Policy_Momentum",
            "confidence_score": 0.87,
            "cluster_views": [
                {"cluster_id": "C5_VALUE_UP", "expected_return": 0.045, "confidence": 0.92, "top_pick": "SOL 금융지주플러스고배당"},
                {"cluster_id": "C5_VALUE_UP", "expected_return": 0.038, "confidence": 0.89, "top_pick": "KODEX 코리아밸류업"},
                {"cluster_id": "C6_DIVIDEND", "expected_return": 0.028, "confidence": 0.84, "top_pick": "PLUS 고배당주"}
            ],
            "cash_park_ratio": 0.10,
            "reasoning": "코리아 디스카운트 해소 정책과 주주환원율 제고에 따른 국내 저평가 금융/밸류업 ETF의 구조적 리레이팅."
        }
    },
    # 5. 지정학적 갈등 & K-방산 수주
    {
        "user": "[지정학 속보] 동유럽 및 중동 긴장 고조로 나토 회원국 국방예산 GDP 3% 상향 합의. K-방산 주요 기업 폴란드 및 루마니아 대상 4조 원 규모 K2 전차 및 자주포 2차 이행계약 체결 공시.",
        "assistant": {
            "regime": "Defense_Capex_Expansion",
            "confidence_score": 0.88,
            "cluster_views": [
                {"cluster_id": "C4_DEFENSE", "expected_return": 0.052, "confidence": 0.93, "top_pick": "ACE K방산TOP5+"},
                {"cluster_id": "C4_DEFENSE", "expected_return": 0.046, "confidence": 0.90, "top_pick": "HANARO 유럽방산"},
                {"cluster_id": "C7_COMMODITY", "expected_return": 0.030, "confidence": 0.86, "top_pick": "ACE KRX금현물"}
            ],
            "cash_park_ratio": 0.12,
            "reasoning": "글로벌 재무장 흐름과 K-방산 수주잔고 폭증 모멘텀. 독립적 알파 자산으로서 방산 ETF 비중 확대."
        }
    },
    # 6. 스태그플레이션 우려 & VIX 급등 (최대 방어 국면)
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
    },
    # 7. 횡보장 속 월배당 & 커버드콜 인컴 극대화
    {
        "user": "[시장 동향] S&P 500 및 코스피 박스권 등락 지속. 거시 지표 혼조세 속에 변동성 지수 14 내외 안정적 유지. 시장 전반 배당 및 인컴 ETF로 리테일 자금 유입 가속.",
        "assistant": {
            "regime": "Range_Bound_Income_Focus",
            "confidence_score": 0.85,
            "cluster_views": [
                {"cluster_id": "C6_DIVIDEND", "expected_return": 0.032, "confidence": 0.92, "top_pick": "TIGER 미국배당다우존스타겟데일리커버드콜"},
                {"cluster_id": "C6_DIVIDEND", "expected_return": 0.028, "confidence": 0.89, "top_pick": "SOL 미국배당다우존스"},
                {"cluster_id": "C5_VALUE_UP", "expected_return": 0.025, "confidence": 0.85, "top_pick": "PLUS 고배당주"}
            ],
            "cash_park_ratio": 0.20,
            "reasoning": "뚜렷한 추세가 없는 횡보장에서는 옵션 프리미엄 및 고배당 캐시플로우를 확보하는 커버드콜 전략이 우위."
        }
    },
    # 8. 피지컬 AI & 휴머노이드 로봇 상용화
    {
        "user": "[테크 속보] 테슬라 옵티머스 3세대 공장 양산 배치 발표 및 현대차 보스턴다이내믹스 물류 로봇 공급 계약 체결. 빅테크 기업들의 피지컬 AI 투자액 500억 달러 돌파.",
        "assistant": {
            "regime": "Physical_AI_Robotics_Expansion",
            "confidence_score": 0.86,
            "cluster_views": [
                {"cluster_id": "C4_DEFENSE", "expected_return": 0.048, "confidence": 0.90, "top_pick": "RISE 미국휴머노이드로봇"},
                {"cluster_id": "C4_DEFENSE", "expected_return": 0.044, "confidence": 0.88, "top_pick": "TIGER 글로벌AI&로보틱스 INDXX"},
                {"cluster_id": "C1_AI_SEMI", "expected_return": 0.036, "confidence": 0.84, "top_pick": "KODEX AI반도체TOP2플러스"}
            ],
            "cash_park_ratio": 0.10,
            "reasoning": "생성형 AI가 물리적 로봇으로 확장되는 피지컬 AI 테마의 모멘텀 부각. 로봇 및 엣지 AI 반도체 틸팅."
        }
    }
]

def generate_augmented_datasets(output_dir: str = "./data", total_samples: int = 240):
    """기본 시나리오를 변형/증강하여 train.jsonl과 valid.jsonl 생성"""
    os.makedirs(output_dir, exist_ok=True)
    
    variations = [
        ("미국 대선 직전 정책 불확실성 지속. 방산 및 전통 에너지 강세 속 기술주 차익실현 매물 출회.", "C4_DEFENSE", "C8_CASH_PARK"),
        ("글로벌 반도체 장비사 ASML 및 TSMC 호실적 발표. 한국 AI 소부장 공급망 수혜 집중.", "C1_AI_SEMI", "C3_US_TECH"),
        ("미국 AI 데이터센터용 소형 원자로 SMR 승인 가속화 및 국내 원전 수출 기대감 고조.", "C2_AI_POWER", "C1_AI_SEMI"),
        ("국내 기업 밸류업 세제 혜택 확정으로 금융주 외국인 10일 연속 순매수 행진.", "C5_VALUE_UP", "C6_DIVIDEND"),
        ("국제 금 시세 온스당 사상 최고치 경신. 안전자산 선호 심리 강화 및 환율 변동성 확대.", "C7_COMMODITY", "C8_CASH_PARK")
    ]

    all_data = []
    
    # 원본 시나리오 복제 및 변형
    for sc in SCENARIOS:
        all_data.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": sc["user"]},
                {"role": "assistant", "content": json.dumps(sc["assistant"], ensure_ascii=False)}
            ]
        })

    # 증강 데이터 생성
    for i in range(total_samples - len(SCENARIOS)):
        base_sc = random.choice(SCENARIOS)
        user_text = base_sc["user"]
        assistant_obj = dict(base_sc["assistant"])
        
        # 약간의 난수 변동(Jitter) 추가하여 일반화 성능 향상
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
    
    # 8:2 Split (Train / Valid)
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

    print(f"✅ LoRA 데이터셋 생성 완료! Train: {len(train_data)}건 -> {train_path} | Valid: {len(valid_data)}건 -> {valid_path}")

if __name__ == "__main__":
    generate_augmented_datasets()
