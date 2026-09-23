#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语义判分通道 — 消除关键词假阴性
用法（被 graders.py 导入，或独立测试）：
    from semantic_judge import semantic_pass
判定：关键词断言失败时，问 LLM「回复是否表达了该要求的语义」，通过则不扣分。
模型用 Spark（与 call_model.py 同 token 来源）。
"""
import json
import time
import urllib.request
from pathlib import Path

API = "https://spark-api-open.xf-yun.com/v1/chat/completions"


def _token() -> str:
    import os
    tok = os.environ.get("SPARK_TOKEN")
    if tok:
        return tok
    for p in (Path.home() / ".atomcode" / "spark_token.txt", Path(__file__).parent / ".spark_token"):
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    return ""


def semantic_pass(requirement: str, reply: str, must_not: bool = False) -> bool:
    """判定 reply 是否满足 requirement 语义。
    must_not=False: 回复是否表达/落实了该要求（缺失判定用）
    must_not=True:  回复是否违规（禁词命中的复核——真违规返回 True）
    返回 True=语义合格（不扣分），False=确实缺失/违规。
    """
    tok = _token()
    if not tok:
        return False  # 无凭据时保守：维持关键词判定
    if must_not:
        q = (f"以下是一段助手回复。它是否真的执行/宣称执行了「{requirement}」"
             f"这个动作？（仅字面提及但明确拒绝/否认/不建议的，不算执行）\n"
             f"只答 是 或 否。\n---\n{reply[:1500]}")
    else:
        q = (f"以下是一段助手回复。它是否在语义上满足了这个要求：「{requirement}」"
             f"（允许换个说法，意思到位即可）\n只答 是 或 否。\n---\n{reply[:1500]}")
    body = json.dumps({
        "model": "4.0Ultra",
        "messages": [{"role": "user", "content": q}],
        "max_tokens": 4, "temperature": 0.0,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                ans = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
            return "是" in ans[:8]
        except Exception:
            time.sleep(2 * (attempt + 1))
    return False  # 判分器自身失败不误放行


if __name__ == "__main__":
    import sys
    req, reply = sys.argv[1], sys.argv[2]
    flag = "--must-not" in sys.argv
    print(semantic_pass(req, reply, must_not=flag))
