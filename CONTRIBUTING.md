# CONTRIBUTING.md — 贡献指南

> 中文版（本仓库的蒸馏笔记、规则、skill 均以中文撰写）。
> English-speaking contributors: the machine checks below are language-agnostic —
> run them, and read `DISTILLER.md` for the distillation process.

本项目的唯一卖点是**可溯源**：每个 skill 都能追到它来自哪篇文章、解决哪个痛点。
所以本指南的第一原则不是"格式规范"，而是：

> **宁可少一个 skill，也不要一个没有出处的 skill。**

---

## 一、你可以贡献什么

| 类型 | 说明 | 门槛 |
|---|---|---|
| 📝 新来源 | 推荐一篇值得蒸馏的高质量文章 | 低（开 issue 即可） |
| 🔧 新 skill | 基于蒸馏模板提交一个 skill | 高（见第三节 6 条硬要求） |
| 🌐 翻译 | 把 skill 翻译成其它语言 | 中（不许改语义） |
| 🐛 修 bug | 改进现有 skill | 低（但要说明改了什么、为什么） |

前三类中，📝 新来源、🔧 新 skill、🐛 修 bug 都有对应的 issue 模板
（`.github/ISSUE_TEMPLATE/`），提 PR 时会自动带出 `PULL_REQUEST_TEMPLATE.md`。
**模板里的必填项就是本指南的硬要求**，照着填即可。

> 模板里的 `labels` 只用仓库**已存在**的 label。
> GitHub 规则：模板引用了不存在的 label 时不会报错，而是**静默不添加**——
> 这类静默失效由机验 D19 盯着。

---

## 二、提交 skill 的流程

```
1. 读文章 → 按 DISTILLER.md「简化版/完整版」模板提取痛点与解法
2. 判断层级（见 DISTILLER.md 步骤 2）：
   同一痛点在工作里重复 3 次以上 → 才值得写成 skill
3. 草稿放 skills-drafts/<name>/SKILL.md
4. 跑本地自检（第四节），全绿
5. 移入 skills/<name>/SKILL.md，并在 sources/ 记录来源
6. 跑一次全量机验，提 PR
```

被拒绝的草稿不会删除，而是移入 `skills-drafts-archive/rejected/` 并附评审意见
（见 `skills-drafts-archive/rejected/REVIEW-2026-09-23.md`）——**拒绝也是资产**。

---

## 三、6 条硬要求（不满足会被 CI 拦下）

### 1. frontmatter 四个字段必须齐全

```yaml
---
name: debug-flow
description: 一句话说清它干什么 + 触发词：调试、debug、修Bug...
argument-hint: ["帮我修这个Bug", "这个报错怎么回事"]
allowed-tools: bash, read_file, grep, glob
---
```

`description` 里**必须带触发词**（用户会说的自然语言），否则 skill 不会被调用。

### 2. 规则句必须带溯源标记

经验规则不许"裸奔"——防止单次踩坑被写成铁律。含"必须/禁止/不许/绝不/一定要"的
一级 bullet 必须带以下标记之一：

| 标记 | 含义 |
|---|---|
| `[R<N>]` | 规则源自蒸馏第 N 轮（见 `sources/` 笔记） |
| `[实测]` | 本仓库/本机双向实测过 |
| `[设计]` | 结构性设计决策，非经验归纳 |
| `[复现:2+]` | 至少 2 个独立来源复现 |

机验：`python tools/check_skill_tags.py`（代码块与 frontmatter 内不查）。

### 3. 命名规范

格式 `<动词>-<名词>`，全小写加连字符：`acceptance-checker`、`debug-flow`、`cli-safety`。

### 4. 中英文描述都要有

skill 正文可用中文，但 `description` 要让不读中文的 Agent 也能判断该不该触发。

### 5. 至少解决一个明确痛点

PR 描述里要写：解决什么痛点、来自哪篇文章/哪次实战、不写会怎样。

### 6. 不许凑数

`README` 里的 skill 数是**机验从 `skills/` 目录数出来的**，手写改不动。
但"数量增长"从来不是目标——凑数的 skill 会稀释「可溯源」这个唯一卖点。

---

## 四、本地自检（提 PR 前必须全绿）

```bash
# 1) 文档一致性 —— 21 条判据，含变异自验
python scripts/check_doc_consistency.py
python scripts/check_doc_consistency.py --self-test

# 2) skill 溯源标记（无裸规则）
python tools/check_skill_tags.py
python tools/check_skill_tags.py --self-test

# 3) 计数同步 —— 数字必须等于工作区事实（改完 skill/笔记后先 --fix 再复核）
python tools/sync_counts.py --self-test
python tools/sync_counts.py

# 4) 判分器自检
python golden/graders.py --self-test
```

四条命令都退出 0 才提 PR。

**数字不要手敲。** 加了一个 skill / 一篇笔记后，被机验强制的计数散落在
README ×2 / HEARTBEAT / NEXT / CONTRIBUTING 里（实测每轮 16+ 处）。
`python tools/sync_counts.py --fix` 从 `skills/` 与 `sources/` 的实际内容改回去，
省掉逐个手改——**人力一定会漏**（本项目就漏过一次 HEARTBEAT 那行，靠门禁回头抓出来）。
它只改计数，不碰历史/实测记录；skill 表的摘要得人来写。

依赖实情（别信"本机跑通"）：

| 命令 | 第三方依赖 |
|---|---|
| `check_doc_consistency.py` | 无（纯标准库） |
| `check_skill_tags.py` | 无（纯标准库） |
| `sync_counts.py` | 无（纯标准库） |
| `workbuddy_skills.py` | 无（纯标准库）—— 但只在**装了 WorkBuddy 的机器**上有意义，**不是 PR 门禁**；它的 `--self-test` 用临时 fixture，所以能进 CI |
| `graders.py` | **需要 PyYAML** —— `pip install pyyaml` |

`graders.py` 那一条要特别小心：**本机装了 PyYAML 不代表 CI 有**。
CI 已在 workflow 里显式 `pip install pyyaml`；如果你新加了依赖，
必须同步改 workflow，并用干净环境验一次。

提交时本地还有 4 道 pre-commit 门禁：密钥扫描 / 诚实口径 / 口径数字 / 结构守卫。

---

## 五、CI 会跑什么

`.github/workflows/golden-regression.yml` 共 5 个 job：

| job | 作用 |
|---|---|
| `doc-consistency` | 文档与实际是否一致（21 条判据 + 计数同步机验：`tools/sync_counts.py` + CI 触发范围覆盖：D20） |
| `skill-tags` | skill 有无裸规则 + frontmatter 结构（`name` == 目录名、`allowed-tools` 逗号分隔） |
| `workbuddy-sync` | WorkBuddy 通道同步器的变异自验（`tools/workbuddy_skills.py --self-test`，临时 fixture，不碰真实目录） |
| `graders-smoke` | 判分器冒烟 |
| `mock-regression` | 判分逻辑回归 |

> `allowed-tools` 的分隔符**别照着单一规范改**：agentskills.io 的开放标准写空格，
> 而 Claude Code（本仓唯一实测过的宿主）的 schema 写 `Comma-separated string or YAML list`。
> **两份规范是冲突的**，本仓按已实测宿主用逗号，证据见 `sources/anthropic/skill-authoring-standard.md` §八。
> 门禁会拦住反向改动。

> 注意：**本机绿 ≠ CI 绿**。本机环境可能自带依赖而 CI 是裸的；
> 反过来，workflow 里若调用了不存在的脚本或参数，也会一直是红的。
> 加新检查时，把 workflow 里的命令**原样在本地跑一遍**。

> **触发范围也由机器保证**：workflow 的 `paths` 由判据 **D20** 强制 ——
> 凡被机验读到的文件，都必须落在触发范围内。它走「跑一遍全部判据、记录实际读了哪些文件」
> 的**执行取证**路线，不靠人维护清单。所以：把文件搬到新目录、或新增一条读新文件的检查之后，
> **忘了同步 `paths` 会直接让 CI 红**，不用靠记忆兜。
> （D20 本身就是一次教训的产物：把 `plugin.json` 移进 `.claude-plugin/` 时脚本路径跟着改了，
> 而 `paths` 里那条根级 `plugin.json` 再也没匹配到它 —— 门在，但不为这个改动而开。）

---

## 六、诚实口径（本仓库的红线）

- 没实测过的东西，不许标 ✅。要标就写清实测口径（跑了哪条命令、什么版本、看到什么输出）。
- 没达成的目标，不许打勾。愿景和成绩分两列写。
- 数字不许手写——README / HEARTBEAT 里的数量都是从工作区数出来的，由机验盯着。

这不是洁癖：**一个号称"什么平台都支持"却一个都没跑过的仓库，比只支持一个但真跑过的仓库更没用。**
