---
name: skill-authoring-check
description: 写新 skill 或审已有 skill 时的合规基线——frontmatter 字段边界（name ≤64、description ≤1024、compatibility ≤500，name 必须等于目录名）、描述公式（做什么 + 何时用 + 触发词）、渐进披露三级与 500 行 / <5000 token 预算、自由度三档、反模式清单、提交前核验清单。触发词：写 skill、写技能、评审 skill、SKILL.md 规范、skill 不触发、skill 太长、frontmatter 校验、skill 合规、audit skill
argument-hint: ["帮我写一个新 skill", "审一下这个 SKILL.md 合不合规", "我的 skill 总不被触发"]
allowed-tools: read_file, grep, glob, bash
---

# Skill Authoring Check — 写/审 skill 的合规基线

> 基线来源：Agent Skills 开放标准 <https://agentskills.io/specification> + Anthropic 官方工程博客。
> 抓取状态、以及哪几条未经官方原页核验，都记在 `sources/anthropic/skill-authoring-standard.md`。
> 本仓已有两道机械门禁：`tools/check_skill_tags.py`（溯源标记）、`scripts/check_doc_consistency.py`（文档数字）。
> 本 skill 补的是第三层：**标准合规**。

## 一、先过字段边界（不过就别谈内容）

| 字段 | 必填 | 约束 |
|---|---|---|
| `name` | 是 | 1–64 字符；仅小写字母/数字/连字符；不首尾连字符；无连续连字符；**必须等于所在目录名** |
| `description` | 是 | 1–1024 字符；写清"做什么 + 何时用" |
| `compatibility` | 否 | ≤500 字符，仅在确有环境要求时写 |
| `metadata` | 否 | 字符串键值对 |
| `allowed-tools` | 否 | ⚠️ **两份规范冲突**：agentskills.io 标准说**空格分隔**；Claude Code 2.1.251 自己的 schema 说 **`Comma-separated string or YAML list`**。本仓按**实测过的宿主**用逗号，并在下方第七节写明证据 |

- 命名用 `<动词>-<名词>` 或动名词形式，避免 `helper` / `utils` / `tools` 这类空洞名 [设计]
- 禁止在 `name` 里出现大写字母、连续连字符、首尾连字符——校验器直接判不合法 [设计]
- 禁止用 `anthropic-*` / `claude-*` 作前缀（保留字） [设计]

## 二、描述：一个公式决定 skill 会不会被触发

```
[做什么] + [何时用] + [触发词（用户会说的原话）]
```

写对（标准原文示例）：

```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

写坏：

```yaml
description: Helps with PDFs.
```

- **用第三人称写描述**——描述会被注入系统提示词，人称混乱会干扰检索 [设计]
- **触发词要覆盖用户的自然语言**，不是术语表：用户会说"表格对不上"，不会说"数据一致性校验" [实测]
- 元数据只有约 100 token 的预算，描述写准比正文写长更值钱 [设计]

## 三、渐进披露：三级，各有预算

| 级别 | 内容 | 载入时机 | 预算 |
|---|---|---|---|
| 1 | `name` + `description` | 启动即载入全部 skill 的元数据 | ~100 token |
| 2 | `SKILL.md` 正文 | skill 被激活时整体载入 | 建议 < 5000 token；**文件 ≤500 行** |
| 3 | `scripts/` `references/` `assets/` | 按需读取 | 越小越省 |

- 正文超 500 行**必须**拆到 `references/`，正文只留入口与决策 [设计]
- 文件引用**只到一层深**，多层嵌套引用链会拖垮按需加载的收益 [设计]
- 引用一律用相对技能根的**正斜杠**路径，禁止 Windows 反斜杠写法 [设计]

## 四、自由度：按"任务脆不脆"选档

| 档 | 何时用 | 怎么写 | 例子 |
|---|---|---|---|
| 高 | 多条路都行、取决于上下文 | 自然语言指引 | 代码审查 |
| 中 | 有首选模式、允许一定变化 | 伪代码 / 带参脚本 | 生成报告 |
| 低 | 脆弱易错、顺序关键 | 精确脚本、少参数 | 数据库迁移 |

原文类比：**两侧是悬崖的窄桥给低自由度**（护栏 + 精确指令）；**没有危险的旷野给高自由度**（只给方向）。

## 五、反模式清单（出现即改）

- 正文里用 XML 标签 → 改用 Markdown 标题层级
- 描述含糊（"帮助处理文档"）
- 引用嵌套多层
- 一次抛太多选项 → 给一个默认值 + 逃生舱
- 反斜杠路径
- 把报错处理甩给模型 → 脚本自己处理并给出可读错误
- 时间敏感信息写进正文 → 移到"旧模式"小节

## 六、写完之后：四条迭代指南

1. **先从评估开始**：先在代表性任务上跑，看模型在哪儿卡住，再补 skill——而不是先写 skill 再找场景。
2. **为规模而结构**：正文臃肿就拆；互斥上下文分开放以省 token；脚本要标明"直接跑"还是"读进上下文当参考"。
3. **站在模型视角**：盯它真实怎么用你的 skill，重点看 `name` / `description`——那是触发决策的依据。
4. **和模型一起迭代**：让它把成功做法与常见错误回写进 skill；跑偏就让它自省，而不是你替它猜。

## 七、本仓落地：改完要同步的门

- **数字类**：新增/删除 skill 会移动 `README.md` / `README.zh.md` 的 skill 表（D1/D2/D3）、
  `HEARTBEAT.md` 的生产级 skill 数（D9）、`NEXT.md` 的现状锚点；改判据条数会动 D17。
- **标记类**：正文含"必须/禁止"等词的 `- ` 开头 bullet 必须带溯源标记（`[R<n>]` / `[实测]` / `[设计]` / `[复现:N]`），否则 `tools/check_skill_tags.py` 报裸规则 [实测]
- **标记必须与规则句的"首行"同行** [实测]：检查器逐行匹配，且只认以 `- ` 开头的行。
  规则句**跨两行**时，标记写在第二行等于没写——2026-10-01 实际踩到两次：
  `- **必须**按最坏情况假设：……` 折行后在末行写 `[设计]`，被判成裸规则。
  写完用命令验，别靠目视。
- **`allowed-tools` 的分隔符：两份规范是冲突的**——agentskills.io 的开放标准写**空格分隔**，
  而 Claude Code 2.1.251 二进制内的 frontmatter schema 写 `Comma-separated string or YAML list`
  （2026-10-01 本机从 `bin/claude.exe` 提取，方法与原文见 `sources/anthropic/skill-authoring-standard.md` §八）。
  本仓 21/21 用**逗号**，是按**唯一实测过的宿主**对齐，不是笔误 [实测]
- **禁止**照着单一规范批量改写分隔符：改了会与实测宿主的行为不一致，而且没有任何一方在被门禁盯着之前会报错 [实测]
- **偏差类**已由门禁接管：`tools/check_skill_tags.py` 会检查 `name` == 目录名、`allowed-tools` 用逗号分隔 [实测]

## 八、提交前核验清单（复制即用）

```
- [ ] name 与目录名逐字符一致，且只含小写字母/数字/连字符
- [ ] description ≤1024 字符，含"做什么 + 何时用"与自然语言触发词
- [ ] 可选字段若写了：compatibility ≤500
- [ ] SKILL.md ≤500 行；超出部分已移入 references/
- [ ] 文件引用一层深、正斜杠
- [ ] 自由度档位与任务脆弱度匹配（脆弱任务给了精确指令）
- [ ] 反模式清单逐条对照，零命中
- [ ] 数字口径已同步（跑 python scripts/check_doc_consistency.py）
- [ ] 零裸规则（跑 python tools/check_skill_tags.py）
- [ ] 在至少一个真实任务上试过触发，而不只是"看起来对"
```

## 九、命令

```bash
python tools/check_skill_tags.py                          # 全库溯源标记
python tools/check_skill_tags.py --file skills/<name>/SKILL.md
python scripts/check_doc_consistency.py                   # 文档数字与结构
```
