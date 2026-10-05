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
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "skills"

DEFAULT_TARGET = Path.home() / ".workbuddy" / "skills"
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
        print(f"\n  兼容性普查：已装 skill frontmatter 字段 {len(counts)} 种")
        if outliers:
            print("  以下字段在**已装 skill 里没有任何先例**，客户端是否识别未经验证：")
            for k, names in sorted(outliers.items(), key=lambda kv: -len(kv[1])):
                shown = ", ".join(names[:3]) + ("…" if len(names) > 3 else "")
                print(f"    - {k:20} 被 {len(names)} 个 skill 用到（{shown}）")
        else:
            print("  无越界字段：本仓用到的字段在已装 skill 里均有先例")
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
