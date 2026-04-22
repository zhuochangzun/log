import uuid
from datetime import datetime
from typing import Any


class ConversationManager:
    """会话管理器"""

    def __init__(self):
        self.conversations: dict[str, dict] = {}

    async def create_conversation(
        self,
        visitor_id: str,
        channel: str = "wechat",
        customer_id: str | None = None,
    ) -> dict:
        """创建新会话"""
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        conversation = {
            "id": conv_id,
            "visitor_id": visitor_id,
            "customer_id": customer_id,
            "channel": channel,
            "mode": "RECEPTION",
            "status": "ACTIVE",
            "messages": [],
            "context": {},
            "skill_sequence": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.conversations[conv_id] = conversation
        return conversation

    async def get_conversation(self, conv_id: str) -> dict | None:
        """获取会话"""
        return self.conversations.get(conv_id)

    async def add_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        skill_triggered: str | None = None,
    ):
        """添加消息到会话"""
        conv = self.conversations.get(conversation_id)
        if not conv:
            return

        message = {
            "id": f"msg_{uuid.uuid4().hex[:12]}",
            "sender": sender,
            "content": content,
            "skill_triggered": skill_triggered,
            "created_at": datetime.utcnow().isoformat(),
        }
        conv["messages"].append(message)
        conv["updated_at"] = datetime.utcnow().isoformat()

        if skill_triggered and skill_triggered not in conv["skill_sequence"]:
            conv["skill_sequence"].append(skill_triggered)

    async def update_context(
        self,
        conversation_id: str,
        context: dict[str, Any],
    ):
        """更新会话上下文"""
        conv = self.conversations.get(conversation_id)
        if conv:
            conv["context"].update(context)
            conv["updated_at"] = datetime.utcnow().isoformat()
