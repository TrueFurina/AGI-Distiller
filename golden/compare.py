#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Golden Test Set 报告对比工具
用法：python compare.py <旧报告.json> <新报告.json>
输出：总分差 / 分类分差 / 场景级回归与提升项定位
退出码：0=无回归，1=发现回归（可接入 CI 做门禁）
"""
import argparse
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        sys.exit(f"❌ 报告不存在: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description="对比两份 Golden 报告")
    ap.add_argument("old", help="旧报告 JSON")
    ap.add_argument("new", help="新报告 JSON")
    ap.add_argument("--threshold", type=float, default=0.0,
                    help="分类分差回归告警阈值（绝对值，默认 0 = 任何下降都算回归）")
    args = ap.parse_args()

    old, new = load(args.old), load(args.new)

    # ── 总分 ──
    dt = round(new["total"] - old["total"], 1)
    arrow = "📈" if dt > 0 else ("📉" if dt < 0 else "➡️")
    print(f"总分: {old['total']} → {new['total']}  {arrow} {dt:+.1f}")
    print(f"模型: {old.get('model', '?')} → {new.get('model', '?')}")
    print()

    # ── 分类分差 ──
    cats = sorted(set(old.get("by_category", {})) | set(new.get("by_category", {})))
    print("分类:")
    regressions = []
    for c in cats:
        o = old.get("by_category", {}).get(c)
        n = new.get("by_category", {}).get(c)
        if o is None or n is None:
            print(f"  {c}: {o} → {n}  ⚠️ 一侧缺失")
            continue
        d = round(n - o, 1)
        mark = "📈" if d > 0 else ("📉" if d < 0 else "➡️")
        print(f"  {c}: {o} → {n}  {mark} {d:+.1f}")
        if d < -args.threshold:
            regressions.append(("category", c, d))

    # ── 场景级定位 ──
    old_cases = {c["id"]: c for c in old.get("cases", [])}
    new_cases = {c["id"]: c for c in new.get("cases", [])}
    print("\n场景级变化:")
    improved, regressed, added, removed = [], [], [], []
    for cid in sorted(set(old_cases) | set(new_cases)):
        o, n = old_cases.get(cid), new_cases.get(cid)
        if o and n:
            os_, ns_ = o["score"] * o["weight"], n["score"] * n["weight"]
            if ns_ < os_:
                regressed.append(cid)
                detail = "; ".join(n.get("details", [])) or "（无详情）"
                print(f"  📉 {cid}: {o['score']}→{n['score']}  {detail}")
            elif ns_ > os_:
                improved.append(cid)
                print(f"  📈 {cid}: {o['score']}→{n['score']}")
        elif n and not o:
            added.append(cid)
            print(f"  ➕ {cid}: 新增场景")
        elif o and not n:
            removed.append(cid)
            print(f"  ➖ {cid}: 场景移除（未判）")
    if not (improved or regressed or added or removed):
        print("  （无变化）")

    # ── 缺失回复 ──
    for label, rep in (("新报告", new), ("旧报告", old)):
        miss = rep.get("missing", [])
        if miss:
            print(f"\n⚠️ {label}缺回复: {', '.join(miss)}")

    # ── 回归结论（CI 门禁语义）──
    print()
    if regressions:
        print(f"❌ 发现 {len(regressions)} 个分类回归 + {len(regressed)} 个场景回归 → 退出码 1")
        sys.exit(1)
    if regressed:
        print(f"⚠️ 分类未回归但 {len(regressed)} 个场景退步: {', '.join(regressed)}")
        sys.exit(0)
    print("✅ 无回归")


if __name__ == "__main__":
    main()