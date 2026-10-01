#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_counts.py — 被机验强制的计数，从工作区事实同步到全部声明处（AGI-Distiller）。

## 为什么需要它（2026-10-01，第 19→20 与 20→21 两轮 skill 增长的实测）

`scripts/check_doc_consistency.py` 能**发现**文档数字漂了，但**不会帮你改**。
于是每加一个 skill / 一篇笔记，都要人工 grep 出一堆站点、逐个手敲：

    实测两轮，每轮都是同 16+ 处，一次漏改（HEARTBEAT 那行）就是靠门禁回头抓出来的。

重复的人工步骤 = 一定会漏。本工具把"改数字"这一步变成一条命令。

## 它取代了什么，没取代什么（如实说清）

| 能自动 | 不能自动（工具会打印待办，但不会替你写） |
|---|---|
| 计数类数字：skill 数、笔记数、ATOMCODE 节数、判据条数 | **README skill 表的英文/中文一句话摘要** —— 那是人工提炼的，不是 frontmatter 的拷贝 |
| `sources/` 的**分类分解**（`laodad 4 / wechat 2 / ...`） | 判断某处数字是"计数"还是"历史/实测记录"（后者不许追改，见下） |

## 红线：区分「计数」与「历史/实测记录」

- **计数**（`20 production skills`）→ 跟着事实改，本工具负责。
- **历史/实测记录**（README 的 `Component inventory: Skills (19)`，来自某次真跑安装链路的观测；
  NEXT.md 的流水账）→ **不许追改**，那等于伪造一次没跑过的验证。本工具**不碰**这些站点
  （`--self-test` 会验证它们确实未被纳入站点表）。

## 用法

    python tools/sync_counts.py            # --check：只报告漂移，不写文件（CI 用）
    python tools/sync_counts.py --fix      # 按事实改写全部计数站点
    python tools/sync_counts.py --self-test  # 变异验证：每个站点被改坏都必须被发现

退出码：0 = 一致；1 = 存在漂移（或在 --fix 后仍有漂移）。

零第三方依赖（与本仓其它机验脚本一致）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover
        pass

ROOT = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────
# 事实：只从工作区数，不读任何文档
# ──────────────────────────────────────────────────────────────


def fact_skills() -> int:
    d = ROOT / "skills"
    return len([p for p in d.iterdir() if p.is_dir()]) if d.is_dir() else 0


def fact_notes() -> int:
    d = ROOT / "sources"
    return len([p for p in d.rglob("*.md") if p.is_file()]) if d.is_dir() else 0


def fact_atomcode() -> int:
    p = ROOT / "rules" / "ATOMCODE.md"
    return len(re.findall(r"^## ", p.read_text(encoding="utf-8"), re.M)) if p.is_file() else 0


def fact_checks() -> int:
    """判据条数 = check_doc_consistency 的 CHECKS 实际长度（自指数字，最容易漂）。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_doc_consistency as cdc  # noqa: E402

    return len(cdc.CHECKS)


def fact_breakdown() -> str:
    """`sources/` 的分类分解，机器生成。

    规则：子目录按其 `*.md` 计数；根层散落的 `*.md` 用文件名作标签
    （`comment-distillery-distilled.md` → `comment-distillery`）。
    排序：计数降序，同数按名称升序 —— 这是**规范形式**，
    因此本工具会把历史上手工写过的顺序（如 `… tencent 1 / comment-distillery 1 / anthropic 1`）
    归一成 `… anthropic 1 / comment-distillery 1 / owasp 1 / tencent 1`。这是预期行为，不是 bug。
    """
    base = ROOT / "sources"
    if not base.is_dir():
        return ""
    counts: dict[str, int] = {}
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        n = len([p for p in d.rglob("*.md") if p.is_file()])
        if n:
            counts[d.name] = n
    for p in sorted(base.glob("*.md")):
        label = p.stem.split("-distilled")[0]
        counts[label] = counts.get(label, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return " / ".join(f"{k} {v}" for k, v in ordered)


def facts() -> dict:
    return {
        "skills": fact_skills(),
        "notes": fact_notes(),
        "atomcode": fact_atomcode(),
        "checks": fact_checks(),
        "breakdown": fact_breakdown(),
    }


# ──────────────────────────────────────────────────────────────
# 站点表：每处"被机验强制的计数"都在这里登记
# 约定：pattern 必须**恰好一个**捕获组，且该组就是那个数字。
# ──────────────────────────────────────────────────────────────

SITES: list[tuple[str, str, str, str]] = [
    # ---- README.md ----
    ("readme_prod_skills", "README.md", r"^- \[x\] (\d+) production skills$", "skills"),
    ("readme_skills_total", "README.md", r"^- \[x\] (\d+) skills total$", "skills"),
    ("readme_notes_roadmap", "README.md", r"^- \[x\] (\d+) distilled source notes on disk in", "notes"),
    ("readme_notes_footer", "README.md", r"\*\*(\d+) distilled source notes on disk\*\*", "notes"),
    ("readme_atomcode_inline", "README.md", r"behavioral specification \((\d+) sections?\)", "atomcode"),
    ("readme_atomcode_roadmap", "README.md", r"^- \[x\] (\d+)-section behavioral specification", "atomcode"),
    # ---- README.zh.md ----
    ("readmezh_prod_skills", "README.zh.md", r"^- \[x\] (\d+) 个生产级 skill$", "skills"),
    ("readmezh_skills_total", "README.zh.md", r"^- \[x\] (\d+) 个 skill$", "skills"),
    ("readmezh_notes_roadmap", "README.zh.md", r"^- \[x\] (\d+) 份蒸馏笔记落盘于", "notes"),
    ("readmezh_notes_footer", "README.zh.md", r"\*\*已落盘 (\d+) 份蒸馏笔记\*\*", "notes"),
    ("readmezh_atomcode_inline", "README.zh.md", r"完整行为规范（(\d+) 节）", "atomcode"),
    # ---- HEARTBEAT.md（D9 强制）----
    ("heartbeat_prod_skills", "HEARTBEAT.md", r"^\| 生产级 skill \| (\d+) \|", "skills"),
    ("heartbeat_notes", "HEARTBEAT.md", r"^\| 落盘蒸馏笔记 \| (\d+) \|", "notes"),
    # ---- NEXT.md 现状锚点 / 长线 ----
    ("next_prod_skills", "NEXT.md", r"^\| 生产级 skill \| (\d+) \|", "skills"),
    ("next_notes", "NEXT.md", r"^\| 落盘蒸馏笔记 \| (\d+)（", "notes"),
    ("next_p2_notes", "NEXT.md", r"使 `sources/` 的 (\d+) 份笔记继续增长", "notes"),
    ("next_p2_skills", "NEXT.md", r"skill 从 (\d+) 继续增长", "skills"),
    # ---- CONTRIBUTING.md（D17 强制口径）----
    ("contrib_checks_inline", "CONTRIBUTING.md", r"文档一致性 —— (\d+) 条判据", "checks"),
    ("contrib_checks_table", "CONTRIBUTING.md", r"文档与实际是否一致（(\d+) 条判据", "checks"),
    # ---- ROADMAP.md（"目标 vs 实际"对照表里的**实际值**，同样是会被事实推翻的声称）----
    ("roadmap_notes", "ROADMAP.md", r"\*\*(\d+) 份\*\*（`sources/", "notes"),
    ("roadmap_p1_actual", "ROADMAP.md", r"目标：5 个 skill → 实际已达 (\d+)", "skills"),
    ("roadmap_phase2_actual", "ROADMAP.md", r"→ 实际 (\d+)，已超额", "skills"),
    ("roadmap_phase2_current", "ROADMAP.md", r"→ 当前 (\d+)\s*$", "skills"),
    # ---- DISTILLER.md（分层示意图里的落盘数示例，同样是会被事实推翻的声称）----
    ("distiller_notes_example", "DISTILLER.md", r"sources/ 下 (\d+) 份笔记", "notes"),
]

# 分类分解站点：捕获的是整个括号内容，由 fact_breakdown() 生成规范形式
BREAKDOWN_SITES: list[tuple[str, str, str]] = [
    ("readme_breakdown", "README.md", r"in `sources/` \(([^)]*)\)"),
    ("readmezh_breakdown", "README.zh.md", r"落盘于 `sources/`（([^）]*)）"),
]

# 明确**不许**纳入自动同步的站点（历史 / 实测记录）。self-test 会验证它们确实被排除。
FROZEN_MARKERS: list[tuple[str, str]] = [
    ("README.md", r"Component inventory: Skills \(19\)"),
    ("README.zh.md", r"Skills \(19\)"),
    ("NEXT.md", r"\| 新增 `scripts/check_doc_consistency\.py` \|"),
]

# 第三类漂移：agent spec 字符数表 —— 值由**文件实际字符数**决定（D11 强制），同样会漂。
# 表格长这样：`| \`SOUL.md\` | 说明 | ~1187 chars |` + `| **Total** | | **~7536 chars** |`
SIZE_SITES: dict[str, tuple[re.Pattern, re.Pattern, str]] = {
    "README.md": (
        re.compile(r"^\|\s*`([A-Z]+\.md)`\s*\|[^|]*\|\s*~(\d+) chars\s*\|", re.M),
        re.compile(r"^\|\s*\*\*Total\*\*\s*\|\s*\|\s*\*\*~(\d+) chars\*\*\s*\|", re.M),
        "chars",
    ),
    "README.zh.md": (
        re.compile(r"^\|\s*`([A-Z]+\.md)`\s*\|[^|]*\|\s*~(\d+) 字符\s*\|", re.M),
        re.compile(r"^\|\s*\*\*总计\*\*\s*\|\s*\|\s*\*\*~(\d+) 字符\*\*\s*\|", re.M),
        "字符",
    ),
}


# ──────────────────────────────────────────────────────────────
# 核心
# ──────────────────────────────────────────────────────────────


def _read_file(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def size_problems(read=_read_file) -> list[str]:
    """agent spec 字符数表：每行 ~N 必须等于该文件实际字符数，总计必须等于各项之和。"""
    out: list[str] = []
    for rel, (row_re, tot_re, _unit) in SIZE_SITES.items():
        txt = read(rel)
        rows = list(row_re.finditer(txt))
        if not rows:
            out.append(f"[sizes] {rel}: 找不到 agent spec 字符数表")
            continue
        total = 0
        for m in rows:
            fname, claimed = m.group(1), int(m.group(2))
            # 注意：spec 文件的字符数一律读**真实文件**（read 注入只用于被改写的 README 文本）
            actual = len(_read_file(fname))
            total += actual
            if actual == 0:
                out.append(f"[sizes] {rel}: 表里列的 {fname} 在工作区不存在")
            elif claimed != actual:
                out.append(f"[sizes] {rel}: {fname} 声称 ~{claimed}，实际 {actual}")
        tm = tot_re.search(txt)
        if not tm:
            out.append(f"[sizes] {rel}: 找不到总计行")
        elif int(tm.group(1)) != total:
            out.append(f"[sizes] {rel}: 总计声称 ~{tm.group(1)}，各项之和 {total}")
    return out


def _fix_sizes(text: str, rel: str) -> str:
    row_re, tot_re, unit = SIZE_SITES[rel]
    total = 0

    def sub_row(m: re.Match) -> str:
        nonlocal total
        fname, claimed = m.group(1), int(m.group(2))
        actual = len(_read_file(fname))
        total += actual
        return m.group(0).replace(f"~{claimed} {unit}", f"~{actual} {unit}")

    new = row_re.sub(sub_row, text)
    tm = tot_re.search(new)
    if tm:
        new = new[: tm.start(1)] + str(total) + new[tm.end(1):]
    return new


def scan(read=_read_file, f: dict | None = None) -> list[str]:
    """返回漂移清单（空 = 一致）。read 可注入，供 self-test 用。"""
    f = f or facts()
    problems: list[str] = []
    for sid, rel, pat, key in SITES:
        txt = read(rel)
        ms = list(re.finditer(pat, txt, re.M))
        if len(ms) != 1:
            problems.append(
                f"[{sid}] {rel}: 命中 {len(ms)} 次（期望恰好 1）—— 站点消失或被复制，需人工确认"
            )
            continue
        got, want = int(ms[0].group(1)), f[key]
        if got != want:
            problems.append(f"[{sid}] {rel}: 声称 {got}，实际 {want}（{key}）")
    for bid, rel, pat in BREAKDOWN_SITES:
        txt = read(rel)
        ms = list(re.finditer(pat, txt, re.M))
        if len(ms) != 1:
            problems.append(f"[{bid}] {rel}: 命中 {len(ms)} 次（期望恰好 1）")
            continue
        got, want = ms[0].group(1).strip(), f["breakdown"]
        if got != want:
            problems.append(f"[{bid}] {rel}: 分解为 {got!r}，规范形式应为 {want!r}")
    problems += size_problems(read)
    return problems


def _replace_once(text: str, pat: str, new_value: str, label: str) -> str:
    ms = list(re.finditer(pat, text, re.M))
    if len(ms) != 1:
        raise AssertionError(f"{label}: 命中 {len(ms)} 次（期望恰好 1），拒绝改写")
    m = ms[0]
    return text[: m.start(1)] + new_value + text[m.end(1):]


SITE_FILES = sorted({s[1] for s in SITES} | {b[1] for b in BREAKDOWN_SITES})


def fixed_texts(f: dict | None = None) -> dict[str, str]:
    """按事实算出每个站点的**目标文本**（只算不写）。

    写盘与 self-test 共用这一份逻辑：self-test 因此**不依赖仓库当前是否已同步**
    （从"修正后"的文本出发做变异，基线恒干净）。
    """
    f = f or facts()
    out: dict[str, str] = {}
    for rel in SITE_FILES:
        p = ROOT / rel
        if not p.is_file():
            continue
        txt = new = p.read_text(encoding="utf-8")
        for sid, r, pat, key in SITES:
            if r == rel:
                new = _replace_once(new, pat, str(f[key]), sid)
        for bid, r, pat in BREAKDOWN_SITES:
            if r == rel:
                new = _replace_once(new, pat, f["breakdown"], bid)
        if rel in SIZE_SITES:
            new = _fix_sizes(new, rel)
        out[rel] = new
    return out


def apply_fix(f: dict | None = None) -> list[str]:
    changed: list[str] = []
    for rel, new in fixed_texts(f).items():
        p = ROOT / rel
        old = p.read_text(encoding="utf-8")
        if new != old:
            p.write_text(new, encoding="utf-8")
            changed.append(rel)
    return changed


# ──────────────────────────────────────────────────────────────
# skill 表待办：工具**不能**替你写英文摘要，但把待办列清楚
# ──────────────────────────────────────────────────────────────

SKILL_ROW = re.compile(r"^\|\s*`([a-z0-9][a-z0-9-]*)`\s*\|", re.M)
TABLES = (("README.md", "### Skills (Cross-Platform)"), ("README.zh.md", "### Skill（跨平台）"))


def missing_skill_rows(read=_read_file) -> dict[str, list[str]]:
    actual = sorted(p.name for p in (ROOT / "skills").iterdir() if p.is_dir())
    out: dict[str, list[str]] = {}
    for rel, head in TABLES:
        txt = read(rel)
        i = txt.find(head)
        seg = txt[i:] if i >= 0 else ""
        for stop in ("\n## ", "\n---"):
            if stop in seg:
                seg = seg.split(stop, 1)[0]
        claimed = set(SKILL_ROW.findall(seg))
        miss = [s for s in actual if s not in claimed]
        if miss:
            out[rel] = miss
    return out


def print_missing_rows(read=_read_file) -> int:
    miss = missing_skill_rows(read)
    if not miss:
        return 0
    print("\n以下 skill 尚未登记进 README 表（**摘要需人工写**，工具不代写）：")
    for rel, names in miss.items():
        for n in names:
            print(f"  {rel}: | `{n}` | <一句话英文/中文摘要> | ✅ Live |")
    return len(miss)


# ──────────────────────────────────────────────────────────────
# self-test：每个站点被改坏都必须被发现；冻结站点必须确实不在站点表内
# ──────────────────────────────────────────────────────────────


def _mutate(text: str, pat: str, delta: int = 1) -> str:
    m = re.search(pat, text, re.M)
    assert m, f"变异锚点缺失（正则未匹配）: {pat!r}"
    return text[: m.start(1)] + str(int(m.group(1)) + delta) + text[m.end(1):]


def _mutate_breakdown(text: str, pat: str, delta: int = 1) -> str:
    """分解站点的变异：把括号内**第一个数字**改掉（不是把整串当成数字）。"""
    m = re.search(pat, text, re.M)
    assert m, f"变异锚点缺失（正则未匹配）: {pat!r}"
    inner = m.group(1)
    m2 = re.search(r"(\d+)", inner)
    assert m2, f"分解内容里找不到数字，无法构造变异: {inner!r}"
    inner2 = inner[: m2.start(1)] + str(int(m2.group(1)) + delta) + inner[m2.end(1):]
    return text[: m.start(1)] + inner2 + text[m.end(1):]


def self_test() -> int:
    print("== 变异验证：每个计数站点被改坏都必须被发现 ==")
    f = facts()
    # 基线取"修正后"的文本 —— 与仓库当前是否已同步无关
    base = fixed_texts(f)

    bad = 0
    baseline = scan(lambda rel: base.get(rel, ""), f)
    if baseline:
        print(f"  FAIL  self-test 自身失败（修正后仍报漂移，说明替换逻辑有 bug）：{baseline[:2]}")
        return 1
    print(f"  PASS  基线一致（{len(SITES)} 个计数站点 + {len(BREAKDOWN_SITES)} 个分解站点）")

    for sid, rel, pat, _key in SITES:
        mutated = dict(base)
        mutated[rel] = _mutate(base[rel], pat, delta=7)
        if not scan(lambda r: mutated.get(r, ""), f):
            print(f"  FAIL  [{sid}] 改坏后仍判为一致 —— 站点无效")
            bad += 1
    for bid, rel, pat in BREAKDOWN_SITES:
        mutated = dict(base)
        mutated[rel] = _mutate_breakdown(base[rel], pat, delta=7)
        if not scan(lambda r: mutated.get(r, ""), f):
            print(f"  FAIL  [{bid}] 改坏后仍判为一致 —— 站点无效")
            bad += 1
    for rel, (row_re, _tot, _unit) in SIZE_SITES.items():
        m = row_re.search(base.get(rel, ""))
        if not m:
            print(f"  FAIL  [sizes/{rel}] 找不到可变异行 —— 站点无效")
            bad += 1
            continue
        mutated = dict(base)
        mutated[rel] = base[rel][: m.start(2)] + str(int(m.group(2)) + 7) + base[rel][m.end(2):]
        if not scan(lambda r: mutated.get(r, ""), f):
            print(f"  FAIL  [sizes/{rel}] 改坏后仍判为一致 —— 站点无效")
            bad += 1

    n_sites = len(SITES) + len(BREAKDOWN_SITES) + len(SIZE_SITES)
    if not bad:
        print(f"  PASS  {n_sites}/{n_sites} 个站点均可自证有效（改坏必被发现）")

    # 冻结站点：必须存在，且必须**不在**站点表里（否则等于追改历史记录）
    frozen_ok = True
    all_pats = {s[2] for s in SITES} | {b[2] for b in BREAKDOWN_SITES}
    for rel, pat in FROZEN_MARKERS:
        txt = _read_file(rel)
        if not re.search(pat, txt):
            print(f"  FAIL  冻结站点的锚点缺失（文档被大改过？）：{rel} / {pat}")
            frozen_ok = False
        for p in all_pats:
            if p == pat:
                print(f"  FAIL  冻结站点被误纳入自动同步：{rel} / {pat}")
                frozen_ok = False
    if frozen_ok:
        print(f"  PASS  {len(FROZEN_MARKERS)} 个历史/实测记录站点均存在且未被自动改写")

    if bad or not frozen_ok:
        print(f"\n变异验证失败：{bad + (0 if frozen_ok else 1)} 项不通过")
        return 1
    print(f"\n变异验证通过：{n_sites} 个站点全部可检出，冻结站点全部守得住")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="同步被机验强制的计数（工作区事实 → 全部声明处）")
    ap.add_argument("--fix", action="store_true", help="按事实改写（默认只检查）")
    ap.add_argument("--self-test", action="store_true", help="变异验证")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    f = facts()
    print(f"== 计数同步 @ {ROOT} ==")
    print(
        f"事实：skills={f['skills']}  notes={f['notes']}  "
        f"atomcode={f['atomcode']} 判据={f['checks']}"
    )
    print(f"      breakdown = {f['breakdown']}")

    if args.fix:
        changed = apply_fix(f)
        if changed:
            print(f"\n已改写 {len(changed)} 个文件：")
            for c in changed:
                print(f"  ✏️  {c}")
        else:
            print("\n无需改写（已一致）")

    problems = scan(_read_file, f)
    if problems:
        print(f"\n仍有 {len(problems)} 处漂移：")
        for p in problems:
            print(f"  ❌ {p}")
        print("\n结果：FAIL —— 跑 `python tools/sync_counts.py --fix` 修正。")
        return 1

    print_missing_rows()
    print("\n结果：全部计数站点与工作区事实一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
