#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""蒸馏管道：从 sources/*.md 提取「可执行规则」→ 生成 SKILL.md 草稿

用法：python tools/distill_skills.py [--out skills-drafts/]
输入：sources/**/*.md（统一结构：## 元信息 / ## 痛点 / ## 解法 / ## 可执行规则 / ## 陷阱）
输出：<out>/<slug>/SKILL.md 草稿（需人工审核后才能进正式 skills/）
"""
import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
OUT = ROOT / "skills-drafts"

RULE_HEADER = re.compile(r"^##\s*可执行规则\s*$", re.M)
META_TITLE = re.compile(r"^\s*[-*]\s*标题[:：]\s*(.+)$", re.M)
TRAP_HEADER = re.compile(r"^##\s*陷阱\s*$", re.M)


def extract_section(text: str, header: re.Pattern, next_header: re.Pattern | None) -> str:
    m = header.search(text)
    if not m:
        return ""
    start = m.end()
    end = next_header.search(text, start).start() if next_header and next_header.search(text, start) else len(text)
    return text[start:end].strip()


def slugify(title: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", title).strip("-").lower()
    return re.sub(r"-{2,}", "-", s)[:40] or "untitled"


def distill(src: Path) -> dict | None:
    text = src.read_text(encoding="utf-8", errors="ignore")
    rules = extract_section(text, RULE_HEADER, TRAP_HEADER)
    if not rules:
        return None
    title_m = META_TITLE.search(text)
    title = title_m.group(1).strip() if title_m else src.stem
    traps = extract_section(text, TRAP_HEADER, None)
    return {"title": title, "source": str(src.relative_to(ROOT)), "rules": rules, "traps": traps}


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


def main():
    out = OUT
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
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

    index = out / "index.json"
    index.write_text(json.dumps({"generated": made}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 生成 {len(made)} 个草稿 → {out}")
    for s in made:
        print(f"  - {s}")


if __name__ == "__main__":
    main()