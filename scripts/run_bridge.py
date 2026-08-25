"""
scripts/run_bridge.py
n8n 연동용 FastAPI 브릿지 서버 구동 스크립트
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.server import start_server

if __name__ == "__main__":
    start_server()
