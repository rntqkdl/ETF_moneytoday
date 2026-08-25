-- PostgreSQL Schema for Pension ETF Championship System
-- 머니투데이 제3회 ETF 투자왕 대회 [연금형] 데이터베이스 스키마

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. ETF 마스터 테이블 (400여 개 연금 적격 ETF 메타데이터)
CREATE TABLE IF NOT EXISTS etf_master (
    ticker VARCHAR(10) PRIMARY KEY,              -- KRX 단축코드 (예: 465580, 069500 등)
    name VARCHAR(150) NOT NULL UNIQUE,          -- 공식 ETF 종목명 (예: KODEX 미국AI반도체TOP3플러스)
    issuer VARCHAR(50) NOT NULL,                -- 운용사 (삼성, 미래에셋, 한투, KB, 신한 등)
    brand VARCHAR(20) NOT NULL,                 -- 브랜드 (KODEX, TIGER, ACE, SOL, RISE 등)
    cluster_id VARCHAR(30) NOT NULL,            -- 8대 클러스터 ID (C1_AI_SEMI, C2_AI_POWER 등)
    cluster_name VARCHAR(100) NOT NULL,         -- 클러스터 명칭
    is_fx_hedged BOOLEAN DEFAULT FALSE,         -- 환헤지 여부 ((H), (합성 H))
    is_synthetic BOOLEAN DEFAULT FALSE,         -- 합성 ETF 여부 ((합성))
    is_active BOOLEAN DEFAULT FALSE,            -- 액티브 ETF 여부 (액티브)
    is_covered_call BOOLEAN DEFAULT FALSE,      -- 커버드콜 여부
    is_pension_eligible BOOLEAN DEFAULT TRUE,   -- 연금 적격 여부 (선물/레버리지/인버스 배제)
    description TEXT,                           -- 상품 개요 및 팩트시트
    key_themes TEXT[],                          -- 주요 투자 테마 태그
    expense_ratio NUMERIC(5, 4) DEFAULT 0.0045, -- 총보수 (기본 추정 0.45%)
    aum_billion_krw NUMERIC(12, 2) DEFAULT 0.0, -- 순자산규모 (억 원 단위)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_etf_master_cluster ON etf_master(cluster_id);
CREATE INDEX IF NOT EXISTS idx_etf_master_brand ON etf_master(brand);
CREATE INDEX IF NOT EXISTS idx_etf_master_name_trgm ON etf_master USING gin (name gin_trgm_ops);

-- 2. RAG 지식 임베딩 테이블 (ETF 팩트시트, 공시, 뉴스, 테마 벡터 검색)
CREATE TABLE IF NOT EXISTS etf_rag_documents (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES etf_master(ticker) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,         -- 'FACTSHEET', 'PDF_COMPONENTS', 'NEWS', 'ANALYSIS'
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(768),                      -- 768차원 임베딩 (Qwen / Nomic / BGE 호환)
    fts_tokens TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', title || ' ' || content)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- RAG 인덱스 (HNSW 벡터 인덱스 + GIN 풀텍스트 검색)
CREATE INDEX IF NOT EXISTS idx_rag_embedding_hnsw ON etf_rag_documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_rag_fts ON etf_rag_documents USING gin (fts_tokens);

-- 3. 일별 시세 및 NAV 시계열 테이블 (Kronos 및 skfolio 입력 데이터)
CREATE TABLE IF NOT EXISTS etf_daily_prices (
    ticker VARCHAR(10) REFERENCES etf_master(ticker) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    open_price NUMERIC(12, 2) NOT NULL,
    high_price NUMERIC(12, 2) NOT NULL,
    low_price NUMERIC(12, 2) NOT NULL,
    close_price NUMERIC(12, 2) NOT NULL,
    volume BIGINT NOT NULL,
    trading_value_krw BIGINT DEFAULT 0,         -- 일 거래대금
    inav NUMERIC(12, 2),                        -- 실시간 추정 순자산가치
    disparity_ratio NUMERIC(6, 4),              -- 괴리율 ((Close - iNAV) / iNAV)
    PRIMARY KEY (ticker, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_prices_date ON etf_daily_prices(trade_date);

-- 4. 거시경제 및 시장 매크로 지표 테이블 (FRED, BOK ECOS)
CREATE TABLE IF NOT EXISTS macro_indicators (
    indicator_code VARCHAR(50) NOT NULL,        -- 'US_FEDFUNDS', 'US_10Y', 'KR_BASE_RATE', 'SOFR'
    record_date DATE NOT NULL,
    value NUMERIC(14, 6) NOT NULL,
    category VARCHAR(50) NOT NULL,              -- 'INTEREST_RATE', 'INFLATION', 'LIQUIDITY', 'FX'
    metadata JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (indicator_code, record_date)
);

-- 5. 리밸런싱 시그널 및 주문 체결 로그 테이블
CREATE TABLE IF NOT EXISTS portfolio_allocation_log (
    id SERIAL PRIMARY KEY,
    decision_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    regime_detected VARCHAR(100) NOT NULL,
    qwen_confidence_score NUMERIC(4, 3) NOT NULL,
    target_weights JSONB NOT NULL,              -- {"KODEX_AI_SEMI": 0.20, "TIGER_SOFR": 0.10, ...}
    portfolio_cvar NUMERIC(8, 6),
    execution_status VARCHAR(30) DEFAULT 'PENDING', -- 'PENDING', 'EXECUTED', 'CIRCUIT_BROKEN'
    notes TEXT
);
