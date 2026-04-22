# AI 销售顾问平台 Phase 2 - 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 SKL103 下单创建、SKL104 收款确认、企业微信 SDK 对接、人工助手转接逻辑

**Architecture:** 在 Phase 1 基础上扩展：新增 SKL103/104 技能定义 + WeChat Work SDK 适配器 + 人工转接服务，继续复用调度/出纳系统适配器

**Tech Stack:** Python/Go 微服务、wechatpy、企业微信 SDK、Redis WebSocket（人工转接通知）

---

## 文件结构

```
ai-sales-advisor/
├── skills/                          # SKILL 技能定义
│   ├── SKL103_下单创建/
│   │   ├── skill.json
│   │   └── prompt.md
│   └── SKL104_收款确认/
│       ├── skill.json
│       └── prompt.md
│
├── adapters/                        # 外部系统适配器（新增）
│   ├── wechat_adapter.py          # 企业微信 SDK 适配器
│   └── human_assistant.py          # 人工助手通知适配器
│
├── services/                        # 服务层（扩展）
│   ├── handoff_service.py         # 人工转接服务
│   ├── payment_loop.py            # 已存在，扩展
│   └── skill_engine.py            # 已存在，扩展
│
├── api/                            # API 接口（扩展）
│   ├── main.py                    # 已存在，扩展路由
│   └── schemas.py                 # 已存在，扩展
│
└── tests/
    └── integration/
```

---

## Task 1: SKL103 下单创建

**Files:**
- Create: `ai-sales-advisor/skills/SKL103_下单创建/skill.json`
- Create: `ai-sales-advisor/skills/SKL103_下单创建/prompt.md`
- Modify: `ai-sales-advisor/services/skill_engine.py` — 添加 SKL103 加载

- [ ] **Step 1: 创建 SKL103 技能配置**

```json
{
  "id": "SKL103",
  "name": "下单创建",
  "description": "调用调度系统创建订单",
  "trigger_keywords": ["下单", "创建订单", "确认下单", "好的", "可以"],
  "required_params": ["customer_id", "warehouse_id", "route_id", "weight", "from_address", "to_address", "to_contact", "to_phone"],
  "optional_params": ["cargo_type", "remarks"],
  "output": {
    "type": "order",
    "next_skill": "SKL104"
  }
}
```

- [ ] **Step 2: 创建 SKL103 prompt 模板**

```markdown
# SKL103 下单创建

你是国际物流订单创建专家，根据客户确认的信息在调度系统创建订单。

## 输入参数

- customer_id: 客户ID
- warehouse_id: 仓库ID
- route_id: 路线ID
- weight: 重量(kg)
- from_address: 发货地址
- to_address: 收货地址
- to_contact: 收货联系人
- to_phone: 收货电话
- cargo_type: 货物类型(可选)
- remarks: 备注(可选)

## 输出格式

```json
{
  "order_id": "ORD123456",
  "dispatch_order_id": "DSP20260422001",
  "status": "PENDING",
  "total_amount": "560元",
  "created_at": "2026-04-22 10:00:00",
  "next_action": "等待付款"
}
```

## 规则

1. 必须调用 dispatch_adapter.create_order() 创建订单
2. 订单创建成功后，自动生成订单确认消息
3. 引导客户进入付款环节（调用 SKL104）
4. 如果调度系统返回错误，友好地告知客户并提供替代方案
```

- [ ] **Step 3: Commit**

```bash
git add skills/SKL103_下单创建/
git commit -m "feat: add SKL103 order creation skill"
```

---

## Task 2: SKL104 收款确认

**Files:**
- Create: `ai-sales-advisor/skills/SKL104_收款确认/skill.json`
- Create: `ai-sales-advisor/skills/SKL104_收款确认/prompt.md`

- [ ] **Step 1: 创建 SKL104 技能配置**

```json
{
  "id": "SKL104",
  "name": "收款确认",
  "description": "生成账单、跟踪付款状态、确认到账",
  "trigger_keywords": ["付款", "怎么付", "支付", "已付", "转账"],
  "required_params": ["order_id"],
  "optional_params": ["payment_channel"],
  "output": {
    "type": "bill",
    "next_skill": null
  }
}
```

- [ ] **Step 2: 创建 SKL104 prompt 模板**

```markdown
# SKL104 收款确认

你是国际物流收款确认专家，负责账单生成和付款跟踪。

## 输入参数

- order_id: 订单ID
- payment_channel: 支付渠道(可选): wechat/alipay/bank

## 输出格式

```json
{
  "bill_id": "BILL123456",
  "order_id": "ORD123456",
  "amount": "560元",
  "due_at": "2026-04-25 10:00:00",
  "payment_methods": [
    {"channel": "微信支付", "account": "xxx"},
    {"channel": "支付宝", "account": "xxx"},
    {"channel": "银行转账", "account": "xxx"}
  ],
  "status": "UNPAID"
}
```

## 规则

1. 必须调用 cash_adapter.create_bill() 生成账单
2. 展示多种支付方式供客户选择
3. 告知客户账单有效期（3天）
4. 如果客户表示已付款，调用 cash_adapter.check_payment_status() 确认
5. 付款确认后，通知仓库允许出库（调用 payment_loop_service）
```

- [ ] **Step 3: Commit**

```bash
git add skills/SKL104_收款确认/
git commit -m "feat: add SKL104 payment confirmation skill"
```

---

## Task 3: 企业微信 SDK 对接

**Files:**
- Create: `ai-sales-advisor/adapters/wechat_adapter.py`
- Modify: `ai-sales-advisor/adapters/__init__.py`

- [ ] **Step 1: 创建企业微信适配器**

```python
# ai-sales-advisor/adapters/wechat_adapter.py
import httpx
from pydantic import BaseModel
from typing import Optional


class WeChatMessage(BaseModel):
    """企业微信消息"""
    to_user: str
    msg_type: str = "text"
    content: str


class WeChatTextMessage(WeChatMessage):
    msg_type: str = "text"


class WeChatImageMessage(WeChatMessage):
    msg_type: str = "image"
    media_id: str


class WeChatCardMessage(WeChatMessage):
    msg_type: str = "miniprogram_card"
    title: str
    description: str
    url: str
    picurl: str


class WeChatAdapter:
    """企业微信 SDK 适配器"""

    def __init__(self, corp_id: str, agent_id: str, secret: str):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        """获取 access_token"""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                params={
                    "corpid": self.corp_id,
                    "corpsecret": self.secret,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def send_text(self, to_user: str, content: str) -> dict:
        """发送文本消息"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                params={"access_token": token},
                json={
                    "touser": to_user,
                    "msgtype": "text",
                    "agentid": self.agent_id,
                    "text": {"content": content},
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def send_image(self, to_user: str, media_id: str) -> dict:
        """发送图片消息"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                params={"access_token": token},
                json={
                    "touser": to_user,
                    "msgtype": "image",
                    "agentid": self.agent_id,
                    "image": {"media_id": media_id},
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def send_bill_card(self, to_user: str, bill_info: dict) -> dict:
        """发送账单卡片消息"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/message/send",
                params={"access_token": token},
                json={
                    "touser": to_user,
                    "msgtype": "miniprogram_card",
                    "agentid": self.agent_id,
                    "miniprogram_card": {
                        "title": f"账单 #{bill_info['bill_id']}",
                        "description": f"应付金额：{bill_info['amount']}",
                        "url": bill_info.get("payment_url", ""),
                        "picurl": bill_info.get("qr_code_url", ""),
                    },
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, user_id: str) -> dict:
        """获取企业微信用户信息"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://qyapi.weixin.qq.com/cgi-bin/user/get",
                params={"access_token": token, "userid": user_id},
            )
            resp.raise_for_status()
            return resp.json()

    async def create_menu(self, menu_config: dict) -> dict:
        """创建应用菜单"""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://qyapi.weixin.qq.com/cgi-bin/menu/create",
                params={"access_token": token, "agentid": self.agent_id},
                json=menu_config,
            )
            resp.raise_for_status()
            return resp.json()
```

- [ ] **Step 2: 更新 adapters/__init__.py**

```python
# ai-sales-advisor/adapters/__init__.py
from .dispatch_adapter import DispatchAdapter, Warehouse, Route, QuoteRequest, QuoteResult
from .cash_adapter import CashAdapter, CreateBillRequest, BillResult
from .wechat_adapter import WeChatAdapter, WeChatTextMessage, WeChatImageMessage, WeChatCardMessage

__all__ = [
    "DispatchAdapter",
    "Warehouse",
    "Route",
    "QuoteRequest",
    "QuoteResult",
    "CashAdapter",
    "CreateBillRequest",
    "BillResult",
    "WeChatAdapter",
    "WeChatTextMessage",
    "WeChatImageMessage",
    "WeChatCardMessage",
]
```

- [ ] **Step 3: Commit**

```bash
git add adapters/wechat_adapter.py adapters/__init__.py
git commit -m "feat: add WeChat Work SDK adapter"
```

---

## Task 4: 人工助手转接逻辑

**Files:**
- Create: `ai-sales-advisor/services/handoff_service.py`
- Create: `ai-sales-advisor/adapters/human_assistant.py`
- Modify: `ai-sales-advisor/models/conversation.py` — 添加 HumanHandoffRecord
- Modify: `ai-sales-advisor/api/schemas.py` — 添加转接相关 schema
- Modify: `ai-sales-advisor/api/main.py` — 添加转接 API 路由

- [ ] **Step 1: 创建人工助手通知适配器**

```python
# ai-sales-advisor/adapters/human_assistant.py
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
```

- [ ] **Step 2: 创建人工转接服务**

```python
# ai-sales-advisor/services/handoff_service.py
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
```

- [ ] **Step 3: 添加 HumanHandoffRecord 模型扩展**

```python
# 在 ai-sales-advisor/models/conversation.py 中添加

class HandoffRecord(BaseModel):
    """转接记录"""
    id: str = Field(..., description="转接记录ID")
    conversation_id: str = Field(..., description="会话ID")
    reason: str = Field(..., description="转接原因")
    priority: str = Field(default="NORMAL", description="优先级")
    handoff_at: datetime = Field(default_factory=datetime.utcnow)
    return_at: datetime | None = Field(None, description="归还AI时间")
    result: str | None = Field(None, description="处理结果")
    agent_id: str | None = Field(None, description="处理人工ID")

    class Config:
        use_enum_values = True
```

- [ ] **Step 4: 扩展 API schemas**

```python
# 在 ai-sales-advisor/api/schemas.py 中添加

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
```

- [ ] **Step 5: 扩展 API 路由**

```python
# 在 ai-sales-advisor/api/main.py 中添加

from services.handoff_service import HandoffService, HandoffReason
from adapters.human_assistant import HumanAssistantAdapter

# 全局实例（添加）
handoff_service: HandoffService = None

# 在 lifespan 中初始化
handoff_service = HandoffService(
    human_adapter=HumanAssistantAdapter(
        webhook_url="http://human-assistant.local/api/handoff",
        api_key="test-key",
    )
)

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
```

- [ ] **Step 6: Commit**

```bash
git add adapters/human_assistant.py services/handoff_service.py api/schemas.py api/main.py models/conversation.py
git commit -m "feat: add human assistant handoff logic"
```

---

## Task 5: 扩展 SKILL 引擎支持转人工

**Files:**
- Modify: `ai-sales-advisor/services/skill_engine.py`

- [ ] **Step 1: 扩展 SkillEngine 支持自动转人工检测**

```python
# 在 ai-sales-advisor/services/skill_engine.py 中修改

class SkillEngine:
    """SKILL 执行引擎"""

    def __init__(self, skills_dir: Path, conversation_mgr: ConversationManager, handoff_service: HandoffService | None = None):
        self.skills_dir = Path(skills_dir)
        self.conversation_mgr = conversation_mgr
        self.handoff_service = handoff_service
        self.skills: dict[str, dict] = {}
        self._load_skills()

    # ... existing methods ...

    async def process_message(
        self,
        conversation_id: str,
        message: str,
    ) -> dict[str, Any]:
        """处理用户消息"""
        conversation = await self.conversation_mgr.get_conversation(conversation_id)
        context = conversation.get("context", {}) if conversation else {}

        # 检查是否需要转人工
        if self.handoff_service:
            should_handoff, reason = self.handoff_service.should_handoff(message)
            if should_handoff:
                handoff_result = await self.handoff_service.execute_handoff(conversation, reason)
                return {
                    "type": "handoff",
                    "handoff": handoff_result,
                }

        skill_id = self.match_skill(message)

        result = await self.execute_skill(skill_id, message, context)

        # 保存消息到会话
        await self.conversation_mgr.add_message(
            conversation_id=conversation_id,
            sender="AI",
            content=result["response"],
            skill_triggered=skill_id,
        )

        return result
```

- [ ] **Step 2: Commit**

```bash
git add services/skill_engine.py
git commit -m "feat: integrate handoff detection into skill engine"
```

---

## Task 6: 集成测试

**Files:**
- Create: `ai-sales-advisor/tests/integration/test_handoff_service.py`
- Create: `ai-sales-advisor/tests/integration/test_wechat_adapter.py`

- [ ] **Step 1: 创建转接服务测试**

```python
# ai-sales-advisor/tests/integration/test_handoff_service.py
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
```

- [ ] **Step 2: 创建企业微信适配器测试**

```python
# ai-sales-advisor/tests/integration/test_wechat_adapter.py
import pytest
from adapters.wechat_adapter import WeChatAdapter


@pytest.fixture
def wechat_adapter():
    return WeChatAdapter(
        corp_id="test_corp_id",
        agent_id="test_agent_id",
        secret="test_secret",
    )


@pytest.mark.asyncio
async def test_send_text_message(wechat_adapter, respx_mock):
    """发送文本消息"""
    respx_mock.get("https://qyapi.weixin.qq.com/cgi-bin/gettoken").mock(
        return_value=Response(200, json={"access_token": "test_token"})
    )
    respx_mock.post("https://qyapi.weixin.qq.com/cgi-bin/message/send").mock(
        return_value=Response(200, json={"errcode": 0, "errmsg": "ok"})
    )

    result = await wechat_adapter.send_text("user123", "您好，有什么可以帮您？")

    assert result["errcode"] == 0


@pytest.mark.asyncio
async def test_get_user_info(wechat_adapter, respx_mock):
    """获取用户信息"""
    respx_mock.get("https://qyapi.weixin.qq.com/cgi-bin/gettoken").mock(
        return_value=Response(200, json={"access_token": "test_token"})
    )
    respx_mock.get("https://qyapi.weixin.qq.com/cgi-bin/user/get").mock(
        return_value=Response(200, json={
            "errcode": 0,
            "errmsg": "ok",
            "userid": "user123",
            "name": "张三",
        })
    )

    result = await wechat_adapter.get_user_info("user123")

    assert result["name"] == "张三"
```

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_handoff_service.py tests/integration/test_wechat_adapter.py
git commit -m "test: add handoff service and WeChat adapter tests"
```

---

## Task 7: 端到端集成测试

**Files:**
- Create: `ai-sales-advisor/tests/integration/test_full_flow.py`

- [ ] **Step 1: 创建完整流程测试**

```python
# ai-sales-advisor/tests/integration/test_full_flow.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.skill_engine import SkillEngine
from services.conversation_mgr import ConversationManager
from services.handoff_service import HandoffService
from services.payment_loop import PaymentLoopService
from adapters import DispatchAdapter, CashAdapter


@pytest.fixture
async def full_setup():
    """完整流程测试设置"""
    conversation_mgr = ConversationManager()
    handoff_service = HandoffService(human_adapter=None)
    skill_engine = SkillEngine(
        skills_dir="skills",
        conversation_mgr=conversation_mgr,
        handoff_service=handoff_service,
    )

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
        "skill_engine": skill_engine,
        "handoff_service": handoff_service,
        "payment_loop": payment_loop,
    }


@pytest.mark.asyncio
async def test_order_to_payment_flow(full_setup):
    """测试：询价 → 下单 → 收款完整流程"""
    setup = await full_setup
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
    setup = await full_setup
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
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/test_full_flow.py
git commit -m "test: add end-to-end integration tests"
```

---

## 实施检查清单

- [ ] Task 1: SKL103 下单创建
- [ ] Task 2: SKL104 收款确认
- [ ] Task 3: 企业微信 SDK 对接
- [ ] Task 4: 人工助手转接逻辑
- [ ] Task 5: SKILL 引擎支持转人工
- [ ] Task 6: 集成测试
- [ ] Task 7: 端到端测试

---

## 下一步

Phase 2 完成后：
- SKL105 跟单状态（物流跟踪）
- SKL106 催付提醒
- SKL107 主动营销
- SKL108 产品推送
- 电话渠道接入（IVR + 来电识别）
- 人工助手工作台开发

---

*计划版本：v1.0 | 日期：2026-04-22*
