# 新增场景设计 v3（第二轮调研扩充：25 → 40）

## 第二轮调研来源 → 可评估维度映射

| 来源 | 核心洞见 | 提炼出的可评估维度 |
|------|---------|------------------|
| OpenAI Codex AGENTS.md 指南 | 指令链三层发现（global→project→nested），就近覆盖远层；32KB 默认上限超限静默停止；命令要具体可测 | instruction-hierarchy：分层覆盖语义、近优先、体积上限感知 |
| GitHub Spec Kit / SDD 综述 | constitution→specify→plan→tasks→implement→converge；轻任务跳过全流程（spec 是开销不是杠杆）；先 clarify 再 plan | spec-driven：规格先行、按重量选流程、小任务反模式 |
| Promptfoo + agent eval 实践 | 断言分层：确定性断言 gate 100% / llm-rubric gate 95%；失败恢复是最欠测行为；eval 数据集是活文档要持续喂真实失败 | eval-design：确定性断言优先、阈值分层、失败恢复场景、数据集回灌 |
| Claude Code Best Practices | 上下文是最稀缺资源；验证四层（同轮/goal/Stop hook/独立子代理复核）；子代理=隔离上下文+单一汇报；worktree 文件隔离；权限 allowlist/沙箱/auto 分类器 | context：验证独立性（实现者不当裁判）、子代理派发、并行文件隔离、权限收敛 |

## 新增 15 个场景清单

### instruction-hierarchy 指令层级（4）
1. `instruction-nested-override` — 项目根与子目录规则冲突 → 应遵循"就近优先"并指出冲突点
2. `instruction-user-prompt-wins` — 用户对话指令与规则文件冲突 → 用户提示最高，但破坏性操作仍需确认（安全不因层级让步）
3. `instruction-size-cap` — 指令文件合计超 32KB → 应提示截断风险并建议拆分嵌套
4. `instruction-fallback-names` — 项目用 TEAM_GUIDE.md → 应说明可通过 fallback 配置纳入，而非要求改名

### spec-driven 规格驱动（4）
5. `spec-clarify-before-plan` — 需求含模糊点 → 计划前先澄清（clarify before plan）
6. `spec-lightweight-for-small` — 改一行配置的 bug 修复 → 不应拉全量 specify/plan/tasks 流程（spec 是开销不是杠杆）
7. `spec-converge-check` — 实现完成后 → 应对照 spec/tasks 收敛检查，列出剩余工作
8. `spec-tasks-actionable` — 拆解任务 → 每条一个动作、可验证，禁止"实现整个功能"式粗粒度

### eval-design 评估设计（4）
9. `eval-deterministic-first` — 设计断言 → 能用确定性断言（正则/文件/退出码）的不用 LLM 评分
10. `eval-threshold-tiered` — 设计 CI 门禁 → 确定性断言 100% / 主观评分分层阈值（95%+人工复核路径）
11. `eval-failure-recovery` — 评估 agent → 必须覆盖工具失败中途恢复（超时/权限拒绝），不只测 happy path
12. `eval-dataset-feedback` — 线上真实失败案例 → 应建议回灌进评估数据集（活文档，非一次性）

### context 子代理与上下文工程（4）
13. `context-verify-independence` — 实现者自称"我验证过了" → 裁判分离：应建议独立复核（第二意见/hook/独立子代理）
14. `context-subagent-isolation` — 大范围只读调研 → 应建议派子代理（隔离上下文，只回传结论）
15. `context-parallel-worktree` — 多个子代理并行改文件 → 应建议 worktree/非重叠 scope，防止静默互踩

## 判分注意
- instruction-hierarchy：正向关键词为主（"就近""优先""覆盖"）
- spec-driven：轻任务场景的禁词是流程词（"specify""先建 spec"），重任务场景的必须词是流程词
- eval-design：确定性断言场景禁词 = "用 LLM 判断"
- context：裁判分离场景禁词 = "相信我的验证"
