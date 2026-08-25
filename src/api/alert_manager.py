"""
src/api/alert_manager.py
디스코드(Discord) 및 슬랙(Slack / Slack Workflow Webhook) 전용 멀티채널 리치 알림 관리자
스마트폰 및 PC로 실시간 목표 비중, 매크로 국면, 포트폴리오 수익률 리포트 전송
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from config.settings import settings

class AlertManager:
    """디스코드 / 슬랙 웹훅 알림 발송기"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL or settings.DISCORD_WEBHOOK_URL

    def send_rebalance_alert(self, decision: Any, weights: Dict[str, float], total_nav: float = 1_000_000_000.0) -> bool:
        """리밸런싱 목표 비중 카드 알림 발송"""
        if not self.webhook_url:
            print("⚠️ [Alert Manager] 웹훅 URL이 설정되지 않아 콘솔 출력으로 대체합니다.")
            return False

        if "discord.com" in self.webhook_url:
            return self._send_discord_rebalance_embed(decision, weights, total_nav)
        elif "slack.com" in self.webhook_url or "hooks.slack.com" in self.webhook_url:
            return self._send_slack_rebalance_blocks(decision, weights, total_nav)
        return False

    def _send_discord_rebalance_embed(self, decision: Any, weights: Dict[str, float], total_nav: float) -> bool:
        """디스코드 전용 Rich Embed 전송"""
        conf_pct = getattr(decision, "confidence_score", 0.90) * 100.0
        regime = getattr(decision, "regime", "AI_Growth_Regime")
        reasoning = getattr(decision, "reasoning", "매크로 뷰 기반 최적화")
        cash_ratio = getattr(decision, "cash_park_ratio", 0.08) * 100.0

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
                    "color": 3447003,
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
            print(f"⚠️ 디스코드 알림 전송 실패 ({res.status_code})")
            return False
        except Exception as e:
            print(f"⚠️ 디스코드 웹훅 오류: {e}")
            return False

    def _send_slack_rebalance_blocks(self, decision: Any, weights: Dict[str, float], total_nav: float) -> bool:
        """슬랙 Incoming Webhook 및 Slack Workflow Trigger 호환 전송"""
        conf_pct = getattr(decision, "confidence_score", 0.90) * 100.0
        regime = getattr(decision, "regime", "AI_Growth_Regime")
        reasoning = getattr(decision, "reasoning", "매크로 뷰 기반 최적화")
        cash_ratio = getattr(decision, "cash_park_ratio", 0.08) * 100.0

        position_lines = []
        for idx, (name, w) in enumerate(weights.items(), 1):
            amount = total_nav * w
            position_lines.append(f"• *{name}*: `{w*100:.1f}%` ({amount:,.0f}원)")

        summary_text = (
            f"🚀 [머니투데이 ETF 투자왕] 실시간 알파 리밸런싱 알림\n\n"
            f"• 시장 국면: {regime}\n"
            f"• 투자 확신도: {conf_pct:.1f}%\n"
            f"• 현금 완충: {cash_ratio:.1f}%\n\n"
            f"📌 목표 비중:\n" + "\n".join(position_lines) + f"\n\n💡 판단 근거: {reasoning}"
        )

        # Slack Workflow Webhook Trigger 및 일반 Webhook을 모두 지원하는 하이브리드 페이로드
        payload = {
            "text": summary_text,
            "headline": "🚀 [머니투데이 ETF 투자왕] 실시간 알파 리밸런싱 알림",
            "regime": regime,
            "confidence": f"{conf_pct:.1f}%",
            "cash_ratio": f"{cash_ratio:.1f}%",
            "positions": "\n".join(position_lines),
            "reasoning": reasoning,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚀 [머니투데이 ETF 투자왕] 실시간 알파 리밸런싱"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*시장 국면:*\n`{regime}`"},
                        {"type": "mrkdwn", "text": f"*투자 확신도:*\n*{conf_pct:.1f}%* 🔥"}
                    ]
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*📌 목표 포트폴리오 비중 (10억 원 기준):*\n" + "\n".join(position_lines)}
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"💡 *판단 근거:* {reasoning}"}]
                }
            ]
        }

        try:
            res = requests.post(self.webhook_url, json=payload, timeout=8)
            if res.status_code in [200, 204]:
                print("✅ 슬랙(Slack) 실시간 리밸런싱 알림 전송 성공!")
                return True
            else:
                print(f"⚠️ 슬랙 알림 응답 코드: {res.status_code} | 내용: {res.text}")
                return False
        except Exception as e:
            print(f"❌ 슬랙 웹훅 전송 오류: {e}")
            return False
