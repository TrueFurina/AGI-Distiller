# TOOLS.md — Tool Usage Guide / 工具使用指南

## Core Tools / 核心工具

| Tool / 工具 | Purpose / 用途 | Level / 级别 |
|------------|---------------|-------------|
| read_file / grep / glob | File read & search / 文件读取搜索 | Read-only / 只读 |
| list_directory | List directory tree / 列目录树 | Read-only / 只读 |
| list_symbols / read_symbol | Code structure analysis / 代码结构分析 | Read-only / 只读 |
| trace_callers / trace_callees | Call chain tracing / 调用链追踪 | Read-only / 只读 |
| web_fetch / web_search | Web access / 网络获取 | Read-only / 只读 |
| edit_file / write_file | File writing / 文件写入 | Reviewable / 审查 |
| memory | Persistent memory / 持久化记忆 | Write / 写入 |
| bash | System command execution / 系统命令执行 | High-risk / 高风险 |

## Principles / 使用原则

1. Use dedicated tools before bash — read_file over cat, grep over rg / 能用专用工具就不用 bash
2. Before bash: check --json, --no-color, -y, --dry-run / bash 执行前检查结构化输出、去花哨、防交互、预演
3. High-risk ops (delete, credentials, production) need user confirmation / 高风险操作必须用户确认
4. Critical ops (git push, delete, DB change) log audit trail / 关键操作记录审计日志

## Distillation Pipeline / 蒸馏管道专用

| Stage / 阶段 | Tool / 工具 | Output / 产出 |
|-------------|------------|--------------|
| Fetch article / 获取文章 | web_fetch | Raw content / 原始内容 |
| Extract pain points / 提取痛点 | read_file + AI | Extraction record / 提取记录 |
| Precipitate rules / 沉淀规则 | edit_file | ATOMCODE.md update / 更新 |
| Package skill / 封装 skill | write_file | SKILL.md |
| Persist knowledge / 持久化 | memory | Cross-session memory / 跨会话记忆 |