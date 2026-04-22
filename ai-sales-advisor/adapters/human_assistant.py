import httpx
from pydantic import BaseModel
from typing import Optional


class HandoffNotification(BaseModel):
    """人工转接通知"""
    conversation_id: str
    customer_id: str | None
    customer_name: str
    customer_phone: str | None
    reason: str
    priority: str = "NORMAL"  # HIGH/NORMAL/LOW
    context: dict


class HumanAssistantAdapter:
    """人工助手工作台通知适配器"""

    def __init__(self, webhook_url: str, api_key: str | None = None):
        self.webhook_url = webhook_url
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def notify_handoff(self, notification: HandoffNotification) -> dict:
        """发送转接通知到人工助手工作台"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.webhook_url,
                json=notification.model_dump(),
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def send_call_summary(self, conversation_id: str, summary: dict) -> dict:
        """发送通话摘要"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.webhook_url}/call-summary",
                json={
                    "conversation_id": conversation_id,
                    "summary": summary,
                },
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()
