from pydantic import BaseModel, Field
from datetime import datetime


class SendMessageRequest(BaseModel):
    conversation_id: str
    message: str


class SendMessageResponse(BaseModel):
    message_id: str
    response: str
    skill_triggered: str


class CreateConversationRequest(BaseModel):
    visitor_id: str
    channel: str = "wechat"
    customer_id: str | None = None


class CreateConversationResponse(BaseModel):
    conversation_id: str
    welcome_message: str


class WebhookRequest(BaseModel):
    event: str
    data: dict