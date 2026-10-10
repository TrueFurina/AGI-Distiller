#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wechat_queue.py —— 微信公众号队列的三态盘点（G4 的机验实现）。

为什么需要它
------------
`skills/wechat-distill/SKILL.md` 的质量门表里写着 G1–G4，并标了 `[实测]`。
其中 **G4 = done/ 与 notes 索引一致（无蒸了没记、记了没移）**。

实测这条"门"：done/ 里 6 篇，索引里 4 条。差的 2 篇并没丢 —— 它们在
`notes/wechat-drafts/*.draft.md` 的 frontmatter 里带着 `reviewed: rejected(...)`。
**裁决一直都存在，只是散落在别处，没有任何东西负责汇总。**

真正的风险不是"已经发生的错"，而是：下次有人归档了一篇、既没复核也没入索引，
`done/` 的文件名和 `status: ok` 都不会有任何异常 —— 那篇就永远停在那里，
而 `wechat_poller.py` 的去重（扫 done/ 的 url）已经把它当成处理完的，不会再抓。

所以本工具做的事：把"每篇到底处于哪一态"算出来，**并为无法解释的态报警**。

四态判定（按 url 归集）
--------------------
| 态 | 判据 | 是否报警 |
|---|---|---|
| `indexed` | url 出现在蒸馏索引里 | 否 —— 完成 |
| `rejected` | 草稿 `reviewed:` 是拒绝结论（`rejected` / `不升格` / `AD`） | 否 —— 已裁决（引用裁决原文） |
| `reviewed` | 草稿 `reviewed:` 有值但**不是**拒绝结论 | **是**（仅当索引可读）—— 通过了却没入索引 |
| `ad` | done/ 的 `.txt` 头写着 `status: AD` | 否 —— skill 规定广告不蒸馏 |
| `draft` | 有草稿但没有 `reviewed:` | 否 —— 在流程中，等复核 |
| `orphan` | done/ 里有，**既不在索引、也没有草稿** | **是** —— 抓了、归档了、什么都没留下 |
| `unknown` | 索引在这台机器上读不到（CI / 沙箱） | 否 —— 无从判断 ≠ 没入索引 |

外加两条反向检查：
- 索引里有、done/ 里没有 → 记了没移（duplicate/index-only）
- done/ 与 drafts 的 url 对不上同名文件 → 一并列出

设计纪律
--------
1. **不造第二个真相源**：裁决读草稿自己的 `reviewed:` 字段，不另设登记表。
   另设一份就得两边同步，而"两边同步"正是本仓库一直在修的那种病。
2. **索引是本机专属资源**（`~/.atomcode/notes/`），CI 上没有。索引不可用时
   这一档如实降到"未核验"，**不把查不到当成"都没入索引"** ——
   否则又是一个在 CI 上必然红的门禁。
3. `--self-test` 用临时 fixture 造全部四态，逐态变异，证明报警真会被触发。

用法
----
    python tools/wechat_queue.py --check         # 盘点，退出码 0 = 无 orphan
    python tools/wechat_queue.py --self-test     # 变异自验（临时 fixture）
    python tools/wechat_queue.py --index <path>  # 指定蒸馏索引（默认 ~/.atomcode/notes/…）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE = REPO_ROOT / "sources" / "wechat"
PENDING = BASE / "pending"
DONE = BASE / "done"
DRAFTS = REPO_ROOT / "notes" / "wechat-drafts"

SANDBOX = os.environ.get("AGIDISTILLER_SANDBOX") == "1"
"""沙箱模式：假装本机没有蒸馏索引（CI 就是这种环境）。

只让资源"不可用"，不改写路径值 —— 改路径会让比对路径的判据跟着误报。
"""

DEFAULT_INDEX = Path.home() / ".atomcode" / "notes" / "wechat-distilled.md"

META_URL = re.compile(r"^url:\s*(\S+)\s*$", re.M)
META_TITLE = re.compile(r"^title:\s*(.+)$", re.M)
META_STATUS = re.compile(r"^status:\s*(\S+)\s*$", re.M)
# 草稿里表示「不升格」的裁决词。skill 规定 AD 篇直接归档、不蒸馏 —— 那类没有草稿，
# 靠 done/*.txt 的 `status: AD` 识别；这里管的是草稿复核后的拒绝结论。
REJECT_MARK = re.compile(r"rejected|不升格|不采纳|AD\b")
FM_SOURCE = re.compile(r"^source:\s*(\S+)\s*$", re.M)
FM_REVIEWED = re.compile(r"^reviewed:\s*(.+)$", re.M)
INDEX_URL = re.compile(r"^\[源:(\S+?)\]\s*$", re.M)


# ──────────────────────────────────────────────────────────────
# 读取
# ──────────────────────────────────────────────────────────────

def read_txt_meta(d: Path) -> dict[str, dict]:
    """done/（或 pending/）里每个 .txt 的 {url: {file, title}}。"""
    out: dict[str, dict] = {}
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.txt")):
        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:800]
        except OSError:
            continue
        m = META_URL.search(head)
        if not m:
            continue
        t = META_TITLE.search(head)
        s = META_STATUS.search(head)
        out[m.group(1)] = {
            "file": f.name,
            "title": t.group(1).strip() if t else f.stem,
            "status": s.group(1) if s else None,
        }
    return out


def read_drafts(d: Path) -> dict[str, dict]:
    """drafts 目录里每个 .draft.md 的 {url: {file, reviewed|None}}。"""
    out: dict[str, dict] = {}
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.draft.md")):
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        src = FM_SOURCE.search(txt)
        if not src:
            continue
        rv = FM_REVIEWED.search(txt)
        out[src.group(1)] = {
            "file": f.name,
            "reviewed": rv.group(1).strip() if rv else None,
        }
    return out


def index_available(p: Path | None = None) -> bool:
    """蒸馏索引在这台机器上是否可读。沙箱下恒 False（但路径值不变）。"""
    if SANDBOX:
        return False
    return (p or DEFAULT_INDEX).is_file()


def read_index(p: Path | None = None) -> dict[str, str] | None:
    """索引里每个 url → 条目标题（含 ✅/❌ 等前缀）。None = 无从判断。"""
    target = p or DEFAULT_INDEX
    if not index_available(target):
        return None
    try:
        txt = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    blocks = re.split(r"^## ", txt, flags=re.M)[1:]
    out: dict[str, str] = {}
    for b in blocks:
        head = b.splitlines()[0].strip() if b.splitlines() else ""
        for u in INDEX_URL.findall(b):
            out[u] = head[:60]
    return out


def read_index_bare(p: Path | None = None) -> list[str] | None:
    """索引里**没有** `[源:URL]` 的条目标题 —— G1（每块必带溯源）违反项。

    None = 索引不可读，无从判断（与 read_index 同一口径）。
    """
    target = p or DEFAULT_INDEX
    if not index_available(target):
        return None
    try:
        txt = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    bare = []
    for b in re.split(r"^## ", txt, flags=re.M)[1:]:
        if not INDEX_URL.search(b):
            head = b.splitlines()[0].strip() if b.splitlines() else ""
            if head:
                bare.append(head[:60])
    return bare


# ──────────────────────────────────────────────────────────────
# 盘点
# ──────────────────────────────────────────────────────────────

def scan(done_dir: Path = DONE, drafts_dir: Path = DRAFTS,
         pending_dir: Path = PENDING, index: Path | None = None) -> dict:
    done = read_txt_meta(done_dir)
    pend = read_txt_meta(pending_dir)
    drafts = read_drafts(drafts_dir)
    idx = read_index(index)

    states: dict[str, str] = {}          # url -> 状态
    verdicts: dict[str, str] = {}        # url -> 裁决原文（rejected 时）
    for u in done:
        if idx is not None and u in idx:
            states[u] = "indexed"
        elif done[u].get("status") == "AD":
            # skill 规定：广告/软文标记 status: AD 直接归档、不蒸馏。
            # 不认这一档就会把合规的 AD 篇报成丢失 —— 那是误报，误报会让人关掉门禁。
            states[u] = "ad"
        elif u in drafts:
            rv = drafts[u]["reviewed"]
            if rv and REJECT_MARK.search(rv):
                states[u] = "rejected"
                verdicts[u] = rv
            elif rv:
                # 已复核但结论不是拒绝（如 approved）。把它和 rejected 混为一谈
                # 会把「通过了却没入索引」这种真问题，伪装成「按裁决不升格」。
                states[u] = "reviewed"
                verdicts[u] = rv
            else:
                states[u] = "draft"
        elif idx is None:
            # 索引读不到时**不许**顺手判 orphan —— 那等于把「查不到」当成「没入索引」，
            # 在 CI / 沙箱上会让这条门禁必然红。无从判断就如实说无从判断。
            states[u] = "unknown"
        else:
            states[u] = "orphan"

    return {
        "done": done,
        "pending": pend,
        "drafts": drafts,
        "index": idx,                                   # None = 本机无索引
        "bare": read_index_bare(index),                 # None = 无从判断（G1）
        "states": states,
        "verdicts": verdicts,
        # 反向：索引里有、done/ 里没有 —— 记了没移
        "index_only": [] if idx is None else [u for u in idx if u not in done],
        # drafts 里有、done/ 里没有 —— 草稿悬空（原文没归档）
        "draft_only": [u for u in drafts if u not in done],
        "orphans": [u for u, s in states.items() if s == "orphan"],
    }


# ──────────────────────────────────────────────────────────────
# 报告
# ──────────────────────────────────────────────────────────────

def collect_problems(r: dict) -> list[str]:
    """把盘点结果翻译成「不可解释项」清单 —— 判据与命令行共用同一份实现。

    判据里再写一遍判定逻辑就是第二份真相源：工具改了、判据没跟上，
    门禁就会一边报绿一边漏。这里只此一份。
    """
    problems: list[str] = []
    for h in r["bare"] or []:
        problems.append(f"G1 违反：索引条目「{h}」没有 [源:URL]")
    if r["index"] is not None:
        for u, s in r["states"].items():
            if s == "reviewed":
                problems.append(
                    f"复核通过却没入索引：{r['done'][u]['file']} —— "
                    f"裁决「{r['verdicts'][u][:40]}」")
        for u in r["index_only"]:
            problems.append(f"记了没移：索引里有 {u} 但 done/ 中没有对应文件")
    for u in r["orphans"]:
        problems.append(f"悬空：{r['done'][u]['file']} —— 已归档但既没入索引也没有草稿")
    for u in r["draft_only"]:
        problems.append(f"草稿悬空：{r['drafts'][u]['file']} 有草稿但原文不在 done/")
    return problems


def cmd_check(index: Path | None = None, verbose: bool = True, *,
              done_dir: Path = DONE, drafts_dir: Path = DRAFTS,
              pending_dir: Path = PENDING) -> int:
    r = scan(done_dir, drafts_dir, pending_dir, index)
    n = len(r["done"])
    label = {  # 状态 → 中文
        "indexed": "✅ 已入索引",
        "rejected": "⛔ 已裁决不升格",
        "reviewed": "📋 已复核（结论非拒绝）",
        "ad": "🚫 广告/软文，按纪律不蒸馏",
        "draft": "📝 草稿待复核",
        "orphan": "❌ 悬空（无索引无草稿）",
        "unknown": "❔ 索引不可读，未核验",
    }
    if verbose:
        print(f"== 微信队列盘点 @ {done_dir}")
        print(f"  done/ {n} 篇   pending/ {len(r['pending'])} 篇   "
              f"drafts/ {len(r['drafts'])} 篇")
        if r["index"] is None:
            print("  蒸馏索引：本机不可读（未核验入索引情况）")
        else:
            print(f"  蒸馏索引：{len(r['index'])} 条")
        print()
        for u in sorted(r["done"], key=lambda x: r["done"][x]["file"]):
            t = r["done"][u]["title"]
            print(f"  {label[r['states'][u]]:16} {t[:44]}")
            if r["states"][u] == "rejected":
                print(f"                     └ {r['verdicts'][u][:70]}")
        if r["pending"]:
            print("\n  pending（待蒸馏）：")
            for u, meta in r["pending"].items():
                print(f"    - {meta['file'][:60]}")

    problems = collect_problems(r)

    if verbose:
        if problems:
            print(f"\n❌ {len(problems)} 项不可解释：")
            for p in problems:
                print(f"  - {p}")
        else:
            note = "" if r["index"] is not None else "（入索引情况未核验：本机无该索引）"
            print(f"\n✅ 全部可解释{note}")
    return 1 if problems else 0


# ──────────────────────────────────────────────────────────────
# 变异自验
# ──────────────────────────────────────────────────────────────

def _mk(tmp: Path, name: str, url: str, title: str, status: str = "ok") -> None:
    (tmp / "done" / f"{name}.txt").write_text(
        f"---\nurl: {url}\nfetched: 2026-01-01\nstatus: {status}\n"
        f"title: {title}\naccount: 测试\nchars: 10\n---\n\n正文\n",
        encoding="utf-8")


def _mk_draft(tmp: Path, name: str, url: str, reviewed: str | None = None) -> None:
    rv = f"reviewed: {reviewed}\n" if reviewed else ""
    (tmp / "drafts" / f"{name}.draft.md").write_text(
        f"---\nstatus: DRAFT\nsource: {url}\ntitle: {name}\n{rv}---\n\n## 痛点\n- x\n",
        encoding="utf-8")


def _mk_index(tmp: Path, entries: list[tuple[str, str]], name: str = "index.md",
              bare: int = 0) -> Path:
    """name 可换：否则第二次调用会覆盖第一次的文件，
    让后续用例拿到的还是上一份索引 —— 报警是真的，报警源却搞错了。"""
    p = tmp / name
    body = "# 索引\n\n"
    for url, title in entries:
        body += f"---\n\n## ✅ {title}\n[源:{url}]\n\n**痛点**：x\n\n"
    for i in range(bare):          # 没有 [源:URL] 的条目 —— G1 违反项
        body += f"---\n\n## ✅ 无溯源条目{i}\n\n**痛点**：x\n\n"
    p.write_text(body, encoding="utf-8")
    return p


def self_test() -> int:
    """变异自验：四态各自能被正确判定，且 orphan 真会报警。"""
    cases: list[tuple[str, bool]] = []
    U = "https://mp.weixin.qq.com/s/"

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for sub in ("done", "drafts", "pending"):
            (tmp / sub).mkdir()

        # 四态各一篇 + 一篇 pending
        _mk(tmp, "a-indexed", U + "A", "甲 已入索引")
        _mk(tmp, "b-rejected", U + "B", "乙 已裁决")
        _mk(tmp, "c-draft", U + "C", "丙 待复核")
        _mk_draft(tmp, "b-rejected", U + "B", "rejected（人工复核：泛化编造，不升格）")
        _mk_draft(tmp, "c-draft", U + "C")
        idx = _mk_index(tmp, [(U + "A", "甲 已入索引")])

        def run() -> dict:
            return scan(tmp / "done", tmp / "drafts", tmp / "pending", idx)

        def check(ip: Path | None) -> int:
            """在 fixture 上跑检查 —— 不传目录就会盘点真实仓库，等于没验。"""
            return cmd_check(index=ip, verbose=False,
                             done_dir=tmp / "done",
                             drafts_dir=tmp / "drafts",
                             pending_dir=tmp / "pending")

        r = run()
        st = r["states"]
        cases.append(("入索引的判为 indexed", st[U + "A"] == "indexed"))
        cases.append(("有裁决的判为 rejected", st[U + "B"] == "rejected"))
        cases.append(("无裁决草稿判为 draft", st[U + "C"] == "draft"))
        cases.append(("四态全可解释 → 退出 0", check(idx) == 0))
        cases.append(("裁决原文被带出", "不升格" in r["verdicts"][U + "B"]))

        # 变异 1：归档一篇、既不给草稿也不入索引 → 必须判 orphan 且报警
        _mk(tmp, "d-orphan", U + "D", "丁 悬空")
        r = run()
        cases.append(("孤儿被判为 orphan", r["states"][U + "D"] == "orphan"))
        cases.append(("孤儿触发报警", check(idx) != 0))
        (tmp / "done" / "d-orphan.txt").unlink()

        # 变异 2：草稿里补上 reviewed → 从 orphan/draft 翻成 rejected，报警消失
        _mk(tmp, "d-orphan", U + "D", "丁 悬空")
        _mk_draft(tmp, "d-orphan", U + "D", "rejected（复核：不升格）")
        cases.append(("补裁决后转为 rejected", run()["states"][U + "D"] == "rejected"))
        cases.append(("补裁决后报警消失", check(idx) == 0))

        # 变异 3：索引里有、done/ 里没有 → 记了没移
        idx2 = _mk_index(tmp, [(U + "A", "甲 已入索引"), (U + "ZZZ", "幽灵条目")],
                         name="index-with-ghost.md")
        r = scan(tmp / "done", tmp / "drafts", tmp / "pending", idx2)
        cases.append(("记了没移被抓出", U + "ZZZ" in r["index_only"]))
        cases.append(("记了没移触发报警", check(idx2) != 0))

        # 变异 4：草稿有、原文不在 done/ → 草稿悬空
        _mk_draft(tmp, "ghost", U + "GHOST")
        r = scan(tmp / "done", tmp / "drafts", tmp / "pending", idx)
        cases.append(("草稿悬空被抓出", U + "GHOST" in r["draft_only"]))
        (tmp / "drafts" / "ghost.draft.md").unlink()

        # 变异 5：pending 里的篇要能被看见（它不参与 orphan 判定 —— 还没走完流程）
        _mk2 = tmp / "pending" / "e-pending.txt"
        _mk2.write_text(f"---\nurl: {U}E\nfetched: 2026-01-01\nstatus: ok\n"
                        f"title: 戊 待蒸馏\naccount: 测试\nchars: 10\n---\n\n正文\n",
                        encoding="utf-8")
        r = scan(tmp / "done", tmp / "drafts", tmp / "pending", idx)
        cases.append(("pending 篇被识别", len(r["pending"]) == 1))
        cases.append(("pending 篇不算 orphan", U + "E" not in r["states"]))
        cases.append(("pending 篇不触发报警", check(idx) == 0))

        # 变异 6：approved 与 rejected 必须分开 ——
        # 混同会把「通过了却没入索引」这种真问题，伪装成「按裁决不升格」而放行
        _mk(tmp, "f-approved", U + "F", "己 复核通过")
        _mk_draft(tmp, "f-approved", U + "F", "approved（人工复核通过）")
        cases.append(("approved 不混同为 rejected", run()["states"][U + "F"] == "reviewed"))
        cases.append(("复核通过却没入索引 → 报警", check(idx) != 0))
        idx3 = _mk_index(tmp, [(U + "A", "甲 已入索引"), (U + "F", "己 复核通过")],
                         name="index-with-f.md")
        cases.append(("补进索引后报警消失", check(idx3) == 0))

        # 变异 7：status: AD 是合规的「不蒸馏」，不得报成丢失 ——
        # 误报会让人关掉门禁，那比漏报更坏
        _mk(tmp, "g-ad", U + "G", "庚 广告", status="AD")
        cases.append(("AD 篇判为 ad", run()["states"][U + "G"] == "ad"))
        cases.append(("AD 篇不触发报警", check(idx3) == 0))

        # 变异 8：G1 —— 索引条目必须有 [源:URL]，缺一个就要报警
        idx4 = _mk_index(tmp, [(U + "A", "甲 已入索引"), (U + "F", "己 复核通过")],
                         name="index-bare.md", bare=1)
        r = scan(tmp / "done", tmp / "drafts", tmp / "pending", idx4)
        cases.append(("G1 违反被抓出", r["bare"] is not None and len(r["bare"]) == 1))
        cases.append(("G1 违反触发报警", check(idx4) != 0))

        # 变异 9：索引不可读（CI / 沙箱）→ 不得把「查不到」当成「都没入索引」
        r = scan(tmp / "done", tmp / "drafts", tmp / "pending", tmp / "nope.md")
        cases.append(("索引不可读时返回 None", r["index"] is None))
        cases.append(("索引不可读时不谎报 index_only", r["index_only"] == []))
        # 此时甲不再算 indexed，但也不该被当成 orphan —— 它只是"未核验"
        cases.append(("索引不可读时入索引篇不误判为 orphan",
                      r["states"][U + "A"] != "orphan"))
        cases.append(("索引不可读时如实标 unknown", r["states"][U + "A"] == "unknown"))
        cases.append(("未核验不触发报警", check(tmp / "nope.md") == 0))

    bad = 0
    for name, ok in cases:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            bad += 1
    print(f"\n{'✅' if not bad else '❌'} {len(cases) - bad}/{len(cases)} 通过")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="微信公众号队列三态盘点（G4 机验）")
    ap.add_argument("--check", action="store_true", help="盘点真实队列")
    ap.add_argument("--self-test", action="store_true", help="变异自验（临时 fixture）")
    ap.add_argument("--index", type=Path, default=None, help="蒸馏索引路径")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    return cmd_check(index=args.index)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
