---
name: session-handoff
description: 会话交接工件——任务中断/换会话/换工具时写 agent-handoff.json 式交接文件（证据链接、fail-closed），而非聊天总结。触发词：会话结束、交接、handoff、下次继续、暂停任务、换会话
argument-hint: ["交接当前任务", "写 handoff 工件", "下次会话继续"]
allowed-tools: read_file, grep, glob, write_file
---

# Session Handoff — 交接工件纪律

## 原则：工件 ≠ 总结
会话可能停在任务中途（限额/权限/超时/换工具）。**脆弱做法**：让下一个会话从对话摘要里猜状态。**可靠做法**：在工作旁边留一个小而经验证的交接工件。它不是版本控制/raw diff/日志的替代品——它是**指向这些记录的索引**，并声明它们证明了什么。

## 字段表（写 handoff 时逐项填）
| 字段 | 内容 | 为什么下一个执行者需要 |
|------|------|----------------------|
| objective | 期望结果 1-2 句 | 防止朝错误目标继续 |
| scope | 包含/排除的路径与动作 | 防止悄悄扩范围 |
| assumptions | 显式假设 + 验证状态（已证/未证） | 把证据与推断分开 |
| changed_files | 路径、状态、目的、验证状态 | 让审查面可枚举 |
| raw_diff | 位置、格式、摘要、捕获状态 | 保留可审查的文件级真相 |
| commands | **精确命令 + 目录 + 退出码 + 完整输出位置** | 区分"执行过"与"声称执行过" |
| failures | 错误类别、观察、影响、已尝试的响应 | 防止下一个会话盲目重走失败路径 |
| pending_approvals | 精确动作、原因、审批角色、状态 | "未授权"≠"未尝试" |
| stop_reason | 为什么停 | 判断从哪续 |
| next_safe_command | 下一条安全命令 | 接续起点 |
| completion_criteria | 怎么算完成 | 防止"差不多"式收尾 |

## 四条设计规则
1. **Self-identifying**：声明约定与 schema 版本
2. **Evidence-linked**：指向 patch/log 而非转述；大文件/敏感证据放单独文件，工件里只存位置+摘要
3. **Fail-closed**：未知状态、缺失证据、未授权审批 = 显式 blocker，不许含糊
4. **Privacy-minimized**：不含凭据/个人数据/不必要的 prompt 内容

## 两条防错（最常见的自欺）
- **"会话能恢复" ≠ "应该恢复"**：repo、权限、分支、secrets、需求可能已变——续接前先核对环境。
- **"工件校验通过" ≠ "任务正确"**：schema 验证证明形状与声明存在，不证明声明为真。

## 泳道纪律（换会话/换工具的时机）
Plan → Execute → Audit → Supervise 四泳道：planner 交**合同**（目标+范围+验收），executor 交**工件**（不是"状态感觉"），auditor 交回**具体 findings**（不是泛泛怀疑）。
- **换**：角色变更（planner→executor→reviewer）、需要更强审计边界、当前会话过旧过载
- **不换**：同 lane 还在深化、重载上下文成本 > 新工具收益、现有权限已就位、工作还是半成品
- **别因为分心换**——因为角色变了才换

## 本机落地（轻量版）
- 常规续接：`plans/current.md`（已完成/进行中/系统理解任务）即简版工件
- 中断/高风险场景：写 `plans/handoff-YYYY-MM-DD.json` 按上表字段；敏感证据单独文件
