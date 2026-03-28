# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a **multi-project repository** with independent front-end projects and design documentation:

| Directory | Purpose |
|-----------|---------|
| `rga-docs/` | Design documentation for RGA AI knowledge platform |
| `word-learner/` | Vocabulary learning app with spaced repetition |
| `logistics-login/` | Logistics company login page |
| `logistics-chat/` | Customer service chatbot UI (Nexus AI agent) |

## Running the Projects

All projects are standalone HTML/CSS/JS — no build step required.

```bash
# word-learner
xdg-open /home/k/桌面/CODING/word-learner/index.html

# logistics-login
xdg-open /home/k/桌面/CODING/logistics-login/index.html

# logistics-chat
xdg-open /home/k/桌面/CODING/logistics-chat/index.html

# Or serve locally
cd /home/k/桌面/CODING/logistics-login && python3 -m http.server 8080
```

**Demo accounts for logistics-login:** `demo/demo123`, `vip/vip123`, `admin/admin123`

## Architecture Notes

### RGA Knowledge Platform (rga-docs/)
This is the design blueprint for an AI middle platform called **Nexus** — not yet implemented as code. Key design elements:

- **Three-tier knowledge architecture**: Platform (global) → Company (tenant-isolated) → Order/User (personal)
- **SKILL Engine**: Task-matching system with 6 skills (track_waybill, quote_price, query_inventory, create_order, search_knowledge, customer_info)
- **SKILL-to-layer mapping**: Each SKILL maps to specific knowledge layers (see 08_retrieval_engine.md)
- **Retrieval flow**: Classification routing → Semantic expansion → Permission filtering → Merge & rank
- **State machine**: Information collection → Task execution → Result output
- **Data storage**: MySQL 8.0 + Redis + vector database (Milvus/Qdrant)
- **Response format**: Structured output with [Current Judgment] / [Suggested Actions] / [Key Evidence] / [Risk Alert]

**RGA docs structure:**
- 01 系统架构设计 — Core architecture + three-tier knowledge overview
- 07 知识分类体系 — Platform/Company/Order/User layer taxonomy
- 08 检索引擎设计 — SKILL-layer mapping, retrieval flow, permission filtering

### word-learner/
- Spaced repetition using Ebbinghaus forgetting curve (intervals: 1, 3, 7, 14, 30 days)
- localStorage persistence (`word_learner_data`, `word_learner_settings`)
- JSON/CSV import supported

### logistics-chat/
- Mock customer service chat interface for logistics domain
- Simulated AI responses for order tracking, pricing, inventory queries
- Mobile-first responsive design with dark mode support

## No Build/Test Infrastructure

These are prototype/demo projects with no npm packages, no test runners, and no CI/CD.
