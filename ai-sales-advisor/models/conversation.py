from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ConversationMode(str, Enum):
    RECEPTION = "RECEPTION"       # 接待模式
    MARKETING = "MARKETING"       # 营销模式


class ConversationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    CLOSED = "CLOSED"


class MessageSender(str, Enum):
    CUSTOMER = "CUSTOMER"
    AI = "AI"
    HUMAN = "HUMAN"


class Conversation(BaseModel):
    id: str = Field(..., description="会话ID")
    customer_id: str | None = Field(None, description="客户ID")
    visitor_id: str = Field(..., description="访客ID")
    channel: str = Field(..., description="渠道: wechat/website/phone")
    mode: ConversationMode = Field(ConversationMode.RECEPTION)
    status: ConversationStatus = Field(ConversationStatus.ACTIVE)
    skill_sequence: list[str] = Field(default_factory=list, description="触发的SKILL顺序")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="会话ID")
    sender: MessageSender = Field(...)
    content: str = Field(..., description="消息内容")
    skill_triggered: str | None = Field(None, description="触发的SKILL")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True