# NEXT.md — 当前真实待办

> 只写**工作区里确实还不存在、且确实需要做**的事。
> 2026-07-17 版写的是「创建 GitHub 仓库 / 写 LICENSE / 写 task-briefer / 批量读 10 篇 laodad 文章」——
> 这些**早已全部完成**，那份清单代表的是历史而非现状（其内容见 git 历史）。
> 核验入口：`python scripts/check_doc_consistency.py` —— 它不 PASS，说明文档又开始漂了。

---

## 现状锚点（由机验强制，不可手写漂移）

| 项 | 值 |
|---|---|
| 仓库 | <https://github.com/TrueFurina/AGI-Distiller>（public） |
| 生产级 skill | 21 |
| ATOMCODE 规则 | 14 节 |
| 落盘蒸馏笔记 | 10（`sources/**/*.md`） |
| CI | `.github/workflows/golden-regression.yml` — 4 个 job（graders-smoke / skill-tags / doc-consistency / mock-regression） |
| 版本 | `0.1.0`（未打 tag） |

---

## P0 · 门禁与一致性 ✅ 本轮完成

| 动作 | 验收 |
|---|---|
| 新增 `scripts/check_doc_consistency.py` | 10 条判据全 PASS + `--self-test` 变异验证 10/10 可检出 |
| 接入 CI（新 job `doc-consistency`） | push/PR 触发；文档类文件改动也会触发 |
| 修正过期数字 | README / README.zh / HEARTBEAT：`7→19` skill、`12→14` 节、`22→8` 笔记 |
| 消除幽灵仓库路径 | `agi-distiller/agi-distiller` 全部改为 `TrueFurina/AGI-Distiller`（README ×2 中英 + plugin.json homepage） |
| 停止跟踪编译产物 | 7 个 `.pyc` 移出索引；`.gitignore` 补 `__pycache__/` + `*.py[cod]` |

---

## P0.2 · 安装链路落地 ✅ 本轮完成（走 A 方案）

| 动作 | 验收证据 |
|---|---|
| 新建 `.claude-plugin/marketplace.json` | `claude plugin validate .` → `√ Validation passed` |
| `plugin.json` 从仓库根移入 `.claude-plugin/` | 单一真相源；机验 D8/D10 路径同步跟进 |
| 修 manifest 字段缺陷 | validate 报出 `author` 应为 object、`tags` 应属 marketplace entry —— 均已修正 |
| **真跑安装全链路** | `marketplace add` → `plugin install agi-distiller@agi-distiller` → `plugin details` 输出 `Skills (19)`，19 个 skill 全部加载（Claude Code v2.1.251） |
| 平台表去虚假 ✅ | 7 个平台原全打 ✅，实际只有 Claude Code 实测过 → 其余 6 个降为 ⚠️ 未实测 |
| 新增判据 D13 / D14 | marketplace 清单自洽 + 平台表 ✅ 必须有实测证据背书；14/14 变异可检出 |

> **为什么不只靠 validate**：官方明确 `claude plugin validate` 对「source 路径不存在」这类问题**照样通过**，
> 只有真 install 才暴露。所以本轮是 validate + 实装双验证。

---

## P0.3 · 断链与数字漂移 ✅ 本轮完成

| 动作 | 验收 |
|---|---|
| 新建 `CONTRIBUTING.md` | 兑现已挂了很久的死链 `[CONTRIBUTING.md](CONTRIBUTING.md)`；内容全部来自项目真实流程（`DISTILLER.md` + `tools/check_skill_tags.py` 的溯源标记要求），不是通用模板 |
| 中文 README 补同一链接 | 此前英文有、中文没有 |
| 新增 D15 断链检测 | 全仓 5 个相对链接逐个验证目标存在；以后写错链接会被 CI 拦下 |
| 新增 D16「N 篇」虚报检测 | 抓出 `DISTILLER.md` 写的「19 篇 laodad.com 文章」（实际 laodad 落盘 4 份、全库 8 份） |
| 修 `DISTILLER.md` 漂移 | 篇数 19 → 实际 8（laodad 4）；笔记目录 `notes/` → 真实目录 `sources/` |
| 修 `DISTILLER.md` 虚假 ✅ | 「能在 Codex CLI 中运行吗」原打 ✅，本机无该 CLI → 改 ⚠️ 未实测；质量门禁的「跨平台兼容」同改 |
| 删 `pipeline/` 空目录 | 真实管道是 `tools/distill_skills.py`，空目录零引用 |

> **D16 的误报教训（已在判据 docstring 写明）**：第一版没有语境豁免，立刻误报 3 处——
> 「规划目标 50 篇」「此前错写 21 篇」「待办：批量蒸馏 10 篇」全是合法语境。
> 已加豁免（目标/规划/此前/待办字样，以及同行带实际值对照的写法）。
> **它是启发式判据，拦得住裸虚报，拦不住"给虚报加个'目标'字样"——别当硬保证。**

---

## P0.4 · skill 增长：第 20 个 ✅ 本轮完成

本轮不是"磨工具"，是**第一次真正走通「真实来源 → 蒸馏笔记 → skill」这条链**——
模板和门禁都是为它服务的，空转久了才发现哪里不对。

| 动作 | 验收证据 |
|---|---|
| 新增 `sources/anthropic/skill-authoring-standard.md` | 落盘蒸馏笔记 8 → **9**；抓取状态逐条标注（2 条直连 ✅ / 3 条标注未核验 ⚠️） |
| 新增 `skills/skill-authoring-check/SKILL.md` | 120 行、描述 269 字符、`name` 与目录名一致——全部落在标准边界内 |
| 补齐「怎么写 skill」这一层 | 此前 19 个 skill 覆盖调试/版本/门禁/交接，**唯独没有 skill 写作本身**，而产出 skill 正是本仓的存在理由 |
| 数字口径同步 | README ×2 / HEARTBEAT / NEXT 共 **19 处**替换（含机验抓出的 1 处漏改），断言式补丁，逐处"恰好命中 N 次" |

本轮实测结论（19 个存量 skill 全量扫描）：

| 检查项 | 标准要求 | 实测 | 结论 |
|---|---|---|---|
| `name` == 目录名 | 必须 | 19/19 一致 | ✅ |
| `description` ≤ 1024 | 是 | 最长 148 字符 | ✅ |
| `SKILL.md` ≤ 500 行 | 建议 | 最长 185 行 | ✅ |
| `allowed-tools` 分隔符 | 空格 | **19/19 用逗号** | ⚠️ 存量偏差，**未批量改**（属"顺手重构"，且该字段为实验性，批量改前需先实测解析器） |

> 局限：本轮只证明"链能跑通一次"。**跑通一次不算证据**——下次换一个来源再走一遍，
> 若仍要人工补同样几处数字，说明缺的不是 skill，是**自动化**（Phase 2 的 `Automated distillation pipeline`）。
>
> **2026-10-01 复核**：预言成立——第二遍仍要人工补同样几处数字（16 处），且差点又漏。
> 缺口已由 `tools/sync_counts.py` 补上，见 P0.5。

---

## P0.5 · 第 21 个 skill + 计数同步自动化 ✅ 本轮完成

P0.4 留了一句预言：**"跑通一次不算证据"**。本轮就是回去验证这句话——换一个来源再走一遍，
看人工步骤会不会重复。

| 动作 | 验收证据 |
|---|---|
| 新增 `sources/owasp/untrusted-content-boundary.md` | 落盘蒸馏笔记 9 → **10**；OWASP GenAI 官方 LLM01 / LLM06 两页**直连抓取 ✅**、十大风险索引页 ✅（其余八页本轮未抓，已在笔记里注明，不凭印象引用） |
| 新增 `skills/untrusted-content-boundary/SKILL.md` | 88 行、描述 201 字符、`name` == 目录名、`allowed-tools` 按标准**空格分隔** |
| 补齐「外部不可信内容」这一层 | 此前 20 个 skill 全在"输出侧/流程侧"，**没有一个是输入侧的信任边界**；而本仓每天在抓外部内容，正落在**间接注入**的定义域内 |
| **新增 `tools/sync_counts.py`** | 计数同步自动化：站点表逐处登记（首版：23 条计数 + 2 条分类分解）一条命令从工作区事实改回；`--self-test` 对**全部**站点可检出，且显式冻结历史/实测记录站点 |

**复现性结论（P0.4 的预言被坐实）**

| 检查项 | P0.4（第一遍，19→20） | P0.5（第二遍，20→21） |
|---|---|---|
| 需要同步的计数站点 | 19 处，人工逐处改 | **16 处——一模一样的活又回来了**（另在 ROADMAP 上又发现 4 处） |
| 改法 | 人工 grep + 手写一次性断言补丁脚本 | `python tools/sync_counts.py --fix`（一条命令） |
| 漏改风险 | 有（漏了 HEARTBEAT 那行，靠门禁回头抓出） | 无（站点表穷举 + "恰好命中 1 次"断言，站点消失/被复制也会报错） |

**结论：第一遍的预测被第二遍坐实——重复的人工步骤就是会重复。** 缺口因此补上。
工具**只改计数**，**不碰历史/实测记录**（如 README 里那次 `Skills (19)` 的安装观测值）——
这些在 `FROZEN_MARKERS` 里显式登记，`--self-test` 会验证它们既存在、又**没被**纳入自动改写。

**仍未自动化的一步（如实标出）**：README 两张 skill 表的**一句话摘要**。
它是人工提炼的，不是 frontmatter 的拷贝（英文表写英文、中文表写中文），工具只列待办、不代写。

---

## P1 · 待办（真实存在，非凑数）

### 1. Codex CLI 安装路径未实装

`npx skills add TrueFurina/AGI-Distiller` —— 已核实 CLI 存在（`skills@1.7.0`）、`add <owner/repo>` 语法合法，
但本机无 Codex CLI，**未实装**。README 已如实标注。待有 Codex CLI 的机器补验。

### 2. ✅ 已解决：CONTRIBUTING.md（见 P0.3）

### 3. ✅ 已解决：`pipeline/` 空目录已删

蒸馏管道的真实实现是 `tools/distill_skills.py`（`sources/*.md` → `skills-drafts/<slug>/SKILL.md`），
`pipeline/` 空目录全仓零引用，纯属误导，已删。剩「双份 pre-commit 脚本」由 D12 盯着，不是缺口。

### 4. ✅ 已解决：ROADMAP 校准

顶部已加「规划目标 vs 实际（2026-09-27 实测）」对照表，关键里程碑的虚假 ✅ 已改为
「已过期 / 进行中 / 未启动」。Phase 2 窗口为 2026.08.17 → 2026.10.17，截至 2026-10-01 仍在窗口内，
故阶段划分本身未过期，不再重排。

### 5. ✅ 已解决：PR / issue 模板

新增 `.github/PULL_REQUEST_TEMPLATE.md` + 3 个 issue form
（`new-skill` / `new-source` / `bug`）+ `config.yml`（禁用空白 issue）。

要点：

- 所有 `labels` 只用仓库**已存在**的 9 个默认 label —— GitHub 规则是
  引用不存在的 label 不报错、只是**静默不添加**，属典型静默失效；
- 单行字段类型是 `input`（不是 `textinput`），按官方 schema 核对过；
- 机验新增 **D18**（PR 模板引用的自检脚本必须真实存在）与 **D19**
  （issue form 结构合法 + label 真实存在），19/19 PASS 且变异全检出。

> 局限：本机无法验证 GitHub 端对 YAML form 的渲染与解析，
> 已做的是「官方 schema 对照 + 结构机验」。首次有人真实开 issue 才算最终验证。

---

## P2 · 长线（不设 deadline）

- 多源蒸馏扩展（Medium / arXiv / 公众号 + 官方规范文档），使 `sources/` 的 10 份笔记继续增长
- marketplace **注册已完成**（`.claude-plugin/marketplace.json` + 实装通过）；剩 skill Web 目录（README Phase 3 目标，**尚未启动**）
- 社区发布（V2EX / 即刻 / 小红书 —— 从未执行）
- skill 从 21 继续增长 —— **但必须有真实来源，不凑数**。凑数的 skill 会稀释「可溯源」这个唯一卖点。
- 2026-10-01 起，新增 skill 前先读 `skills/skill-authoring-check/SKILL.md`：P0.4 新增的 1 处裸规则、
  1 处漏改数字，都是被它列的门禁当场抓出来的。**P0.5 又抓出它自己的一处未覆盖变体**：
  规则句**跨两行**时，标记写在第二行等于没写（检查器逐行匹配）——该 skill 已补上这条。
- 计数同步已自动化（`tools/sync_counts.py`）。**但站点数不写进文档** —— 它随工具演化而变，
  写死就是又一处会漂的数字；要看当前值跑 `--check` / `--self-test`，工具会打印。
  **README skill 表的摘要仍要人工写**——
  若第三遍增长时这一步仍然嫌烦，再考虑让工具生成占位摘要 + 人工润色，而不是现在凭空造。

### 6. 安装链路实测记录滞后于 skill 计数

README 的 `Component inventory: Skills (19)` 是 **Claude Code v2.1.251 那次运行的观测值**，
新增第 20、21 个 skill 后**未复跑**安装链路。已在 README 中就地标注"该记录早于当前计数、未复跑"，
**没有把它追改成 20 或 21**——那等于伪造一次没跑过的验证。
补验条件：有 Claude Code 环境的机器，跑 `plugin validate` → `marketplace add` → `plugin install` → `plugin details`。

---

## P0.6 · 「门在，但不为这个改动而开」 ✅ 本轮完成（2026-10-05）

上一轮把 `plugin.json` 从仓库根移进 `.claude-plugin/`：**脚本里的路径跟着改了，CI 的触发路径没跟着改**。
根级 `plugin.json` 那条 pattern 从此再也匹配不到它。后果是 `.claude-plugin/plugin.json`
（版本号与 homepage 的被断言来源）**改了 CI 不跑**。

这比"文档漂了"更坏：漂了至少 CI 会红；而这属于 **CI 压根不为它而开** ——
本地 `--self-test` 全绿、远端一片绿，漂移直接进去。

同类问题不止一处，程序化核算后共 **17 个**被机验监视、却不在触发范围内的文件
（其中 6 个是我手工核算时找到的，另 11 个是 D20 上线后自己找出来的）：

| 被改却不触发 CI | 谁在断言它 |
|---|---|
| `.claude-plugin/plugin.json`、`marketplace.json` | D8 仓库 URL、D13 清单自洽 |
| `.github/ISSUE_TEMPLATE/*.yml`、`PULL_REQUEST_TEMPLATE.md` | D19 结构/label、D18 脚本引用 |
| `CONTRIBUTING.md` / `NEXT.md` / `ROADMAP.md` / `DISTILLER.md` | `sync_counts.py` 的计数站点 |
| `SOUL.md` / `AGENTS.md` / `USER.md` / `TOOLS.md` / `IDENTITY.md` | D11 字符数表 |
| `scripts/pre-commit/*.py`、`templates/scripts/pre-commit/*.py` | D12 孪生脚本一致性 |
| `hooks/*.py`、`thinking.md`、`skills-drafts-archive/**` | D15/D18 的全仓扫描面 |

修法两层，缺一不可：

1. **触发范围按类型全覆盖**（`**/*.md`、`**/*.py`、`**/*.yml`、`**/*.yaml`、`**/*.json`、
   `**/*.sh`、`**/*.txt`、`**/*.toml`、`.gitignore`）。机验的管辖面本来就跨全仓
   （断链查全仓 `.md`、脚本引用查全仓 `.py`、计数站点散落在全部文档），**逐个列文件名永远会漏**。
2. **新增判据 D20**，把"完整性"变成机器问题：**执行取证** —— 挂一层记录器跑一遍全部判据、
   再读 `sync_counts` 的站点表，凡被读到的具体文件必须落在触发范围内。
   不靠正则猜文件名：猜出来的集合本身就会与真实访问漂移，那正是它要防的病。

> 过程中踩到自己造的伪影：第一版 D20 把 `files_under("skills")` 记成了目录前缀 `skills/**`，
> 而 CI 是按文件类型覆盖的 —— 前缀串自然匹配不上，于是误报 5 个"缺口"。
> **是判据看错了对象，就该改判据，不是改文档去迎合它。** 改成只记录具体文件后归零。

**验证**：20/20 PASS、变异 20/20 可检出（D20 的变异必须**两处触发块都抹**才打得穿 ——
只抹一处时并集仍覆盖，会把自己误判成"判据失效"）；`sync_counts` 的站点变异全部可检出。

顺便清掉一处同类漂移：文档里写着 `sync_counts.py`「25 个站点」，而工具实际登记数早已变化，
且"注册数 / 自检口径"两个数还不一致。**这类数字不写进文档** —— 让工具打印，写死就是又一处会漂的数字。

---

## 停止条件

某条待办**连续 3 轮都没有动作、且没有阻塞别人** → 直接删掉，不留在文件里占位。
留着不做的事，和写了不核的数字一样，都是负债。
