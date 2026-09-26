#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_skill_tags.py —— 机验自产 skill 无「裸规则」（AGI-Distiller 轻量版）。

背景（第九轮 R9，抄自 comment-distillery check_rule_tags.py 思路）：
skill 里的经验规则必须带溯源标记，防止单次踩坑被写成铁律（个案过拟合）：

    [R<N>]           规则源自蒸馏第 N 轮（R1-R15，见 notes/ 蒸馏笔记）
    [实测]           本仓库/本机双向实测过（hook 用例、mock 验证）
    [设计]           结构性设计决策，非经验归纳
    [复现:2+]        至少 2 个独立来源复现（达 R3 升格门槛）

判据（适配我们的 SKILL.md 结构，比原版宽松）：
    1. 正文一级 bullet（`- ` 开头）里含"必须/禁止/不许/绝不/一定要"的
       规则句必须带标记（流程说明/表格行/代码块不查）；
    2. 代码块内与 frontmatter 内不查。
退出码：0 = 通过；1 = 发现裸规则（列出 文件:行号:内容）。

用法：
    python tools/check_skill_tags.py                     # 检查 skills/ 全部
    python tools/check_skill_tags.py --file <path>       # 检查单个文件
    python tools/check_skill_tags.py --self-test         # 变异验证
"""
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

TAG_RE = re.compile(r"\[(?:R\d+(?:·[^[\]]*)?|实测|设计|复现:\d+)\]")
RULE_WORD_RE = re.compile(r"(必须|禁止|不许|绝不|一定要|严禁)")
BULLET_RE = re.compile(r"^-\s+")


def check_file(path: Path):
    """返回 (errors, checked, tagged)。跳过 frontmatter 与代码块。"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors, checked, tagged = [], 0, 0
    in_fm = text.startswith("---")
    in_code = False
    for lineno, line in enumerate(lines, 1):
        s = line.strip()
        if in_fm:
            if lineno > 1 and s == "---":
                in_fm = False
            continue
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not BULLET_RE.match(s):
            continue
        if not RULE_WORD_RE.search(s):
            continue
        checked += 1
        if TAG_RE.search(s):
            tagged += 1
        else:
            errors.append(f"{path.name}:{lineno}: {s[:80]}")
    return errors, checked, tagged


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("---\nname: t\n---\n\n## 规则\n- 必须先跑验证。\n- 禁止硬编码路径。[实测]\n")
            tmp = Path(f.name)
        errs, checked, tagged = check_file(tmp)
        ok = len(errs) == 1 and checked == 2 and tagged == 1
        print(f"self-test: {'✅ PASS' if ok else '❌ FAIL'}（期望 1 裸/2 查/1 带，实际 {len(errs)}/{checked}/{tagged}）")
        tmp.unlink()
        return 0 if ok else 1

    files = [Path(args.file)] if args.file else sorted((REPO / "skills").glob("*/SKILL.md"))
    if not files:
        print("无文件可查"); return 2
    total_e, total_c, total_t = [], 0, 0
    for p in files:
        errs, c, t = check_file(p)
        total_e += errs; total_c += c; total_t += t
    print(f"检查 {len(files)} 个 SKILL.md：规则句 {total_c}，带标记 {total_t}，裸规则 {len(total_e)}")
    for e in total_e[:20]:
        print(f"  ❌ {e}")
    return 0 if not total_e else 1


if __name__ == "__main__":
    sys.exit(main())
