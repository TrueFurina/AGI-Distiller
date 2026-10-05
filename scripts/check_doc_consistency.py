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


MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SKIP_SCHEME = ("http://", "https://", "#", "mailto:")


def d15_relative_links(v: RepoView):
    """所有 Markdown 里的相对链接都必须指向真实存在的文件。

    背景：README 里写着 `See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.`，
    而这个文件根本不存在 —— 对想投稿的人来说，这是第一个、也是最劝退的一个死链。
    """
    problems = []
    checked = 0
    for md in sorted(ROOT.rglob("*.md")):
        if ".git" in md.parts:
            continue
        rel = md.relative_to(ROOT).as_posix()
        for url in MD_LINK.findall(v.text(rel)):
            if url.startswith(SKIP_SCHEME):
                continue
            checked += 1
            target = (md.parent / url.split("#")[0]).resolve()
            try:
                t_rel = target.relative_to(ROOT).as_posix()
                exists = bool(v.text(t_rel))
            except ValueError:
                exists = target.exists()
            if not exists:
                problems.append(f"{rel} → {url}")
    if problems:
        return False, f"{len(problems)} 处断链：{'; '.join(problems[:3])}"
    return True, f"{checked} 个相对链接全部指向存在的文件"


PIAN = re.compile(r"(\d+)\s*篇")
PIAN_FILES = ("DISTILLER.md", "README.md", "README.zh.md", "HEARTBEAT.md", "ROADMAP.md")
# 明确标了「目标 / 规划 / 历史 / 待办」语境的行不算虚报 —— 那是愿景或回顾，不是已完成的声称
PIAN_EXEMPT = ("目标", "规划", "计划", "愿景", "当时", "此前", "实际", "- [ ]", "[ ]")
# 同一行自带实际值对照（如 `| 50 篇 | **8 份** |`）→ 是"目标 vs 实际"对照行，不是虚报
PIAN_HAS_ACTUAL = re.compile(r"\*\*\d+\s*份\*\*")


def d16_source_count_claims(v: RepoView):
    """文档里形如「N 篇」的**已完成声称**不得超过 sources/ 实际落盘笔记数。

    背景：README 的篇数早已校准到 8，但 DISTILLER.md 里还写着「19 篇 laodad.com 文章」——
    同一个数字在多份文档里各写各的，改了一处漏了另一处。

    ⚠️ 局限（必须写明）：这是**纯文本启发式**判据。它只认「行内有没有语境豁免词」，
    分不清真正的语义。第一版没有豁免词，立刻误报 3 处——
    「规划目标 50 篇」「此前错写 21 篇」「待办：批量蒸馏 10 篇」全都是合法语境。
    它拦得住"无语境的裸虚报"，拦不住"给虚报加个'目标'字样"。别把它当硬保证。
    """
    actual = len(v.files_under("sources", ".md"))
    problems = []
    for f in PIAN_FILES:
        for line in v.text(f).splitlines():
            if any(w in line for w in PIAN_EXEMPT) or PIAN_HAS_ACTUAL.search(line):
                continue
            for m in PIAN.finditer(line):
                n = int(m.group(1))
                if n > actual:
                    problems.append(f"{f}: 声称 {n} 篇 > 实际落盘 {actual} 份（行：{line.strip()[:40]}）")
    if problems:
        return False, "; ".join(problems)
    return True, f"所有「N 篇」声称均不超过实际落盘 {actual} 份"


CHECKS_CLAIM = re.compile(r"(\d+)\s*条判据")
# 不含 NEXT.md：那是历史流水账，天然写着「当时 10 条」这类历史数字，
# 用"当前条数"去卡它只会误报（与 D16 的语境豁免同理）。
CHECKS_CLAIM_FILES = ("CONTRIBUTING.md", "README.md", "README.zh.md")


def d17_checks_count_claims(v: RepoView):
    """文档里声称的「N 条判据」必须等于 CHECKS 的实际长度。

    背景：CONTRIBUTING.md 写「14 条判据」时，实际已经是 16 条 ——
    这种自指数字最容易漂：每次加判据都会让它错一点。
    """
    actual = len(CHECKS)
    problems = []
    for f in CHECKS_CLAIM_FILES:
        for m in CHECKS_CLAIM.finditer(v.text(f)):
            n = int(m.group(1))
            if n != actual:
                problems.append(f"{f}: 声称 {n} 条判据 != 实际 {actual} 条")
    if problems:
        return False, "; ".join(problems)
    return True, f"判据条数声称与实际一致（{actual} 条）"


# ── D18 / D19：PR / issue 模板健全性 ──────────────────────────
# 背景：CONTRIBUTING.md 写好了，但 .github/ 下除 workflows 外什么都没有。
# 模板里的命令和 label 一旦写错，是**静默失效**（没人报错，就是不生效），
# 比显式报错更该拦。
#
# 局限（写在明处）：本脚本承诺零第三方依赖，故不做完整 YAML 解析，
# 而是对**我们自己撰写的、缩进规整**的模板做文本层校验。
# 覆盖 GitHub issue form schema 的关键约束，不覆盖 schema 全部细节。

PR_TPL = ".github/PULL_REQUEST_TEMPLATE.md"
ISSUE_TPL_DIR = ".github/ISSUE_TEMPLATE"
ISSUE_CONFIG = ".github/ISSUE_TEMPLATE/config.yml"

# GitHub 官方文档「Syntax for GitHub's form schema」列出的合法 body 元素类型。
# 注意：单行文本是 `input`（不是 `textinput`）—— 官方示例即如此。
ISSUE_BODY_TYPES = {"markdown", "input", "textarea", "dropdown", "checkboxes", "upload"}

# 仓库现有 label（GitHub 建仓时自带的 9 个）。
# 官方明确：「若 label 不存在于仓库，它不会被自动添加到 issue」——
# 即模板里写了个不存在的 label 是**静默失效**，不会报错。
# 局限：此处为静态快照；若远端新增/删除 label，需同步本集合。
REPO_LABELS = {
    "bug", "documentation", "duplicate", "enhancement",
    "good first issue", "help wanted", "invalid", "question", "wontfix",
}

# PR 模板里形如 `python scripts/xxx.py` 的命令引用
PY_CMD = re.compile(r"python\s+([A-Za-z0-9_./\-]+\.py)")


def _form_top_keys(txt: str) -> set[str]:
    return set(re.findall(r"^([A-Za-z_]+):", txt, re.M))


def _form_labels(txt: str) -> list[str]:
    m = re.search(r'^labels:\s*\[(.*?)\]\s*$', txt, re.M)
    if not m:
        return []
    return [x.strip().strip("\"'") for x in m.group(1).split(",") if x.strip()]


def _form_elements(txt: str) -> list[dict]:
    """文本层状态机：解析 body 元素（type / id / label）。"""
    els: list[dict] = []
    cur: dict | None = None
    for line in txt.splitlines():
        m = re.match(r"^  - type:\s*(\S+)\s*$", line)
        if m:
            cur = {"type": m.group(1), "id": None, "label": None}
            els.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^    id:\s*(\S+)\s*$", line)
        if m:
            cur["id"] = m.group(1)
            continue
        # attributes.label 缩进 6 空格；checkbox 的 option `- label:` 缩进 8 且带 "- "
        m = re.match(r"^      label:\s*(.+?)\s*$", line)
        if m:
            cur["label"] = m.group(1)
    return els


def _form_files(v: RepoView) -> list[str]:
    return [f for f in v.files_under(ISSUE_TPL_DIR, ".yml")
            if not f.endswith("config.yml")]


def d18_pr_template_commands(v: RepoView):
    """PR 模板必须存在，且其中 `python <path>` 引用的脚本真实存在。

    背景：CONTRIBUTING.md 承诺"三条命令可自检"，PR 模板是投稿人真正照抄的地方。
    模板里写了个不存在的脚本路径，投稿人会照着跑、然后报"命令不存在"。
    """
    md_files = {f for f in v.files_glob("**/*.md") if ".git/" not in f}
    if PR_TPL not in md_files:
        return False, f"缺少 {PR_TPL}"
    txt = v.text(PR_TPL)
    refs = sorted(set(PY_CMD.findall(txt)))
    if not refs:
        return False, f"{PR_TPL} 未引用任何自检命令（投稿人无从自检）"
    py_files = {f for f in v.files_glob("**/*.py") if ".git/" not in f}
    missing = [r for r in refs if r not in py_files]
    if missing:
        return False, f"{PR_TPL} 引用了不存在的脚本: {missing}"
    return True, f"PR 模板引用的 {len(refs)} 个脚本均真实存在"


def d19_issue_forms_valid(v: RepoView):
    """issue form 必须符合 GitHub schema，且 label 必须真实存在。"""
    files = _form_files(v)
    if not files:
        return False, f"{ISSUE_TPL_DIR} 下无任何 issue form"
    problems = []
    for f in files:
        txt = v.text(f)
        keys = _form_top_keys(txt)
        for need in ("name", "description", "body"):
            if need not in keys:
                problems.append(f"{f}: 缺顶层字段 {need}")
        for lab in _form_labels(txt):
            if lab not in REPO_LABELS:
                problems.append(f"{f}: label 不在仓库现有集合中: {lab!r}（会被静默忽略）")
        seen: set[str] = set()
        for el in _form_elements(txt):
            if el["type"] not in ISSUE_BODY_TYPES:
                problems.append(f"{f}: 非法 body type {el['type']!r}")
                continue
            if el["type"] == "markdown":
                continue
            if not el["id"]:
                problems.append(f"{f}: {el['type']} 元素缺 id")
            elif el["id"] in seen:
                problems.append(f"{f}: id 重复 {el['id']!r}")
            else:
                seen.add(el["id"])
            if not el["label"]:
                problems.append(f"{f}: 元素 {el['id']!r} 缺 label")
    if ISSUE_CONFIG in files or ISSUE_CONFIG in v.files_glob("**/*.yml"):
        cfg = v.text(ISSUE_CONFIG)
        if re.search(r"^blank_issues_enabled:\s*true\s*$", cfg, re.M):
            problems.append(f"{ISSUE_CONFIG}: blank_issues_enabled=true（会绕过全部模板）")
    else:
        problems.append(f"缺少 {ISSUE_CONFIG}（blank_issues_enabled / contact_links）")
    if problems:
        return False, "; ".join(problems)
    return True, f"{len(files)} 个 issue form 均合法，label 均在仓库集合内"


# ── D20：CI 触发路径必须覆盖「被机验监视的文件」 ──────────────
# 背景（2026-10-05 实测）：两套工具（本脚本 + tools/sync_counts.py）共监视 20+ 个文件，
# 而 CI 的 paths 只列了其中一部分 —— 改 CONTRIBUTING.md / NEXT.md / ROADMAP.md /
# DISTILLER.md / .claude-plugin/plugin.json / .github/ISSUE_TEMPLATE/*.yml / 两份
# pre-commit 脚本，**都不会触发 CI**。门存在，但不为这些改动而开。
#
# 最刺眼的一条是自己造的：上一轮把 plugin.json 从仓库根移入 .claude-plugin/ 后，
# CI 里那条根级 `plugin.json` 就再也匹配不到它了（移动文件时不只脚本要跟着改）。
#
# 做法：watched 集合靠**执行取证** —— 挂一层记录器跑一遍全部判据，再读 sync_counts 的
# 站点表；不靠正则猜文件名。猜出来的集合会与真实访问漂移，那正是它要防的病。

CI_WF = ".github/workflows/golden-regression.yml"


def _ci_paths(txt: str) -> list[str]:
    """抽出 workflow 里各触发条件的 paths 条目（容忍缩进与引号差异）。"""
    lines = txt.splitlines()
    out: list[str] = []
    for i, line in enumerate(lines):
        if not re.match(r"^\s*paths:\s*$", line):
            continue
        base = len(line) - len(line.lstrip())
        for nxt in lines[i + 1:]:
            if not nxt.strip():
                continue
            if len(nxt) - len(nxt.lstrip()) > base and nxt.strip().startswith("- "):
                out.append(nxt.strip()[2:].strip().strip("'\""))
            else:
                break
    return out


def _glob_to_re(pat: str) -> str:
    """GitHub paths 语义：`**` 跨目录层级（可匹配零层），`*` 不跨 `/`。

    注意 workflow 里用的是官方示例形式 `**.md`（文档原话：匹配"任意位置的 .md 文件"），
    并额外显式补了 `*.md` 覆盖仓库根 —— `**/*.md` 对根目录文件的行为官方没有权威说明，
    本判据不去赌它。
    """
    out, i = "", 0
    while i < len(pat):
        if pat.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pat.startswith("**", i):
            out += ".*"
            i += 2
        elif pat[i] == "*":
            out += "[^/]*"
            i += 1
        elif pat[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pat[i])
            i += 1
    return out


def _covered(path: str, patterns: list[str]) -> bool:
    return any(re.fullmatch(_glob_to_re(p), path) for p in patterns)


class _ProbeView(RepoView):
    """记录「判据实际读了什么」的视图 —— 执行取证，不靠正则猜文件名。

    只记录**具体文件**：目录本身不是 CI 的触发单位，真正会被改动的是文件。
    早先记录 `skills/**` 这类前缀，导致 CI（按文件类型覆盖）被误判成不达标 ——
    判据看错了对象，改的是判据，不是文档。
    """

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.seen: set[str] = set()

    def text(self, rel: str) -> str:
        self.seen.add(rel)
        return super().text(rel)

    def files_under(self, rel: str, suffix: str) -> list[str]:
        found = super().files_under(rel, suffix)
        self.seen.update(found)
        return found

    def files_glob(self, pattern: str) -> list[str]:
        found = super().files_glob(pattern)
        self.seen.update(found)
        return found

    def dirs(self, rel: str) -> list[str]:
        return super().dirs(rel)  # 目录名不是文件；其下文件由 files_under / files_glob 现身


def _watched(v: RepoView) -> set[str]:
    """被两套工具监视的路径全集（文件 + 目录前缀模式）。"""
    probe = _ProbeView()
    for cid, _title, fn in CHECKS:
        if cid == "D20":  # 跳过自身：否则 run_all -> D20 -> run_all 无限递归
            continue
        try:
            fn(probe)
        except Exception:
            pass  # 某条判据崩溃时它自己会报 FAIL，这里只关心它读了哪些文件
    seen = set(probe.seen)

    sys.path.insert(0, str(ROOT / "tools"))
    import sync_counts as sc  # noqa: E402

    for _n, f, _p, _fld in sc.SITES:
        seen.add(f)
    for _n, f, _p in sc.BREAKDOWN_SITES:
        seen.add(f)
    for f, _p in sc.FROZEN_MARKERS:
        seen.add(f)
    seen |= set(sc.SIZE_SITES.keys())

    def _rec(rel: str) -> str:
        seen.add(rel)
        return v.text(rel)

    try:
        sc.scan(read=_rec)
    except Exception:
        pass

    # 只保留真实存在的文件：路径写错、文件不存在属别的判据管辖，不由本判据报
    return {p for p in seen if "*" not in p and (ROOT / p).is_file()}


def d20_ci_paths_cover_watched(v: RepoView):
    """CI 必须为「每一个被机验监视的文件」而触发。

    否则会出现最坏的一种假绿：门写好了、判据也是活的，但**改那个文件时 CI 根本不跑** ——
    本地 --self-test 全绿、远端一片绿，而漂移已经进去了。
    """
    txt = v.text(CI_WF)
    if not txt:
        return False, f"缺少 {CI_WF}"
    pats = _ci_paths(txt)
    if not pats:
        return False, f"{CI_WF} 未解析到 paths —— 触发范围不可核验（放开为全量跑时请更新本判据）"
    watched = _watched(v)
    gaps = sorted(p for p in watched if not _covered(p, pats))
    if gaps:
        return False, (
            f"{len(gaps)}/{len(watched)} 个被监视路径不在 CI 触发范围（改它们 CI 不会跑）: "
            + ", ".join(gaps)
        )
    return True, f"CI 触发范围覆盖全部 {len(watched)} 个被监视路径"


# ── D21：文档里的 WorkBuddy 路径 == 同步工具的默认目标 ──────────
# 背景：本仓新增了 WorkBuddy 通道（tools/workbuddy_skills.py 负责把 skills/ 同步进
# `~/.workbuddy/skills/`）。文档里若把它写成 `~/.workbuddy/skill` 之类，读者照着拷就会
# 装到错地方 —— 而这类错字没有任何别的判据管得住（D14 只查「中英对等 + ✅ 有证据」，
# 不查路径本身对不对）。
# 解法不是"两边都写对"，而是**只让它有一处事实来源**：文档里的路径必须等于工具常量。

WB_ROW = re.compile(r"^\|\s*WorkBuddy\s*\|\s*`([^`]+)`\s*\|", re.M)
WB_TOOL = "tools/workbuddy_skills.py"


def _wb_expected_path() -> str:
    """从同步工具里读默认目标，渲染成文档形式（~/... + 结尾斜杠）。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_wb_skills_for_check", ROOT / WB_TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p = mod.DEFAULT_TARGET
    try:
        rel = str(p.relative_to(Path.home())).replace("\\", "/")
        return "~/" + rel.rstrip("/") + "/"
    except ValueError:  # 目标不在 home 下（自定义 --target 才会发生）
        return str(p).replace("\\", "/").rstrip("/") + "/"


def d21_workbuddy_path_sot(v: RepoView):
    """README ×2 里写的 WorkBuddy skill 路径必须等于同步工具的默认目标。

    单一真相源：路径的事实来源是 `tools/workbuddy_skills.py` 的 DEFAULT_TARGET，
    文档只是它的展示形式。两者一旦分离，就是本项目反复在治的同一种病。
    """
    v.text(WB_TOOL)  # 执行取证：让 D20 知道这个文件在监视范围内
    expected = _wb_expected_path()
    problems = []
    for f in ("README.md", "README.zh.md"):
        hits = WB_ROW.findall(v.text(f))
        if len(hits) != 1:
            problems.append(f"{f}: WorkBuddy 行匹配到 {len(hits)} 处（应为 1 处）")
        elif hits[0] != expected:
            problems.append(f"{f}: 文档写 `{hits[0]}` != 工具默认目标 `{expected}`")
    if problems:
        return False, "; ".join(problems)
    return True, f"WorkBuddy 路径与工具默认目标一致（{expected}）"


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
    ("D15", "Markdown 相对链接无死链", d15_relative_links),
    ("D16", "「N 篇」声称不超过实际落盘", d16_source_count_claims),
    ("D17", "「N 条判据」声称 == 实际条数", d17_checks_count_claims),
    ("D18", "PR 模板引用的自检脚本真实存在", d18_pr_template_commands),
    ("D19", "issue form 合法且 label 真实存在", d19_issue_forms_valid),
    ("D20", "CI 触发范围覆盖全部被监视文件", d20_ci_paths_cover_watched),
    ("D21", "文档里的 WorkBuddy 路径 == 工具默认目标", d21_workbuddy_path_sot),
]


# ──────────────────────────────────────────────────────────────
# 变异定义（--self-test 用）：每条判据必须能被自己的变异打破
# ──────────────────────────────────────────────────────────────


def _sub1(text: str, old: str, new: str) -> str:
    assert old in text, f"变异锚点缺失: {old!r}"
    return text.replace(old, new, 1)


def _mut_num(text: str, pattern: str, offset: int = 1) -> str:
    """把文本中首个匹配到的数字改成「该数 + offset」，pattern 需含一个数字捕获组。

    为什么不用 _sub1 硬写当前值（如 "19 条判据" → "3 条判据"）：
    这类锚点等于把**当前实际值抄进了变异定义**。实际值一变（判据从 19 增到 20、
    skill 从 19 增到 20、SOUL.md 字数一改），锚点就 assert 失败、self-test 直接崩。
    这与"文档里手写数字会漂"是同一种病，只是换了个地方犯。
    改成从文本里读出当前值再偏移，锚点永不失效，且 当前值+offset != 实际值 恒成立。
    """
    m = re.search(pattern, text)
    assert m, f"变异锚点缺失（正则未匹配）: {pattern!r}"
    n = int(m.group(1))
    return text[:m.start(1)] + str(n + offset) + text[m.end(1):]


def _mut_d16(v) -> dict[str, str]:
    """D16 变异：把「N 份笔记」改成「N+50 篇笔记」。

    单位必须一起换成「篇」——D16 判据匹配的是「N 篇」声称，「份」不在其口径内，
    只改数字不改单位是打不穿判据的（这一条曾踩过：锚点打在「份」上，判据查「篇」）。
    """
    txt = v.text("DISTILLER.md")
    return {"DISTILLER.md": _mut_num(txt, r"(\d+) 份笔记", offset=50).replace("份笔记", "篇笔记", 1)}


def _mut_d20(v) -> dict[str, str]:
    """D20 变异：把 CI 触发范围里的 .gitignore 抹掉。

    必须**两处都抹**（push 与 pull_request 各有一条）—— 只抹一条时另一条仍在，
    `_ci_paths` 取并集后覆盖依旧成立，变异打不穿判据，会被误判成"判据失效"。
    """
    txt = v.text(CI_WF)
    mut = re.sub(r"^[ \t]*- ['\"]?\.gitignore['\"]?[ \t]*\n", "", txt, count=0, flags=re.M)
    assert mut != txt, "D20 变异锚点缺失：CI paths 里找不到 .gitignore"
    return {CI_WF: mut}


MUTATIONS: dict[str, callable] = {
    "D1": lambda v: {"README.md": _sub1(v.text("README.md"), "`workspace-isolation`", "`ghost-skill`")},
    "D2": lambda v: {"README.zh.md": _sub1(v.text("README.zh.md"), "`workspace-isolation`", "`ghost-skill`")},
    "D3": lambda v: {"README.zh.md": _sub1(v.text("README.zh.md"), "`workspace-isolation`", "`ghost-skill`")},
    "D4": lambda v: {"README.md": _sub1(v.text("README.md"), "(14 sections)", "(12 sections)")},
    "D5": lambda v: {"README.md": _mut_num(v.text("README.md"), r"\*\*(\d+) distilled source notes")},
    "D6": lambda v: {"README.md": _sub1(v.text("README.md"), "- [x] CI pipeline", "- [ ] CI pipeline")},
    "D7": lambda v: {".gitignore": v.text(".gitignore").replace("__pycache__/", "__never_ignore__/")},
    "D8": lambda v: {".claude-plugin/plugin.json": _sub1(v.text(".claude-plugin/plugin.json"), "TrueFurina/AGI-Distiller", PHANTOM)},
    "D9": lambda v: {"HEARTBEAT.md": _mut_num(v.text("HEARTBEAT.md"), r"\| 生产级 skill \| (\d+) \|")},
    "D10": lambda v: {".claude-plugin/plugin.json": _sub1(v.text(".claude-plugin/plugin.json"), '"version": "0.1.0"', '"version": "9.9.9"')},
    "D11": lambda v: {"README.md": _mut_num(v.text("README.md"), r"~(\d+) chars")},
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
    "D15": lambda v: {
        "README.md": _sub1(v.text("README.md"), "](CONTRIBUTING.md)", "](NO_SUCH_FILE.md)")
    },
    "D16": _mut_d16,
    "D17": lambda v: {"CONTRIBUTING.md": _mut_num(v.text("CONTRIBUTING.md"), r"(\d+) 条判据")},
    "D18": lambda v: {
        PR_TPL: _sub1(v.text(PR_TPL),
                      "python scripts/check_doc_consistency.py",
                      "python scripts/no_such_check.py")
    },
    "D19": lambda v: {
        ".github/ISSUE_TEMPLATE/bug.yml": _sub1(
            v.text(".github/ISSUE_TEMPLATE/bug.yml"),
            'labels: ["bug"]', 'labels: ["triage"]')
    },
    "D20": _mut_d20,
    # D21 的变异必须打在**平台表那一行**上：路径在 README 里出现两次
    # （安装章节的代码块 + 平台表），只改首处的话表格仍是正确值，判据照过，
    # 变异就成了"打不穿"的假绿。锚点取整行，天然唯一。
    "D21": lambda v: {
        "README.md": _sub1(
            v.text("README.md"),
            "| WorkBuddy | `~/.workbuddy/skills/` |",
            "| WorkBuddy | `~/.workbuddy/skils/` |",
        )
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
