#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_doc_consistency.py — 文档一致性机验（AGI-Distiller 版）

问题：本仓库的 README / HEARTBEAT / NEXT 曾长期写「7 skills / 21 篇文章 / 12 节规则」，
      而工作区的真实值是「19 / — / 14」；README 里甚至同时存在真实仓库 URL 与幽灵仓库
      URL（`agi-distiller/agi-distiller`）。根因是**没有单一真值源，也没有门禁**。

做法：把「文档里声称的数字 / 路径 / 命令」与「工作区的事实」做机验。
     每个判据都能从工作区独立核验，不依赖网络、不依赖第三方库。

用法：
    python scripts/check_doc_consistency.py              # 跑全部判据
    python scripts/check_doc_consistency.py --self-test  # 变异验证：判据自身必须能 FAIL

退出码：0 = 全部通过；1 = 存在 FAIL。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover
        pass

ROOT = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────────────────────
# 工作区只读视图（变异测试时用 tamper 覆盖文件内容）
# ──────────────────────────────────────────────────────────────


class RepoView:
    def __init__(self, root: Path = ROOT, tamper: dict | None = None):
        self.root = root
        self.tamper = dict(tamper or {})

    def text(self, rel: str) -> str:
        if rel in self.tamper:
            return self.tamper[rel]
        p = self.root / rel
        if not p.is_file():
            return ""
        return p.read_text(encoding="utf-8", errors="replace")

    def dirs(self, rel: str) -> list[str]:
        d = self.root / rel
        if not d.is_dir():
            return []
        return sorted(x.name for x in d.iterdir() if x.is_dir())

    def files_under(self, rel: str, suffix: str) -> list[str]:
        d = self.root / rel
        if not d.is_dir():
            return []
        return sorted(
            str(p.relative_to(self.root)).replace("\\", "/")
            for p in d.rglob(f"*{suffix}")
            if p.is_file()
        )

    def files_glob(self, pattern: str) -> list[str]:
        return sorted(
            str(p.relative_to(self.root)).replace("\\", "/")
            for p in self.root.glob(pattern)
            if p.is_file()
        )

    def git(self, *args: str) -> str:
        try:
            r = subprocess.run(
                ["git", *args], cwd=str(self.root), capture_output=True, text=True, timeout=30
            )
            return r.stdout.strip()
        except Exception:
            return ""


# ──────────────────────────────────────────────────────────────
# 解析helpers
# ──────────────────────────────────────────────────────────────

SKILL_ROW = re.compile(r"^\|\s*`([a-z0-9][a-z0-9-]*)`\s*\|", re.M)


def _section(text: str, start: str) -> str:
    """取 start 标记之后、下一个 ### / --- 之前的内容。"""
    i = text.find(start)
    if i < 0:
        return ""
    i += len(start)
    ends = [len(text)]
    for m in ("\n### ", "\n## ", "\n---"):
        k = text.find(m, i)
        if k >= 0:
            ends.append(k)
    return text[i : min(ends)]


def _table_skills(text: str, head: str) -> list[str]:
    return SKILL_ROW.findall(_section(text, head))


def _cmp_skill_sets(label: str, claimed: list[str], actual: list[str]) -> list[str]:
    problems: list[str] = []
    dupes = sorted({s for s in claimed if claimed.count(s) > 1})
    if dupes:
        problems.append(f"{label}: 表格里重复列出 {dupes}")
    ghost = sorted(set(claimed) - set(actual))
    missing = sorted(set(actual) - set(claimed))
    if ghost:
        problems.append(f"{label}: 表格声称存在但目录里没有 -> {ghost}")
    if missing:
        problems.append(f"{label}: 目录里存在但表格漏列 -> {missing}")
    return problems


# ──────────────────────────────────────────────────────────────
# 判据
# ──────────────────────────────────────────────────────────────

HEAD_EN = "### Skills (Cross-Platform)"
HEAD_ZH = "### Skill（跨平台）"


def d1_skill_table_en(v: RepoView):
    actual = v.dirs("skills")
    if not actual:
        return False, "skills/ 目录为空或不存在"
    claimed = _table_skills(v.text("README.md"), HEAD_EN)
    problems = _cmp_skill_sets("README.md", claimed, actual)
    if problems:
        return False, "; ".join(problems)
    return True, f"README.md 表格 {len(claimed)} 项 == skills/ 目录 {len(actual)} 个"


def d2_skill_table_zh(v: RepoView):
    actual = v.dirs("skills")
    claimed = _table_skills(v.text("README.zh.md"), HEAD_ZH)
    problems = _cmp_skill_sets("README.zh.md", claimed, actual)
    if problems:
        return False, "; ".join(problems)
    return True, f"README.zh.md 表格 {len(claimed)} 项 == skills/ 目录 {len(actual)} 个"


def d3_zh_en_parity(v: RepoView):
    en = _table_skills(v.text("README.md"), HEAD_EN)
    zh = _table_skills(v.text("README.zh.md"), HEAD_ZH)
    if not en or not zh:
        return False, "中英 README 至少一侧解析不到 skill 表"
    if set(en) != set(zh):
        diff = sorted(set(en) ^ set(zh))
        return False, f"中英 skill 集合不一致 -> {diff}"
    if len(en) != len(zh):
        return False, f"中英条数不一致 en={len(en)} zh={len(zh)}"
    return True, f"中英 skill 集合一致，各 {len(en)} 项"


ATOM_EN = re.compile(r"\((\d+) sections?\)")
ATOM_EN2 = re.compile(r"(\d+)-section behavioral specification")
ATOM_ZH = re.compile(r"（(\d+) 节）")


def d4_atomcode_sections(v: RepoView):
    actual = len(re.findall(r"^## ", v.text("rules/ATOMCODE.md"), re.M))
    if actual == 0:
        return False, "rules/ATOMCODE.md 里数不到 ## 小节"
    problems = []
    for label, txt, rgx in (
        ("README.md", v.text("README.md"), ATOM_EN),
        ("README.md(roadmap)", v.text("README.md"), ATOM_EN2),
        ("README.zh.md", v.text("README.zh.md"), ATOM_ZH),
    ):
        ms = rgx.findall(txt)
        if not ms:
            problems.append(f"{label}: 找不到节数口径")
            continue
        for m in ms:
            if int(m) != actual:
                problems.append(f"{label}: 声称 {m} 节，实际 {actual} 节")
    if problems:
        return False, "; ".join(problems)
    return True, f"所有文档口径一致，ATOMCODE.md 实为 {actual} 节"


SRC_EN = re.compile(r"\*\*(\d+) distilled source notes on disk\*\*")
SRC_ZH = re.compile(r"已落盘 (\d+) 份蒸馏笔记")


def d5_sources_count(v: RepoView):
    actual = len(v.files_under("sources", ".md"))
    if actual == 0:
        return False, "sources/ 下数不到 .md 笔记"
    problems = []
    for label, txt, rgx in (
        ("README.md", v.text("README.md"), SRC_EN),
        ("README.zh.md", v.text("README.zh.md"), SRC_ZH),
    ):
        ms = rgx.findall(txt)
        if not ms:
            problems.append(f"{label}: 找不到落盘数口径")
            continue
        for m in ms:
            if int(m) != actual:
                problems.append(f"{label}: 声称 {m} 份，实际 {actual} 份")
    if problems:
        return False, "; ".join(problems)
    return True, f"落盘 {actual} 份，文档口径一致"


def d6_ci_flag(v: RepoView):
    wf = v.files_glob(".github/workflows/*.yml") + v.files_glob(".github/workflows/*.yaml")
    has = len(wf) > 0
    txt = v.text("README.md")
    checked = bool(re.search(r"^- \[x\] CI pipeline", txt, re.M))
    unchecked = bool(re.search(r"^- \[ \] CI pipeline", txt, re.M))
    if not checked and not unchecked:
        return False, "README.md 的 roadmap 里找不到 CI pipeline 条目"
    if has and not checked:
        return False, f"存在 {len(wf)} 个工作流，但 README 未勾选 CI pipeline"
    if (not has) and checked:
        return False, "README 勾选了 CI pipeline，但 .github/workflows/ 下没有工作流"
    return True, f"CI 实际存在={has}，README 勾选状态一致"


def d7_pycache_ignored(v: RepoView):
    gi = v.text(".gitignore")
    if "__pycache__/" not in gi:
        return False, ".gitignore 未忽略 __pycache__/（编译产物会再次误入仓）"
    tracked = [x for x in v.git("ls-files").splitlines() if x.endswith(".pyc")]
    if tracked:
        return False, f"仍有 {len(tracked)} 个 .pyc 被 git 跟踪 -> {tracked[:3]}"
    return True, "__pycache__/ 已忽略，且索引里无 .pyc"


PHANTOM = "agi-distiller/agi-distiller"
INSTALL_LINE = re.compile(r"^\s*(?:npx skills add|/plugin marketplace add)\s+(\S+)")


def _origin_slug(v: RepoView) -> str | None:
    url = v.git("remote", "get-url", "origin")
    m = re.search(r"github\.com[:/]+([^/]+)/([^/\s]+?)(?:\.git)?$", url)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2)}"


def d8_repo_url(v: RepoView):
    slug = _origin_slug(v)
    if not slug:
        return False, "无法从 git remote 解析 owner/repo"
    problems = []
    for f in ("README.md", "README.zh.md", ".claude-plugin/plugin.json"):
        if PHANTOM in v.text(f):
            problems.append(f"{f}: 含幽灵仓库路径 {PHANTOM}")
    try:
        hp = json.loads(v.text(".claude-plugin/plugin.json")).get("homepage", "")
    except Exception:
        hp = ""
    if slug.lower() not in hp.lower():
        problems.append(f"plugin.json homepage={hp!r} != origin {slug!r}")
    for f in ("README.md", "README.zh.md"):
        for line in v.text(f).splitlines():
            m = INSTALL_LINE.match(line)
            if m and slug.lower() not in m.group(1).lower():
                problems.append(f"{f}: 安装命令指向 {m.group(1)!r}，而非 {slug!r}")
    if problems:
        return False, "; ".join(problems)
    return True, f"仓库 URL 全部指向 {slug}"


HB_NUM = {
    "生产级 skill": lambda v: len(v.dirs("skills")),
    "行为规范节数（ATOMCODE.md）": lambda v: len(re.findall(r"^## ", v.text("rules/ATOMCODE.md"), re.M)),
    "落盘蒸馏笔记": lambda v: len(v.files_under("sources", ".md")),
}


def d9_heartbeat_numbers(v: RepoView):
    txt = v.text("HEARTBEAT.md")
    if not txt:
        return False, "HEARTBEAT.md 不存在"
    problems = []
    for label, fn in HB_NUM.items():
        m = re.search(r"\|\s*" + re.escape(label) + r"\s*\|\s*(\d+)\s*\|", txt)
        if not m:
            problems.append(f"HEARTBEAT.md 找不到「{label}」行")
            continue
        claimed, actual = int(m.group(1)), fn(v)
        if claimed != actual:
            problems.append(f"HEARTBEAT.md「{label}」声称 {claimed}，实际 {actual}")
    if problems:
        return False, "; ".join(problems)
    return True, f"HEARTBEAT.md 的 {len(HB_NUM)} 个数字与工作区一致"


VER_HB = re.compile(r"`(\d+\.\d+\.\d+)`（未打 tag）")


def d10_version_parity(v: RepoView):
    try:
        pj = json.loads(v.text(".claude-plugin/plugin.json")).get("version", "")
    except Exception:
        return False, "plugin.json 无法解析"
    m = VER_HB.search(v.text("HEARTBEAT.md"))
    if not m:
        return False, "HEARTBEAT.md 找不到版本口径"
    if pj != m.group(1):
        return False, f"plugin.json={pj!r} != HEARTBEAT.md={m.group(1)!r}"
    return True, f"版本口径一致：{pj}"


SPEC_ROW_EN = re.compile(r"^\|\s*`([A-Z]+\.md)`\s*\|[^|]*\|\s*~(\d+) chars\s*\|", re.M)
SPEC_TOT_EN = re.compile(r"^\|\s*\*\*Total\*\*\s*\|\s*\|\s*\*\*~(\d+) chars\*\*\s*\|", re.M)
SPEC_ROW_ZH = re.compile(r"^\|\s*`([A-Z]+\.md)`\s*\|[^|]*\|\s*~(\d+) 字符\s*\|", re.M)
SPEC_TOT_ZH = re.compile(r"^\|\s*\*\*总计\*\*\s*\|\s*\|\s*\*\*~(\d+) 字符\*\*\s*\|", re.M)


def d11_spec_sizes(v: RepoView):
    """README 里 agent spec 文件表声明的字符数 == 文件实际字符数（此前整表全错）。"""
    problems = []
    for label, txt, row_rgx, tot_rgx in (
        ("README.md", v.text("README.md"), SPEC_ROW_EN, SPEC_TOT_EN),
        ("README.zh.md", v.text("README.zh.md"), SPEC_ROW_ZH, SPEC_TOT_ZH),
    ):
        rows = row_rgx.findall(txt)
        if not rows:
            problems.append(f"{label}: 找不到 agent spec 字符数表")
            continue
        total = 0
        for fname, claimed in rows:
            actual = len(v.text(fname))
            if actual == 0:
                problems.append(f"{label}: 表里列的 {fname} 在工作区不存在")
                continue
            if int(claimed) != actual:
                problems.append(f"{label}: {fname} 声称 {claimed}，实际 {actual}")
            total += actual
        m = tot_rgx.search(txt)
        if not m:
            problems.append(f"{label}: 找不到 Total 行")
        elif int(m.group(1)) != total:
            problems.append(f"{label}: 总计声称 {m.group(1)}，各项之和 {total}")
    if problems:
        return False, "; ".join(problems)
    return True, "agent spec 字符数表与实际文件一致"


def d12_twin_scripts(v: RepoView):
    """仓库自用的 scripts/pre-commit/ 与分发的 templates/scripts/pre-commit/ 必须逐字节一致。

    两份是孪生文件：一份给本仓库用，一份给下游项目当模板。任一改另一份不改 → 模板静默漂移。
    """
    a_dir, b_dir = "scripts/pre-commit", "templates/scripts/pre-commit"
    a = {p.rsplit("/", 1)[1] for p in v.files_under(a_dir, ".py")}
    b = {p.rsplit("/", 1)[1] for p in v.files_under(b_dir, ".py")}
    if not a and not b:
        return False, "两处 pre-commit 目录都没有 .py 脚本"
    problems = []
    only_a = sorted(a - b)
    only_b = sorted(b - a)
    if only_a:
        problems.append(f"只在 {a_dir} 有：{only_a}")
    if only_b:
        problems.append(f"只在 {b_dir} 有：{only_b}")
    for n in sorted(a & b):
        ca, cb = v.text(f"{a_dir}/{n}"), v.text(f"{b_dir}/{n}")
        if ca != cb:
            problems.append(f"{n}: 两份内容不一致（仓库自用 vs 模板）")
    if problems:
        return False, "; ".join(problems)
    return True, f"{len(a)} 个 pre-commit 脚本在两处内容一致"


MKT = ".claude-plugin/marketplace.json"
PLG = ".claude-plugin/plugin.json"
INSTALL_PLUGIN_CMD = re.compile(r"^\s*/plugin install\s+([A-Za-z0-9_-]+)@([A-Za-z0-9_-]+)\s*$", re.M)


def d13_marketplace_manifest(v: RepoView):
    """Claude Code marketplace 清单必须与 plugin 清单对齐，且 README 的安装命令能解析成同一 (plugin, marketplace) 对。

    背景：此前 README 白纸黑字写着 `/plugin install agi-distiller@agi-distiller`，
    但仓库里连 `.claude-plugin/` 目录都不存在 —— 这条命令 100% 失败，却从未有人跑过一次。
    """
    problems = []
    mkt_raw, plg_raw = v.text(MKT), v.text(PLG)
    if not mkt_raw:
        return False, f"{MKT} 不存在（`/plugin marketplace add` 必然失败）"
    if not plg_raw:
        return False, f"{PLG} 不存在"
    try:
        mkt = json.loads(mkt_raw)
        plg = json.loads(plg_raw)
    except Exception as e:
        return False, f"manifest JSON 解析失败: {e}"
    if not mkt.get("name"):
        problems.append("marketplace.json 缺 name")
    if not mkt.get("owner"):
        problems.append("marketplace.json 缺 owner")
    entries = mkt.get("plugins") or []
    if not entries:
        return False, "marketplace.json plugins 为空"
    e = entries[0]
    if e.get("name") != plg.get("name"):
        problems.append(
            f"entry name={e.get('name')!r} != plugin.json name={plg.get('name')!r}（安装会报 not found）"
        )
    if e.get("version") != plg.get("version"):
        problems.append(
            f"entry version={e.get('version')!r} != plugin.json version={plg.get('version')!r}"
        )
    src = e.get("source")
    if not isinstance(src, str) or ".." in src:
        problems.append(f"entry source={src!r} 应为 marketplace 根起的相对路径且不含 '..'")
    for f in ("README.md", "README.zh.md"):
        seen = False
        for line in v.text(f).splitlines():
            m = INSTALL_PLUGIN_CMD.match(line)
            if not m:
                continue
            seen = True
            if m.group(1) != plg.get("name") or m.group(2) != mkt.get("name"):
                problems.append(
                    f"{f}: 安装命令 {m.group(0).strip()!r} 与 manifest 不符"
                    f"（应为 {plg.get('name')}@{mkt.get('name')}）"
                )
        if not seen:
            problems.append(f"{f}: 找不到 /plugin install 命令")
    if problems:
        return False, "; ".join(problems)
    return True, f"marketplace 清单自洽：{plg.get('name')}@{mkt.get('name')} v{plg.get('version')}"


PLAT_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*`[^`]+`\s*\|\s*([^|]+?)\s*\|\s*$", re.M)
PLAT_HDR_EN = "### Platform Compatibility"
PLAT_HDR_ZH = "### 平台兼容性"
VERIFIED_MARK = "✅"
EVIDENCE_HDR_EN = "Verified"
EVIDENCE_HDR_ZH = "实测口径"


def _plat_section(txt: str, header: str) -> str:
    if header not in txt:
        return ""
    seg = txt.split(header, 1)[1]
    for stop in ("\n---", "\n## "):
        if stop in seg:
            seg = seg.split(stop, 1)[0]
    return seg


def _plat_rows(txt: str, header: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in PLAT_ROW.finditer(_plat_section(txt, header))]


def _plat_prose(txt: str, header: str) -> str:
    seg = _plat_section(txt, header)
    return "\n".join(l for l in seg.splitlines() if not l.lstrip().startswith("|"))


def d14_platform_table_parity(v: RepoView):
    """中英平台兼容表必须逐行对等，且每个 ✅ 都必须有实测证据背书。

    背景：英文表 6 行、中文表 7 行（英文漏了 Windsurf）；更严重的是 7 个平台全打 ✅，
    而实际上除了 Claude Code 之外一个都没在本机跑过 —— 把"未经实测"写成了"已支持"。
    """
    problems = []
    en = _plat_rows(v.text("README.md"), PLAT_HDR_EN)
    zh = _plat_rows(v.text("README.zh.md"), PLAT_HDR_ZH)
    if not en or not zh:
        return False, f"平台表缺失（en={len(en)} 行, zh={len(zh)} 行）"
    en_names = [n for n, _ in en]
    zh_names = [n for n, _ in zh]
    if en_names != zh_names:
        problems.append(
            f"中英平台不对等：仅英文有 {[x for x in en_names if x not in zh_names]}，"
            f"仅中文有 {[x for x in zh_names if x not in en_names]}"
        )
    if [s for _, s in en] != [s for _, s in zh]:
        problems.append("中英平台表的状态列不一致")
    # 每个 ✅ 必须有实测证据：在「实测口径」说明文字里被点名
    for label, txt, header in (
        ("README.md", v.text("README.md"), PLAT_HDR_EN),
        ("README.zh.md", v.text("README.zh.md"), PLAT_HDR_ZH),
    ):
        prose = _plat_prose(txt, header)
        if not prose.strip():
            problems.append(f"{label} 平台表下方缺「实测口径」说明")
            continue
        for name, status in _plat_rows(txt, header):
            if VERIFIED_MARK in status and name not in prose:
                problems.append(
                    f"{label}: 平台「{name}」标 ✅ 但未在实测口径说明中点名（无证据的 ✅ = 虚假宣称）"
                )
    if problems:
        return False, "; ".join(problems)
    n_ok = sum(1 for _, s in en if VERIFIED_MARK in s)
    return True, f"平台表中英对等（{len(en)} 个平台，其中 {n_ok} 个有实测证据）"


CHECKS = [
    ("D1", "README.md skill 表 == skills/ 目录", d1_skill_table_en),
    ("D2", "README.zh.md skill 表 == skills/ 目录", d2_skill_table_zh),
    ("D3", "中英 README skill 集合对等", d3_zh_en_parity),
    ("D4", "ATOMCODE 节数口径", d4_atomcode_sections),
    ("D5", "sources 落盘笔记数口径", d5_sources_count),
    ("D6", "CI 状态勾选 vs 工作流实际", d6_ci_flag),
    ("D7", "编译产物不进仓", d7_pycache_ignored),
    ("D8", "仓库 URL 无幽灵路径", d8_repo_url),
    ("D9", "HEARTBEAT 数字可核验", d9_heartbeat_numbers),
    ("D10", "版本号中英/配置对等", d10_version_parity),
    ("D11", "agent spec 字符数表 == 实际文件", d11_spec_sizes),
    ("D12", "自用/模板 pre-commit 脚本内容一致", d12_twin_scripts),
    ("D13", "marketplace 清单与安装命令自洽", d13_marketplace_manifest),
    ("D14", "中英平台兼容表对等", d14_platform_table_parity),
]


# ──────────────────────────────────────────────────────────────
# 变异定义（--self-test 用）：每条判据必须能被自己的变异打破
# ──────────────────────────────────────────────────────────────


def _sub1(text: str, old: str, new: str) -> str:
    assert old in text, f"变异锚点缺失: {old!r}"
    return text.replace(old, new, 1)


MUTATIONS: dict[str, callable] = {
    "D1": lambda v: {"README.md": _sub1(v.text("README.md"), "`workspace-isolation`", "`ghost-skill`")},
    "D2": lambda v: {"README.zh.md": _sub1(v.text("README.zh.md"), "`workspace-isolation`", "`ghost-skill`")},
    "D3": lambda v: {"README.zh.md": _sub1(v.text("README.zh.md"), "`workspace-isolation`", "`ghost-skill`")},
    "D4": lambda v: {"README.md": _sub1(v.text("README.md"), "(14 sections)", "(12 sections)")},
    "D5": lambda v: {"README.md": _sub1(v.text("README.md"), "**8 distilled source notes", "**7 distilled source notes")},
    "D6": lambda v: {"README.md": _sub1(v.text("README.md"), "- [x] CI pipeline", "- [ ] CI pipeline")},
    "D7": lambda v: {".gitignore": v.text(".gitignore").replace("__pycache__/", "__never_ignore__/")},
    "D8": lambda v: {".claude-plugin/plugin.json": _sub1(v.text(".claude-plugin/plugin.json"), "TrueFurina/AGI-Distiller", PHANTOM)},
    "D9": lambda v: {"HEARTBEAT.md": _sub1(v.text("HEARTBEAT.md"), "| 生产级 skill | 19 |", "| 生产级 skill | 7 |")},
    "D10": lambda v: {".claude-plugin/plugin.json": _sub1(v.text(".claude-plugin/plugin.json"), '"version": "0.1.0"', '"version": "9.9.9"')},
    "D11": lambda v: {"README.md": _sub1(v.text("README.md"), "~1187 chars", "~1 chars")},
    "D12": lambda v: {
        "templates/scripts/pre-commit/caliber_check.py": v.text(
            "templates/scripts/pre-commit/caliber_check.py"
        )
        + "\n# mutated in self-test\n"
    },
    "D13": lambda v: {
        MKT: _sub1(v.text(MKT), '"name": "agi-distiller"', '"name": "phantom-marketplace"')
    },
    "D14": lambda v: {
        "README.md": _sub1(v.text("README.md"), "| GitHub Copilot |", "| Ghost Platform |")
    },
}


# ──────────────────────────────────────────────────────────────
# 运行器
# ──────────────────────────────────────────────────────────────


def run_all(view: RepoView, verbose: bool = True) -> int:
    fails = 0
    for cid, title, fn in CHECKS:
        try:
            ok, detail = fn(view)
        except Exception as e:  # 判据自身崩溃也算 FAIL，绝不静默通过
            ok, detail = False, f"判据崩溃 {type(e).__name__}: {e}"
        if ok:
            if verbose:
                print(f"  PASS  [{cid}] {title} -- {detail}")
        else:
            fails += 1
            print(f"  FAIL  [{cid}] {title} -- {detail}")
    return fails


def self_test() -> int:
    """变异验证：把每条判据的真值来源故意改坏，判据必须 FAIL。"""
    print("== 变异验证：判据必须能检出被篡改的文档 ==")
    bad = 0
    base = RepoView()
    for cid, title, fn in CHECKS:
        mut = MUTATIONS.get(cid)
        if mut is None:
            print(f"  FAIL  [{cid}] 缺少变异定义")
            bad += 1
            continue
        try:
            tamper = mut(base)
        except Exception as e:
            print(f"  FAIL  [{cid}] 变异构造失败: {e}")
            bad += 1
            continue
        ok, _ = fn(RepoView(tamper=tamper))
        if ok:
            print(f"  FAIL  [{cid}] 变异未被检出 —— 判据无效（{title}）")
            bad += 1
        else:
            print(f"  PASS  [{cid}] 变异已检出（{title}）")
    if bad:
        print(f"\n变异验证失败：{bad}/{len(CHECKS)} 条判据无法自证有效性")
        return 1
    print(f"\n变异验证通过：{len(CHECKS)}/{len(CHECKS)} 条判据均可检出对应变异")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    print(f"== 文档一致性机验 @ {ROOT} ==")
    fails = run_all(RepoView())
    if fails:
        print(f"\n结果：{fails}/{len(CHECKS)} 条判据 FAIL —— 文档落后于事实，请修正后重跑。")
        return 1
    print(f"\n结果：{len(CHECKS)}/{len(CHECKS)} 条判据全部 PASS。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
