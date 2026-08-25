"""
scripts/run_dashboard.py
실시간 웹 대시보드 및 FastAPI 브릿지 서버 구동 스크립트
브라우저에서 http://localhost:8000/dashboard 로 즉시 접속
"""

import sys
import webbrowser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.server import start_server

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 [Web Dashboard] 실시간 웹 대시보드 서버 가동 중...")
    print("👉 로컬 접속 URL: http://localhost:8000/dashboard")
    print("👉 API 문서 URL: http://localhost:8000/docs")
    print("=" * 70)
    start_server()
