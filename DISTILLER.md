# 🧪 AGI Distiller — 知识蒸馏管道规范

> **Read → Distill → Precipitate → Evolve**
>
> 从高质量技术内容中提取知识，沉淀为 Agent 可执行的规则与 skill。

---

## 一、核心理念

知识蒸馏不是"总结文章"，而是**把文章中的隐性知识转化为 Agent 可执行的显性行为规范**。

```
文章中的知识：          "调试的时候应该先复现问题，不要直接改代码"
                        ↓ 蒸馏
Agent 可执行的规则：     调试5步流程：复现→定位→最小改动→测试→回归
                        ↓ 封装
跨平台 skill：           debug-flow/SKILL.md
```

---

## 二、蒸馏流程

### 步骤 1：阅读

每次读一篇文章，按固定格式提取关键信息：

```json
{
  "source": "https://laodad.com/tools/7500.html",
  "title": "AI编程学习路线怎么走？",
  "date": "2026-05-16",
  "category": "terminal-ai-efficiency",
  "pain_points": [
    "零基础用户不知道如何提问",
    "AI 编程容易把工具当成许愿机",
    "需求越模糊，结果越不可用"
  ],
  "solutions": [
    "把模糊想法拆成输入、处理、输出、验收",
    "先学会读代码结构，不是逐行死磕",
    "小步修改，每轮只做一件事"
  ],
  "actionable_rules": [
    "每次任务前先写需求，再让 AI 分析目录",
    "修改后必须跑测试或手动验证",
    "不要一次性改几十个文件"
  ],
  "traps": [
    "把需求写得越模糊，越容易得到看似完整但不可维护的代码"
  ],
  "keywords": ["AI编程", "学习路线", "调试", "验收"],
  "skill_candidates": ["task-briefer", "debug-flow"]
}
```

### 步骤 2：分类

根据提取的痛点，决定沉淀到哪个层级：

```
┌─ 层级 1: 行为规范（ATOMCODE.md） ─────────────────┐
│  条件：该规则改变 Agent 的通用行为方式              │
│  示例："每次任务结束必须输出验收清单"               │
│  位置：~/.atomcode/ATOMCODE.md                     │
└───────────────────────────────────────────────────┘

┌─ 层级 2: 持久化记忆（memory） ─────────────────────┐
│  条件：该知识需要跨会话记住，但不改变行为规范       │
│  示例："CLI 退出码虚假是常见陷阱，失败返回0需额外检查" │
│  位置：memory 工具                                  │
└───────────────────────────────────────────────────┘

┌─ 层级 3: 可复用 skill（skills/） ──────────────────┐
│  条件：同一个模式在工作中重复出现 3 次以上          │
│  示例："调试5步流程" → debug-flow skill             │
│  位置：skills/<name>/SKILL.md                       │
└───────────────────────────────────────────────────┘

┌─ 层级 4: 深度知识库（notes/） ─────────────────────┐
│  条件：文章有完整知识体系，值得保留完整分析         │
│  示例：19 篇 laodad.com 文章的体系化分析            │
│  位置：notes/ 目录                                  │
└───────────────────────────────────────────────────┘
```

### 步骤 3：转化

从提取的痛点中，按以下规则转化为 skill：

```
一个痛点被一篇文章提到     → 写 notes
同一痛点被 2 篇文章提到   → 写入 memory
同一痛点被 3 篇以上文章提到 → 写入 ATOMCODE.md
同一痛点在日常工作中重复 3 次以上 → 写成 skill
```

### 步骤 4：验证

每个 skill 创建后，验证：

```
✅ 它解决了文章中的痛点吗？
✅ 它能在 Claude Code 中运行吗？
✅ 它能在 Codex CLI 中运行吗？
✅ 它的 YAML frontmatter 完整吗？
✅ 它的触发词覆盖了用户会说的自然语言吗？
✅ 它的输出格式清晰可读吗？
```

### 步骤 5：记录

在 sources/ 目录中记录已蒸馏的文章：

```
sources/laodad/
├── index.json          # 已读文章索引
├── 7500-learning-path.json
├── 7489-cursor-rules.json
├── 7613-rule-layering.json
└── ...
```

---

## 三、提取模板

### 简化版（快速提取）

```
痛点：_______
解法：_______
可执行规则：_______
陷阱：_______
是否适合写成 skill：是/否
如果适合，skill 名称：_______
```

### 完整版（深度提取）

```json
{
  "source": "",
  "title": "",
  "date": "",
  "category": "terminal-ai-efficiency | ai-coding | cli-tools | agent-collaboration | general",
  "pain_points": [],
  "solutions": [],
  "actionable_rules": [],
  "traps": [],
  "keywords": [],
  "skill_candidates": [],
  "distillation_date": "",
  "distilled_by": "AtomCode (deepseek-v4-flash)"
}
```

---

## 四、Skill 命名规范

```
格式：<动词>-<名词>
示例：
  acceptance-checker  (验收检查)
  debug-flow          (调试流程)
  task-briefer        (任务说明)
  code-review-p0      (代码审查)
  cli-safety          (CLI 安全执行)
```

---

## 五、质量门禁

每个 skill 提交前必须通过：

- [ ] YAML frontmatter 完整（name, description, argument-hint, allowed-tools）
- [ ] 代码块成对，没有未闭合的 ```
- [ ] 触发词覆盖用户自然语言
- [ ] 输出格式清晰，有具体示例
- [ ] 至少解决一个明确的痛点
- [ ] 跨平台兼容（至少 Claude Code + Codex CLI）
- [ ] 中英文描述都有

---

## 六、持续迭代

```
遇到重复问题 → 提炼成规则
  → 写入 ATOMCODE.md
  → 如果规则频率高 → 固化为 skill
  → 如果 skill 三个月没用 → 删掉或合并
  → 如果犯错 → 补一条 memory
```

---

## 七、最终目标

> **"给我一篇好文章，我还你一个可执行的 skill。"**

这个蒸馏管道的最终形态是：

1. **自动发现** — 从 sitemap、RSS、公众号自动发现新文章
2. **自动提取** — 用 AI 自动提取痛点、解法、规则
3. **自动分类** — 判断沉淀到哪个层级
4. **自动生成** — 生成 skill 草稿供人工审核
5. **自动发布** — 合入 GitHub 仓库，更新 marketplace

一步一步来，先从手动蒸馏跑通闭环。