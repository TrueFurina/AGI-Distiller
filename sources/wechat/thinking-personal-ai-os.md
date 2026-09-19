# 提取记录：thinking.md（WorkBuddy 10技能 + 个人AI工程系统对话录）

## 元信息
- 来源：用户与 AI 的深度对话记录（含 WorkBuddy 10 技能清单、Vibe Coding 用好 Skill、项目级 Skill SOP、2050 程序员职业推演等 8 个主题）
- 位置：E:/Program/AGI-Distiller/thinking.md（3022 行）
- 蒸馏日期：2026-07-21
- 分类：AI 工程化 / Skill 体系 / 个人 AI 工程系统

## 核心痛点
1. Skill 装了一堆但 description 太烂，AI 永远不触发
2. 多工具玩家每个工具各养一套 Skill，版本漂移，AI"精神分裂"
3. 上下文一股脑塞给 AI，context rot（指令腐烂，AI 假装听话但忽略你）
4. Vibe Coding 飞快，代码量巨大，但对项目失去理解（AI 把"写代码"和"理解系统"解耦了）
5. 把 Skill 当"插件收藏夹"：全局装 30 个，项目里一个不写
6. 跨会话/跨项目上下文丢失，每次回来都要重新解释

## 核心解法

### 1. Prompt / Agent / Skill 分工
- Prompt：这次要干什么（入口）
- Agent：拆任务、读文件、跑命令（执行）
- Skill：这类事该怎么干（能力沉淀/SOP）
- 成熟状态：「人说目标 → Agent 编排 → Skill 控质量 → 人做决策」

### 2. Skill 三层结构
- 常驻层：project-context / coding-style / arch-rules（AI 启动就懂）
- 流程层：spec-to-plan → tdd → code-review → github（按阶段调用）
- 领域层：mcp-builder / 业务 Skill（按需触发）

### 3. 项目级四件套（每个项目必装）
1. project-context：技术栈版本、目录结构、统一返回、启动命令、禁区
2. coding-style：命名、分层、日志、异常、DTO/VO 规范
3. arch-rules：架构红线（Controller 不查库、事务边界、缓存一致性）
4. api-contract：URL 规范、出入参分离、兼容旧接口、DDL 变更规则

### 4. 全局 vs 项目分界
- 全局（~/.agents/skills/）：输出风格、spec-to-plan、debug-playbook、git-safe 等跨项目能力
- 项目（.agents/skills/）：本项目技术栈、业务红线、MQ 拓扑、脏知识
- 一句话：全局管"你是谁"，项目管"这项目是什么"
- 同名冲突时：项目级 > 全局级

### 5. 多工具唯一真相源
- 一份真相源 ~/.agents/skills/ + 每个工具软链（.claude/.cursor/.codex/.gemini）
- 只有 2 种例外装工具专属目录：工具独有功能、同名 Skill 分版本

### 6. Rules ≠ Skills
- Rule = 写这类文件时的硬约束（自动触发、强约束、更底层）
- Skill = 某类任务的执行 SOP（按任务触发）
- 红线类 → Rule；流程类 → Skill；项目独有坑 → 项目 AGENTS.md

### 7. 计划外脑（对抗多项目上下文丢失）
- plans/current.md（当前任务）+ decisions.md（决策记录）+ docs/system-map.md（系统地图）
- 换项目第一句："读 plans/current.md，总结当前进度，再等我下令"

### 8. 反依赖三关（大项目掌控）
- 第一关：写之前先画心智地图，能复述才动手
- 第二关：AI 写代码，你补 WHY/RISK/TEST 三行注释
- 第三关：改完手动走查关键路径，记一句理解确认
- 分层掌控：核心领域模型/关键业务流程/外部集成必须懂，工具类知道就行

### 9. 2050 职业推演 → 现在可落地的 Agent 分工
- 上下文工程师、数据治理 Agent、Multi-Agent 代码审计、Meta-Agent 编排、LLM 安全护栏、FinOps Agent、合规审计
- 三层体系：基础层（数据与安全）→ 执行层（研发流水线）→ 治理层（质量与伦理）

## 可执行规则
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