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
| 生产级 skill | 19 |
| ATOMCODE 规则 | 14 节 |
| 落盘蒸馏笔记 | 8（`sources/**/*.md`） |
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

- 多源蒸馏扩展（Medium / arXiv / 公众号），使 `sources/` 的 8 份笔记继续增长
- marketplace **注册已完成**（`.claude-plugin/marketplace.json` + 实装通过）；剩 skill Web 目录（README Phase 3 目标，**尚未启动**）
- 社区发布（V2EX / 即刻 / 小红书 —— 从未执行）
- skill 从 19 继续增长 —— **但必须有真实来源，不凑数**。凑数的 skill 会稀释「可溯源」这个唯一卖点。

---

## 停止条件

某条待办**连续 3 轮都没有动作、且没有阻塞别人** → 直接删掉，不留在文件里占位。
留着不做的事，和写了不核的数字一样，都是负债。
