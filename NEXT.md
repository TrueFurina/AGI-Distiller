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

## P1 · 待办（真实存在，非凑数）

### 1. ⚠️ 安装命令从未实测

README 写了两条安装路径：

```
/plugin marketplace add TrueFurina/AGI-Distiller
npx skills add TrueFurina/AGI-Distiller
```

但仓库根**没有 `.claude-plugin/marketplace.json`**，这两条命令**在本机从未跑过**。
按「宣称必须有可复现命令背书」的纪律，二选一：

- **A**：补 marketplace manifest，然后真跑一次，把输出贴进 README；
- **B**：在 README 把这两条标为「未验证」，并把**已验证**的手动安装（`cp -r skills/* ...`）提到第一屏。

### 2. 无 CONTRIBUTING.md

README 有 Contributing 章节，但仓库里没有独立文件；`.github/` 下除 workflows 外没有 PR / issue 模板。
对「希望他人投稿 skill」的定位来说，这是硬缺口。

### 3. 一处空目录 + 一处双份脚本

- **`pipeline/` 是空目录**（git 不跟踪，但本地结构上误导人）—— 要么填内容，要么删。
- `scripts/pre-commit/` 与 `templates/scripts/pre-commit/` 各有一份**内容相同**的 4 个脚本
  （前者是仓库自用，后者是分发给其它项目的模板）。
  这不是缺陷，但**两份必须同步** —— 否则模板会静默漂移。目前没有任何机验盯着这对孪生文件。

> 更正记录：本条初稿曾把 `scripts/pre-commit/` 写成空目录，属误判（`ls scripts/` 只看到目录名，未进去看）。
> 这正是本文件要防的病 —— 已按实际核对结果改写。

### 4. ROADMAP 阶段已过期

`ROADMAP.md` 停在「Phase 1: 现在 → 2026.08」「Phase 2: 2026.08 → 2026.10」，
而今天已是 **2026-09-27**，实际 skill 数 19 已超过 Phase 1 目标（10）。需按实际重排阶段与指标。

---

## P2 · 长线（不设 deadline）

- 多源蒸馏扩展（Medium / arXiv / 公众号），使 `sources/` 的 8 份笔记继续增长
- marketplace 注册 + skill Web 目录（README Phase 3 目标，**尚未启动**）
- 社区发布（V2EX / 即刻 / 小红书 —— 从未执行）
- skill 从 19 继续增长 —— **但必须有真实来源，不凑数**。凑数的 skill 会稀释「可溯源」这个唯一卖点。

---

## 停止条件

某条待办**连续 3 轮都没有动作、且没有阻塞别人** → 直接删掉，不留在文件里占位。
留着不做的事，和写了不核的数字一样，都是负债。
