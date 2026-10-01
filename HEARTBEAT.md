# HEARTBEAT.md — Session & Health Tracking / 会话与健康跟踪

> 本文件里的**每个数字都必须能从工作区直接核验**，口径由 `scripts/check_doc_consistency.py` 强制。
> 不许写"大概""约"或过期的历史累计值 —— 那些数字一定会漂移（本文件曾写 7 skills / 21 篇文章 / 12 节，三处全与工作区实际不符）。

## Current Status / 当前状态

| 指标 | 值 | 核验方式 |
|---|---|---|
| 生产级 skill | 21 | `ls -d skills/*/ \| wc -l` |
| 行为规范节数（ATOMCODE.md） | 14 | `grep -c '^## ' rules/ATOMCODE.md` |
| 落盘蒸馏笔记 | 10 | `find sources -name '*.md' \| wc -l` |
| 远端同步 | 见 `git status -sb` | `git log origin/main..HEAD` |

## Health / 健康

- **蒸馏管道**：运行中。`sources/` 持续扩展（laodad / wechat / tencent / 姊妹项目回流）。
- **CI**：`.github/workflows/golden-regression.yml` 已在跑。
- **社区发布**：**尚未启动**。marketplace 注册、Web 目录、多源蒸馏均为 README Phase 3 目标，未开始。
- **已知债**：见 `NEXT.md`（当前唯一条目：文档一致性机验已落地，剩余为分发动作）。

## 版本

`0.1.0`（未打 tag）。版本号口径以 README 徽章 + `plugin.json` 为准，两处由机验对齐。
