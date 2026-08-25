"""
config/settings.py
연금형 ETF 퀀트 시스템 전역 설정 및 환경 변수 관리 (.env 자동 로드 지원)
"""

import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일 로드
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

class Settings(BaseModel):
    PROJECT_NAME: str = "MoneyToday Pension ETF Quant System"
    VERSION: str = "2.1.0"
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR}/pension_etf.db"
    )
    
    # API 키 및 웹훅
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    DART_API_KEY: str = os.getenv("DART_API_KEY", "")

    # 로컬 LLM 및 어댑터 경로
    BASE_MODEL_NAME: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    ADAPTER_PATH: str = str(BASE_DIR / "adapters" / "pension_qwen7b_lora")
    DATA_DIR: str = str(BASE_DIR / "data")
    
    # API 서버 설정
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # 1등 우승형 컴플라이언스 제약 (공격형 40% 몰입 허용)
    MAX_SINGLE_ASSET_WEIGHT: float = 0.40  # 단일 1등 주도 ETF 최대 40% 집중 공격 허용
    MIN_CASH_PARK_RATIO: float = 0.05      # 최소 현금성 완충 5%
    CIRCUIT_BREAKER_MDD: float = -0.03     # -3% 도달 시 서킷브레이커

settings = Settings()
