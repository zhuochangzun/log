-- =====================================================
-- RGA 知识平台 - MySQL 8.0 建表脚本
-- 版本: v1.0
-- 日期: 2026-03-28
-- =====================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS rga_platform
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE rga_platform;

-- =====================================================
-- 1. 用户表 (USER)
-- =====================================================
CREATE TABLE IF NOT EXISTS `USER` (
    `user_id`           VARCHAR(32)         NOT NULL,
    `username`          VARCHAR(64)        NOT NULL,
    `password_hash`     VARCHAR(256)       NOT NULL,
    `real_name`         VARCHAR(64)        NOT NULL,
    `role`              ENUM('ADMIN','SALES','CS','WAREHOUSE','FINANCE','RD') NOT NULL,
    `department`        VARCHAR(64)        DEFAULT NULL,
    `email`             VARCHAR(128)       DEFAULT NULL,
    `phone`             VARCHAR(20)        DEFAULT NULL,
    `status`            ENUM('ACTIVE','INACTIVE','LOCKED') DEFAULT 'ACTIVE',
    `last_login_time`   TIMESTAMP          DEFAULT NULL,
    `last_login_ip`     VARCHAR(64)        DEFAULT NULL,
    `created_at`        TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`        TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email` (`email`),
    KEY `idx_role` (`role`),
    KEY `idx_status` (`status`),
    KEY `idx_department` (`department`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

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

-- =====================================================
-- 2. 客户表 (CUSTOMER)
-- =====================================================
CREATE TABLE IF NOT EXISTS `CUSTOMER` (
    `customer_id`       VARCHAR(32)         NOT NULL,
    `customer_name`     VARCHAR(128)       NOT NULL,
    `contact_name`      VARCHAR(64)         DEFAULT NULL,
    `contact_phone`     VARCHAR(20)         DEFAULT NULL COMMENT '脱敏存储',
    `contact_email`     VARCHAR(128)        DEFAULT NULL,
    `tier`              ENUM('VIP','NORMAL','TRIAL') DEFAULT 'NORMAL',
    `account_manager`   VARCHAR(64)         DEFAULT NULL,
    `credit_limit`      DECIMAL(12,2)      DEFAULT 0,
    `status`            ENUM('ACTIVE','SUSPENDED','CANCELLED') DEFAULT 'ACTIVE',
    `created_at`        TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`        TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`customer_id`),
    KEY `idx_tier` (`tier`),
    KEY `idx_status` (`status`),
    KEY `idx_account_manager` (`account_manager`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户表';

-- =====================================================
-- 3. 仓库表 (WAREHOUSE)
-- =====================================================
CREATE TABLE IF NOT EXISTS `WAREHOUSE` (
    `warehouse_id`      VARCHAR(32)         NOT NULL,
    `warehouse_code`   VARCHAR(16)         NOT NULL,
    `warehouse_name`   VARCHAR(128)       NOT NULL,
    `warehouse_type`    ENUM('CENTRAL','REGIONAL','FRONT') DEFAULT NULL,
    `location`         VARCHAR(256)        DEFAULT NULL,
    `country`          VARCHAR(32)         DEFAULT NULL,
    `city`             VARCHAR(64)         DEFAULT NULL,
    `capacity`         INT                  DEFAULT NULL COMMENT '容量（立方米）',
    `current_stock`    INT                  DEFAULT 0,
    `manager_name`     VARCHAR(64)         DEFAULT NULL,
    `manager_phone`    VARCHAR(20)         DEFAULT NULL,
    `status`           ENUM('OPERATIONAL','MAINTENANCE','CLOSED') DEFAULT 'OPERATIONAL',
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`warehouse_id`),
    UNIQUE KEY `uk_warehouse_code` (`warehouse_code`),
    KEY `idx_country` (`country`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仓库表';

-- =====================================================
-- 4. 订单表 (ORDER)
-- =====================================================
CREATE TABLE IF NOT EXISTS `ORDER` (
    `order_id`         VARCHAR(32)         NOT NULL,
    `customer_id`      VARCHAR(32)         DEFAULT NULL,
    `order_no`         VARCHAR(64)         NOT NULL,
    `status`           ENUM('PENDING','CONFIRMED','PROCESSING','SHIPPED','COMPLETED','CANCELLED') DEFAULT 'PENDING',
    `order_type`       ENUM('B2B','B2C','C2C') DEFAULT NULL,
    `items`            JSON                NOT NULL COMMENT '订单明细',
    `total_amount`     DECIMAL(12,2)      DEFAULT NULL,
    `currency`         VARCHAR(8)          DEFAULT 'CNY',
    `receiver_name`    VARCHAR(128)        DEFAULT NULL,
    `receiver_phone`   VARCHAR(20)         DEFAULT NULL,
    `receiver_address` TEXT                DEFAULT NULL,
    `receiver_country` VARCHAR(32)         DEFAULT NULL,
    `remarks`          TEXT                DEFAULT NULL,
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`order_id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_customer_id` (`customer_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_order_customer` FOREIGN KEY (`customer_id`) REFERENCES `CUSTOMER` (`customer_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

-- =====================================================
-- 5. 运单表 (WAYBILL)
-- =====================================================
CREATE TABLE IF NOT EXISTS `WAYBILL` (
    `waybill_no`           VARCHAR(32)         NOT NULL,
    `customer_id`          VARCHAR(32)         DEFAULT NULL,
    `order_id`             VARCHAR(32)         DEFAULT NULL,
    `warehouse_id`         VARCHAR(32)         DEFAULT NULL,
    `status`               ENUM('CREATED','PICKED','IN_TRANSIT','OUT_FOR_DELIVERY','DELIVERED','EXCEPTION','RETURNED') DEFAULT 'CREATED',
    `origin_country`       VARCHAR(32)         DEFAULT NULL,
    `dest_country`         VARCHAR(32)         DEFAULT NULL,
    `current_location`     VARCHAR(256)        DEFAULT NULL,
    `current_status_desc`  VARCHAR(256)        DEFAULT NULL,
    `eta`                  TIMESTAMP          DEFAULT NULL,
    `actual_delivery_time` TIMESTAMP          DEFAULT NULL,
    `weight`               DECIMAL(10,3)      DEFAULT NULL COMMENT '重量(KG)',
    `length`               DECIMAL(10,2)      DEFAULT NULL COMMENT '长(CM)',
    `width`                DECIMAL(10,2)      DEFAULT NULL COMMENT '宽(CM)',
    `height`               DECIMAL(10,2)      DEFAULT NULL COMMENT '高(CM)',
    `shipping_fee`         DECIMAL(10,2)      DEFAULT NULL,
    `created_at`           TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`           TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`waybill_no`),
    KEY `idx_customer_id` (`customer_id`),
    KEY `idx_order_id` (`order_id`),
    KEY `idx_warehouse_id` (`warehouse_id`),
    KEY `idx_status` (`status`),
    KEY `idx_dest_country` (`dest_country`),
    CONSTRAINT `fk_waybill_customer` FOREIGN KEY (`customer_id`) REFERENCES `CUSTOMER` (`customer_id`) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT `fk_waybill_order` FOREIGN KEY (`order_id`) REFERENCES `ORDER` (`order_id`) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT `fk_waybill_warehouse` FOREIGN KEY (`warehouse_id`) REFERENCES `WAREHOUSE` (`warehouse_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='运单表';

-- =====================================================
-- 6. 库存表 (INVENTORY)
-- =====================================================
CREATE TABLE IF NOT EXISTS `INVENTORY` (
    `inventory_id`     VARCHAR(32)         NOT NULL,
    `warehouse_id`     VARCHAR(32)         NOT NULL,
    `sku`              VARCHAR(64)         NOT NULL,
    `sku_name`         VARCHAR(256)        DEFAULT NULL,
    `quantity`         INT                  DEFAULT 0,
    `reserved`         INT                  DEFAULT 0,
    `available`        INT                  GENERATED ALWAYS AS (quantity - reserved) STORED COMMENT '可用数量',
    `unit`             VARCHAR(16)         DEFAULT 'PCS',
    `shelf_location`   VARCHAR(64)         DEFAULT NULL,
    `last_check_time`  TIMESTAMP          DEFAULT NULL,
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`inventory_id`),
    UNIQUE KEY `uk_warehouse_sku` (`warehouse_id`, `sku`),
    KEY `idx_warehouse_id` (`warehouse_id`),
    KEY `idx_sku` (`sku`),
    CONSTRAINT `fk_inventory_warehouse` FOREIGN KEY (`warehouse_id`) REFERENCES `WAREHOUSE` (`warehouse_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库存表';

-- =====================================================
-- 7. 报价规则表 (PRICING)
-- =====================================================
CREATE TABLE IF NOT EXISTS `PRICING` (
    `pricing_id`       VARCHAR(32)         NOT NULL,
    `pricing_name`     VARCHAR(128)        DEFAULT NULL,
    `country`          VARCHAR(64)         NOT NULL,
    `country_code`     VARCHAR(8)          DEFAULT NULL,
    `service_type`     ENUM('EXPRESS','STANDARD','ECONOMY') DEFAULT 'EXPRESS',
    `min_weight`       DECIMAL(10,2)      DEFAULT 0 COMMENT '最小重量(KG)',
    `max_weight`       DECIMAL(10,2)      DEFAULT NULL COMMENT '最大重量(KG)',
    `unit_price`       DECIMAL(10,4)      NOT NULL COMMENT '单价（元/千克）',
    `base_fee`         DECIMAL(10,2)      DEFAULT 0 COMMENT '基础费用',
    `currency`         VARCHAR(8)          DEFAULT 'CNY',
    `surcharge`       JSON                DEFAULT NULL COMMENT '附加费明细',
    `discount`         JSON                DEFAULT NULL COMMENT '折扣规则',
    `effective_date`   DATE                NOT NULL,
    `expiry_date`      DATE                DEFAULT NULL,
    `status`           ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`pricing_id`),
    KEY `idx_country` (`country`),
    KEY `idx_service_type` (`service_type`),
    KEY `idx_effective` (`effective_date`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报价规则表';

-- =====================================================
-- 8. 技能配置表 (SKILLS)
-- =====================================================
CREATE TABLE IF NOT EXISTS `SKILLS` (
    `skill_id`             VARCHAR(32)         NOT NULL,
    `skill_name`           VARCHAR(64)        NOT NULL,
    `skill_desc`           VARCHAR(256)        DEFAULT NULL,
    `keywords`             JSON                NOT NULL COMMENT '触发关键词',
    `exclude_keywords`     JSON                DEFAULT NULL COMMENT '排除关键词',
    `conditions`           JSON                DEFAULT NULL COMMENT '执行条件',
    `required_params`      JSON                DEFAULT NULL COMMENT '必填参数',
    `optional_params`      JSON                DEFAULT NULL COMMENT '可选参数',
    `decision_template`    TEXT                DEFAULT NULL COMMENT '决策模板',
    `response_template`    TEXT                DEFAULT NULL COMMENT '响应模板',
    `error_template`       TEXT                DEFAULT NULL COMMENT '错误模板',
    `priority`             INT                  DEFAULT 100 COMMENT '优先级（越小越高）',
    `enabled`               BOOLEAN            DEFAULT TRUE,
    `version`               VARCHAR(16)        DEFAULT '1.0',
    `created_at`           TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    `updated_at`           TIMESTAMP          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`skill_id`),
    UNIQUE KEY `uk_skill_name` (`skill_name`),
    KEY `idx_enabled` (`enabled`),
    KEY `idx_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技能配置表';

-- =====================================================
-- 9. 知识库表 (KNOWLEDGE) - 支持三层知识架构
-- =====================================================
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

-- =====================================================
-- 10. 操作日志表 (AUDIT_LOG)
-- =====================================================
CREATE TABLE IF NOT EXISTS `AUDIT_LOG` (
    `log_id`           VARCHAR(32)         NOT NULL,
    `user_id`          VARCHAR(32)         DEFAULT NULL,
    `user_name`        VARCHAR(64)         DEFAULT NULL,
    `user_role`        VARCHAR(32)         DEFAULT NULL,
    `action`           VARCHAR(64)         NOT NULL,
    `action_type`      ENUM('QUERY','CREATE','UPDATE','DELETE','EXPORT','LOGIN') DEFAULT NULL,
    `task_type`        VARCHAR(32)         DEFAULT NULL,
    `module`           VARCHAR(32)         DEFAULT NULL,
    `input_params`     JSON                DEFAULT NULL COMMENT '输入参数',
    `output_result`    TEXT                DEFAULT NULL COMMENT '输出结果',
    `status`           ENUM('SUCCESS','FAIL','PARTIAL') DEFAULT 'SUCCESS',
    `error_message`    TEXT                DEFAULT NULL,
    `ip_address`       VARCHAR(64)         DEFAULT NULL,
    `user_agent`       VARCHAR(256)        DEFAULT NULL,
    `execution_time`   INT                  DEFAULT NULL COMMENT '执行时长(ms)',
    `created_at`       TIMESTAMP          DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`log_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_action` (`action`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_module` (`module`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- =====================================================
-- 初始化默认管理员账户
-- =====================================================
INSERT INTO `USER` (`user_id`, `username`, `password_hash`, `real_name`, `role`, `department`, `email`, `status`)
VALUES
    ('USR001', 'admin', '$2b$10$...', '系统管理员', 'ADMIN', 'IT', 'admin@company.com', 'ACTIVE'),
    ('USR002', 'sales001', '$2b$10$...', '销售员', 'SALES', '销售部', 'sales@company.com', 'ACTIVE');

-- 插入平台管理员公司（睿云平台）
INSERT INTO `COMPANY` (`company_id`, `company_name`, `company_type`, `status`)
VALUES ('PLATFORM', '睿云平台', 'PLATFORM', 'ACTIVE');

-- =====================================================
-- 初始化示例技能配置
-- =====================================================
INSERT INTO `SKILLS` (`skill_id`, `skill_name`, `skill_desc`, `keywords`, `required_params`, `priority`, `enabled`)
VALUES
    ('SKL001', 'track_waybill', '运单追踪', '["查单", "追踪", "运单", "物流", "到哪了"]', '["waybill_no"]', 10, TRUE),
    ('SKL002', 'quote_price', '运费报价', '["报价", "价格", "多少钱", "费用"]', '["weight", "country"]', 20, TRUE),
    ('SKL003', 'query_inventory', '库存查询', '["库存", "有货", "多少件"]', '["warehouse_id", "sku"]', 30, TRUE),
    ('SKL004', 'create_order', '创建订单', '["下单", "创建订单", "新订单"]', '["customer_id", "items"]', 40, TRUE),
    ('SKL005', 'search_knowledge', '知识检索', '["怎么操作", "SOP", "流程", "政策"]', '["keywords"]', 50, TRUE),
    ('SKL006', 'customer_info', '客户信息', '["客户信息", "账号", "联系人"]', '["customer_id"]', 60, TRUE);

-- =====================================================
-- 完成
-- =====================================================
