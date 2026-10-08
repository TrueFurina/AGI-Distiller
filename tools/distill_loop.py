#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""distill_loop.py —— 微信蒸馏每日循环（蒸馏环节自动化的常驻侧）。

每日 09:30 后首次唤醒时执行一轮（幂等，重复执行安全）：
    1. poller：we-mp-rss RSS → 新文章 → fetch_wechat → pending/
    2. predistill：pending → Spark 预蒸馏草稿 → notes/wechat-drafts/（DRAFT 状态）

调度：循环 sleep 到下一个 09:30（已跑过当天则跳到明天）。
启动方式：explorer 启动（脱离 bash 进程树，实测可存活）+ startup 快捷方式（登录自启）。
日志：sources/wechat/distill_loop.log

诚实边界：产出仅为 DRAFT，人工复核后才入库（见 wechat_predistill.py 自述）。
用法：python tools/distill_loop.py          # 常驻
      python tools/distill_loop.py --once   # 单次立即执行（测试用）
"""
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "sources" / "wechat" / "distill_loop.log"
RUN_HOUR = 9
RUN_MIN = 30


def log(msg: str):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_step(name: str, script: str, *args: str) -> bool:
    r = subprocess.run([sys.executable, str(REPO / "tools" / script), *args],
                       capture_output=True, text=True, timeout=600,
                       cwd=str(REPO))
    tail = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
    log(f"  {'✅' if r.returncode == 0 else '❌'} {name}: {tail[:120]}")
    return r.returncode == 0


def daily_run():
    log("=== 每日蒸馏流程开始 ===")
    run_step("poller 抓新文章", "wechat_poller.py")
    run_step("predistill 预蒸馏", "wechat_predistill.py", "--max", "3")
    log("=== 每日蒸馏流程结束 ===")


def next_run_time() -> datetime:
    now = datetime.now()
    target = now.replace(hour=RUN_HOUR, minute=RUN_MIN, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def main():
    once = "--once" in sys.argv
    if once:
        daily_run()
        return
    log(f"蒸馏循环启动（每日 {RUN_HOUR:02d}:{RUN_MIN:02d}）")
    while True:
        nxt = next_run_time()
        wait = (nxt - datetime.now()).total_seconds()
        log(f"下次执行: {nxt.isoformat(timespec='seconds')}（{wait/3600:.1f}h 后）")
        time.sleep(min(wait, 3600))  # 每小时醒一次，防止长 sleep 期间系统休眠漂移
        if datetime.now() >= nxt:
            daily_run()


if __name__ == "__main__":
    main()
