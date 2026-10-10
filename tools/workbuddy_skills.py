#!/usr/bin/env python3
"""WorkBuddy skill 通道同步器 —— 本仓 skills/ → ~/.workbuddy/skills/

为什么需要它
------------
本仓 skill 的真实消费通道不止 Claude Code 的 plugin marketplace。WorkBuddy
（本机主力工具）按目录扫描 `~/.workbuddy/skills/<name>/SKILL.md`，把它们登记为
`source: "userSettings"` 的 skill。2026-09-19 手工拷进去过 4 个，仓库此后又改了三轮
（`context: fork` 隔离改造、溯源标记回填、五步定位法……），**本地通道就停在那天的快照上**：
4/21 在位、其中 3 个内容已过期、17 个从未安装。

手工拷贝的问题和文档手写数字是同一个病：**没人负责在源头改动后回灌下游**。
这个工具就是那条回灌路径，且可被 `--check` 机器核验。

它**只做同步**，不做内容转换
---------------------------
不再生成"针对 WorkBuddy 改一版"的副本 —— 那会制造第二个真相源，正是本仓在治的病。
上游 `skills/<name>/` 是唯一事实源，这里逐字节（归一化换行后）复制。

但它**会报告**兼容性风险：若某个 skill 的 frontmatter 用到了"**除本仓外**其他已装 skill 里
从未出现过"的字段（例如 Claude Code 专有的 `context` / `agent` / `maxTurns` / `disallowedTools`），
说明这些字段在 WorkBuddy 侧是否被识别**没有先例可依**。工具只列出来，不擅自删改。
（基线必须排除本仓自身，否则字段一装上就自证有先例 —— 那是自证循环，不是证据。）

用法
----
    python tools/workbuddy_skills.py --check       # 报告漂移（退出码 0=一致 / 1=漂移）
    python tools/workbuddy_skills.py --apply       # 同步（覆盖前默认先备份）
    python tools/workbuddy_skills.py --census      # 只打印 frontmatter 字段普查
    python tools/workbuddy_skills.py --self-test   # 变异自验（用临时 fixture，不碰真实目录）

    --target DIR    改目标目录（默认 ~/.workbuddy/skills）
    --no-backup     --apply 时不备份

边界（如实声明）
----------------
本工具证明的是**文件级一致**：目标目录里存在同名 skill、且 SKILL.md 与上游逐字节相同。
它**不能**证明客户端真的会加载它们 —— 那需要重启客户端后由会话内验证。
能拿到的旁证会一并打印：客户端自己的 skill 缓存 `.skill-list-cache.json` 里
哪些 skill 被登记为 `source: "userSettings"`。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "skills"

SANDBOX = os.environ.get("AGIDISTILLER_SANDBOX") == "1"
"""沙箱模式：假装本机没装 WorkBuddy（CI 就是这种环境）。

自验必须能在这种环境下同样全绿 —— 否则本机绿、CI 红，而必然红的门禁等于没有门禁。
"""

DEFAULT_TARGET = Path.home() / ".workbuddy" / "skills"


def channel_available(target: Path | None = None) -> bool:
    """WorkBuddy 通道在这台机器上是否成立（目录存在）。

    沙箱下**只在没显式给 target 时**为 False —— 但**不改写 DEFAULT_TARGET 的值**。
    - 不改写路径值：沙箱要模拟的是"资源不存在"，不是"路径变了"。改路径会连带让
      比对路径的判据（D21）必然红，那是用一个新故障去演示旧故障。
    - 豁免显式 target：否则沙箱会把自验自己的 fixture 一起屏蔽 ——
      `wechat_queue.py` 就在这上面栽过一次，27 条用例在 CI 上崩了一半。
    """
    if SANDBOX and target is None:
        return False
    return (target or DEFAULT_TARGET).is_dir()
CACHE_NAME = ".skill-list-cache.json"
BACKUP_ROOT_NAME = "skills-backup-agidistiller"

# 本工具自有文件的前缀标记：写入备份目录/报告时用，避免与真实 skill 目录混淆。
OWN_TAG = "agi-distiller"


def norm_bytes(b: bytes) -> bytes:
    """归一化换行后再比哈希 —— 仓库里 LF、Windows 上拷贝可能变 CRLF，那是伪差异。"""
    return b.replace(b"\r\n", b"\n")


def sha(b: bytes) -> str:
    return hashlib.sha256(norm_bytes(b)).hexdigest()


def src_skills() -> dict[str, Path]:
    """上游 skill 名 → 目录。只认含 SKILL.md 的目录。"""
    out: dict[str, Path] = {}
    if not SRC_DIR.is_dir():
        return out
    for d in sorted(SRC_DIR.iterdir()):
        if d.is_dir() and (d / "SKILL.md").is_file():
            out[d.name] = d
    return out


def scan_state(target: Path) -> dict[str, dict]:
    """目标目录里，本仓这 21 个 skill 各自的状态。"""
    state: dict[str, dict] = {}
    for name, sdir in src_skills().items():
        td = target / name
        tf = td / "SKILL.md"
        if not td.is_dir():
            state[name] = {"status": "missing", "detail": "目录不存在"}
        elif not tf.is_file():
            state[name] = {"status": "missing", "detail": "目录在但无 SKILL.md"}
        else:
            a, b = sha((sdir / "SKILL.md").read_bytes()), sha(tf.read_bytes())
            if a == b:
                state[name] = {"status": "ok", "detail": "内容一致"}
            else:
                state[name] = {
                    "status": "stale",
                    "detail": f"上游 {a[:8]} → 本地 {b[:8]}",
                    "src": a,
                    "dst": b,
                }
    return state


def extra_files(src_dir: Path, dst_dir: Path) -> list[str]:
    """目标目录里多出来的文件（相对上游）—— 只报告，不删。"""
    if not dst_dir.is_dir():
        return []
    src_rel = {
        str(p.relative_to(src_dir)).replace("\\", "/")
        for p in src_dir.rglob("*")
        if p.is_file()
    }
    out = []
    for p in dst_dir.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(dst_dir)).replace("\\", "/")
            if rel not in src_rel:
                out.append(rel)
    return sorted(out)


def read_cache(target: Path) -> tuple[list[str] | None, str]:
    """读客户端自己的 skill 缓存，返回（本仓被登记的 skill 名, 说明）。

    这是**旁证**：缓存是客户端生成的，不是我们写的。
    """
    cache = target.parent / CACHE_NAME
    if not cache.is_file():
        return None, f"未找到客户端缓存（{cache}）——无法核对客户端是否已登记"
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - 缓存是外部产物，格式变了不该炸工具
        return None, f"客户端缓存解析失败（{type(exc).__name__}: {exc}）"
    entries = data.get("results") or []
    ours = set(src_skills())
    hit = [
        e.get("name")
        for e in entries
        if e.get("name") in ours and e.get("source") == "userSettings"
    ]
    total = len(entries)
    return sorted(hit), f"客户端缓存共 {total} 条，其中本仓 skill 被登记 {len(hit)} 个"


def frontmatter_fields(path: Path) -> list[str]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", txt, re.S)
    if not m:
        return []
    return [
        mm.group(1)
        for mm in (re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:", l) for l in m.group(1).splitlines())
        if mm
    ]


EVIDENCE_FILE = REPO_ROOT / "tools" / "wb_field_evidence.json"


def load_field_evidence() -> dict | None:
    """客户端 frontmatter 字段取证结果（由 tools/wb_frontmatter_probe.py 产出）。

    没有它时，普查只能说「无先例」——那是没见过，不等于不支持。有它就能给出结论。
    客户端升级后 bundle 的 sha 会变，届时这张快照过期，重跑取证即可刷新。
    """
    try:
        ev = json.loads(EVIDENCE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(ev, dict):
        return None
    ev["stale"] = _evidence_staleness(ev)
    return ev


def _evidence_staleness(ev: dict) -> bool | None:
    """这张证据快照是不是已经跟着客户端升级过期了。None = 本机没那个 bundle，无从判断。

    委托给取证器本身实现 —— 判据和取值用同一份代码，不然两边会各自漂移。
    """
    import importlib.util

    probe = REPO_ROOT / "tools" / "wb_frontmatter_probe.py"
    if not probe.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location("_wb_probe_for_check", probe)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.evidence_is_stale(ev)
    except Exception:
        return None


def fields_not_read_but_used(ev: dict | None) -> dict[str, int]:
    """本仓在写、但取证显示 skill 解析器不读的字段 → {字段: 用到的 skill 数}。

    与 outliers 是两件事：outliers 问的是"别人用过吗"（ popularity ），
    这里问的是"客户端读它吗"（ effectiveness ）。有先例不代表生效。
    """
    if not ev:
        return {}
    fields = ev.get("fields", {})
    used: dict[str, int] = {}
    for sdir in src_skills().values():
        for k in frontmatter_fields(sdir / "SKILL.md"):
            if k in fields and not fields[k].get("read"):
                used[k] = used.get(k, 0) + 1
    return used


def _report_outliers(outliers: dict[str, list[str]], ev: dict | None) -> None:
    """把「无先例」字段按证据分成三档，不再一律标成"未经验证"。

    三档：已确证被读取 / 已确证写了不生效 / 无证据。混成一档是用别人的沉默当答案，
    也让真正要删的死字段和只在本仓出现的合法字段享受同等待遇。
    """
    fields = (ev or {}).get("fields", {})
    unread, verified, unknown = [], [], []
    for k, names in sorted(outliers.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        shown = ", ".join(names[:3]) + ("…" if len(names) > 3 else "")
        line = f"    - {k:20} 被 {len(names)} 个 skill 用到（{shown}）"
        if k not in fields:
            unknown.append(line)
        elif fields[k]["read"]:
            verified.append(line)
        else:
            unread.append(line)

    print("  以下字段在**已装 skill 里没有任何先例**：")
    basis = ""
    if ev:
        basis = (f"依据 {ev.get('fetched_at', '?')} 对 "
                 f"{ev.get('bundle_bytes', 0):,} 字节 bundle 的取证")
    if verified:
        print("    ✅ 客户端解析确实读取了它们（只是别人没用过）：")
        print("\n".join(verified))
    if unread:
        print("    ❌ 写了不生效 —— 客户端的 skill 解析器不读取这些字段：")
        print("\n".join(unread))
        print("       （搬运清单见 tools/wb_field_evidence.json；删不删由人裁决，工具不代劳）")
    if unknown:
        print("    ⚠️  无取证数据（字段不在本次快照内 / 未跑取证），是否支持未知：")
        print("\n".join(unknown))
    if basis:
        if ev.get("stale") is None:
            basis += "（本机无该客户端 bundle，无法复核是否过期）"
        elif ev["stale"]:
            basis = "⚠️ 证据已过期：客户端 bundle 变了 —— " + basis
        print(f"       {basis}；重取证："
              f"`python tools/wb_frontmatter_probe.py --write tools/wb_field_evidence.json`")


def census(target: Path) -> tuple[dict[str, int], dict[str, list[str]]]:
    """目标目录下**其他** skill 的 frontmatter 字段普查 + 本仓越界字段。

    返回 (他方字段计数, {越界字段: [用到它的本仓 skill]})。

    为什么基线要**排除本仓自身**：本工具会把本仓 skill 拷进目标目录，
    若基线把本仓自己的 skill 也算作"先例"，那字段一旦装上就自动获得先例 ——
    警告会被自己的产物消解（实测：同步 21 个之后从"4 个字段无先例"变成"无越界字段"）。
    那是自证循环，不是证据。因此基线只认**他方** skill 用过的字段。
    """
    counts: dict[str, int] = {}
    ours = set(src_skills())
    if target.is_dir():
        for d in sorted(target.iterdir()):
            f = d / "SKILL.md"
            if d.is_dir() and f.is_file() and d.name not in ours:
                for k in frontmatter_fields(f):
                    counts[k] = counts.get(k, 0) + 1
    outliers: dict[str, list[str]] = {}
    for name, sdir in src_skills().items():
        for k in frontmatter_fields(sdir / "SKILL.md"):
            if k not in counts:
                outliers.setdefault(k, []).append(name)
    return counts, outliers


# ──────────────────────────────────────────────────────────────
# 命令
# ──────────────────────────────────────────────────────────────


def cmd_check(target: Path, verbose: bool = True) -> int:
    state = scan_state(target)
    ok = [n for n, s in state.items() if s["status"] == "ok"]
    stale = [n for n, s in state.items() if s["status"] == "stale"]
    missing = [n for n, s in state.items() if s["status"] == "missing"]

    if verbose:
        print(f"== WorkBuddy 通道核验 @ {target}")
        print(f"  上游 skills/ 共 {len(state)} 个")
        print(f"  ✅ 一致 {len(ok)}    ⚠️  过期 {len(stale)}    ❌ 未安装 {len(missing)}")
        if stale:
            print("\n  过期（上游已改，本地是旧快照）：")
            for n in stale:
                print(f"    - {n:28} {state[n]['detail']}")
                extras = extra_files(SRC_DIR / n, target / n)
                if extras:
                    print(f"      本地多出文件（未删）：{', '.join(extras)}")
        if missing:
            print("\n  未安装：")
            for n in missing:
                print(f"    - {n}")
        hit, note = read_cache(target)
        print(f"\n  旁证：{note}")
        if hit is not None:
            print(f"        已登记为 userSettings 的本仓 skill：{hit or '（无）'}")
        counts, outliers = census(target)
        ev = load_field_evidence()
        print(f"\n  兼容性普查：已装 skill frontmatter 字段 {len(counts)} 种")
        if outliers:
            _report_outliers(outliers, ev)
        else:
            print("  无越界字段：本仓用到的字段在已装 skill 里均有先例")
        dead = fields_not_read_but_used(ev)
        if dead:
            print("  ⚠️  取证显示 skill 解析器不读取、但本仓仍在写的字段：")
            for k, n in sorted(dead.items(), key=lambda kv: -kv[1]):
                print(f"    - {k:20} {n} 个 skill 在写")
            print("       注：`argumentHint` 在 **slash command** 路径被读取；skill 是否另走该路径未取证，")
            print("       删之前先确认场景 —— 工具只负责把事实摆出来，不动别人的文件。")
    print("\n  结论：文件级一致" + ("（无漂移）" if not (stale or missing) else "（存在漂移，跑 --apply 回灌）"))

    return 0 if not (stale or missing) else 1


def cmd_apply(target: Path, backup: bool = True, verbose: bool = True) -> int:
    def say(*a):
        if verbose:
            print(*a)

    state = scan_state(target)
    todo = {n: s for n, s in state.items() if s["status"] != "ok"}
    if not todo:
        say("已一致，无需同步。")
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = target.parent / BACKUP_ROOT_NAME / stamp

    if backup:
        saved = 0
        for name, st in todo.items():
            tf = target / name / "SKILL.md"
            if st["status"] == "stale" and tf.is_file():
                bdir = backup_root / name
                bdir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(tf, bdir / "SKILL.md")
                saved += 1
        say(f"备份：{saved} 个将被覆盖的文件 → {backup_root}" if saved else "备份：无需备份（均为新增）")

    added = refreshed = 0
    for name, st in sorted(todo.items()):
        sdir, td = SRC_DIR / name, target / name
        td.mkdir(parents=True, exist_ok=True)
        for p in sdir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(sdir)
                dst = td / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
        if st["status"] == "stale":
            refreshed += 1
        else:
            added += 1
        say(f"  {'刷新' if st['status'] == 'stale' else '新增'}  {name}")

    say(f"\n完成：新增 {added}，刷新 {refreshed}。未触碰目标目录里非本仓的 skill。")
    rc = cmd_check(target, verbose=False)
    say("回读核验：" + ("一致 ✅" if rc == 0 else "仍有漂移 ❌"))
    say("\n注意：这是文件级同步。客户端需重启/刷新技能列表后才会加载新 skill —— 本工具无法代证客户端加载。")
    return rc


def cmd_census(target: Path) -> int:
    counts, outliers = census(target)
    print(f"已装 skill frontmatter 字段普查 @ {target}")
    for k, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:22} {c:3}")
    if outliers:
        print("\n本仓用到、但已装 skill 中无先例的字段：")
        for k, names in sorted(outliers.items()):
            print(f"  {k:22} ← {', '.join(names)}")
    return 0


# ──────────────────────────────────────────────────────────────
# 变异自验：每条判据必须能被"伪造的漂移"打破
# ──────────────────────────────────────────────────────────────


def cmd_self_test() -> int:
    """在临时 fixture 上验证检测能力 —— 全绿不等于有效，得证明它抓得住。"""
    cases: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory(prefix="wbskill-") as tmp:
        tmpdir = Path(tmp)

        # 造 3 个上游 skill
        src = tmpdir / "repo" / "skills"
        for n in ("alpha", "beta", "gamma"):
            (src / n).mkdir(parents=True)
            (src / n / "SKILL.md").write_text(
                f"---\nname: {n}\ndescription: d\n---\n\nbody {n}\n", encoding="utf-8"
            )
        (src / "alpha" / "refs").mkdir()
        (src / "alpha" / "refs" / "note.md").write_text("ref\n", encoding="utf-8")
        target = tmpdir / "wb" / "skills"
        target.mkdir(parents=True)

        # 0. 环境判定必须尊重**显式给的** target。
        #    沙箱（AGIDISTILLER_SANDBOX=1）只屏蔽"默认的本机目录"；若连 fixture 一起屏蔽，
        #    自验会在 CI 上成片崩 —— wechat_queue.py 就在这上面栽过，27 条用例崩掉 8 条。
        cases.append(("显式 target 按真实存在性判定（不被沙箱开关误伤）",
                      channel_available(target) is True
                      and channel_available(target / "nope") is False))

        global SRC_DIR
        saved_src = SRC_DIR
        SRC_DIR = src
        try:
            # 1. 全空 → 必须报漂移
            st = scan_state(target)
            cases.append((
                "空目标：3 个全部判为 missing",
                all(st[n]["status"] == "missing" for n in ("alpha", "beta", "gamma")),
            ))
            cases.append(("空目标：--check 退出码为 1", cmd_check(target, verbose=False) == 1))

            # 2. 全量拷入 → 必须一致
            for n in ("alpha", "beta", "gamma"):
                shutil.copytree(src / n, target / n)
            st = scan_state(target)
            cases.append(("全量拷入：3 个全部判为 ok", all(s["status"] == "ok" for s in st.values())))
            cases.append(("全量拷入：--check 退出码为 0", cmd_check(target, verbose=False) == 0))

            # 3. 改一处内容 → 必须抓出 stale
            f = target / "beta" / "SKILL.md"
            f.write_text(f.read_text(encoding="utf-8") + "本地私改\n", encoding="utf-8")
            st = scan_state(target)
            cases.append(("内容私改：beta 判为 stale", st["beta"]["status"] == "stale"))
            cases.append(("内容私改：--check 退出码为 1", cmd_check(target, verbose=False) == 1))

            # 4. 只改换行（CRLF↔LF）→ 不得误报（归一化必须生效）
            #    注意：Path.write_text 在 Windows 上默认写 CRLF，所以这里显式写成 LF，
            #    制造一个**真实的**仅换行差异。早先版本误写成 replace(b"\n", b"\r\n")，
            #    在 CRLF 源上会得到 \r\r\n（不是换行差异而是内容差异），用例本身就错了。
            f.write_bytes((src / "beta" / "SKILL.md").read_bytes().replace(b"\r\n", b"\n"))
            cases.append(("仅换行差异：不误报（CRLF 归一化）", scan_state(target)["beta"]["status"] == "ok"))

            # 5. 目录里有别的 skill → 不得被当作本仓（也不得被删）
            (target / "someone-else").mkdir()
            (target / "someone-else" / "SKILL.md").write_text("---\nname: someone-else\n---\n", encoding="utf-8")
            cmd_apply(target, backup=True, verbose=False)
            cases.append(("非本仓 skill 不被触碰", (target / "someone-else" / "SKILL.md").is_file()))

            # 6. --apply 后必须回读一致
            cases.append(("--apply 后 --check 退出码为 0", cmd_check(target, verbose=False) == 0))

            # 7. 备份必须真的落盘（覆盖前）
            f.write_text("again-dirty\n", encoding="utf-8")
            cmd_apply(target, backup=True, verbose=False)
            backups = list((tmpdir / "wb" / BACKUP_ROOT_NAME).rglob("beta/SKILL.md"))
            cases.append(("覆盖前产生备份", len(backups) >= 1))

            # 8. 子目录文件（refs/）也必须同步
            cases.append(("子目录文件已同步", (target / "alpha" / "refs" / "note.md").is_file()))

            # 9. 多出文件只报告、不删除
            (target / "alpha" / "stray.txt").write_text("x\n", encoding="utf-8")
            extras = extra_files(src / "alpha", target / "alpha")
            cases.append(("多余文件被报告", "stray.txt" in extras))
            cmd_apply(target, backup=True, verbose=False)
            cases.append(("多余文件不被删除", (target / "alpha" / "stray.txt").is_file()))

            # 10. 越界字段必须被普查抓出
            (src / "gamma" / "SKILL.md").write_text(
                "---\nname: gamma\ndescription: d\ncontext: fork\nweirdField: 1\n---\n", encoding="utf-8"
            )
            _, outliers = census(target)
            cases.append(("越界字段被抓出（context）", "context" in outliers))
            cases.append(("越界字段被抓出（weirdField）", "weirdField" in outliers))
            # 回归用例：本仓自身不得进入普查基线。
            # 实测过的伪影——基线含自身时，把 skill 装上就等于给它自己造了先例，
            # 警告当场消失（21 个同步完从"4 字段无先例"变成"无越界字段"）。
            cases.append(("本仓自身不计入基线：装上后仍报越界", "context" in outliers))
        finally:
            SRC_DIR = saved_src

    # 取证驱动的字段结论：三档输出必须能被证据文件推翻。
    # 没有它时 census 只会说"无先例"（popularity），有它才谈得上"是否生效"（effectiveness）。
    with tempfile.TemporaryDirectory() as td:
        ev_path = Path(td) / "wb_field_evidence.json"
        ev_path.write_text(json.dumps({
            "fetched_at": "2026-01-01T00:00:00Z",
            "bundle_sha256": "deadbeef",
            "fields": {
                "context": {"read": True, "as": "context"},
                "maxTurns": {"read": False, "as": "maxTurns"},
                "argument-hint": {"read": False, "as": "argumentHint"},
            },
        }, ensure_ascii=False), encoding="utf-8")
        saved_ev = EVIDENCE_FILE
        try:
            globals()["EVIDENCE_FILE"] = ev_path
            cases.append(("有证据：能读到 bundle 标识",
                          (load_field_evidence() or {}).get("bundle_sha256") == "deadbeef"))
            dead_now = fields_not_read_but_used(load_field_evidence())
            cases.append(("有证据：不被读取且本仓在写的字段被点名", "argument-hint" in dead_now))
            cases.append(("有证据：已被读取的字段不算死字段", "context" not in dead_now))
            # 变异：把该字段的 read 翻成 true → 必须不再被点名
            flipped = json.loads(ev_path.read_text(encoding="utf-8"))
            flipped["fields"]["argument-hint"]["read"] = True
            ev_path.write_text(json.dumps(flipped, ensure_ascii=False), encoding="utf-8")
            cases.append(("证据翻转 read 后结论跟着变",
                          "argument-hint" not in fields_not_read_but_used(load_field_evidence())))
            # 变异 2：本仓没在写的字段不得被点名（人口和情感 winner 又👍 两码事）
            cases.append(("本仓未在写的字段不进提示",
                          "maxTurns" not in fields_not_read_but_used(load_field_evidence())))
        finally:
            globals()["EVIDENCE_FILE"] = saved_ev
        # 证据缺失（别人机器上没跑过取证）→ 不得假装知道，也不得崩
        try:
            globals()["EVIDENCE_FILE"] = Path(td) / "no-such-evidence.json"
            cases.append(("证据缺失：不崩且不给结论",
                          load_field_evidence() is None
                          and fields_not_read_but_used(None) == {}))
        finally:
            globals()["EVIDENCE_FILE"] = saved_ev

    print("== 自我变异验证（临时 fixture，未触碰真实目录）")
    bad = 0
    for desc, okk in cases:
        print(f"  {'PASS' if okk else 'FAIL'}  {desc}")
        bad += 0 if okk else 1
    if bad:
        print(f"\n变异验证失败：{bad}/{len(cases)} 项不通过")
        return 1
    print(f"\n变异验证通过：{len(cases)}/{len(cases)} 项全部符合预期")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="本仓 skills/ → WorkBuddy ~/.workbuddy/skills/ 同步与核验")
    ap.add_argument("--check", action="store_true", help="报告漂移（退出码 0=一致 / 1=漂移）")
    ap.add_argument("--apply", action="store_true", help="同步（覆盖前默认备份）")
    ap.add_argument("--census", action="store_true", help="只打印 frontmatter 字段普查")
    ap.add_argument("--self-test", action="store_true", help="变异自验（临时 fixture）")
    ap.add_argument("--target", type=Path, default=DEFAULT_TARGET, help=f"目标目录（默认 {DEFAULT_TARGET}）")
    ap.add_argument("--no-backup", action="store_true", help="--apply 时不备份")
    a = ap.parse_args(argv)

    chosen = [x for x in (a.check, a.apply, a.census, a.self_test) if x]
    if len(chosen) != 1:
        ap.error("必须且只能指定 --check / --apply / --census / --self-test 之一")

    if a.self_test:
        return cmd_self_test()
    if a.census:
        return cmd_census(a.target)
    if a.apply:
        return cmd_apply(a.target, backup=not a.no_backup)
    return cmd_check(a.target)


if __name__ == "__main__":
    sys.exit(main())
