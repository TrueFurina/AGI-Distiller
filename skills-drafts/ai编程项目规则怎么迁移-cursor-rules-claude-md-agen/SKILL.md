---
name: ai编程项目规则怎么迁移-cursor-rules-claude-md-agen
description: 蒸馏自《AI编程项目规则怎么迁移？Cursor Rules、CLAUDE.md、AGENTS.md 同步清单》的可执行规则（草稿，需人工审核）；来源 sources\laodad\7766-rule-migration.md
---

# AI编程项目规则怎么迁移？Cursor Rules、CLAUDE.md、AGENTS.md 同步清单 — 可执行规则

## 规则

1. 规则分四类：项目事实、行为约束、协作偏好、交付标准
2. 通用层+工具适配层两层分离，不复制
3. CLAUDE.md 逐条标记有效期，过期内容直接删
4. 建立规则对照表，测试命令变了知道改哪些地方
5. 迁移后用小任务验证三件事：是否读到规则、是否按范围修改、是否按要求汇报

## 关联 skill
- deploy-checker（迁移验证可用其框架）

## 审核清单（定稿前删掉本节）

- [ ] 规则可执行可验证（非愿望清单）
- [ ] 与现有 skill/memory 无重复
- [ ] 触发词补全
