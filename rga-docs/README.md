# RGA 知识平台设计文档

> AI 中台综合知识平台完整技术设计文档

---

## 文档目录

| 序号 | 文件 | 说明 |
|------|------|------|
| 01 | [系统架构设计](./01_system_architecture.md) | 系统定位、模块划分、技术架构 |
| 02 | [数据库设计](./02_database_design.md) | ER图、表结构、字段说明 |
| 03 | [建表 SQL](./03_schema.sql) | MySQL 8.0 建表脚本 |
| 04 | [SKILL 技能体系](./04_skills_definition.md) | 技能定义、触发规则、响应模板 |
| 05 | [知识库体系](./05_knowledge_base_design.md) | 知识分类、录入规范、质量标准 |
| 06 | [实施路线图](./06_implementation_roadmap.md) | 阶段划分、里程碑、风险评估 |
| 07 | [知识分类体系](./07_knowledge_taxonomy.md) | 三层知识分类、分类管理API |
| 08 | [检索引擎设计](./08_retrieval_engine.md) | SKILL-知识层映射、检索流程 |

---

## 快速导航

### 核心模块
- [数据表清单](./02_database_design.md#数据表清单)
- [技能列表](./04_skills_definition.md#技能总览)
- [知识分类](./05_knowledge_base_design.md#知识分类体系)
- [三层知识体系](./07_knowledge_taxonomy.md)
- [检索引擎](./08_retrieval_engine.md)

### 关键设计
- [参数规则](./04_skills_definition.md#参数slot规则)
- [响应格式](./04_skills_definition.md#响应模板)
- [状态机](./04_skills_definition.md#状态机设计)
- [SKILL-知识层映射](./08_retrieval_engine.md#1-skill-与知识层映射)

---

## 版本信息

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1 | 2026-03-28 | 新增知识分类体系(07)、检索引擎设计(08)、三层知识架构 |
| v1.0 | 2026-03-28 | 初始版本 |

---

*本文档为开发实施蓝图，后续代码实现以此为准。*
