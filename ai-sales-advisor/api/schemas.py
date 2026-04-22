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


class HandoffRequest(BaseModel):
    conversation_id: str
    reason: str | None = None


class HandoffResponse(BaseModel):
    handoff_id: str
    reason: str
    estimated_wait_time: str
    message: str


class ReturnToAIRequest(BaseModel):
    conversation_id: str
    result: str | None = None


class CallSummaryRequest(BaseModel):
    conversation_id: str
    customer_name: str
    customer_phone: str | None
    tier: str
    call_purpose: str
    recent_development: str
    pending_items: list[str]
    historical_notes: list[str]
    suggestions: list[str]