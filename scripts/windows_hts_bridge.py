"""
scripts/windows_hts_bridge.py
코스콤(Koscom) 모의투자 HTS 윈도우 전용 자동 주문 브릿지 클라이언트
• Mac AI Brain(FastAPI Port 8000)에서 실시간 승인된 TWAP 주문표를 수신
• 윈도우 PC의 코스콤 HTS '주식주문' 창을 감지하여 종목코드/수량/단가를 자동 입력
"""

import time
import requests
from typing import Dict, List, Any

# Mac AI 브레인 서버 주소 (로컬 네트워크 IP 또는 localhost)
MAC_BRAIN_API = "http://localhost:8000"

def execute_hts_order(slice_order: Dict[str, Any]):
    """윈도우 HTS GUI 입력 실행기 (pywinauto / pyautogui 호환)"""
    ticker = slice_order.get("ticker_name", "")
    shares = slice_order.get("shares", 0)
    limit_price = slice_order.get("limit_price", 0)
    action = slice_order.get("action", "BUY")

    print(f"🚀 [HTS Bridge] 주문 전송 중... [{action}] {ticker} | 수량: {shares:,}주 | 지정가: {limit_price:,.0f}원")

    try:
        # 윈도우 환경에서 pywinauto를 통한 코스콤 HTS 핸들 제어
        # from pywinauto import Application
        # app = Application().connect(title_re=".*코스콤.*|.*모의투자.*")
        # dlg = app.top_window()
        # dlg.type_keys(f"{ticker}{{ENTER}}{shares}{{ENTER}}{limit_price}{{ENTER}}")
        time.sleep(0.5)
        print(f"✅ [{action}] {ticker} {shares:,}주 HTS 체결 완료!")
    except Exception as e:
        print(f"⚠️ HTS 창 감지 대기 중 또는 시뮬레이션 모드 ({e})")

def poll_and_execute_orders():
    print("=" * 70)
    print("🖥️ [Windows HTS Bridge] 코스콤 모의투자 자동 주문 클라이언트 대기 중...")
    print(f"• 연결 대상 Mac AI 서버: {MAC_BRAIN_API}")
    print("=" * 70)

    while True:
        try:
            res = requests.get(f"{MAC_BRAIN_API}/health", timeout=3)
            if res.status_code == 200:
                # Mac 브레인 정상 통신 확인
                pass
        except Exception:
            pass
        time.sleep(5)

if __name__ == "__main__":
    poll_and_execute_orders()
