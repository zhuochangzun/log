from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from .schemas import (
    SendMessageRequest,
    SendMessageResponse,
    CreateConversationRequest,
    CreateConversationResponse,
)
from services.skill_engine import SkillEngine
from services.conversation_mgr import ConversationManager
from adapters import DispatchAdapter, CashAdapter


# 全局实例
skill_engine: SkillEngine = None
conversation_mgr: ConversationManager = None
dispatch_adapter: DispatchAdapter = None
cash_adapter: CashAdapter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global skill_engine, conversation_mgr, dispatch_adapter, cash_adapter

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