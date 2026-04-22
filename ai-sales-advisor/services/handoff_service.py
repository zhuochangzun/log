import uuid
from datetime import datetime
from typing import Any
from models.conversation import ConversationStatus
from adapters.human_assistant import HumanAssistantAdapter, HandoffNotification


class HandoffReason:
    """转接原因常量"""
    CUSTOMER_REQUEST = "customer_request"       # 客户要求转人工
    NEGATIVE_EMOTION = "negative_emotion"      # 负面情绪检测
    PRICE_NEGOTIATION = "price_negotiation"    # 砍价/议价
    COMPLEX_ISSUE = "complex_issue"            # 复杂业务问题
    LOW_CONFIDENCE = "low_confidence"          # AI 置信度低
    KEYWORD_TRIGGER = "keyword_trigger"        # 关键词触发


class HandoffService:
    """人工转接服务"""

    # 触发关键词
    HUMAN_TRIGGER_KEYWORDS = [
        "打电话", "电话", "语音", "人工", "客服",
        "投诉", "不满", "太差", "废物", "没用",
        "找老板", "找经理", "找销售"
    ]

    # 负面情绪词
    NEGATIVE_EMOTION_WORDS = [
        "生气", "愤怒", "失望", "不满", "差劲",
        "垃圾", "骗子", "坑人", "投诉"
    ]

    def __init__(
        self,
        human_adapter: HumanAssistantAdapter | None = None,
    ):
        self.human_adapter = human_adapter

    def should_handoff(self, message: str, confidence: float | None = None) -> tuple[bool, str | None]:
        """判断是否需要转人工"""
        message_lower = message.lower()

        # 检查触发关键词
        for keyword in self.HUMAN_TRIGGER_KEYWORDS:
            if keyword in message_lower:
                return True, HandoffReason.KEYWORD_TRIGGER

        # 检查负面情绪
        for word in self.NEGATIVE_EMOTION_WORDS:
            if word in message_lower:
                return True, HandoffReason.NEGATIVE_EMOTION

        # 置信度检查
        if confidence is not None and confidence < 0.6:
            return True, HandoffReason.LOW_CONFIDENCE

        return False, None

    def build_handoff_context(self, conversation: dict, reason: str) -> dict:
        """构建转接上下文"""
        customer = conversation.get("customer")
        messages = conversation.get("messages", [])

        # 提取最近对话
        recent_messages = messages[-10:] if len(messages) > 10 else messages

        # 生成摘要
        summary = self._generate_summary(conversation, recent_messages)

        return {
            "conversation_id": conversation["id"],
            "customer_id": customer.get("id") if customer else None,
            "customer_name": customer.get("name", "未知") if customer else "访客",
            "customer_phone": customer.get("phone") if customer else None,
            "reason": reason,
            "priority": "HIGH" if reason in [HandoffReason.NEGATIVE_EMOTION, HandoffReason.CUSTOMER_REQUEST] else "NORMAL",
            "context": {
                "channel": conversation.get("channel", "unknown"),
                "mode": conversation.get("mode", "RECEPTION"),
                "skill_sequence": conversation.get("skill_sequence", []),
                "last_10_messages": recent_messages,
                "ai_summary": summary,
            }
        }

    def _generate_summary(self, conversation: dict, messages: list) -> str:
        """生成 AI 摘要（通话前展示给人工）"""
        customer = conversation.get("customer")
        skill_sequence = conversation.get("skill_sequence", [])

        lines = [
            f"【会话概要】",
            f"渠道：{conversation.get('channel', '未知')}",
            f"模式：{conversation.get('mode', 'RECEPTION')}",
            f"触发技能：{', '.join(skill_sequence) if skill_sequence else '无'}",
        ]

        if customer:
            lines.append(f"客户：{customer.get('name', '未知')} ({customer.get('tier', 'NORMAL')})")
            lines.append(f"电话：{customer.get('phone', '未知')}")

        if messages:
            lines.append("")
            lines.append("【最近对话】")
            for msg in messages[-5:]:
                sender = "客户" if msg.get("sender") == "CUSTOMER" else "AI"
                lines.append(f"{sender}: {msg.get('content', '')[:100]}")

        return "\n".join(lines)

    async def execute_handoff(self, conversation: dict, reason: str) -> dict:
        """执行转人工"""
        context = self.build_handoff_context(conversation, reason)

        # 更新会话状态
        conversation["status"] = ConversationStatus.HUMAN_HANDOFF.value
        conversation["handoff_reason"] = reason
        conversation["handoff_at"] = datetime.utcnow().isoformat()

        # 通知人工助手工作台
        if self.human_adapter:
            notification = HandoffNotification(**context)
            await self.human_adapter.notify_handoff(notification)

        return {
            "status": "handoff",
            "reason": reason,
            "handoff_id": f"h_{uuid.uuid4().hex[:12]}",
            "estimated_wait_time": "< 1分钟",
            "message": "正在为您转接人工客服，请稍候..."
        }

    async def return_to_ai(self, conversation_id: str, handoff_result: dict | None = None) -> dict:
        """人工处理完毕后交回 AI"""
        # 更新会话状态
        conversation["status"] = ConversationStatus.ACTIVE.value
        conversation["ai_resumed_at"] = datetime.utcnow().isoformat()
        if handoff_result:
            conversation["handoff_result"] = handoff_result

        return {
            "status": "ai_resumed",
            "message": "人工服务已结束，继续为您服务"
        }
