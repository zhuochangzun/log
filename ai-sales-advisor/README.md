# AI 销售顾问平台

国际物流 AI 客服系统 Phase 1：接待 + 收款闭环

## 功能

- AI 接待客户咨询
- 智能报价（对接调度系统）
- 订单创建
- 账单生成与收款确认

## Quick Start

```bash
cd ai-sales-advisor
pip install -e ".[dev]"
uvicorn api.main:app --reload
```

## 项目结构

- `skills/` - SKILL 技能定义
- `services/` - 核心服务
- `adapters/` - 外部系统适配器
- `models/` - 数据模型
- `api/` - API 接口
