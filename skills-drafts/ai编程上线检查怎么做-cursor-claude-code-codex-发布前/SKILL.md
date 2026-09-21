---
name: ai编程上线检查怎么做-cursor-claude-code-codex-发布前
description: 蒸馏自《AI编程上线检查怎么做？Cursor、Claude Code、Codex 发布前清单》的可执行规则（草稿，需人工审核）；来源 sources\laodad\7725-deploy-checklist.md
---

# AI编程上线检查怎么做？Cursor、Claude Code、Codex 发布前清单 — 可执行规则

## 规则

1. 每次上线前按 8 项清单逐项检查：需求范围→diff审查→测试匹配→页面检查→移动端→回滚方案→发布备注→上线后观察
2. 写代码可以快，发布要慢半拍
3. AI 先筛风险，但最终要人工确认关键文件

## 陷阱

- "既然它已经改完并解释清楚了，那就可以上线"——这是最大的陷阱
- AI 交付最怕把不确定包装成确定

## 关联 skill
- acceptance-checker（验收清单）：互补关系，验收是任务完成时，上线检查是发布前
- 建议新建：deploy-checker（发布检查）

## 审核清单（定稿前删掉本节）

- [ ] 规则可执行可验证（非愿望清单）
- [ ] 与现有 skill/memory 无重复
- [ ] 触发词补全
