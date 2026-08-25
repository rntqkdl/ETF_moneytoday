"""
src/api/alert_manager.py
디스코드(Discord) 및 슬랙(Slack) 전용 멀티채널 리치 임베드 알림 관리자
스마트폰 및 PC로 실시간 목표 비중, 매크로 국면, 포트폴리오 수익률 리포트 전송
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from config.settings import settings

class AlertManager:
    """디스코드 / 슬랙 웹훅 알림 발송기"""

    def __init__(self, webhook_url: Optional[str] = None, channel_type: str = "discord"):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("SLACK_WEBHOOK_URL")
        self.channel_type = channel_type.lower()

    def send_rebalance_alert(self, decision: Any, weights: Dict[str, float], total_nav: float = 1_000_000_000.0) -> bool:
        """리밸런싱 목표 비중 카드 알림 발송"""
        if not self.webhook_url:
            print("⚠️ [Alert Manager] 웹훅 URL이 설정되지 않아 콘솔 출력으로 대체합니다.")
            return False

        if "discord" in self.channel_type or "discord.com" in (self.webhook_url or ""):
            return self._send_discord_rebalance_embed(decision, weights, total_nav)
        elif "slack" in self.channel_type or "slack.com" in (self.webhook_url or ""):
            return self._send_slack_rebalance_blocks(decision, weights, total_nav)
        return False

    def _send_discord_rebalance_embed(self, decision: Any, weights: Dict[str, float], total_nav: float) -> bool:
        """디스코드 전용 Rich Embed 전송"""
        conf_pct = getattr(decision, "confidence_score", 0.90) * 100.0
        regime = getattr(decision, "regime", "AI_Growth_Regime")
        reasoning = getattr(decision, "reasoning", "매크로 뷰 기반 최적화")
        cash_ratio = getattr(decision, "cash_park_ratio", 0.08) * 100.0

        # 종목별 필드 구성
        fields = []
        for idx, (name, w) in enumerate(weights.items(), 1):
            amount = total_nav * w
            fields.append({
                "name": f"{idx}. {name}",
                "value": f"**비중: {w*100:.1f}%** | 배분액: `{amount:,.0f} 원`",
                "inline": False
            })

        payload = {
            "username": "머니투데이 ETF 퀀트봇",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/3135/3135679.png",
            "embeds": [
                {
                    "title": "🚀 [머니투데이 ETF 투자왕] 고확신도 알파 포트폴리오 리밸런싱",
                    "description": f"**시장 국면**: `{regime}`\n**투자 확신도**: **{conf_pct:.1f}%** 🔥\n**현금 완충(SOFR/CD)**: `{cash_ratio:.1f}%`",
                    "color": 3447003, # 블루
                    "fields": fields,
                    "footer": {
                        "text": f"💡 판단 근거: {reasoning}"
                    }
                }
            ]
        }

        try:
            res = requests.post(self.webhook_url, json=payload, timeout=5)
            if res.status_code in [200, 204]:
                print("✅ 디스코드 리치 카드 알림 전송 성공!")
                return True
            else:
                print(f"⚠️ 디스코드 알림 전송 실패 (상태코드: {res.status_code})")
                return False
        except Exception as e:
            print(f"⚠️ 디스코드 웹훅 오류: {e}")
            return False

    def _send_slack_rebalance_blocks(self, decision: Any, weights: Dict[str, float], total_nav: float) -> bool:
        """슬랙 Block Kit 카드 전송"""
        conf_pct = getattr(decision, "confidence_score", 0.90) * 100.0
        regime = getattr(decision, "regime", "AI_Growth_Regime")
        reasoning = getattr(decision, "reasoning", "매크로 뷰 기반 최적화")

        position_lines = []
        for idx, (name, w) in enumerate(weights.items(), 1):
            amount = total_nav * w
            position_lines.append(f"• *{name}*: `{w*100:.1f}%` ({amount:,.0f}원)")

        payload = {
            "text": "🚀 [머니투데이 ETF 투자왕] 실시간 리밸런싱 알림",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚀 [머니투데이 ETF 투자왕] 실시간 리밸런싱 알림"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*시장 국면:*\n`{regime}`"},
                        {"type": "mrkdwn", "text": f"*투자 확신도:*\n*{conf_pct:.1f}%*"}
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*📌 목표 포트폴리오 비중:*\n" + "\n".join(position_lines)}
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"💡 *판단 근거:* {reasoning}"}]
                }
            ]
        }

        try:
            res = requests.post(self.webhook_url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception as e:
            print(f"⚠️ 슬랙 웹훅 오류: {e}")
            return False
