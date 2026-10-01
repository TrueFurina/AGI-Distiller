# 蒸馏笔记：Agent Skills 写作标准（Anthropic 官方口径）

- **蒸馏日期**：2026-10-01
- **蒸馏人**：WorkBuddy (Gu)
- **分类**：agent-collaboration / skill-authoring
- **入仓原因**：本仓 19 个 skill 覆盖了调试、版本、门禁、交接等主题，**唯独没有「怎么写 skill 本身」**——
  而产出 skill 正是这个仓库存在的理由。本文是该空缺的外部权威基线。

## 〇、来源与抓取状态（别把没抓到的当抓到了）

| # | 来源 | 状态 | 用途 |
|---|---|---|---|
| 1 | <https://agentskills.io/specification> | ✅ 直连抓取成功 | **开放标准全文**：frontmatter 字段与边界、目录结构、渐进披露 token 预算、文件引用规范、校验工具 |
| 2 | <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills> | ✅ 直连抓取成功 | 官方工程博客：skill 的定义与解剖、渐进披露三级、上下文窗口行为、代码执行、开发与评估四条指南、安装安全 |
| 3 | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> | ⚠️ **区域封锁，未直连** | 该页返回 `app-unavailable-in-region`。其「自由度三档 / 反模式清单 / 提交前 checklist」经第三方镜像 <https://skills-guides.com/en/skills/creating-agent-skills-mrx3xymr>（页面日期 2026-07-23）转述核实，**未与官方原页逐字对照** |
| 4 | 官方 PDF《The Complete Guide to Building Skills for Claude》(resources.anthropic.com) | ⚠️ 下载失败（`content_type=application/pdf` 但 `size_download=0`） | 未采用 |
| 5 | <https://github.com/anthropics/skills>（README 与 `spec/agent-skills-spec.md`） | ✅ 直连抓取成功 | 官方仓库自述；`spec/` 已是指针文件，正文指向来源 1 |
| 6 | **本机实测**：`@anthropic-ai/claude-code` v2.1.251 的 `bin/claude.exe` 内嵌 frontmatter schema | ✅ 本机提取（2026-10-01） | **推翻了来源 1 对 `allowed-tools` 分隔符的说法**——详见 §八。提取方法：在二进制里检索字段描述串（如 `Tools available to the model while this file is active`） |

> 口径说明：**标注 ✅ 的内容是按抓取到的原文整理的；标注 ⚠️ 的内容来自第三方转述，属于"未经官方原页核验"。**
> 使用本笔记时，若要与官方逐字对齐，需先解决来源 3 的访问问题。

## 一、frontmatter 字段边界（来源 1，原文口径）

| 字段 | 必填 | 约束 |
|---|---|---|
| `name` | 是 | **1–64 字符**；只允许小写字母、数字、连字符；**不得以连字符开头或结尾**；**不得含连续连字符**；**必须与父目录名一致** |
| `description` | 是 | **1–1024 字符**；非空；应同时说明"做什么"和"何时用" |
| `license` | 否 | 许可证名或捆绑许可证文件名 |
| `compatibility` | 否 | **最长 500 字符**；仅在确有环境要求时写（目标产品、系统依赖、网络需求） |
| `metadata` | 否 | 字符串键值映射；键名建议唯一化以避免冲突 |
| `allowed-tools` | 否 | 工具串，**实验性，各实现支持度不一**。来源 1（agentskills.io）说**空格分隔**；但来源 6 的实测显示 Claude Code 实现的是**逗号分隔**——**两份规范冲突，见 §八** |

最小可用示例（原文）：

```yaml
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

## 二、目录结构（来源 1）

```
skill-name/
├── SKILL.md          # 必需：元数据 + 指令
├── scripts/          # 可选：可执行代码
├── references/       # 可选：按需读取的文档
├── assets/           # 可选：模板、资源
```

- `scripts/` 脚本应自包含或明确声明依赖、给出可读的报错、优雅处理边界。
- `references/` 单个文件保持聚焦——**按需加载，文件越小越省上下文**。
- 文件引用一律用**相对技能根的相对路径**，且**只到一层深**，禁止多层嵌套引用链。

## 三、渐进披露三级 + 预算（来源 1，原文给出数值）

1. **元数据**（约 100 token）：所有已装 skill 的 `name` + `description` 在启动时预载。
2. **指令**（建议 < 5000 token）：skill 被激活时，整个 `SKILL.md` 正文载入。
3. **资源**（按需）：`scripts/` `references/` `assets/` 只在需要时载入。

原文："Keep your main `SKILL.md` under 500 lines. Move detailed reference material to separate files."

上下文窗口的序列（来源 2）：系统提示词 + 各 skill 元数据 + 用户消息 → 触发 skill → 读取 `SKILL.md` →
按需读取捆绑文件 → 执行任务。**这条序列解释了为什么"描述写得准"比"正文写得长"更重要**：
描述决定 skill 会不会被触发，而正文只在被触发后才有成本。

## 四、自由度三档（来源 3，第三方转述）

| 档位 | 何时用 | 表达形式 | 例子 |
|---|---|---|---|
| 高 | 多条路径都可行、取决于上下文、靠启发式 | 自然语言指引 | 代码审查 |
| 中 | 存在首选模式、允许一定变化、配置影响行为 | 伪代码 / 带参脚本 | 生成报告 |
| 低 | 操作脆弱易错、一致性关键、必须按固定顺序 | 具体脚本、少或无参数 | 数据库迁移 |

原文类比：**"两侧是悬崖的窄桥"给低自由度（护栏 + 精确指令）**；**"没有危险的旷野"给高自由度**（只给方向）。

## 五、反模式（来源 3，第三方转述）

- 正文里用 XML 标签（应改用 Markdown 标题层级）
- 描述含糊（"帮助处理文档"）
- 引用链深层嵌套（应保持距 `SKILL.md` 一层）
- 一次性给太多选项（应给默认值 + 逃生舱）
- Windows 反斜杠路径（统一用正斜杠）
- 把错误处理甩给模型（脚本自己该处理错误）
- 时间敏感信息写进正文（应放进"旧模式"小节）

## 六、开发与评估四条指南（来源 2，官方原文）

1. **Start with evaluation**：先在代表性任务上跑 agent，**观察它在哪儿卡住或需要额外上下文**，再增量补 skill。
2. **Structure for scale**：`SKILL.md` 变臃肿就拆分引用；互斥或少共用的上下文分开放以省 token；
   代码既可作可执行工具也可作文档，但要**明确是"直接跑"还是"读进上下文当参考"**。
3. **Think from Claude's perspective**：在真实场景观察 skill 被怎么用，重点盯 `name` 与 `description`——
   它们是触发决策的依据。
4. **Iterate with Claude**：让模型把成功做法与常见错误沉淀回 skill；跑偏时让它自省。
   目的是**发现模型真正需要什么上下文，而不是事先猜**。

## 七、安装侧安全（来源 2，官方原文）

只从可信来源安装 skill；从低信任来源安装前应完整审计：读捆绑文件内容、**特别关注代码依赖与捆绑资源
（图片、脚本）**、注意 skill 内是否指示模型连接不可信外部网络。

## 八、与本仓（AGI-Distiller）的实测对照 —— 2026-10-01 全量扫描

| 检查项 | 标准要求 | 本仓实测 | 结论 |
|---|---|---|---|
| `name` == 目录名 | 必须 | 19/19 一致 | ✅ 合规 |
| `description` ≤ 1024 字符 | 是 | 最长 148 字符（`memory-layer-router`） | ✅ 远低于上限 |
| `SKILL.md` ≤ 500 行 | 建议 | 最长为 `deploy-checker` 185 行 | ✅ 合规 |
| `allowed-tools` 分隔符 | 来源 1：空格；**来源 6：逗号** | 存量 19/19 用逗号 | ⚠️ **两份规范冲突**，见下（**不是本仓的错**） |

### ⚠️ 重要更正（2026-10-01）：`allowed-tools` 的分隔符，两份规范是冲突的

**原先的结论是错的。** 本文第一版写「标准要求空格分隔，本仓 19/19 用逗号 → 存量偏差，建议新增按标准写」。
那个结论**只看了来源 1（开放标准），没去看实际实现**。查了 Claude Code 之后反过来了：

**实测证据**（来源 6，本机 `@anthropic-ai/claude-code` v2.1.251 —— 正是本仓 README 里那次安装实测所用的版本）：

```
"allowed-tools": hE().optional().describe(
  "Tools available to the model while this file is active. Comma-separated string or YAML list.")
"disallowed-tools": ... .describe(
  "Tools removed from the model while this file is active. Comma-separated string or YAML list. ...")
```

同一 schema 块还含 `Display name` / `One-line summary shown in listings and the Skill tool` /
`Placeholder text shown after the slash command name` / `disable-model-invocation` / `user-invocable`，
即**该技能/斜杠命令 frontmatter 的解析器**。另有类型校验串佐证：
`allowed-tools must be a string or array of strings, got `（接受字符串或数组两种写法）。

**因此**：

- **Claude Code 实现的是逗号分隔**（`Comma-separated string or YAML list`）。
- **agentskills.io 的开放标准写的是空格分隔。**
- 这是**两份规范之间的冲突**，不是本仓写错了。本仓 21 个 skill 用逗号，与**唯一实测过的宿主**一致。
- **不要照着任何单独一份条文批量改**——改了在另一端就不对；而且没有任何一方在被门禁盯住之前会报错（典型静默失效）。
- 已加门禁：`tools/check_skill_tags.py` 现在检查 `allowed-tools` 用逗号分隔 + `name` == 目录名。

**仍未验证的部分（如实说）**：其余平台（Codex CLI 等）如何解析该字段**未实测**，
本仓 README 的平台表把它们标为 ⚠️ 未实测。所以"逗号"是**按已实测宿主**的选择，不是"事实上的唯一正确写法"。
