# Three-Tier Knowledge Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the three-tier knowledge architecture (Platform/Company/User layers) with SKILL-layer mapping and retrieval flow.

**Architecture:** Three-tier tenant isolation with hierarchical permissions. Platform layer is globally visible, Company layer is tenant-isolated, User layer is personal with optional sharing. Knowledge retrieval uses classification routing + semantic expansion + permission filtering.

**Tech Stack:** MySQL 8.0, Redis, FastAPI/Node.js, Milvus/Qdrant (vector DB)

---

## 1. Database Schema Changes

### 1.1 Overview of Changes

| Table | Action | Changes |
|-------|--------|---------|
| `KNOWLEDGE` | Modify | Add `layer`, `company_id`, `order_stage` fields |
| `SKILLS` | Modify | Add `retrieval_layers` JSON field |
| `COMPANY` | Create | New tenant isolation table |
| `CATEGORY` | Create | New taxonomy management table |
| `USER_LAYER_CONTENT` | Create | User personal knowledge table |
| `USER_CONTENT_SHARE` | Create | User content sharing table |

### 1.2 Files

- Modify: `rga-docs/03_schema.sql:224-251` (KNOWLEDGE table)
- Modify: `rga-docs/03_schema.sql:198-219` (SKILLS table)
- Create: `rga-docs/03_schema.sql` (new tables section)

---

### Task 1: Add COMPANY Table for Tenant Isolation

**Files:**
- Modify: `rga-docs/03_schema.sql`

- [ ] **Step 1: Add COMPANY table after USER table section**

```sql
-- =====================================================
-- 11. 公司表 (COMPANY) - 租户隔离
-- =====================================================
CREATE TABLE IF NOT EXISTS `COMPANY` (
    `company_id`        VARCHAR(32)         NOT NULL,
    `company_name`     VARCHAR(128)       NOT NULL,
    `company_type`      ENUM('PLATFORM','FREIGHT','LOGISTICS') DEFAULT 'FREIGHT',
    `contact_name`     VARCHAR(64)         DEFAULT NULL,
    `contact_phone`    VARCHAR(20)         DEFAULT NULL,
    `contact_email`    VARCHAR(128)        DEFAULT NULL,
    `status`           ENUM('ACTIVE','SUSPENDED','CANCELLED') DEFAULT 'ACTIVE',
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`company_id`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='公司表-租户隔离';
```

- [ ] **Step 2: Add Platform admin company record**

```sql
-- 插入平台管理员公司（睿云平台）
INSERT INTO `COMPANY` (`company_id`, `company_name`, `company_type`, `status`)
VALUES ('PLATFORM', '睿云平台', 'PLATFORM', 'ACTIVE');
```

- [ ] **Step 3: Commit**

```bash
git add rga-docs/03_schema.sql
git commit -m "feat: add COMPANY table for tenant isolation"
```

---

### Task 2: Modify KNOWLEDGE Table for Layer Support

**Files:**
- Modify: `rga-docs/03_schema.sql:224-251`

- [ ] **Step 1: Drop existing KNOWLEDGE table and recreate with layer fields**

```sql
-- =====================================================
-- 9. 知识库表 (KNOWLEDGE) - 支持三层知识架构
-- =====================================================
DROP TABLE IF EXISTS `KNOWLEDGE`;

CREATE TABLE IF NOT EXISTS `KNOWLEDGE` (
    `kb_id`            VARCHAR(32)         NOT NULL,
    `layer`            ENUM('PLATFORM','COMPANY','ORDER','USER') NOT NULL DEFAULT 'COMPANY',
    `company_id`       VARCHAR(32)         DEFAULT NULL COMMENT '租户ID，PLATFORM层为NULL',
    `order_stage`      ENUM('PENDING','PROCESSING','COMPLETED','EXCEPTION') DEFAULT NULL COMMENT '订单阶段，仅ORDER层使用',
    `user_id`          VARCHAR(32)         DEFAULT NULL COMMENT '用户ID，仅USER层使用',

    `category`         VARCHAR(64)         NOT NULL COMMENT '分类名称',
    `subcategory`      VARCHAR(64)         DEFAULT NULL,
    `title`            VARCHAR(256)       NOT NULL,
    `content`          TEXT                NOT NULL,
    `summary`          VARCHAR(512)        DEFAULT NULL COMMENT '摘要（用于检索）',
    `tags`             JSON                DEFAULT NULL,
    `attachments`       JSON                DEFAULT NULL COMMENT '附件列表',

    `confidence`       DECIMAL(5,4)       DEFAULT 1.0000,
    `source`           VARCHAR(32)         DEFAULT 'INTERNAL' COMMENT '来源：INTERNAL/EXTERNAL',
    `source_url`       VARCHAR(512)        DEFAULT NULL COMMENT '原文链接',
    `author`           VARCHAR(64)         DEFAULT NULL,

    `status`           ENUM('DRAFT','PUBLISHED','ARCHIVED') DEFAULT 'DRAFT',
    `view_count`       INT                  DEFAULT 0,
    `useful_count`     INT                  DEFAULT 0,
    `version`          VARCHAR(16)        DEFAULT '1.0',

    `created_by`       VARCHAR(32)         DEFAULT NULL,
    `approved_by`      VARCHAR(32)         DEFAULT NULL,
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `published_at`     TIMESTAMP          DEFAULT NULL,

    PRIMARY KEY (`kb_id`),
    KEY `idx_layer` (`layer`),
    KEY `idx_company_id` (`company_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_category` (`category`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    FULLTEXT KEY `ft_search` (`title`, `content`, `summary`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库表-支持三层架构';
```

- [ ] **Step 2: Verify old INSERT statements still work (no changes needed for seed data)**

The existing seed INSERT uses `category` field which is still present. No changes needed for seed data.

- [ ] **Step 3: Commit**

```bash
git add rga-docs/03_schema.sql
git commit -m "feat: add layer/company_id/order_stage fields to KNOWLEDGE table"
```

---

### Task 3: Modify SKILLS Table for Retrieval Layers

**Files:**
- Modify: `rga-docs/03_schema.sql:198-219`

- [ ] **Step 1: Add retrieval_layers field to SKILLS table**

```sql
-- 修改 SKILLS 表，添加检索层配置
ALTER TABLE `SKILLS` ADD COLUMN `retrieval_layers` JSON DEFAULT NULL COMMENT '检索层配置，如["PLATFORM","COMPANY"]';
```

- [ ] **Step 2: Update skill INSERT statements with retrieval layers**

```sql
-- 更新技能配置的检索层
UPDATE `SKILLS` SET `retrieval_layers` = '["COMPANY","ORDER"]' WHERE `skill_id` = 'SKL001'; -- 运单追踪
UPDATE `SKILLS` SET `retrieval_layers` = '["PLATFORM","COMPANY"]' WHERE `skill_id` = 'SKL002'; -- 报价
UPDATE `SKILLS` SET `retrieval_layers` = '["COMPANY"]' WHERE `skill_id` = 'SKL003'; -- 库存查询
UPDATE `SKILLS` SET `retrieval_layers` = '["COMPANY","ORDER"]' WHERE `skill_id` = 'SKL004'; -- 创建订单
UPDATE `SKILLS` SET `retrieval_layers` = '["PLATFORM","COMPANY","USER"]' WHERE `skill_id` = 'SKL005'; -- 知识检索
UPDATE `SKILLS` SET `retrieval_layers` = '["COMPANY","USER"]' WHERE `skill_id` = 'SKL006'; -- 客户信息
```

- [ ] **Step 3: Commit**

```bash
git add rga-docs/03_schema.sql
git commit -m "feat: add retrieval_layers to SKILLS table"
```

---

### Task 4: Create USER_LAYER_CONTENT Table

**Files:**
- Create: `rga-docs/03_schema.sql`

- [ ] **Step 1: Add USER_LAYER_CONTENT table for personal user knowledge**

```sql
-- =====================================================
-- 12. 用户层内容表 (USER_LAYER_CONTENT)
-- =====================================================
CREATE TABLE IF NOT EXISTS `USER_LAYER_CONTENT` (
    `content_id`       VARCHAR(32)         NOT NULL,
    `user_id`          VARCHAR(32)         NOT NULL,
    `content_type`      ENUM('SCRIPT','TEMPLATE','NOTE','BOOKMARK') NOT NULL,
    `title`            VARCHAR(256)       NOT NULL,
    `content`          TEXT                NOT NULL,
    `is_shared`        BOOLEAN            DEFAULT FALSE COMMENT '是否授权给公司',
    `share_company_id`  VARCHAR(32)         DEFAULT NULL COMMENT '授权给的公司',
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`content_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_content_type` (`content_type`),
    KEY `idx_is_shared` (`is_shared`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户层内容表';
```

- [ ] **Step 2: Commit**

```bash
git add rga-docs/03_schema.sql
git commit -m "feat: add USER_LAYER_CONTENT table"
```

---

### Task 5: Create CATEGORY Table for Taxonomy Management

**Files:**
- Create: `rga-docs/03_schema.sql`

- [ ] **Step 1: Add CATEGORY table**

```sql
-- =====================================================
-- 13. 知识分类表 (CATEGORY)
-- =====================================================
CREATE TABLE IF NOT EXISTS `CATEGORY` (
    `category_id`       VARCHAR(32)         NOT NULL,
    `layer`            ENUM('PLATFORM','COMPANY','ORDER','USER') NOT NULL,
    `parent_id`        VARCHAR(32)         DEFAULT NULL,
    `category_name`     VARCHAR(64)         NOT NULL,
    `description`       VARCHAR(256)        DEFAULT NULL,
    `sort_order`       INT                  DEFAULT 0,
    `status`           ENUM('ACTIVE','DISABLED') DEFAULT 'ACTIVE',
    `created_by`       VARCHAR(32)         DEFAULT NULL,
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`category_id`),
    KEY `idx_layer` (`layer`),
    KEY `idx_parent_id` (`parent_id`),
    KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识分类表';
```

- [ ] **Step 2: Insert default platform layer categories**

```sql
-- 插入平台层默认分类
INSERT INTO `CATEGORY` (`category_id`, `layer`, `category_name`, `description`, `sort_order`) VALUES
('PLT001', 'PLATFORM', '快递公司', '市场主流快递公司信息', 1),
('PLT002', 'PLATFORM', '电商平台', '主流电商平台物流政策', 2),
('PLT003', 'PLATFORM', '海关政策', '各国家/地区进出口规定', 3),
('PLT004', 'PLATFORM', '物流方案', '物流方案百科', 4),
('PLT005', 'PLATFORM', '行业术语', '物流专业名词解释', 5),
('PLT006', 'PLATFORM', '竞品动态', '行业新闻、竞品分析', 6);

-- 插入公司层默认分类
INSERT INTO `CATEGORY` (`category_id`, `layer`, `category_name`, `description`, `sort_order`) VALUES
('CO001', 'COMPANY', '公司资料', '资质、协议、合作条款', 1),
('CO002', 'COMPANY', '产品信息', '航线、时效、价格表', 2),
('CO003', 'COMPANY', '客户信息', '客户档案、联系人', 3),
('CO004', 'COMPANY', 'SOP流程', '内部操作标准流程', 4),
('CO005', 'COMPANY', '报价规则', '折扣政策、账期规则', 5),
('CO006', 'COMPANY', '常见问题', '客户高频问题回复', 6);

-- 插入订单层默认分类
INSERT INTO `CATEGORY` (`category_id`, `layer`, `category_name`, `description`, `sort_order`) VALUES
('ORD001', 'ORDER', '待处理', '新下单未确认', 1),
('ORD002', 'ORDER', '执行中', '已确认处理中', 2),
('ORD003', 'ORDER', '已完成', '正常完结', 3),
('ORD004', 'ORDER', '异常', '问题件、退件等', 4);

-- 插入用户层默认分类
INSERT INTO `CATEGORY` (`category_id`, `layer`, `category_name`, `description`, `sort_order`) VALUES
('USR001', 'USER', '个人话术', '常用回复模板', 1),
('USR002', 'USER', '常用模板', '邮件/消息模板', 2),
('USR003', 'USER', '学习笔记', '个人学习记录', 3),
('USR004', 'USER', '收藏内容', '收藏的知识条目', 4);
```

- [ ] **Step 3: Commit**

```bash
git add rga-docs/03_schema.sql
git commit -m "feat: add CATEGORY table with default taxonomies"
```

---

### Task 6: Update USER Table with Company Association

**Files:**
- Modify: `rga-docs/03_schema.sql:17-37`

- [ ] **Step 1: Add company_id to USER table**

```sql
-- 修改 USER 表，添加公司关联
ALTER TABLE `USER` ADD COLUMN `company_id` VARCHAR(32) DEFAULT NULL COMMENT '所属公司ID';
ALTER TABLE `USER` ADD COLUMN `user_type` ENUM('PLATFORM_ADMIN','COMPANY_ADMIN','EMPLOYEE','CUSTOMER') DEFAULT 'EMPLOYEE' COMMENT '用户类型';
```

- [ ] **Step 2: Commit**

```bash
git add rga-docs/03_schema.sql
git commit -m "feat: add company_id and user_type to USER table"
```

---

## 2. Documentation Updates

### Task 7: Update 02_database_design.md

**Files:**
- Modify: `rga-docs/02_database_design.md`

- [ ] **Step 1: Update ER diagram and table list**

Update section 1 (ER图) and section 2 (数据表清单) to reflect new tables and fields.

- [ ] **Step 2: Add new table sections**

Add sections 3.11-3.13 for COMPANY, USER_LAYER_CONTENT, CATEGORY tables.

- [ ] **Step 3: Commit**

```bash
git add rga-docs/02_database_design.md
git commit -m "docs: update database design for three-tier architecture"
```

---

## 3. Implementation Summary

### Files Modified/Created

| File | Action |
|------|--------|
| `rga-docs/03_schema.sql` | Modified - Added layer fields, new tables |
| `rga-docs/02_database_design.md` | Modified - Updated ER diagram and table list |

### New Tables

| Table | Purpose |
|-------|---------|
| `COMPANY` | Tenant isolation for freight companies |
| `CATEGORY` | Taxonomy management for all layers |
| `USER_LAYER_CONTENT` | Personal user knowledge (scripts, templates, notes) |

### Modified Tables

| Table | Changes |
|-------|---------|
| `KNOWLEDGE` | Added `layer`, `company_id`, `order_stage`, `user_id` |
| `SKILLS` | Added `retrieval_layers` JSON field |
| `USER` | Added `company_id`, `user_type` |

---

## 4. Self-Review Checklist

- [ ] All new tables have PRIMARY KEY
- [ ] All foreign keys have appropriate constraints
- [ ] Indexes match the query patterns (layer, company_id, user_id)
- [ ] Default categories inserted for all four layers
- [ ] SKILL retrieval_layers updated for all 6 skills
- [ ] No "TBD" or placeholder content
- [ ] Commit history is atomic (one feature per commit)
