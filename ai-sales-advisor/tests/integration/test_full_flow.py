import pytest
from unittest.mock import AsyncMock, MagicMock
from services.skill_engine import SkillEngine
from services.conversation_mgr import ConversationManager
from services.handoff_service import HandoffService, HandoffReason
from services.payment_loop import PaymentLoopService
from adapters import DispatchAdapter, CashAdapter
from adapters.dispatch_adapter import CreateOrderRequest, QuoteRequest


@pytest.fixture
def full_setup():
    """完整流程测试设置"""
    conversation_mgr = ConversationManager()
    handoff_service = HandoffService(human_adapter=None)

    # Mock dispatch and cash adapters
    mock_dispatch = MagicMock(spec=DispatchAdapter)
    mock_dispatch.create_order = AsyncMock(return_value=MagicMock(
        dispatch_order_id="ORD123",
        status="PENDING",
        created_at="2026-04-22T10:00:00Z",
    ))
    mock_dispatch.calculate_quote = AsyncMock(return_value=MagicMock(
        total_price=560.0,
        route_id="ROUTE_US",
        warehouse_id="WH_SH",
    ))
    mock_dispatch.get_order = AsyncMock(return_value={"bill_id": "BILL123"})

    mock_cash = MagicMock(spec=CashAdapter)
    mock_cash.create_bill = AsyncMock(return_value=MagicMock(
        bill_id="BILL123",
        order_id="ORD123",
        amount=560.0,
        status="UNPAID",
        due_at="2026-04-25T10:00:00Z",
        created_at="2026-04-22T10:00:00Z",
    ))
    mock_cash.check_payment_status = AsyncMock(return_value="PAID")

    payment_loop = PaymentLoopService(mock_dispatch, mock_cash)

    return {
        "conversation_mgr": conversation_mgr,
        "handoff_service": handoff_service,
        "payment_loop": payment_loop,
    }


@pytest.mark.asyncio
async def test_order_to_payment_flow(full_setup):
    """测试：询价 → 下单 → 收款完整流程"""
    setup = full_setup
    conv_mgr = setup["conversation_mgr"]
    payment_loop = setup["payment_loop"]

    # 1. 创建会话
    conv = await conv_mgr.create_conversation(
        visitor_id="v_test123",
        channel="wechat",
    )
    assert conv["status"] == "ACTIVE"

    # 2. 创建订单和账单
    order, bill = await payment_loop.create_order_and_bill(
        customer_id="CUST001",
        warehouse_id="WH_SH",
        route_id="ROUTE_US",
        weight=20.0,
        from_address="上海",
        to_address="纽约",
        to_contact="李经理",
        to_phone="13800001111",
    )

    assert order.id == "ORD123"
    assert order.total_amount == 560.0
    assert bill.status == "UNPAID"


@pytest.mark.asyncio
async def test_handoff_flow(full_setup):
    """测试：正常对话 → 转人工 → 交回 AI"""
    setup = full_setup
    conv_mgr = setup["conversation_mgr"]
    handoff_service = setup["handoff_service"]

    # 1. 创建会话
    conv = await conv_mgr.create_conversation(
        visitor_id="v_test456",
        channel="wechat",
    )

    # 2. 添加一些消息
    await conv_mgr.add_message(conv["id"], "CUSTOMER", "我想寄货到美国")
    await conv_mgr.add_message(conv["id"], "AI", "您好！美国专线28元/kg，请问您的货物重量是？")

    # 3. 客户要求转人工
    should, reason = handoff_service.should_handoff("帮我转人工客服")
    assert should is True

    # 4. 执行转人工
    result = await handoff_service.execute_handoff(conv, reason)
    assert result["status"] == "handoff"
    assert result["reason"] == HandoffReason.KEYWORD_TRIGGER

    # 5. 更新会话状态
    updated_conv = await conv_mgr.get_conversation(conv["id"])
    assert updated_conv["status"] == "HUMAN_HANDOFF"
