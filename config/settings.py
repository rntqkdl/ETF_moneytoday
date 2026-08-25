"""
config/settings.py
연금형 ETF 퀀트 시스템 전역 설정 및 환경 변수 관리
"""

import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    PROJECT_NAME: str = "MoneyToday Pension ETF Quant System"
    VERSION: str = "2.0.0"
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR}/pension_etf.db"
    )
    
    # 로컬 LLM 및 어댑터 경로
    BASE_MODEL_NAME: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    ADAPTER_PATH: str = str(BASE_DIR / "adapters" / "pension_qwen7b_lora")
    DATA_DIR: str = str(BASE_DIR / "data")
    
    # API 서버 설정
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # 컴플라이언스 제약
    MAX_SINGLE_ASSET_WEIGHT: float = 0.25  # 단일 ETF 최대 25% 비중
    MIN_CASH_PARK_RATIO: float = 0.05      # 최소 현금성 완충 5%
    CIRCUIT_BREAKER_MDD: float = -0.03     # -3% 도달 시 서킷브레이커

settings = Settings()
