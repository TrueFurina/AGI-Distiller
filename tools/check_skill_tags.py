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

附加结构检查（hygiene，2026-10-01 第 21 轮加）：
    H1. frontmatter 的 `name` 必须**等于所在目录名**（开放标准要求）；
    H2. `allowed-tools` 用**逗号**分隔。

    H2 的依据不是"空格更标准"，恰恰相反——**两份规范冲突，而实测站逗号这边**：
      · agentskills.io 开放标准：空格分隔；
      · Claude Code v2.1.251 二进制内的 frontmatter schema：
        "Comma-separated string or YAML list"（2026-10-01 本机提取）。
    本仓按**唯一实测过的宿主**对齐，证据与提取方法见
    `sources/anthropic/skill-authoring-standard.md` §八。
    这条检查的作用是**防误改**（防止有人照着单一规范批量改回去），不是断言逗号更正确。

退出码：0 = 通过；1 = 发现裸规则或结构问题（列出 文件:行号:内容）。

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


FM_NAME = re.compile(r"^name:\s*(.+?)\s*$", re.M)
FM_TOOLS = re.compile(r"^allowed-tools:\s*(.+?)\s*$", re.M)


def hygiene_errors(path: Path) -> list[str]:
    """结构检查：name == 目录名；allowed-tools 逗号分隔（详见模块 docstring 的 H1/H2）。"""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return [f"{path.parent.name}: 缺少 frontmatter"]
    fm = text.split("---", 2)[1]
    errs: list[str] = []
    m = FM_NAME.search(fm)
    if not m:
        errs.append(f"{path.parent.name}: frontmatter 缺 name")
    elif m.group(1).strip() != path.parent.name:
        errs.append(
            f"{path.parent.name}: name={m.group(1).strip()!r} != 目录名 {path.parent.name!r}"
        )
    t = FM_TOOLS.search(fm)
    if t:
        v = t.group(1).strip()
        # 合法写法只有两种：YAML 列表 `[a, b]`，或形如 `a, b, c` 的行内字符串
        if not v.startswith("[") and not re.fullmatch(r"\S+(?:\s*,\s*\S+)*", v):
            errs.append(
                f"{path.parent.name}: allowed-tools 不是逗号分隔（{v[:48]!r}）"
                " —— 本仓按实测宿主 Claude Code 的 schema 用逗号，别照 agentskills.io 那套改"
            )
    return errs


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
        print(
            f"self-test 裸规则: {'✅ PASS' if ok else '❌ FAIL'}"
            f"（期望 1 裸/2 查/1 带，实际 {len(errs)}/{checked}/{tagged}）"
        )
        tmp.unlink()
        bad = 0 if ok else 1

        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "demo-skill"
            d.mkdir()
            p = d / "SKILL.md"
            good = "---\nname: demo-skill\nallowed-tools: read_file, grep\n---\n\n正文。\n"
            p.write_text(good, encoding="utf-8")
            ok_good = hygiene_errors(p) == []
            p.write_text(good.replace("name: demo-skill", "name: other"), encoding="utf-8")
            ok_name = len(hygiene_errors(p)) == 1
            p.write_text(good.replace("read_file, grep", "read_file grep"), encoding="utf-8")
            ok_tools = len(hygiene_errors(p)) == 1
            p.write_text(good.replace("read_file, grep", "[read_file, grep]"), encoding="utf-8")
            ok_yaml = hygiene_errors(p) == []
            h_ok = ok_good and ok_name and ok_tools and ok_yaml
            print(
                f"self-test 结构 H1/H2: {'✅ PASS' if h_ok else '❌ FAIL'}"
                f"（合规={ok_good} name不符={ok_name} 空格分隔={ok_tools} YAML列表豁免={ok_yaml}）"
            )
            if not h_ok:
                bad += 1
        return 0 if not bad else 1

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
    hy = []
    for p in files:
        hy += hygiene_errors(p)
    print(f"结构检查（name==目录名 / allowed-tools 逗号分隔）：{len(hy)} 处问题")
    for e in hy[:20]:
        print(f"  ❌ {e}")
    return 0 if not (total_e or hy) else 1


if __name__ == "__main__":
    sys.exit(main())
