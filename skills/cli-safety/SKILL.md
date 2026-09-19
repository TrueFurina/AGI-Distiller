---
name: cli-safety
description: CLI 安全执行规则 — Agent 通过 bash 调用命令行工具时的 5 条安全规则：优先结构化输出、验证退出码、避免交互弹窗、幂等与 dry-run、输出可审计。附 2026 CLI 生态陷阱清单。触发词：cli、命令行、bash 安全、执行命令、退出码、dry-run、非交互
argument-hint: ["这个命令怎么安全执行", "bash 执行规则", "CLI 陷阱", "退出码验证"]
allowed-tools: bash, read_file, grep, glob
---

# CLI 安全执行规则

> 来源：卡码大模型《为什么 Agent 时代大家都在做 CLI》
> 核心洞见：今天很多 CLI 默认操作者是人，失败返回 0、输出彩色进度条、弹交互确认——这些对 Agent 是陷阱。

---

## 5 条规则

### 规则 1：优先结构化输出

```bash
# ❌ 从花哨日志里猜字段
npm outdated

# ✅ 优先 --json 或稳定格式
npm outdated --json
```

- 优先 `--json`、`--format=json`、`-o json`
- 不支持 JSON 时用 `grep`/`awk` 提取关键行，而非全量日志
- 避免输出彩色 ANSI 码、进度条、spinner 的命令

### 规则 2：验证退出码，不只看 stdout

```bash
command; echo "EXIT_CODE=$?"
```

- **失败返回 0 的工具是陷阱**，必须额外解析 stderr 印证
- 不确定退出码是否可靠时，加验证命令（如 `test -f` 检查产物）
- 不要把 stdout 为空当作失败判断的唯一依据

### 规则 3：避免交互弹窗

```bash
# ❌ 可能弹 Y/n 或密码框
git push

# ✅ 非交互模式
git push --no-verify
```

- 优先 `-y`、`--yes`、`--non-interactive`、`--no-verify`
- git 操作前先确认凭据可用，不弹密码框
- 可能耗时过长的命令设置 timeout

### 规则 4：优先幂等和 dry-run

```bash
# ❌ 直接执行无回退
rm -rf dist/

# ✅ 先 dry-run 或先确认目标存在
if [ -d "dist/" ]; then rm -rf dist/; fi
```

- 优先 `--dry-run`、`--check`、`--diff` 预演
- 删除/覆盖前先检查目标是否存在
- 数据库迁移、文件删除、配置覆盖必须先说明影响

### 规则 5：输出可审计

```bash
echo "[$(date)] EXEC: git push origin main" >> ~/.atomcode/audit.log
```

- 关键操作（git push、删除文件、数据库变更）记录审计日志
- 审计日志含：时间、命令、工作目录、退出码、关键输出摘要
- 高风险操作（凭据读写、生产服务）必须审批

---

## 2026 CLI 生态已知陷阱清单

| 陷阱 | 现象 | 应对 |
|------|------|------|
| 退出码虚假 | 失败返回 0 | 额外检查 stderr 或产物 |
| 交互弹窗 | 卡在 Y/n 或密码框 | 加 `-y` / `--non-interactive` |
| 彩色输出 | ANSI 码污染 stdout | 用 `--no-color` 或 `grep -a` |
| 进度条 | 持续输出 `\r` 覆盖行 | 用 `--progress=false` |
| 无 dry-run | 无法预演 | 先在隔离环境测试 |
| 凭据残留 | 密码写入 .git/config | 用环境变量或临时凭据 |

---

## 落盘判成功原则（补充，来自企业微信 94% 实践）

> 任何"长跑命令"都不靠 stdout 报告成功，全靠**落盘文件**判定。

```bash
# ❌ 靠 stdout 判断
python gen.py 2>&1 | tail -5   # 输出可能被缓冲吞掉

# ✅ 落盘 + sentinel 文件判定
python gen.py > out.log 2>&1
test -f result.json && echo "SUCCESS" || echo "FAIL"
```

- 长任务、生成器、批量脚本：写结果到文件，用 `test -f` / 检查文件内容判定成功
- 过滤命令（`| grep -v`）会吞掉失败行，得出"全绿"假结论
- 判据：落盘产物存在 + 内容正确，而非命令输出
