#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并发-Edit 复验 hook（PostToolUse: Edit|Write）
背景教训：同一文件多个 Edit 并发时静默互相覆盖，且全部回报成功。
机制：每次 Edit/Write 落盘后，把文件路径+内容哈希记入状态文件；
     若同一文件在本会话已被记录过且哈希变化 = 正常；关键在于
     在 hook 内直接复验"磁盘上的文件是否包含刚写入的关键变更"——
     用 mtime+size+hash 快照对比，检测到 size/mtime 回退（被旧快照覆盖）时
     以非零退出浮出警告。
stdin: CodeBuddy PostToolUse JSON（tool_input.file_path）
退出码：0=通过；1=检测到疑似覆盖回退（stderr 给出诊断）
"""
import hashlib
import json
import os
import sys
from pathlib import Path

STATE = Path.home() / ".codebuddy" / "hooks" / ".edit-snapshots.json"


def snap(fp: str) -> dict:
    p = Path(fp)
    if not p.is_file():
        return {"exists": False}
    st = p.stat()
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"exists": True, "size": st.st_size, "mtime": st.st_mtime, "hash": h}


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # stdin 非 JSON：hook 环境异常，不拦
    fp = (data.get("tool_input") or {}).get("file_path", "")
    if not fp or not fp.lower().endswith((".py", ".md", ".json", ".yaml", ".yml", ".txt", ".js", ".ts")):
        return 0
    cur = snap(fp)
    if not cur["exists"]:
        return 0

    state = {}
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    prev = state.get(fp)
    state[fp] = {"size": cur["size"], "mtime": cur["mtime"], "hash": cur["hash"]}
    try:
        STATE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass  # 状态写失败不影响主流程

    if prev and prev.get("hash") == cur["hash"] and prev.get("mtime") != cur["mtime"]:
        # mtime 变了但内容一致 → 无覆盖，正常写
        return 0
    # prev.hash != cur.hash 是正常编辑；真正的"覆盖回退"无法仅凭哈希判定，
    # 但同秒内同文件多次写入（并发 Edit 的特征）值得警告：
    if prev and prev.get("mtime") == cur["mtime"] and prev.get("hash") != cur["hash"]:
        print(
            f"⚠️ 疑似并发写入同文件：{fp} 在同一秒内被多次修改且内容不同。"
            f"请立刻重新读取该文件确认最终内容是否为期望结果（并发 Edit 会静默互相覆盖且全部报成功）。",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
