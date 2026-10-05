#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""蒸馏管道：从 sources/**/*.md 提取「可执行规则」→ 生成 SKILL.md 草稿

用法：
    python tools/distill_skills.py              # 生成草稿到 skills-drafts/（默认）
    python tools/distill_skills.py --out DIR    # 生成到指定目录
    python tools/distill_skills.py --check      # 只体检，不写产物
    python tools/distill_skills.py --self-test  # 变异自验（证明上面的判据能被打破）

输入：sources/**/*.md
输出：<out>/<slug>/SKILL.md 草稿（需人工审核后才能进正式 skills/）

设计红线（别改回去）：
    * 不可蒸馏的 source 必须**显式报出来**，不许静默跳过。
      早期版本只 print「✅ 生成 N 个」，把不可蒸馏的吞掉 —— 那是假绿：
      N 是"成功数"不是"总数"，看输出的人会以为全部处理完了。
    * 不为了刷绿而放宽标题正则。素材用 `## 解法（可执行规则）` 这类变体时，
      正确做法是**报出来让人裁决**（改素材 or 登记为手工通道），
      不是悄悄放宽匹配把不合格的产物算进去。
"""
import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
OUT = ROOT / "skills-drafts"
ARCHIVE = ROOT / "skills-drafts-archive"

RULE_HEADER = re.compile(r"^##\s*可执行规则\s*$", re.M)
META_TITLE = re.compile(r"^\s*[-*]\s*标题[:：]\s*(.+)$", re.M)
TRAP_HEADER = re.compile(r"^##\s*陷阱\s*$", re.M)
ANY_HEADER = re.compile(r"^##\s+.+$", re.M)

# 「淘汰」的合法登记值：产物被判定无承接物，不是丢了。
NO_OUTCOME = "(已淘汰，无承接物)"

# 与「可执行规则」形近但本管道不认的标题 —— 用来给出**具体**的失败原因，
# 而不是干巴巴一句"缺少该章节"。这里只做诊断，不做匹配放宽。
NEAR_MISS = re.compile(r"^##\s*.*可执行规则.*$", re.M)


def extract_section(text: str, header: re.Pattern, next_header: re.Pattern | None) -> str:
    m = header.search(text)
    if not m:
        return ""
    start = m.end()
    nxt = next_header.search(text, start) if next_header else None
    end = nxt.start() if nxt else len(text)
    return text[start:end].strip()


def slugify(title: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", title).strip("-").lower()
    return re.sub(r"-{2,}", "-", s)[:40] or "untitled"


def diagnose(text: str) -> str:
    """为什么这份 source 不可蒸馏 —— 给具体原因，别只说"缺章节"。"""
    near = NEAR_MISS.search(text)
    if near:
        return f"标题形近但不匹配：`{near.group(0).strip()}`（本管道只认精确的 `## 可执行规则`）"
    heads = [m.group(0).strip() for m in ANY_HEADER.finditer(text)]
    if heads:
        preview = "；".join(h[:24] for h in heads[:4])
        return f"无 `## 可执行规则` 段，实际章节：{preview}"
    return "无任何 `## ` 章节"


def distill(src: Path) -> dict | None:
    text = src.read_text(encoding="utf-8", errors="ignore")
    rules = extract_section(text, RULE_HEADER, TRAP_HEADER)
    if not rules.strip():
        return None
    title_m = META_TITLE.search(text)
    title = title_m.group(1).strip() if title_m else src.stem
    traps = extract_section(text, TRAP_HEADER, None)
    return {"title": title, "source": src.relative_to(ROOT).as_posix(), "rules": rules, "traps": traps}


def render(d: dict) -> str:
    lines = [
        "---",
        f'name: {slugify(d["title"])}',
        f'description: 蒸馏自《{d["title"]}》的可执行规则（草稿，需人工审核）；来源 {d["source"]}',
        "---",
        "",
        f"# {d['title']} — 可执行规则",
        "",
        "## 规则",
        "",
        d["rules"],
        "",
    ]
    if d["traps"]:
        lines += ["## 陷阱", "", d["traps"], ""]
    lines += ["## 审核清单（定稿前删掉本节）", "",
              "- [ ] 规则可执行可验证（非愿望清单）",
              "- [ ] 与现有 skill/memory 无重复",
              "- [ ] 触发词补全", ""]
    return "\n".join(lines)


def scan(out: Path) -> dict:
    """体检：每份 source 的蒸馏状态 + index.json 产物的去向。"""
    ok, skipped = [], []
    for src in sorted(SOURCES.rglob("*.md")):
        d = distill(src)
        rel = src.relative_to(ROOT).as_posix()
        if d is None:
            skipped.append((rel, diagnose(src.read_text(encoding="utf-8", errors="ignore"))))
        else:
            ok.append((rel, slugify(d["title"])))

    idx = out / "index.json"
    entries: list[str] = []
    if idx.is_file():
        try:
            entries = json.loads(idx.read_text(encoding="utf-8")).get("generated", [])
        except (json.JSONDecodeError, OSError):
            entries = []
    in_place, missing = [], []
    for slug in entries:
        if (out / slug / "SKILL.md").is_file():
            in_place.append(slug)
        else:
            missing.append(slug)

    graduated = {}
    manual: dict[str, str] = {}
    if idx.is_file():
        try:
            data = json.loads(idx.read_text(encoding="utf-8"))
            graduated = data.get("graduated", {})
            manual = data.get("manual-channel", {})
        except (json.JSONDecodeError, OSError):
            graduated = {}

    return {
        "sources_total": len(ok) + len(skipped),
        "distillable": ok,
        "skipped": skipped,
        "entries": entries,
        "in_place": in_place,
        "missing": missing,
        "graduated": graduated,
        "manual": manual,
    }


def cmd_check(out: Path) -> int:
    r = scan(out)
    print("=== 蒸馏管道体检 ===")
    print(f"sources: {r['sources_total']} 份 → 可蒸馏 {len(r['distillable'])}，不可蒸馏 {len(r['skipped'])}")
    if r["skipped"]:
        print("\n不可蒸馏（管道覆盖不到，走手工通道）：")
        for rel, why in r["skipped"]:
            print(f"  ✗ {rel}\n      {why}")
    print(f"\nindex.json: {len(r['entries'])} 条 → 在位 {len(r['in_place'])}，不在位 {len(r['missing'])}")
    for slug in r["missing"]:
        g = r["graduated"].get(slug)
        if not g:
            print(f"  → {slug}\n      ❌ 无去向登记（无法区分「已毕业」与「产物被误删」）")
            continue
        draft = g.get("draft", "")
        outcome = g.get("outcome", "")
        ok_draft = bool(draft) and (ROOT / draft).exists()
        ok_out = outcome == NO_OUTCOME or (bool(outcome) and (ROOT / outcome).exists())
        if ok_draft and ok_out:
            print(f"  → {slug}\n      ✅ 原稿 {draft}\n      ✅ 结果 {outcome}")
        else:
            if not ok_draft:
                print(f"  → {slug}\n      ❌ 原稿路径不存在（{'未登记' if not draft else draft}）")
            if not ok_out:
                print(f"  → {slug}\n      ❌ 结果路径不存在（{'未登记' if not outcome else outcome}）")
    # 注意：不可蒸馏**不算失败**，只报告。
    # 早期版本把它算进失败数，结果 --check 永远非 0 —— 一个永远红的门禁等于没有门禁，
    # 而且会掩盖真正的失败（自验里「产物消失」那条就是被它假性带过的）。
    # 不可蒸馏该不该红，交给判据 D22 用「数字钉住 + 逐份点名」来管。
    def unexplainable(slug: str) -> bool:
        g = r["graduated"].get(slug)
        if not g:
            return True
        draft, outcome = g.get("draft", ""), g.get("outcome", "")
        ok_draft = bool(draft) and (ROOT / draft).exists()
        ok_out = outcome == NO_OUTCOME or (bool(outcome) and (ROOT / outcome).exists())
        return not (ok_draft and ok_out)

    registered = set(r["manual"])
    actual = {rel for rel, _ in r["skipped"]}
    if registered == actual:
        print(f"\n手工通道：{len(registered)} 份已登记，与实测不可蒸馏集合一致 ✅")
    else:
        only_reg = sorted(registered - actual)
        only_act = sorted(actual - registered)
        if only_reg:
            print(f"\n❌ 登记了但实际可蒸馏（登记过期）：{only_reg}")
        if only_act:
            print(f"❌ 不可蒸馏但未登记（新增素材忘了处理）：{only_act}")

    bad = sum(1 for s in r["missing"] if unexplainable(s)) + len(registered ^ actual)
    print(f"\n{'✅ 产物去向全部可解释' if bad == 0 else f'❌ {bad} 项去向不可解释'}")
    return 0 if bad == 0 else 1


def cmd_generate(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for src in sorted(SOURCES.rglob("*.md")):
        d = distill(src)
        if not d:
            continue
        slug = slugify(d["title"])
        dest = out / slug / "SKILL.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(d), encoding="utf-8")
        made.append(slug)

    idx = out / "index.json"
    prev = {}
    if idx.is_file():
        try:
            prev = json.loads(idx.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            prev = {}
    idx.write_text(json.dumps(
        {
            "generated": made,
            "graduated": prev.get("graduated", {}),
            "manual-channel": prev.get("manual-channel", {}),
        },
        ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(1 for _ in SOURCES.rglob("*.md"))
    print(f"生成 {len(made)} 个草稿 → {out}（sources 共 {total} 份，"
          f"{total - len(made)} 份不可蒸馏，见 --check）")
    for s in made:
        print(f"  - {s}")
    if total - len(made):
        print("\n⚠️ 上面是「成功数」不是「总数」——不可蒸馏的没有被处理，不是被处理失败了。")
    return 0


def self_test() -> int:
    """变异自验：每条判据都必须能被打破，否则它只是装饰。"""
    import shutil
    import tempfile

    cases: list[tuple[str, bool]] = []

    def mk(**kw) -> Path:
        t = Path(tempfile.mkdtemp(prefix="distill-"))
        (t / "sources").mkdir()
        (t / "sources" / "a.md").write_text(
            "## 元信息\n\n- 标题：测试标题一二三\n\n## 可执行规则\n\n1. 规则甲\n\n"
            "## 陷阱\n\n- 坑\n", encoding="utf-8")
        (t / "sources" / "b.md").write_text(
            "## 元信息\n\n## 别的章节\n\n没有规则段\n", encoding="utf-8")
        (t / "sources" / "c.md").write_text(
            "## 元信息\n\n## 解法（可执行规则）\n\n1. 变体标题\n", encoding="utf-8")
        return t

    def run(t: Path, fn, *a):
        global ROOT, SOURCES, OUT, ARCHIVE
        old = (ROOT, SOURCES, OUT, ARCHIVE)
        ROOT, SOURCES, OUT = t, t / "sources", t / "drafts"
        try:
            return fn(*a)
        finally:
            ROOT, SOURCES, OUT, ARCHIVE = old

    t = mk()
    try:
        # 预置 index.json：先把两份不可蒸馏素材登记进手工通道，
        # 否则 registered != actual 会让下面每条产物去向用例都被这份额外的 bad 污染 ——
        # 表现为 5 条用例一起红，看起来像"到处都坏"，实际只有一处根因。
        (t / "drafts").mkdir(parents=True, exist_ok=True)
        idx = t / "drafts" / "index.json"
        MANUAL = {
            "sources/b.md": "无规则段的结构化笔记，走手工通道处理",
            "sources/c.md": "标题变体「## 解法（可执行规则）」，管道正则只认精确标题",
        }
        idx.write_text(json.dumps({"generated": [], "graduated": {}, "manual-channel": MANUAL},
                                  ensure_ascii=False, indent=2), encoding="utf-8")

        # 1. 可蒸馏的正例被识别
        r = run(t, scan, t / "drafts")
        cases.append(("可蒸馏 1 份", len(r["distillable"]) == 1))
        # 2. 无规则段 → 归入 skipped（不静默）
        cases.append(("缺章节 → skipped", len(r["skipped"]) == 2))
        # 3. 失败原因具体：形近标题被点出来
        why = dict(r["skipped"]).get("sources/c.md", "")
        cases.append(("形近标题被诊断出来", "解法（可执行规则）" in why))
        # 4. 生成产物真的落盘
        run(t, cmd_generate, t / "drafts")
        cases.append(("产物落盘", (t / "drafts" / "测试标题一二三" / "SKILL.md").is_file()))
        # 5. 生成后 index 在位
        r = run(t, scan, t / "drafts")
        cases.append(("生成后 index 在位", r["in_place"] and not r["missing"]))
        # 6. 变异：产物被删 → 无去向登记时必须报错（判据能被打破）
        shutil.rmtree(t / "drafts" / "测试标题一二三")
        cases.append(("产物消失且无登记 → --check 失败", run(t, cmd_check, t / "drafts") != 0))
        # 7. 补上真实去向 → 恢复通过
        idx = t / "drafts" / "index.json"
        data = json.loads(idx.read_text(encoding="utf-8"))
        (t / "skills").mkdir()
        (t / "skills" / "x").mkdir()
        (t / "skills" / "x" / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        data["graduated"] = {"测试标题一二三": {"draft": "skills/x", "outcome": "skills/x"}}
        idx.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        cases.append(("登记真实去向 → --check 通过", run(t, cmd_check, t / "drafts") == 0))
        # 8. 变异：结果路径不存在 → 必须报错
        data["graduated"] = {"测试标题一二三": {"draft": "skills/x", "outcome": "skills/不存在的"}}
        idx.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        cases.append(("结果路径不存在被抓出", run(t, cmd_check, t / "drafts") != 0))
        # 9. 变异：原稿路径不存在（但结果在）→ 也必须报错（两层都要真）
        data["graduated"] = {"测试标题一二三": {"draft": "skills/没了", "outcome": "skills/x"}}
        idx.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        cases.append(("原稿路径不存在被抓出", run(t, cmd_check, t / "drafts") != 0))
        # 10. 「已淘汰」是合法结果（产物被判定无承接物，不是丢了）
        data["graduated"] = {"测试标题一二三": {"draft": "skills/x", "outcome": NO_OUTCOME}}
        idx.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        cases.append(("已淘汰作为合法结果", run(t, cmd_check, t / "drafts") == 0))
        # 11. 生成时保留已有 graduated 登记（不被覆盖清空）
        run(t, cmd_generate, t / "drafts")
        kept = json.loads((t / "drafts" / "index.json").read_text(encoding="utf-8"))
        cases.append(("重新生成不冲掉毕业登记",
                      kept.get("graduated") == {"测试标题一二三": {"draft": "skills/x", "outcome": NO_OUTCOME}}))
        # 12. 生成同样不能冲掉手工通道登记
        cases.append(("重新生成不冲掉手工通道登记", kept.get("manual-channel") == MANUAL))
        # 13. 变异：漏登记一份不可蒸馏源 → 必须报错（防止新素材被静默吞掉）
        data = json.loads(idx.read_text(encoding="utf-8"))
        data["manual-channel"] = {"sources/b.md": MANUAL["sources/b.md"]}
        idx.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        cases.append(("漏登记不可蒸馏源被抓出", run(t, cmd_check, t / "drafts") != 0))
        # 14. 变异：登记一份不存在的源 → 必须报错（防止登记表自己腐烂）
        data["manual-channel"] = {**MANUAL, "sources/幽灵.md": "这条素材根本不存在"}
        idx.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        cases.append(("登记了不存在的源被抓出", run(t, cmd_check, t / "drafts") != 0))
        # 15. 放宽正则刷绿是被禁止的：形近标题仍不算可蒸馏
        r = run(t, scan, t / "drafts")
        cases.append(("形近标题不被偷偷算作可蒸馏", len(r["distillable"]) == 1))
        # 12. 空 index/无 index 不崩
        (t / "drafts" / "index.json").unlink()
        cases.append(("无 index.json 不崩", isinstance(run(t, scan, t / "drafts"), dict)))
    finally:
        shutil.rmtree(t, ignore_errors=True)

    for name, passed in cases:
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    bad = sum(1 for _, p in cases if not p)
    print(f"\n{len(cases) - bad}/{len(cases)} 通过")
    return 0 if bad == 0 else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return self_test()

    out = OUT
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
        if not out.is_absolute():
            out = (Path.cwd() / out).resolve()

    if "--check" in argv:
        return cmd_check(out)
    return cmd_generate(out)


if __name__ == "__main__":
    sys.exit(main())
