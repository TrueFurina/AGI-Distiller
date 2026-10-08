#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wechat_poller.py —— 自动发现→自动抓取的轮询器（管道第 -0.5 步）。

对接 we-mp-rss 桥接服务（http://127.0.0.1:8001，需用户微信扫码授权订阅）：
    服务后台定时同步订阅号 → 本轮询器读 /rss 全量源
    → 提取文章直链 → 去重（对比 pending/ done/ 已存 URL）
    → 新文章交给 fetch_wechat.py 抓正文 → 落 pending/（蒸馏队列）

模式：
    python tools/wechat_poller.py            # 单次轮询（计划任务用）
    python tools/wechat_poller.py --loop     # 常驻循环，每 6h 轮询一次
退出码：0=正常（含无新文章）；1=服务不可达/异常
"""
import re
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "sources" / "wechat"
PENDING, DONE = BASE / "pending", BASE / "done"
LOG = BASE / "poller.log"
RSS_URL = "http://127.0.0.1:8001/feed/all.xml"  # 聚合 feed（含精选文章直链）；主 /rss 只有订阅号占位条目
LINK_RE = re.compile(r"https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_\-]+")


def log(msg: str):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    BASE.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def known_urls() -> set:
    """已抓取过的 URL（pending+done 的 meta 头）——去重依据。"""
    seen = set()
    for d in (PENDING, DONE):
        for f in d.glob("*.txt"):
            m = re.search(r"^url: (\S+)", f.read_text(encoding="utf-8")[:400], re.M)
            if m:
                seen.add(m.group(1))
    return seen


def poll_once() -> int:
    try:
        with urllib.request.urlopen(RSS_URL, timeout=15) as r:
            xml = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"❌ 服务不可达: {type(e).__name__}: {e}")
        return 1
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        log(f"❌ RSS 解析失败: {e}")
        return 1
    links = [el.text.strip() for el in root.iter("link") if el.text and LINK_RE.match(el.text.strip())]
    seen = known_urls()
    fresh = [u for u in links if u not in seen]
    log(f"RSS 条目 {len(links)}，新文章 {len(fresh)}")
    if not fresh:
        return 0
    r = subprocess.run([sys.executable, str(REPO / "tools" / "fetch_wechat.py"), *fresh],
                       capture_output=True, text=True, timeout=300)
    log(f"抓取完成: {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'no output'}")
    return 0


def main():
    if "--loop" in sys.argv:
        log("轮询器启动（loop 模式，间隔 6h）")
        while True:
            poll_once()
            time.sleep(6 * 3600)
    rc = poll_once()
    sys.exit(rc)


if __name__ == "__main__":
    main()
