#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden 跑分：逐场景调用真实模型生成回复（落盘 replies/<case_id>.txt）
用法：python call_model.py --model 4.0Ultra --out replies-spark40/
成本控制：每场景单轮短调用，max_tokens=500；预计 41 次 × <1K tokens。
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

API = "https://spark-api-open.xf-yun.com/v1/chat/completions"


def _load_token() -> str:
    """凭据来源：环境变量 SPARK_TOKEN 优先，其次本地 secrets 文件（gitignored，不入库）。"""
    import os
    tok = os.environ.get("SPARK_TOKEN")
    if tok:
        return tok
    for p in (Path.home() / ".atomcode" / "spark_token.txt", Path(__file__).parent / ".spark_token"):
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    sys.exit("❌ 未找到 Spark token：设 SPARK_TOKEN 环境变量或写入 ~/.atomcode/spark_token.txt")


TOKEN = _load_token()

# 被测 persona：裸模型（不带我们的规则），测基线
SYSTEM = "你是一个编码助手。直接回答用户的问题或按指令执行。"


def call(model: str, prompt: str, retries: int = 3) -> str:
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 500,
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            if attempt == retries - 1:
                return f"[CALL_FAILED] {exc}"
            time.sleep(3 * (attempt + 1))
    return "[CALL_FAILED]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="golden/cases")
    ap.add_argument("--model", default="4.0Ultra")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="*", help="只跑指定 case_id")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    import yaml
    cases = sorted(Path(args.cases).glob("*.yaml"))
    done, fail = 0, 0
    for i, cf in enumerate(cases, 1):
        case = yaml.safe_load(cf.read_text(encoding="utf-8"))
        cid = case["id"]
        if args.only and cid not in args.only:
            continue
        rf = out / f"{cid}.txt"
        if rf.exists() and "[CALL_FAILED]" not in rf.read_text(encoding="utf-8"):
            done += 1
            continue
        reply = call(args.model, case["prompt"])
        rf.write_text(reply, encoding="utf-8")
        if "[CALL_FAILED]" in reply:
            fail += 1
            print(f"  ❌ [{i}/{len(cases)}] {cid}")
        else:
            done += 1
            print(f"  ✅ [{i}/{len(cases)}] {cid}")
        time.sleep(1)  # 限速保护

    print(f"\n完成: {done} 成功, {fail} 失败 → {out}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()