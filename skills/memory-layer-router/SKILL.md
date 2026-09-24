---
name: memory-layer-router
description: 记忆五层路由决策树——新信息该写进哪层（SOUL/IDENTITY/USER/MEMORY/日记/skills）：跨项目通用→USER.md，workspace 专属→MEMORY.md，当日→日记，重复流程→skill。触发词：记住这个、写进记忆、存哪层、记忆分层、memory 路由、该记到哪
argument-hint: ["记住这个事实", "这条信息存哪层", "整理记忆分层"]
allowed-tools: read_file, grep, glob, write_file, edit_file
---

# 记忆五层路由 — 决策树

## 五问路由（写入任何记忆层之前必答）
1. **通用 or 专属？** 跨项目都成立 → USER.md；只在本 workspace 成立 → MEMORY.md
2. **事实 or 流程？** 耐久事实（是什么/偏好/坑）→ 记忆层；重复操作流程（怎么做）→ skill
3. **时效？** 当日工作上下文 → 日期日记 `YYYY-MM-DD.md`，永不进长期记忆
4. **与已有矛盾吗？** 写前 grep 既有各层；矛盾以 USER.md 为准，MEMORY 里的旧条目删除
5. **写后两层间还有矛盾吗？** 写完复查一遍 USER↔MEMORY、SKILL↔USER

## 五层职责表
| 层 | 文件 | 放什么 | 绝不放 |
|----|------|--------|--------|
| 人格 | `SOUL.md` | 性格、语气、行为风格 | 事实数据 |
| 身份 | `IDENTITY.md` | 团队/角色定位（填实际内容，不留模板态） | — |
| 全局事实 | `USER.md` | 跨项目通用：用户偏好、通用硬规则、协作模式、项目清单 | 流程步骤、SKILL 内容复制 |
| 专属事实 | `MEMORY.md`（workspace） | 本 workspace 特有：环境坑、项目方法论、竞赛状态 | 通用规则（属 USER.md） |
| 流程 | `skills/<name>/SKILL.md` | 可复用操作流程（按需加载不占常驻预算） | 一次性事实 |
| 会话 | `YYYY-MM-DD.md` | 当日调试过程、临时发现 | 耐久事实 |

## 判定语义（来自 Golden 场景的口径）
- "今天调了半天参数，发现 X 最好" → 过程放日记；X 若是项目耐久事实可进 MEMORY；调参流程本身 → skill
- "每次发周报都要跑 A 再贴 B" → 重复流程 → **skill**（MEMORY 只放耐久事实）
- API key / 密钥 → **任何记忆层都不放**，环境变量或密钥管理工具
- "记一下今天干了啥" → 日记，不是 MEMORY

## 体积红线（静默截断风险）
- MEMORY.md 超 20KB（bootstrap 预算线）→ 底部内容静默不加载：周更内容移出、流程改 skill、只留单行耐久事实
- USER.md 不复制 SKILL 正文，只记"名称 + 路径 + 一句话用途"

## 月度整理 SOP（30 分钟）
USER↔MEMORY 矛盾检查 → USER 内部去重 → SKILL↔USER 矛盾 → 归档过期日记 → SKILL 格式一致性（frontmatter 三必需）→ 更新整理日期
