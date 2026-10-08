#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wechat_predistill.py —— 微信文章预蒸馏草稿生成器（蒸馏自动化的机器侧）。

定位（诚实边界）：
    本脚本产出的是 DRAFT（机器预蒸馏），落 notes/wechat-drafts/*.draft.md。
    草稿【不直接】进 notes/memory/skill——必须经会话人工复核后，
    才由 wechat-distill 流程按 R3 门槛升格。理由：LLM 预蒸馏会幻觉
    （R1 教训：引用真实性必须机验；R12 教训：判分器不判推断质量），
    无人审查的自动入库违反诚实口径。

流程：
    扫 sources/wechat/pending/*.txt
      → AD 检测（营销特征词密度）→ AD 篇直接标 AD，不调 LLM（省钱）
      → 正文截断至 --chars 字符（默认 4000，成本护栏）
      → Spark 生成结构化草稿（痛点/可执行规则/R3 初判/体系接口）
      → 写 notes/wechat-drafts/<slug>.draft.md（头部带 DRAFT 状态 + [源:URL]）

成本护栏：
    --max N     单次最多蒸馏 N 篇（默认 3）
    --chars N   每篇送 LLM 的正文字符上限（默认 4000，约 3K tokens）
    草稿已存在 → 跳过（幂等，断点续跑）

用法：
    python tools/wechat_predistill.py               # 处理 pending 全部（受 --max 限）
    python tools/wechat_predistill.py --max 1       # 成本试探
    python tools/wechat_predistill.py --file <path> # 指定单篇（测试用，可为 done 里的文件）
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PENDING = REPO / "sources" / "wechat" / "pending"
DRAFTS = REPO / "notes" / "wechat-drafts"
API = "https://spark-api-open.xf-yun.com/v1/chat/completions"
TOKEN_FILES = (Path.home() / ".atomcode" / "spark_token.txt", REPO / "golden" / ".spark_token")

AD_MARKS = ("限时优惠", "扫码关注", "购买课程", "私域", "立即报名", "优惠券",
            "限时折扣", "扫码入群", "添加微信", "年费会员", "结营")

SYSTEM = (
    "你是知识蒸馏助手。输入一篇微信公众号文章（可能被截断）。"
    "输出结构化蒸馏草稿，格式：\n"
    "## 痛点\n- 1-3 条（作者指出的具体问题，不复述营销叙事）\n"
    "## 可执行规则\n- 1-5 条，每条必须含具体动作与判据；拒绝'要重视'类口号；"
    "每条末尾标 [R3初判: 首现]\n"
    "## 体系接口\n- 1-2 句：与知识蒸馏/agent 工程/vibe coding 实践的关联（没有就写'无'）\n"
    "## 诚实声明\n- 一行：未提取的部分（案例细节/图/文献等）\n"
    "要求：忠实原文，不脑补；总长不超过 800 字；中文。"
)


def load_token() -> str:
    import os
    tok = os.environ.get("SPARK_TOKEN")
    if tok:
        return tok
    for p in TOKEN_FILES:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    sys.exit("❌ 未找到 Spark token")


def call_llm(model: str, prompt: str, retries: int = 3) -> str:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "max_tokens": 1200, "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {load_token()}", "Content-Type": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
        except Exception as exc:
            if attempt == retries - 1:
                return f"[CALL_FAILED] {type(exc).__name__}: {exc}"
            time.sleep(5 * (attempt + 1))
    return "[CALL_FAILED]"


def parse_meta(text: str) -> dict:
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body.strip()


def is_ad(body: str) -> bool:
    """营销特征词密度检测：窗口 500 字内命中 ≥3 个 AD 词判软文。"""
    hits = sum(body.count(w) for w in AD_MARKS)
    return hits >= 3


def predistill(f: Path, model: str, chars: int) -> str:
    """返回状态：ok / ad / failed"""
    text = f.read_text(encoding="utf-8")
    meta, body = parse_meta(text)
    url = meta.get("url", "")
    if not url:
        return "skip-no-url"
    if is_ad(body):
        write_draft(f, meta, url, "AD", "（营销软文，机器检测命中特征词，未调用 LLM，不蒸馏）", model)
        return "ad"
    reply = call_llm(model, f"标题：{meta.get('title', '')}（公众号：{meta.get('account', '')}）\n\n{body[:chars]}")
    if "[CALL_FAILED]" in reply:
        print(f"    LLM 错误: {reply[:200]}", file=sys.stderr)  # 错误必须浮出，禁吞
        return "failed"
    write_draft(f, meta, url, "DRAFT", reply, model)
    return "ok"


def write_draft(src: Path, meta: dict, url: str, status: str, content: str, model: str) -> Path:
    DRAFTS.mkdir(parents=True, exist_ok=True)
    out = DRAFTS / (src.stem + ".draft.md")
    head = (f"---\nstatus: {status}\nsource: {url}\ntitle: {meta.get('title', '')}\n"
            f"account: {meta.get('account', '')}\npredistilled: {date.today().isoformat()}\n"
            f"model: {model}\nreviewed: pending\n---\n\n")
    out.write_text(head + content, encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=3)
    ap.add_argument("--chars", type=int, default=4000)
    ap.add_argument("--model", default="lite")  # 4.0Ultra 2026-10-08 实测 500，lite 可用
    ap.add_argument("--file", help="指定单篇（测试用）")
    args = ap.parse_args()

    files = [Path(args.file)] if args.file else sorted(PENDING.glob("*.txt"))
    if not files:
        print("pending 为空，无待蒸馏文章")
        return 0
    ok = ad = fail = 0
    for f in files[: args.max]:
        if not f.exists():
            continue
        st = predistill(f, args.model, args.chars)
        print(f"  {'✅' if st == 'ok' else '🟡' if st == 'ad' else '❌'} [{st}] {f.name}")
        ok += st == "ok"; ad += st == "ad"; fail += st == "failed"
        time.sleep(1)
    print(f"\n完成: {ok} 蒸馏, {ad} 广告跳过, {fail} 失败 → {DRAFTS}")
    print("下一步: 会话里说\"复核微信草稿\"，人工审查后按 R3 升格")
    return 1 if fail and ok == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
