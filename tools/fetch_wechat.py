#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_wechat.py —— 微信公众号推文抓取器（蒸馏管道第 0 步，纯标准库零依赖）。

## 管道架构（第九轮后新增的持续知识源）

    用户丢链接（微信转发/粘贴，可混在文本里自动提取）
        ↓
    [本脚本] fetch_wechat.py <url|文本文件>     ← 确定性抓取，无需 LLM
        直取 mp.weixin.qq.com（UA 伪装）
        验证码页检测（wappoc_appmsgcaptcha 特征）→ 重试 1 次 → 仍失败标记 FAILED
        提取标题 + 正文（js_content 区去标签）
        落盘 sources/wechat/pending/YYYY-MM-DD-<slug>.txt（带 meta 头）
        ↓
    [蒸馏会话] 一句话："蒸馏 pending 里的微信文章"（skill: wechat-distill）
        按蒸馏笔记格式（痛点/解法/可执行规则/陷阱）提炼
        R3 门槛裁决：首现→notes；第 2 次复现→memory；≥2 独立来源→skill
        移 pending → done/，追加 digest 行
        ↓
    [定时化]（P1，两条路可选）
        a) WorkBuddy 自动化任务：每日 09:30 读 pending/ 蒸馏（需用户 UI 挂载）
        b) Windows 计划任务：schtasks 每日跑本脚本批量抓取，攒着等会话蒸馏
        ↓
    [P2 自动发现]（诚实局限）
        公众号列表监控需桥接服务（wewe-rss / wechat2rss，需登录态），
        且微信反爬实测约 1/3 概率触发验证码——全自动发现可靠性打折。
        最可靠的"发现"来源仍是用户随手转发链接进 pending。

## 实测数据（2026-09-26）
    3 篇样本：2 篇直取成功（7.4k / 9.8k 字符全文），1 篇 302 到验证码页。
    结论：单篇成功率约 2/3，重试可提高；批量抓取必须容忍失败并显式报告。

## 用法
    python tools/fetch_wechat.py https://mp.weixin.qq.com/s/xxx          # 单篇
    python tools/fetch_wechat.py links.txt                               # 批量（每行一个 URL，# 注释）
    python tools/fetch_wechat.py --status                                # 查看 pending/done 状态
"""
import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "sources" / "wechat"
PENDING = BASE / "pending"
DONE = BASE / "done"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
CAPTCHA_MARKS = ("wappoc_appmsgcaptcha", "环境异常", "完成验证")
URL_RE = re.compile(r"https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_\-]+")


def fetch(url: str) -> tuple[str, str]:
    """返回 (状态, 正文或诊断)。状态: ok / captcha / error"""
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                page = resp.read().decode("utf-8", errors="replace")
            if any(m in page for m in CAPTCHA_MARKS) and "js_content" not in page:
                if attempt == 1:
                    continue
                return "captcha", "触发微信验证码（反爬），稍后重试或换网络出口"
            return "ok", page
        except Exception as e:
            if attempt == 2:
                return "error", f"{type(e).__name__}: {e}"
    return "error", "unreachable"


def extract(page: str) -> dict:
    """从微信 HTML 提取 标题/公众号名/正文纯文本。"""
    def _re(pat, default=""):
        m = re.search(pat, page)
        return html.unescape(m.group(1)).strip() if m else default
    title = _re(r'(?s)<h1[^>]*?id="activity-name"[^>]*>(.*?)</h1>') or _re(r"(?s)<title>(.*?)</title>")
    title = html.unescape(re.sub(r"<[^>]+>", "", title))  # 剥离内层标签（js_title_inner span 等）
    title = re.sub(r"\s+", " ", title).strip()
    account = html.unescape(re.sub(r"<[^>]+>", "", _re(r'(?s)<a[^>]*?id="js_name"[^>]*>(.*?)</a>'))).strip()
    m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*<script', page, re.S)
    body_html = m.group(1) if m else ""
    # 去标签 → 纯文本（保留段落换行）
    text = re.sub(r"<(br|/p|/section|/li)[^>]*>", "\n", body_html)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return {"title": title, "account": account, "text": text, "chars": len(text)}


def slugify(title: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title)[:40].strip("-")
    return s or "untitled"


def save(url: str, status: str, meta: dict) -> Path:
    PENDING.mkdir(parents=True, exist_ok=True)
    fname = f"{date.today().isoformat()}-{slugify(meta.get('title') or url)}.txt"
    f = PENDING / fname
    head = (f"---\nurl: {url}\nfetched: {date.today().isoformat()}\n"
            f"status: {status}\ntitle: {meta.get('title', '')}\n"
            f"account: {meta.get('account', '')}\nchars: {meta.get('chars', 0)}\n---\n\n")
    f.write_text(head + meta.get("text", meta.get("error", "")), encoding="utf-8")
    return f


def cmd_fetch(args: list[str]) -> int:
    urls: list[str] = []
    for a in args:
        if Path(a).is_file():
            urls += [u for u in URL_RE.findall(Path(a).read_text(encoding="utf-8"))]
        else:
            urls += URL_RE.findall(a) or [a]
    if not urls:
        print("未发现微信公众号链接"); return 2
    ok = fail = 0
    for u in dict.fromkeys(urls):
        status, payload = fetch(u)
        meta = extract(payload) if status == "ok" else {"title": "", "account": "", "text": "", "chars": 0, "error": payload}
        if status == "ok" and meta["chars"] < 200:
            status, meta = "error", {**meta, "error": "正文提取过短（页面结构变化或反爬）"}
        f = save(u, status, meta)
        tag = "✅" if status == "ok" else "❌"
        print(f"{tag} [{status}] {meta.get('title') or u} → {f.name} ({meta.get('chars', 0)} 字)")
        ok += status == "ok"; fail += status != "ok"
    print(f"\n完成: {ok} 成功, {fail} 失败 → {PENDING}")
    print("下一步: 蒸馏 pending 里的文章（skill: wechat-distill）")
    return 0 if fail == 0 else 1


def cmd_status() -> int:
    for d, label in ((PENDING, "pending（待蒸馏）"), (DONE, "done（已蒸馏）")):
        files = sorted(d.glob("*.txt")) if d.exists() else []
        print(f"{label}: {len(files)}")
        for f in files:
            print(f"  {f.name}")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); return 0
    if args[0] == "--status":
        return cmd_status()
    return cmd_fetch(args)


if __name__ == "__main__":
    sys.exit(main())
