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

草稿产出后有两种结局，落到不同目录（**目录名必须等于结局**，
历史上 `rejected/` 里混放过 2 个转正原稿，靠肉眼才辨认出来）：

| 结局 | 目录 | 含义 |
|---|---|---|
| 转正为正式 skill | `skills-drafts-archive/graduated/` | 评审通过，已重写为 `skills/<name>/` |
| 淘汰 | `skills-drafts-archive/rejected/` | 与现有 skill 重复或无增量，**原稿保留** |

无论哪种结局，都必须同时在 `skills-drafts/index.json` 的 `graduated` 里登记
`draft`（原稿真实路径）+ `outcome`（转正的 skill 路径，或 `(已淘汰，无承接物)`）——
判据 D23 会核验每一条路径真实存在。**没登记的产物无法区分「已毕业」与「被误删」。**

写新 source 笔记时注意：蒸馏管道只认 `## 可执行规则` 这一精确标题，
不满足的素材会被**跳过**。要么把笔记写成五段结构，要么在 index.json 的
`manual-channel` 里逐份登记（写明它为什么走手工通道）——判据 D22 双向锁死：
漏登记会红，登记了不存在的也会红。别跳过这一步指望管道悄悄处理。

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
# 1) 文档一致性 —— 26 条判据，含变异自验
python scripts/check_doc_consistency.py
python scripts/check_doc_consistency.py --self-test

# 2) skill 溯源标记（无裸规则）
python tools/check_skill_tags.py
python tools/check_skill_tags.py --self-test

# 3) 计数同步 —— 数字必须等于工作区事实（改完 skill/笔记后先 --fix 再复核）
python tools/sync_counts.py --self-test

# 4) 字段取证器自验（本机无客户端 bundle 时加 --allow-missing）
python tools/wb_frontmatter_probe.py --self-test

# 5) 微信队列 —— 每篇抓到的文章必须有下落（入索引 / 草稿裁决 / status: AD）
python tools/wechat_queue.py --self-test
python tools/wechat_queue.py --check

# 6) 判分器自检（需 PyYAML）
python golden/graders.py --self-test
```

六条都退出 0 才提 PR（含 `--self-test` 子步骤）。

> `wechat_queue.py --check` 在没有蒸馏索引的机器上会显示"入索引情况未核验"并照样退出 0 ——
> 那是**如实降级**，不是假绿：查不到就说查不到，不许当成"都没入索引"。

> **本地全绿 ≠ CI 绿**：别人往同一仓库推的东西，是你本地没有的事实源。
> 提 PR 前额外跑一次 `gh run list --limit 3`，看主干最近几次 run 是不是**真的成功** ——
> 门禁能把红 CI 修绿，但它不会自己发现 CI 红。

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
| `wb_frontmatter_probe.py` | 无（纯标准库）—— 只在**本机有 WorkBuddy 客户端 bundle** 时才能取证；无 bundle 时装作不知道（打印说明），不猜答案 |
| `graders.py` | **需要 PyYAML** —— `pip install pyyaml` |

`graders.py` 那一条要特别小心：**本机装了 PyYAML 不代表 CI 有**。
CI 已在 workflow 里显式 `pip install pyyaml`；如果你新加了依赖，
必须同步改 workflow，并用干净环境验一次。

提交时本地还有 4 道 pre-commit 门禁：密钥扫描 / 诚实口径 / 口径数字 / 结构守卫。

---

## 五、CI 会跑什么

`.github/workflows/golden-regression.yml` 共 7 个 job：

| job | 作用 |
|---|---|
| `doc-consistency` | 文档与实际是否一致（26 条判据 + 计数同步机验：`tools/sync_counts.py` + CI 触发范围覆盖：D20） |
| `distill-pipeline` | 蒸馏管道：变异自验 + 体检（不可蒸馏是否登记、产物去向是否可核验：`tools/distill_skills.py`）；外加微信队列盘点（`tools/wechat_queue.py` —— 每篇抓到的文章必须有下落：入索引 / 草稿裁决 / `status: AD`） |
| `skill-tags` | skill 有无裸规则 + frontmatter 结构（`name` == 目录名、`allowed-tools` 逗号分隔） |
| `workbuddy-sync` | WorkBuddy 通道同步器的变异自验（`tools/workbuddy_skills.py --self-test`，临时 fixture，不碰真实目录）+ 字段取证器的自验与降级（`tools/wb_frontmatter_probe.py`） |
| `sandbox-parity` | **专防「本机绿、CI 红」**：`AGIDISTILLER_SANDBOX=1` 假装这台机器没装 WorkBuddy、没有客户端 bundle，全套机验必须照样全绿。凡是依赖本机专属资源的判据会在这里当场现形 |
| `graders-smoke` | 判分器冒烟 |
| `mock-regression` | 判分逻辑回归 |

> `allowed-tools` 的分隔符**别照着单一规范改**：agentskills.io 的开放标准写空格，
> 而两个实测宿主的**实现**都按逗号切 ——
> Claude Code 的 schema 写 `Comma-separated string or YAML list`；
> WorkBuddy 客户端的 `parseSkillFile` → `MarkdownUtils.parseListField()` →
> `splitByCommaRespectingBraces()`（源码级取证，`tools/wb_frontmatter_probe.py`）。
> **规范条文与实现对不上时以防实现为准**，本仓用逗号。门禁会拦住反向改动。
>
> 这条口径本身曾被判错过一次：早期按开放标准把「逗号」记成待改的存量偏差，
> 读实现后翻案 —— 详见 `NEXT.md` P0.4。

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

### 本机绿 ≠ CI 绿

加检查时最容易漏的一点：**你机器上装了的东西，CI 上没有。**
`sandbox-parity` job 用 `AGIDISTILLER_SANDBOX=1` 把本机专属资源（WorkBuddy 技能目录、
客户端 bundle）全部假装不存在，再跑一遍全套机验。

- 自验用例里**不许读真实本机路径** —— 要什么就自己造 fixture。依赖真实资源的用例在本机绿、CI 必然红。
- 必然红的门禁**比没有门禁更糟**：它不仅没拦住任何东西，还会把真失败一起淹没在红里。
- 「查不到」要如实说「未核验」，不许当成 0（D25 与取证器的过期检测都是两档：`None` = 无从判断）。

### 「没看到」≠「不存在」

取证器和判据最容易犯的错：**扫到一处就下结论。**
P0.13 的实例 —— 取证器只看 `parseSkillFile` 的第一个 `return`，于是把「这一处没搬 `argumentHint`」
判成「字段没人读」，一条本可以有结论的事被挂成了「待人工裁决」。

- 静态取证要**报覆盖度**（例如「解析点 4 处」；只找到 1 处要显式警告）。
  漏看伪装成结论时不会报错，只会安静地等下一次决策来引用它。
- 扫面放宽之后要**收窄回来**：把不是目标对象的解析点也算进来，
  会拿别处的字段给本该判死的字段发通行证 —— **误报比漏报更坏**。
- 补覆盖的用例必须配**反向用例**（把新纳入的那条路径删掉，结论要翻回去），
  否则新用例恒真，等于没写。
