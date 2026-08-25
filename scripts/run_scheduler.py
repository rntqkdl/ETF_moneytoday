"""
scripts/run_scheduler.py
장 시간 자동화 퀀트 스케줄러 실행기
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.scheduler_daemon import start_daemon_loop

if __name__ == "__main__":
    start_daemon_loop()
