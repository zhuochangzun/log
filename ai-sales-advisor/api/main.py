import uuid
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from .schemas import (
    SendMessageRequest,
    SendMessageResponse,
    CreateConversationRequest,
    CreateConversationResponse,
    HandoffRequest,
    HandoffResponse,
    ReturnToAIRequest,
    CallSummaryRequest,
    WebhookRequest,
)
from services.skill_engine import SkillEngine
from services.conversation_mgr import ConversationManager
from services.handoff_service import HandoffService, HandoffReason
from adapters import DispatchAdapter, CashAdapter
from adapters.human_assistant import HumanAssistantAdapter


# 全局实例
skill_engine: SkillEngine = None
conversation_mgr: ConversationManager = None
dispatch_adapter: DispatchAdapter = None
cash_adapter: CashAdapter = None
handoff_service: HandoffService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global skill_engine, conversation_mgr, dispatch_adapter, cash_adapter, handoff_service

    conversation_mgr = ConversationManager()

    # TODO: 从配置加载
    dispatch_adapter = DispatchAdapter(
        base_url="http://dispatch-api.local",
        api_key="test-key",
    )
    cash_adapter = CashAdapter(
        base_url="http://cash-api.local",
        api_key="test-key",
    )
    handoff_service = HandoffService(
        human_adapter=HumanAssistantAdapter(
            webhook_url="http://human-assistant.local/api/handoff",
            api_key="test-key",
        )
    )

    skill_engine = SkillEngine(
        skills_dir="skills",
        conversation_mgr=conversation_mgr,
    )

    yield
    # Shutdown


app = FastAPI(title="AI Sales Advisor API", lifespan=lifespan)


@app.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation(request: CreateConversationRequest):
    """创建新会话"""
    conv = await conversation_mgr.create_conversation(
        visitor_id=request.visitor_id,
        channel=request.channel,
        customer_id=request.customer_id,
    )
    return CreateConversationResponse(
        conversation_id=conv["id"],
        welcome_message="您好！我是您的国际物流智能助手。有什么可以帮您的？",
    )


@app.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(conversation_id: str, request: SendMessageRequest):
    """发送消息"""
    # 保存用户消息
    await conversation_mgr.add_message(
        conversation_id=conversation_id,
        sender="CUSTOMER",
        content=request.message,
    )

    # 处理并生成回复
    result = await skill_engine.process_message(
        conversation_id=conversation_id,
        message=request.message,
    )

    # 获取刚发送的 AI 消息 ID
    conv = await conversation_mgr.get_conversation(conversation_id)
    msg_id = conv["messages"][-1]["id"]

    return SendMessageResponse(
        message_id=msg_id,
        response=result["response"],
        skill_triggered=result["skill_id"],
    )


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取会话详情"""
    conv = await conversation_mgr.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@app.post("/webhook/dispatch")
async def dispatch_webhook(request: WebhookRequest):
    """接收调度系统回调"""
    # TODO: 处理调度系统回调（如订单状态更新）
    return {"status": "ok"}


@app.post("/webhook/cash")
async def cash_webhook(request: WebhookRequest):
    """接收出纳系统回调"""
    # TODO: 处理出纳系统回调（如付款确认）
    return {"status": "ok"}


@app.post("/conversations/{conversation_id}/handoff", response_model=HandoffResponse)
async def handoff_to_human(conversation_id: str, request: HandoffRequest):
    """转人工客服"""
    conversation = await conversation_mgr.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    reason = request.reason or HandoffReason.CUSTOMER_REQUEST
    result = await handoff_service.execute_handoff(conversation, reason)

    return HandoffResponse(
        handoff_id=result["handoff_id"],
        reason=reason,
        estimated_wait_time=result["estimated_wait_time"],
        message=result["message"],
    )


@app.post("/conversations/{conversation_id}/return-to-ai")
async def return_to_ai(conversation_id: str, request: ReturnToAIRequest):
    """人工处理完毕后交回 AI"""
    conversation = await conversation_mgr.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await handoff_service.return_to_ai(conversation_id, request.result)

    return result


@app.post("/call-summary")
async def create_call_summary(request: CallSummaryRequest):
    """创建通话摘要（用于电话渠道）"""
    summary = {
        "customer_name": request.customer_name,
        "customer_phone": request.customer_phone,
        "tier": request.tier,
        "call_purpose": request.call_purpose,
        "recent_development": request.recent_development,
        "pending_items": request.pending_items,
        "historical_notes": request.historical_notes,
        "suggestions": request.suggestions,
    }

    if handoff_service.human_adapter:
        await handoff_service.human_adapter.send_call_summary(
            conversation_id=request.conversation_id,
            summary=summary,
        )

    return {"status": "ok", "summary_id": f"sum_{uuid.uuid4().hex[:12]}"}