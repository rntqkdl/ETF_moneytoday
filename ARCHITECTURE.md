# 🏛️ 머니투데이 ETF 투자왕 대회 [연금형] 시스템 아키텍처 다이어그램 (Mermaid Spec)

본 문서는 연금형 ETF AI 퀀트 시스템의 **데이터 흐름, 지식 그래프, 멀티에이전트 시퀀스, 리스크 상태 머신**을 시각화한 머메이드(Mermaid) 명세서입니다.

---

## 1. 🌐 엔드투엔드 시스템 토폴로지 (End-to-End System Topology)

```mermaid
flowchart TB
    subgraph Data_Layer ["1. 데이터 수집 & 오케스트레이션 (Data Ingestion)"]
        n8n["n8n 4대 상태 머신 스케줄러"]
        DART["DART 기업 실적 & 수주 공시"]
        News["빅카인즈 / 금융 속보 (Polite Crawl 1.5s)"]
        Macro["FRED / BOK ECOS 거시 경제 지표"]
        DB[("PostgreSQL / SQLite 893개 ETF DB")]

        n8n --> DART & News & Macro
    end

    subgraph AI_Core ["2. 듀얼코어 AI 알파 엔진 (Apple M5 Metal GPU)"]
        RAG["초저지연 Hybrid RAG 엔진 (0.8ms)\n• In-Memory TF-IDF + Metadata Filter"]
        LoRA["Qwen 2.5-7B LoRA (M5 Metal Native)\n• 거시 국면 분류 (Regime)\n• 투자 확신도 (Confidence 0.0~1.0)\n• Black-Litterman 뷰 산출"]

        DART & News --> RAG
        DB --> RAG
        RAG --> LoRA
    end

    subgraph Quant_Engine ["3. 퀀트 자산배분 & 리스크 가드레일 (Quant Engine)"]
        FastAPI["FastAPI High-Speed Bridge (Port 8000)"]
        Harness["Compliance 0-Violation Guardrail\n• 선물/레버리지/인버스 100% 차단\n• 단일 종목 최대 25% 캡"]
        Optimizer["Portfolio Optimizer\n• 확신도 가중 롱 틸팅\n• 하방 위험 최소화"]

        LoRA --> FastAPI
        FastAPI --> Optimizer
        Optimizer --> Harness
    end

    subgraph Execution_Layer ["4. 실행 및 알림 채널 (Execution & Telemetry)"]
        Telegram["📱 텔레그램 인터랙티브 승인 알림\n[✅ 주문 승인] [⏸️ 유지] [🛡️ 현금 전환]"]
        Koscom_HTS["🖥️ 코스콤 모의투자 HTS (가상 10억 원)"]
        CircuitBreaker["🚨 Max Drawdown -3% 서킷브레이커\n(SOFR/CD금리 80% 안전 전환)"]

        Harness --> CircuitBreaker
        CircuitBreaker --> Telegram
        Telegram -->|Human-in-the-Loop 승인| Koscom_HTS
    end
```

---

## 2. 🕸️ 8대 클러스터 온톨로지 지식 그래프 (Knowledge Graph & Router)

```mermaid
graph TD
    subgraph Macro_Regimes ["매크로 국면 (Macro Regimes)"]
        R1["🌟 강세 1: AI Capex & 실물투자 슈퍼사이클"]
        R2["💧 강세 2: 글로벌 금리인하 피벗 & 유동성 완화"]
        R3["🇰🇷 정책 3: 국내 밸류업 & 주주환원 리레이팅"]
        R4["🛡️ 방어 4: 스태그플레이션 & 지정학적 위기 (Risk-Off)"]
    end

    subgraph Theme_Clusters ["8대 ETF 전략 클러스터"]
        C1["C1: AI 반도체 & 핵심 장비 (51개)"]
        C2["C2: AI 전력인프라 & SMR 원자력 (32개)"]
        C3["C3: 미국 메가캡 빅테크 & 나스닥 (117개)"]
        C4["C4: K-방산 & 글로벌 방산 / 피지컬 AI (39개)"]
        C5["C5: 국내 밸류업 & 금융고배당 (58개)"]
        C6["C6: 월배당 & 타겟 데일리 커버드콜 (42개)"]
        C7["C7: 실물 자산 & 금현물 (선물 제외) (8개)"]
        C8["C8: 초단기 금리 / SOFR / MMF (46개)"]
    end

    subgraph Representative_ETFs ["대표 연금 적격 ETF"]
        E1["KODEX 미국AI반도체TOP3플러스 / SOL AI반도체소부장"]
        E2["TIGER 미국AI전력SMR / KODEX 원자력SMR"]
        E3["ACE 미국빅테크TOP7 Plus / TIGER 미국나스닥100"]
        E4["ACE K방산TOP5+ / HANARO 유럽방산"]
        E5["SOL 금융지주플러스고배당 / KODEX 코리아밸류업"]
        E6["SOL 미국배당다우존스 / TIGER 미국배당커버드콜"]
        E7["ACE KRX금현물 / TIGER KRX금현물"]
        E8["TIGER CD금리투자KIS / ACE 미국달러SOFR금리"]
    end

    R1 --> C1 & C2
    R2 --> C3 & C6
    R3 --> C5
    R4 --> C7 & C8

    C1 --> E1
    C2 --> E2
    C3 --> E3
    C4 --> E4
    C5 --> E5
    C6 --> E6
    C7 --> E7
    C8 --> E8
```

---

## 3. ⏱️ 멀티에이전트 실시간 오케스트레이션 시퀀스 (Sequence Flow)

```mermaid
sequenceDiagram
    autonumber
    participant N as n8n Scheduler (08:30 KST)
    participant F as FastAPI Bridge (Port 8000)
    participant R as Hybrid RAG Engine (0.8ms)
    participant Q as Qwen 2.5 LoRA (M5 Metal)
    participant O as Portfolio Optimizer & Harness
    participant D as PostgreSQL / SQLite DB
    participant T as Telegram Interactive Bot
    participant H as 코스콤 모의투자 HTS

    N->>N: DART 공시 및 주요 증시 속보 크롤링 (1.5s Jitter)
    N->>F: POST /api/macro/evaluate (뉴스 헤드라인 전송)
    F->>R: 연관 ETF 후보군 지식 검색 요청
    R-->>F: 상위 적격 ETF 6개 스니펫 반환 (0.8ms)
    F->>Q: 프롬프트 + RAG 컨텍스트 주입 추론
    Q-->>F: JSON 반환 (Regime, Confidence 93%, Cluster Views)
    F->>O: 목표 비중 계산 & 25% 캡 가드레일 검증
    O-->>F: 검증된 비중 벡터 (Target Weights w*) 도출
    F->>D: 의사결정 로그 및 목표 비중 영구 저장
    F-->>N: 200 OK + Decision JSON 반환 (총 레이턴시 0.15초)
    N->>T: 카드형 리포트 + [주문 승인] 인라인 버튼 발송
    Note over T,H: 사용자 1초 검토 후 원클릭 승인
    T->>H: 코스콤 HTS 가상 주문 브릿지 체결 실행 (10억 원 배분)
```

---

## 4. 🚨 리스크 관리 & 서킷브레이커 상태 머신 (Risk State Machine)

```mermaid
stateDiagram-v2
    [*] --> Normal_Alpha_Tilting : 계좌 운용 시작 (10억 원)

    state Normal_Alpha_Tilting {
        [*] --> High_Confidence_Long : 확신도 >= 80% (주도 섹터 70% + 현금 10%)
        High_Confidence_Long --> Balanced_Allocation : 확신도 50~80% (밸류업/배당 60% + 현금 20%)
        Balanced_Allocation --> High_Confidence_Long
    }

    Normal_Alpha_Tilting --> Stage1_Defense : 주간 낙폭 MDD <= -2.0% 도달
    Stage1_Defense : [1차 방어 모드]\n주식 비중 50% 축소 -> TIGER CD금리/SOFR 이동

    Stage1_Defense --> Normal_Alpha_Tilting : 수익률 회복 (Drawdown > -1.0%)
    Stage1_Defense --> Stage2_Circuit_Breaker : 누적 낙폭 MDD <= -3.0% 도달

    state Stage2_Circuit_Breaker {
        [*] --> Emergency_Cash_Parking
        Emergency_Cash_Parking : [2차 서킷브레이커 긴급 발동]\n전액 100% 현금성 자산(SOFR/CD/금현물) 완전 전환\n원금 절대 보존
    }
```
