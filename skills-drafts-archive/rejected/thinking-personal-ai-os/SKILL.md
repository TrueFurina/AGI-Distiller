---
name: thinking-personal-ai-os
description: 蒸馏自《thinking-personal-ai-os》的可执行规则（草稿，需人工审核）；来源 sources\wechat\thinking-personal-ai-os.md
---

# thinking-personal-ai-os — 可执行规则

## 规则

1. Skill description 必须写触发条件，否则永远不会被调用
2. 重复两次以上的事，立刻升格成 Skill（好 Skill 是类别，不是实例）
3. AGENTS.md 保持"无聊且短"（100-300 行），是门禁不是培训手册
4. 全局 Skill 只装 6-8 个高频通用的，其余按项目装
5. 一份真相源 + 软链，不在多个工具目录维护副本
6. 任何"你第 2 次解释的东西"都写成 Rule 或 Skill
7. 高危路径（资金/权限/登录/DDL）必须写进 Skill 的人工审查点
8. 理解项目是第一类任务，不是副作用——plans/ 里加"系统理解任务"
9. 用 Golden Test Set 验证 AI 变强，不看感觉看数据
10. 关键路径设 Checkpoint，人签字才能上线

## 关联 skill
- 现有 4 个 skill 与本篇体系高度一致（acceptance-checker≈code-review、debug-flow≈debug-playbook、deploy-checker≈release-checklist、task-automator≈流程层）
- 候选新 skill：project-bootstrap（项目四件套初始化）、spec-to-plan（需求拆解）
- AGENTS.md/权限矩阵设计与本篇"三层分离"完全同构，方向验证正确

## 审核清单（定稿前删掉本节）

- [ ] 规则可执行可验证（非愿望清单）
- [ ] 与现有 skill/memory 无重复
- [ ] 触发词补全
