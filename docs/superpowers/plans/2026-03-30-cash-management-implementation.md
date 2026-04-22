# 出纳管理系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现出纳管理系统，支持多公司多账号、信用额度同步、资金流水管理、发票管理、自动对账、财务报表、纳税申报、固定资产折旧。

**Architecture:** 多公司多账号体系，账号独立本位币。资金流水分为有发票/无发票，自动对账，报表审批流程，固定资产折旧联动。

**Tech Stack:** Spring Boot + MyBatis-Plus + PostgreSQL + Redis（复用 suppliersystem 技术栈）

---

## 1. 数据库设计

### 1.1 核心表结构

| 表 | Action | 说明 |
|----|--------|------|
| `CASH_COMPANY` | Create | 公司主数据 |
| `CASH_ACCOUNT` | Create | 账号主数据（银行/现金账户） |
| `CASH_CREDIT_LIMIT` | Create | 信用额度台账 |
| `CASH_FUND_TRANSACTION` | Create | 资金流水 |
| `CASH_INVOICE` | Create | 发票主表 |
| `CASH_INVOICE_LINE` | Create | 发票明细 |
| `CASH_RECONCILIATION` | Create | 对账记录 |
| `CASH_JOURNAL_ENTRY` | Create | 凭证/日记账 |
| `CASH_FIXED_ASSET` | Create | 固定资产主数据 |
| `CASH_FIXED_ASSET_DEPRECIATION` | Create | 折旧记录 |
| `CASH_APPROVAL_TASK` | Create | 审批任务 |
| `CASH_APPROVAL_RECORD` | Create | 审批记录 |
| `CASH_FINANCIAL_STATEMENT` | Create | 财务报表 |
| `CASH_TAX_REPORT` | Create | 纳税申报表 |

### 1.2 文件

- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

---

## 2. 实施任务

### Task 1: 创建公司 (CASH_COMPANY) 和账号 (CASH_ACCOUNT) 表

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建公司表和账号表**

```sql
-- =====================================================
-- 1. 公司表 (CASH_COMPANY)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_company (
    company_id       VARCHAR(32)         NOT NULL,
    company_name     VARCHAR(128)       NOT NULL,
    tax_id           VARCHAR(32)         DEFAULT NULL COMMENT '纳税人识别号',
    legal_person     VARCHAR(64)         DEFAULT NULL COMMENT '法人代表',
    contact_phone    VARCHAR(20)         DEFAULT NULL,
    contact_email    VARCHAR(128)        DEFAULT NULL,
    address          VARCHAR(256)        DEFAULT NULL,
    status           VARCHAR(20)         DEFAULT 'ACTIVE',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (company_id),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公司主数据';

-- =====================================================
-- 2. 账号表 (CASH_ACCOUNT)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_account (
    account_id       VARCHAR(32)         NOT NULL,
    company_id      VARCHAR(32)         NOT NULL,
    account_name     VARCHAR(128)       NOT NULL COMMENT '账户名称',
    account_type     VARCHAR(20)         NOT NULL COMMENT 'BANK-银行账户 CASH-现金账户',
    bank_name        VARCHAR(128)        DEFAULT NULL COMMENT '开户银行',
    bank_account_no  VARCHAR(64)         DEFAULT NULL COMMENT '银行账号',
    currency         VARCHAR(10)         DEFAULT 'CNY' COMMENT '本位币',
    status           VARCHAR(20)         DEFAULT 'ACTIVE',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (account_id),
    KEY idx_company_id (company_id),
    KEY idx_account_type (account_type),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='账号主数据';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_COMPANY and CASH_ACCOUNT tables"
```

---

### Task 2: 创建信用额度表 (CASH_CREDIT_LIMIT)

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建信用额度表**

```sql
-- =====================================================
-- 3. 信用额度表 (CASH_CREDIT_LIMIT)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_credit_limit (
    credit_id        VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    credit_type      VARCHAR(20)         NOT NULL COMMENT 'RECEIVABLE-应收 PAYABLE-应付',
    counterparty_type VARCHAR(20)         NOT NULL COMMENT 'SUPPLIER-供应商 CUSTOMER-客户',
    counterparty_code VARCHAR(64)         NOT NULL COMMENT '供应商/客户代码',
    counterparty_name VARCHAR(128)       NOT NULL COMMENT '供应商/客户名称',
    contact_name     VARCHAR(64)         DEFAULT NULL COMMENT '联系人',
    contact_phone    VARCHAR(20)         DEFAULT NULL COMMENT '联系电话',
    credit_limit     DECIMAL(18,2)      NOT NULL DEFAULT 0 COMMENT '信用额度',
    used_amount      DECIMAL(18,2)      NOT NULL DEFAULT 0 COMMENT '已用额度',
    available_amount  DECIMAL(18,2)      NOT NULL DEFAULT 0 COMMENT '可用额度',
    currency         VARCHAR(10)         DEFAULT 'CNY',
    status           VARCHAR(20)         DEFAULT 'ACTIVE',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (credit_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_credit_type (credit_type),
    KEY idx_counterparty_code (counterparty_code),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='信用额度台账';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_CREDIT_LIMIT table"
```

---

### Task 3: 创建资金流水表 (CASH_FUND_TRANSACTION)

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建资金流水表**

```sql
-- =====================================================
-- 4. 资金流水表 (CASH_FUND_TRANSACTION)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_fund_transaction (
    transaction_id   VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    transaction_no   VARCHAR(64)         NOT NULL UNIQUE COMMENT '流水号',
    transaction_type VARCHAR(20)         NOT NULL COMMENT 'BANK_IN/BANK_OUT/CASH_IN/CASH_OUT',
    has_invoice      VARCHAR(10)         NOT NULL DEFAULT 'NO' COMMENT '是否有发票 YES/NO',
    amount           DECIMAL(18,2)      NOT NULL,
    currency         VARCHAR(10)         DEFAULT 'CNY',
    counterparty     VARCHAR(128)        DEFAULT NULL COMMENT '对方名称',
    invoice_no       VARCHAR(64)         DEFAULT NULL COMMENT '关联发票号',
    transaction_date DATE                NOT NULL,
    remarks          VARCHAR(512)        DEFAULT NULL,
    status           VARCHAR(20)         DEFAULT 'ACTIVE',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (transaction_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_transaction_no (transaction_no),
    KEY idx_transaction_type (transaction_type),
    KEY idx_has_invoice (has_invoice),
    KEY idx_transaction_date (transaction_date),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资金流水';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_FUND_TRANSACTION table"
```

---

### Task 4: 创建发票表 (CASH_INVOICE / CASH_INVOICE_LINE)

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建发票表**

```sql
-- =====================================================
-- 5. 发票主表 (CASH_INVOICE)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_invoice (
    invoice_id       VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    invoice_no       VARCHAR(64)         NOT NULL UNIQUE COMMENT '发票号',
    invoice_type     VARCHAR(20)         NOT NULL COMMENT 'SALES-销项 PURCHASE-进项',
    invoice_amount   DECIMAL(18,2)      NOT NULL COMMENT '发票金额',
    tax_amount      DECIMAL(18,2)      NOT NULL DEFAULT 0 COMMENT '税额',
    tax_rate        DECIMAL(5,4)       NOT NULL DEFAULT 0 COMMENT '税率',
    total_amount    DECIMAL(18,2)      NOT NULL COMMENT '价税合计',
    counterparty    VARCHAR(128)        NOT NULL COMMENT '对方名称',
    counterparty_tax_id VARCHAR(32)      DEFAULT NULL COMMENT '对方税号',
    invoice_date    DATE                NOT NULL,
    status          VARCHAR(20)         DEFAULT 'DRAFT' COMMENT 'DRAFT/PENDING/CONFIRMED/PARTIAL/FULL/CANCELLED',
    reconciled_amount DECIMAL(18,2)      DEFAULT 0 COMMENT '已核销金额',
    unreconciled_amount DECIMAL(18,2)   DEFAULT 0 COMMENT '未核销金额',
    remarks         VARCHAR(512)         DEFAULT NULL,
    insert_date     TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user     VARCHAR(50),
    update_date     TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user     VARCHAR(50),
    version         NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (invoice_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_invoice_no (invoice_no),
    KEY idx_invoice_type (invoice_type),
    KEY idx_status (status),
    KEY idx_invoice_date (invoice_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票主表';

-- =====================================================
-- 6. 发票明细表 (CASH_INVOICE_LINE)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_invoice_line (
    line_id          VARCHAR(32)         NOT NULL,
    invoice_id       VARCHAR(32)         NOT NULL,
    line_no          INT                NOT NULL COMMENT '行号',
    product_name     VARCHAR(256)        DEFAULT NULL COMMENT '商品名称',
    quantity         DECIMAL(18,4)      DEFAULT 1 COMMENT '数量',
    unit_price       DECIMAL(18,4)      DEFAULT 0 COMMENT '单价',
    amount           DECIMAL(18,2)      NOT NULL COMMENT '金额',
    tax_rate         DECIMAL(5,4)       DEFAULT 0 COMMENT '税率',
    tax_amount       DECIMAL(18,2)      DEFAULT 0 COMMENT '税额',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (line_id),
    KEY idx_invoice_id (invoice_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='发票明细';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_INVOICE and CASH_INVOICE_LINE tables"
```

---

### Task 5: 创建对账表 (CASH_RECONCILIATION)

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建对账表**

```sql
-- =====================================================
-- 7. 对账记录表 (CASH_RECONCILIATION)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_reconciliation (
    reconciliation_id VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    transaction_id   VARCHAR(32)         NOT NULL COMMENT '流水ID',
    invoice_id       VARCHAR(32)         NOT NULL COMMENT '发票ID',
    reconcile_amount DECIMAL(18,2)      NOT NULL COMMENT '核销金额',
    reconcile_date   DATE                NOT NULL,
    reconcile_type   VARCHAR(20)         DEFAULT 'AUTO' COMMENT 'AUTO-自动 MANUAL-人工',
    status           VARCHAR(20)         DEFAULT 'ACTIVE',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user     VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (reconciliation_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_transaction_id (transaction_id),
    KEY idx_invoice_id (invoice_id),
    KEY idx_reconcile_date (reconcile_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对账记录';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_RECONCILIATION table"
```

---

### Task 6: 创建凭证表 (CASH_JOURNAL_ENTRY)

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建凭证表**

```sql
-- =====================================================
-- 8. 凭证/日记账表 (CASH_JOURNAL_ENTRY)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_journal_entry (
    journal_id       VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    journal_no       VARCHAR(64)         NOT NULL UNIQUE COMMENT '凭证号',
    journal_type     VARCHAR(20)         NOT NULL COMMENT '类型',
    debit_account    VARCHAR(64)         NOT NULL COMMENT '借方科目',
    credit_account   VARCHAR(64)         NOT NULL COMMENT '贷方科目',
    amount           DECIMAL(18,2)      NOT NULL,
    currency         VARCHAR(10)         DEFAULT 'CNY',
    summary          VARCHAR(256)        DEFAULT NULL COMMENT '摘要',
    journal_date     DATE                NOT NULL,
    related_doc_type VARCHAR(20)         DEFAULT NULL COMMENT '关联单据类型',
    related_doc_id   VARCHAR(32)         DEFAULT NULL COMMENT '关联单据ID',
    status           VARCHAR(20)         DEFAULT 'ACTIVE',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (journal_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_journal_no (journal_no),
    KEY idx_journal_type (journal_type),
    KEY idx_journal_date (journal_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='凭证/日记账';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_JOURNAL_ENTRY table"
```

---

### Task 7: 创建固定资产表 (CASH_FIXED_ASSET / CASH_FIXED_ASSET_DEPRECIATION)

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建固定资产表**

```sql
-- =====================================================
-- 9. 固定资产主表 (CASH_FIXED_ASSET)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_fixed_asset (
    asset_id         VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    asset_no         VARCHAR(64)         NOT NULL UNIQUE COMMENT '资产编号',
    asset_name       VARCHAR(128)       NOT NULL COMMENT '资产名称',
    asset_category   VARCHAR(64)         DEFAULT NULL COMMENT '资产类别',
    purchase_date    DATE                NOT NULL COMMENT '购置日期',
    original_value   DECIMAL(18,2)      NOT NULL COMMENT '原值',
    net_value        DECIMAL(18,2)      NOT NULL DEFAULT 0 COMMENT '净值',
    useful_life_years INT               NOT NULL COMMENT '预计使用年限(月)',
    depreciation_method VARCHAR(20)      NOT NULL DEFAULT 'STRAIGHT_LINE' COMMENT '折旧方法',
    accumulated_depreciation DECIMAL(18,2) DEFAULT 0 COMMENT '累计折旧',
    salvage_value    DECIMAL(18,2)      DEFAULT 0 COMMENT '残值',
    status           VARCHAR(20)         DEFAULT 'IN_USE' COMMENT 'PURCHASED/IN_USE/DEPRECIATING/COMPLETED/DISPOSED',
    disposal_type    VARCHAR(20)         DEFAULT NULL COMMENT '处置方式',
    disposal_date    DATE                DEFAULT NULL COMMENT '处置日期',
    disposal_gain_loss DECIMAL(18,2)    DEFAULT 0 COMMENT '处置收益/损失',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (asset_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_asset_no (asset_no),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='固定资产主数据';

-- =====================================================
-- 10. 固定资产折旧记录表 (CASH_FIXED_ASSET_DEPRECIATION)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_fixed_asset_depreciation (
    depreciation_id   VARCHAR(32)         NOT NULL,
    asset_id         VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    period           VARCHAR(10)         NOT NULL COMMENT '折旧期间 YYYY-MM',
    depreciation_amount DECIMAL(18,2)    NOT NULL COMMENT '折旧金额',
    accumulated_depreciation DECIMAL(18,2) DEFAULT 0 COMMENT '累计折旧',
    net_value        DECIMAL(18,2)      NOT NULL COMMENT '折旧后净值',
    journal_id       VARCHAR(32)         DEFAULT NULL COMMENT '关联凭证ID',
    status           VARCHAR(20)         DEFAULT 'CALCULATED',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    PRIMARY KEY (depreciation_id),
    KEY idx_asset_id (asset_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_period (period),
    UNIQUE KEY uk_asset_period (asset_id, period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='固定资产折旧记录';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_FIXED_ASSET and CASH_FIXED_ASSET_DEPRECIATION tables"
```

---

### Task 8: 创建审批表 (CASH_APPROVAL_TASK / CASH_APPROVAL_RECORD)

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建审批表**

```sql
-- =====================================================
-- 11. 审批任务表 (CASH_APPROVAL_TASK)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_approval_task (
    task_id          VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    report_type      VARCHAR(20)         NOT NULL COMMENT 'FINANCIAL/TAX',
    report_id        VARCHAR(32)         NOT NULL COMMENT '报表ID',
    period           VARCHAR(10)         NOT NULL COMMENT '报表期间',
    status           VARCHAR(20)         DEFAULT 'PENDING' COMMENT 'PENDING/APPROVED/REJECTED',
    approver         VARCHAR(64)         DEFAULT NULL COMMENT '审批人',
    approve_time     TIMESTAMP          DEFAULT NULL,
    comment          VARCHAR(512)        DEFAULT NULL COMMENT '审批意见',
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (task_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_report_type (report_type),
    KEY idx_report_id (report_id),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批任务';

-- =====================================================
-- 12. 审批记录表 (CASH_APPROVAL_RECORD)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_approval_record (
    record_id        VARCHAR(32)         NOT NULL,
    task_id          VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    action           VARCHAR(20)         NOT NULL COMMENT 'APPROVE/REJECT',
    approver         VARCHAR(64)         NOT NULL,
    comment          VARCHAR(512)        DEFAULT NULL,
    action_time      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (record_id),
    KEY idx_task_id (task_id),
    KEY idx_company_id (company_id),
    KEY idx_approver (approver)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批记录';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_APPROVAL_TASK and CASH_APPROVAL_RECORD tables"
```

---

### Task 9: 创建报表表 (CASH_FINANCIAL_STATEMENT / CASH_TAX_REPORT)

**Files:**
- Create: `suppliersystem/src/main/resources/db/init_cash_system.sql`

- [ ] **Step 1: 创建报表表**

```sql
-- =====================================================
-- 13. 财务报表表 (CASH_FINANCIAL_STATEMENT)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_financial_statement (
    statement_id     VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    report_type      VARCHAR(20)         NOT NULL COMMENT 'BALANCE_SHEET/PROFIT_LOSS/CASH_FLOW',
    period_start     DATE                NOT NULL,
    period_end       DATE                NOT NULL,
    content          JSON                NOT NULL COMMENT '报表内容JSON',
    total_assets     DECIMAL(18,2)       DEFAULT NULL,
    total_liabilities DECIMAL(18,2)      DEFAULT NULL,
    equity           DECIMAL(18,2)       DEFAULT NULL,
    revenue          DECIMAL(18,2)       DEFAULT NULL,
    net_profit       DECIMAL(18,2)      DEFAULT NULL,
    cash_balance     DECIMAL(18,2)       DEFAULT NULL,
    status           VARCHAR(20)         DEFAULT 'DRAFT' COMMENT 'DRAFT/PENDING/APPROVED/SUBMITTED',
    generated_at     TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    submitter        VARCHAR(64)         DEFAULT NULL,
    submitted_at     TIMESTAMP          DEFAULT NULL,
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (statement_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_report_type (report_type),
    KEY idx_period_start (period_start),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务报表';

-- =====================================================
-- 14. 纳税申报表 (CASH_TAX_REPORT)
-- =====================================================
CREATE TABLE IF NOT EXISTS cash_tax_report (
    tax_report_id    VARCHAR(32)         NOT NULL,
    company_id       VARCHAR(32)         NOT NULL,
    account_id       VARCHAR(32)         NOT NULL,
    tax_type         VARCHAR(20)         NOT NULL COMMENT 'VAT/CIT/IIT/SCT/BT/VAT_SURCHARGE',
    period           VARCHAR(10)         NOT NULL COMMENT '申报期间 YYYY-MM',
    output_tax       DECIMAL(18,2)      DEFAULT 0 COMMENT '销项税额',
    input_tax        DECIMAL(18,2)      DEFAULT 0 COMMENT '进项税额',
    tax_payable      DECIMAL(18,2)      DEFAULT 0 COMMENT '应纳税额',
    tax_paid         DECIMAL(18,2)      DEFAULT 0 COMMENT '已缴税额',
    balance          DECIMAL(18,2)      DEFAULT 0 COMMENT '欠税/留抵',
    content          JSON                DEFAULT NULL COMMENT '申报内容JSON',
    status           VARCHAR(20)         DEFAULT 'DRAFT' COMMENT 'DRAFT/PENDING/APPROVED/SUBMITTED',
    deadline         DATE                DEFAULT NULL COMMENT '申报截止日',
    generated_at     TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    submitter        VARCHAR(64)         DEFAULT NULL,
    submitted_at     TIMESTAMP          DEFAULT NULL,
    insert_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    insert_user      VARCHAR(50),
    update_date      TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    update_user      VARCHAR(50),
    version          NUMERIC(18,0)      DEFAULT 0,
    PRIMARY KEY (tax_report_id),
    KEY idx_company_id (company_id),
    KEY idx_account_id (account_id),
    KEY idx_tax_type (tax_type),
    KEY idx_period (period),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='纳税申报表';
```

- [ ] **Step 2: Commit**

```bash
git add suppliersystem/src/main/resources/db/init_cash_system.sql
git commit -m "feat(cash): add CASH_FINANCIAL_STATEMENT and CASH_TAX_REPORT tables"
```

---

## 3. 代码实现

### Task 10: 创建 Entity 类

**Files:**
- Create: `suppliersystem/src/main/java/com/ruiyun/suppliersystem/entity/cash/*.java`

**Entities:**
- CashCompanyEntity
- CashAccountEntity
- CashCreditLimitEntity
- CashFundTransactionEntity
- CashInvoiceEntity
- CashInvoiceLineEntity
- CashReconciliationEntity
- CashJournalEntryEntity
- CashFixedAssetEntity
- CashFixedAssetDepreciationEntity
- CashApprovalTaskEntity
- CashApprovalRecordEntity
- CashFinancialStatementEntity
- CashTaxReportEntity

- [ ] **Step 1: 创建所有 Entity 类（参考现有 Entity 模式）**

---

### Task 11: 创建 Service 和 Controller

**Files:**
- Create: `suppliersystem/src/main/java/com/ruiyun/suppliersystem/service/cash/*.java`
- Create: `suppliersystem/src/main/java/com/ruiyun/suppliersystem/controller/cash/*.java`

**Services:**
- CashCompanyService / CashCompanyController
- CashAccountService / CashAccountController
- CashCreditLimitService / CashCreditLimitController
- CashTransactionService / CashTransactionController
- CashInvoiceService / CashInvoiceController
- CashReconciliationService / CashReconciliationController
- CashJournalEntryService / CashJournalEntryController
- CashFixedAssetService / CashFixedAssetController
- CashApprovalService / CashApprovalController
- CashReportService / CashReportController

- [ ] **Step 1: 创建 Company/Account 模块 (CASH001 前置)**
- [ ] **Step 2: 创建 CreditLimit 模块 (CASH001)**
- [ ] **Step 3: 创建 Transaction 模块 (CASH002)**
- [ ] **Step 4: 创建 Invoice 模块 (CASH003)**
- [ ] **Step 5: 创建 Reconciliation 模块 (CASH004 自动对账)**
- [ ] **Step 6: 创建 FixedAsset 模块 (CASH008)**
- [ ] **Step 7: 创建 Report 模块 (CASH005/CASH006)**
- [ ] **Step 8: 创建 Approval 模块 (CASH007)**
- [ ] **Step 9: 创建 OCR 模块 (CASH009 发票识别)**
- [ ] **Step 10: 创建额度关联模块 (CASH010 供应商-客户关联/共享额度池)**

---

## 4. 实施总结

### 文件创建

| 文件 | Action |
|------|--------|
| `init_cash_system.sql` | Created - 17 tables |
| Entity classes | Created - 17 entities |
| Service classes | Created - 12 services |
| Controller classes | Created - 12 controllers |

### 新增表

| 表 | 用途 |
|----|------|
| `cash_company` | 公司主数据 |
| `cash_account` | 账号主数据 |
| `cash_credit_limit` | 信用额度台账 |
| `cash_fund_transaction` | 资金流水 |
| `cash_invoice` | 发票主表 |
| `cash_invoice_line` | 发票明细 |
| `cash_reconciliation` | 对账记录 |
| `cash_journal_entry` | 凭证/日记账 |
| `cash_fixed_asset` | 固定资产主数据 |
| `cash_fixed_asset_depreciation` | 折旧记录 |
| `cash_approval_task` | 审批任务 |
| `cash_approval_record` | 审批记录 |
| `cash_financial_statement` | 财务报表 |
| `cash_tax_report` | 纳税申报表 |
| `cash_ocr_invoice_image` | OCR发票图片原始数据 |
| `cash_credit_relation` | 供应商-客户额度关联关系 |
| `cash_credit_pool` | 共享额度池 |

---

## 5. Self-Review Checklist

- [ ] 所有新表都有 PRIMARY KEY
- [ ] 所有表都有 audit 字段 (insert_date, update_date, version)
- [ ] 外键关系正确建立
- [ ] 索引覆盖常见查询字段
- [ ] 无 "TBD" 或占位符内容
- [ ] Commit 历史原子化（一个功能一次提交）
- [ ] 复用现有 suppliersystem 架构模式
