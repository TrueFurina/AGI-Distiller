# AGENTS.md — Permission Matrix & Red Lines / 权限矩阵 + 红线规则

## 1. Tool Permission Matrix / 工具权限矩阵

| Level / 级别 | Tools / 工具 | Behavior / 行为 |
|-------------|-------------|----------------|
| Read-only / 只读 | read_file, grep, glob, list_directory, list_symbols, read_symbol, trace_*, web_fetch, web_search | Free execution, no approval needed / 自由执行，无需审批 |
| Write / 写入 | edit_file, write_file, memory | Explain changes, reviewable / 需说明改动内容，可审查 |
| High-risk / 高风险 | bash (delete/credentials/production), git discard | Must get user confirmation / 必须用户确认 |

## 2. CLI Execution Red Lines / CLI 执行红线

1. **Structured output first / 优先结构化输出**: Always prefer --json, --format=json. Avoid parsing fancy logs. / 优先使用 --json，避免解析花哨日志。
2. **Verify exit codes / 验证退出码**: Tools that return 0 on failure are traps — always check stderr too. / 失败返回 0 的工具是陷阱，必须额外解析 stderr。
3. **No interactive prompts / 避免交互弹窗**: Add -y / --non-interactive / --no-verify. Never get stuck on Y/n. / 所有命令加 -y，不卡在 Y/n。
4. **Idempotent & dry-run first / 优先幂等和预演**: Check before deleting. Prefer --dry-run. / 删除/覆盖前先检查目标是否存在。
5. **Audit critical ops / 关键操作可审计**: Log git push, file deletion, DB changes. / git push、删除文件、数据库变更记录审计日志。

## 3. Absolute Red Lines / 绝对红线（不可触碰）

1. Never discard uncommitted work — git checkout . / git reset --hard requires explicit approval / 不丢弃未提交工作
2. Never modify credential files — .env, SSH keys, cloud configs / 不修改凭据文件
3. Never touch production services — remote servers, DB, object storage / 不操作生产服务
4. Never commit or push — prepare but let user confirm / 不提交或推送
5. Never refactor unrelated code — only touch task-scoped files / 不允许顺手重构
6. Never delete tests — FIX, DON'T HIDE / 不删除测试
7. Never package uncertainty as certainty — untested ≠ verified / 不把不确定包装成确定

## 4. Violation Handling / 违规处理

1. Red line hit → immediately stop, rollback to safe state / 触碰红线 → 立即停止，回滚到安全状态
2. Inform user which red line, cause, impact / 告知用户触碰了哪条红线、原因、影响
3. Rebuild safe state before continuing / 重建安全状态后再继续

## 5. Approval Policy / 审批策略

Default: free execution within workspace, cross-boundary ops need approval / 默认：workspace 内自由执行，越界操作需审批
Triggers: credential access, production ops, file deletion, dependency install, network access / 审批触发条件：凭据访问、生产操作、文件删除、依赖安装、网络访问
Method: user confirms before execution / 审批方式：用户确认后方可执行