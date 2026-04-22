import pytest
from services.handoff_service import HandoffService, HandoffReason


@pytest.fixture
def handoff_service():
    return HandoffService(human_adapter=None)


def test_should_handoff_customer_request(handoff_service):
    """客户要求转人工"""
    should, reason = handoff_service.should_handoff("帮我转人工客服")
    assert should is True
    assert reason == HandoffReason.KEYWORD_TRIGGER


def test_should_handoff_negative_emotion(handoff_service):
    """负面情绪检测"""
    should, reason = handoff_service.should_handoff("太差了，很不满意")
    assert should is True
    assert reason == HandoffReason.NEGATIVE_EMOTION


def test_should_handoff_price_negotiation(handoff_service):
    """砍价意图"""
    should, reason = handoff_service.should_handoff("能不能便宜点")
    assert should is False  # 砍价由 AI 处理，不直接转人工


def test_should_not_handoff_normal_message(handoff_service):
    """正常消息不转人工"""
    should, reason = handoff_service.should_handoff("我想寄到美国多少钱")
    assert should is False
    assert reason is None


def test_should_handoff_low_confidence(handoff_service):
    """低置信度转人工"""
    should, reason = handoff_service.should_handoff("some ambiguous message", confidence=0.5)
    assert should is True
    assert reason == HandoffReason.LOW_CONFIDENCE


def test_build_handoff_context(handoff_service):
    """构建转接上下文"""
    conversation = {
        "id": "conv_123",
        "channel": "wechat",
        "mode": "RECEPTION",
        "skill_sequence": ["SKL101", "SKL102"],
        "customer": {
            "id": "cust_456",
            "name": "张总",
            "phone": "13800001111",
            "tier": "VIP",
        },
        "messages": [
            {"sender": "CUSTOMER", "content": "寄到美国多少钱"},
            {"sender": "AI", "content": "美国专线 28元/kg"},
        ],
    }

    context = handoff_service.build_handoff_context(conversation, HandoffReason.CUSTOMER_REQUEST)

    assert context["conversation_id"] == "conv_123"
    assert context["customer_name"] == "张总"
    assert context["reason"] == HandoffReason.CUSTOMER_REQUEST
    assert context["priority"] == "HIGH"
    assert "SKL101" in context["context"]["skill_sequence"]
