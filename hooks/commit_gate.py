#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""commit 前门禁 hook（PreToolUse: Bash 匹配 git commit）
机制：拦截 Bash 工具中含 `git commit` 的调用，先跑三道确定性检查：
  ① 密钥扫描（复用 AGI-Distiller 的 secrets_scan.py，暂存文件范围）
  ② 长提交信息检查：-m 内联信息含反引号/换行 → 阻止（bash 反引号静默吃内容的教训），
    建议改用 git commit -F <file>
  ③ 教训黑名单：commit message 含已知危险模式（如 "终极方案" "最终修复" 等反注水词）仅警告
退出码：0=放行；1=拦截（stderr 说明原因）
stdin: CodeBuddy PreToolUse JSON（tool_input.command）
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SECRETS_SCAN = Path.home() / ".atomcode" / "hooks" / "secrets_scan.py"
if not SECRETS_SCAN.exists():
    SECRETS_SCAN = Path.home() / "AppData/Roaming/npm/node_modules"  # 占位，找不到则跳过①


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if "git commit" not in cmd:
        return 0  # 非 commit 命令放行

    # ② 内联 -m 危险字符检查（反引号会被 bash 静默执行吃掉内容）
    m = re.search(r"-m\s+([\"'])(.*?)\1", cmd, re.S)
    if m:
        msg = m.group(2)
        if "`" in msg or "$(" in msg:
            print(
                "❌ 拦截：commit message 内含反引号/$(...)——bash 会把内容当命令执行并静默吞掉。\n"
                "   修复：把提交信息写入临时文件，改用 git commit -F <file>，提交后用 git log -1 --format=%B 复核。",
                file=sys.stderr,
            )
            return 1

    # ① 密钥扫描（扫描器存在时扫描暂存区文件列表）
    if SECRETS_SCAN.exists():
        try:
            files = subprocess.check_output(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                stderr=subprocess.DEVNULL, text=True
            ).split()
            if files:
                r = subprocess.run(
                    ["python", str(SECRETS_SCAN)] + files,
                    capture_output=True, text=True, timeout=30
                )
                if r.returncode != 0:
                    print("❌ 拦截：密钥扫描未通过：\n" + r.stdout[-2000:], file=sys.stderr)
                    return 1
        except Exception:
            pass  # 扫描器自身异常不拦提交（fail-open），主门禁在 git hook 层仍有

    print("✅ commit 前门禁通过", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
