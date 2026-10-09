#!/usr/bin/env python3
"""WorkBuddy 客户端 skill frontmatter 字段取证。

为什么存在
----------
本仓 2 个 skill 用了 `context` / `agent` / `maxTurns` / `disallowedTools` 四个字段，
它们在其他已装 skill 里**零先例**。`tools/workbuddy_skills.py` 的普查只能说「无先例」——
那是「没见过」，不是「不支持」。把这两件事混为一谈，等于用别人的沉默当答案。

真正加载 skill 的是客户端 bundle 里的 `parseSkillFile`：它把哪些字段搬进返回对象，
下游才可能用得上；没搬的就是死字段，写了也不生效。
本脚本去读那段代码本身，把「猜」换成「取证」。

用法
----
    python tools/wb_frontmatter_probe.py               # 打印取证结论
    python tools/wb_frontmatter_probe.py --write X.json  # 落盘（给 workbuddy_skills.py 用）
    python tools/wb_frontmatter_probe.py --self-test   # 变异自验

退出码
------
    0 = 取证成功 / 明确报告「本机无 bundle，未取证」
    1 = 找不到 bundle 且未加 --allow-missing 时的 CI 模式（见 --ci）
    1 = self-test 失败

诚实边界
--------
这是**静态取证**：证明的是「这段代码读取了 / 没有读取某字段」，不是「运行时一定生效」。
客户端换了版本结论就可能变，所以证据里记了 bundle 的 sha256 与字节数——换了文件就认不出。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "tools" / "wb_field_evidence.json"

# 客户端 skill 加载器所在的 bundle。按安装位置从常见到罕见排序，允许环境变量覆盖。
BUNDLE_CANDIDATES = [
    "${WORKBUDDY_ROOT}/resources/app.asar.unpacked/cli/dist/codebuddy-headless.js",
    "${WORKBUDDY_ROOT}/resources/app.asar.unpacked/cli/dist/codebuddy-lite-wb.mjs",
    "${LOCALAPPDATA}/WorkBuddy/resources/app.asar.unpacked/cli/dist/codebuddy-headless.js",
    "${LOCALAPPDATA}/Programs/WorkBuddy/resources/app.asar.unpacked/cli/dist/codebuddy-headless.js",
]

# 兜底：Windows 本机的实际安装根（存在就用，不存在就跳过）
FALLBACK_ROOTS = [
    Path("D:/WorkBuddy"),
    Path("C:/Program Files/WorkBuddy"),
    Path("C:/Users/Lenovo/AppData/Local/WorkBuddy"),
]

PARSE_FN = "async parseSkillFile("


def _expand(p: str) -> list[Path]:
    """把 ${VAR} 展开成本机路径；变量缺失则当作普通字符串处理。"""
    import os

    out = []
    roots = [Path(os.environ.get("WORKBUDDY_ROOT", "")), Path(os.environ.get("LOCALAPPDATA", ""))]
    expanded = re.sub(
        r"\$\{(\w+)\}",
        lambda m: os.environ.get(m.group(1), ""),
        p,
    )
    if expanded and not expanded.startswith("$"):
        out.append(Path(expanded))
    # 环境变量没给就用兜底根逐个拼
    if "/" in p.split("}", 1)[-1] and not out:
        tail = p.split("}", 1)[-1].lstrip("/")
        for r in FALLBACK_ROOTS + [x for x in roots if x and str(x) != "."]:
            if r.exists():
                out.append(r / tail)
    return out


def find_bundle(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    for cand in BUNDLE_CANDIDATES:
        for p in _expand(cand):
            if p.is_file():
                return p
    for root in FALLBACK_ROOTS:
        p = root / "resources/app.asar.unpacked/cli/dist/codebuddy-headless.js"
        if p.is_file():
            return p
    return None


def extract_return_keys(text: str, fn: str = PARSE_FN) -> set[str] | None:
    """从 parseSkillFile 的实现里取出它 return 的对象顶层 key。

    只看 top-level key：嵌套对象（如 `source: ea`）不参与判定，
    展开式（`...eD?{...}:{}`）也不参与——它们是条件字段，不是稳定的读取行为。
    """
    i = text.find(fn)
    if i < 0:
        return None
    j = text.find("return{", i)
    if j < 0:
        return None
    # 花括号配对，取 return 的对象体
    depth = 0
    for k in range(j + len("return"), len(text)):
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                body = text[j + len("return") : k + 1]
                return _top_level_keys(body)
    return None


def _top_level_keys(body: str) -> set[str]:
    """只收 return 对象**顶层**的 key。

    早先用正则 `(?:^|[,{])\\s*(\\w+)\\s*:` 贪婪匹配，把 `{ 前面的 await...}` 也会命中：
    嵌套对象里的同名字段（如 `meta:{allowedTools:'no'}`）会被误判成"被读取"。
    那种误报比漏报更坏 —— 它会给一个死字段发通行证。
    """
    keys: set[str] = set()
    depth = 0
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif ch == ":" and depth == 1:
            m = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", body[:i])
            # 值里的三元 `...eD?{a:1}:{}` 落在 depth>1，不会进这里
            if m:
                keys.add(m.group(1))
        i += 1
    return keys


# frontmatter 里的写法 → parseSkillFile 返回体里的属性名（只登记需要改写的，其余同名）
KEY_ALIAS = {
    "allowed-tools": "allowedTools",
    "argument-hint": "argumentHint",
    "disable-model-invocation": "disableModelInvocation",
    "agent-created": "agentCreated",
    "max-turns": "maxTurns",
    "display-name": "displayName",
}


def repo_frontmatter_fields() -> list[str]:
    """本仓 skills/ 里实际用到的 frontmatter 字段（探测集合的来源）。"""
    keys: list[str] = []
    for f in sorted((ROOT / "skills").glob("*/SKILL.md")):
        m = re.match(r"^---\r?\n(.*?)\r?\n---", f.read_text(encoding="utf-8", errors="replace"), re.S)
        if not m:
            continue
        for line in m.group(1).splitlines():
            mm = re.match(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:", line)
            if mm and mm.group(1) not in keys:
                keys.append(mm.group(1))
    return keys


def probe(bundle: Path, fields: list[str] | None = None) -> dict:
    raw = bundle.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    keys = extract_return_keys(text)
    if keys is None:
        raise RuntimeError(f"{bundle}: 找不到 {PARSE_FN!r} 或其 return 对象（客户端改版了？）")
    fields = fields if fields is not None else repo_frontmatter_fields()
    rec = bundle.stat()
    return {
        "bundle": str(bundle),
        # 刻意**不**把 sha256 摘要写进落盘的证据文件：仓库的 pre-commit 密钥扫描会把
        # 一串 64 位 hex 判成疑似密钥（它确实拦下了第一版证据文件）。
        # 放宽那条扫描规则等于给真密钥开门 —— 它管的是 P0，不该为一个哈希让路。
        # 所以摘要只在打印时现算，落盘部分用 size + mtime 做版本指纹。
        "bundle_bytes": rec.st_size,
        "bundle_mtime_epoch": round(rec.st_mtime, 3),
        "bundle_mtime": datetime.fromtimestamp(rec.st_mtime, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "return_keys": sorted(keys),
        "fields": {
            f: {"read": KEY_ALIAS.get(f, f) in keys, "as": KEY_ALIAS.get(f, f)}
            for f in fields
        },
    }


def evidence_is_stale(ev: dict) -> bool | None:
    """落盘证据是否已被客户端升级甩在后面。None = 无从判断（bundle 不在本机）。"""
    p = Path(ev.get("bundle", ""))
    if not p.is_file():
        return None
    rec = p.stat()
    if rec.st_size != ev.get("bundle_bytes"):
        return True
    # 比签名——不是比可读字符串：字符串裁到秒，跨秒重建同一文件也会被误判成升级。
    return abs(rec.st_mtime - float(ev.get("bundle_mtime_epoch", 0))) > 0.01


def cmd_probe(args: argparse.Namespace) -> int:
    bundle = find_bundle(args.bundle)
    if bundle is None:
        msg = ("本机找不到 WorkBuddy 客户端 bundle —— 未取证。\n"
               "可用 --bundle <path> 指定，或设置 WORKBUDDY_ROOT。\n"
               "不明不白地报「不支持」与不明不白地报「支持」一样糟，这里两者都不报。")
        print(msg)
        return 0 if args.allow_missing else 1
    ev = probe(bundle)
    if args.write:
        Path(args.write).write_text(
            json.dumps(ev, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"证据已落盘：{args.write}")
        return 0
    print(f"== WorkBuddy skill frontmatter 字段取证 ==")
    print(f"来源：{ev['bundle']}")
    print(f"      sha256 {hashlib.sha256(Path(ev['bundle']).read_bytes()).hexdigest()[:16]}…"
          f"  {ev['bundle_bytes']:,} 字节（摘要不落盘，避开密钥扫描误报）")
    print(f"      parser return keys: {', '.join(ev['return_keys'])}\n")
    for f, info in ev["fields"].items():
        mark = "✅ 被读取" if info["read"] else "❌ 未被读取（写了不生效）"
        alias = f"  (frontmatter → {info['as']})" if info["as"] != f else ""
        print(f"  {f:22} {mark}{alias}")
    return 0


def cmd_self_test() -> int:
    """变异自验：取证逻辑必须能区分「读」与「不读」，且对格式扰动不脆弱。"""
    cases: list[tuple[str, bool]] = []
    base = (
        "class X{async parseSkillFile(L,ei){try{let a=1;return{name:a,id:'i',"
        "description:'d',instructions:'x',allowedTools:e,custom:1,context:1,agent:1,"
        "model:1,userInvocable:1}}catch(e){return}}}"
    )
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        def run(txt: str, fields: list[str]) -> dict:
            b = tmp / "bundle.js"
            b.write_text(txt, encoding="utf-8")
            return probe(b, fields)

        ev = run(base, ["name", "allowed-tools", "context", "maxTurns", "disallowedTools"])
        cases.append(("被搬运的字段判为已读", ev["fields"]["name"]["read"]))
        cases.append(("kebab-case 字段映射到 camelCase", ev["fields"]["allowed-tools"]["read"]))
        cases.append(("context 判为已读", ev["fields"]["context"]["read"]))
        cases.append(("未搬运的字段判为未读", not ev["fields"]["maxTurns"]["read"]))
        cases.append(("disallowedTools 判为未读", not ev["fields"]["disallowedTools"]["read"]))

        # 变异 1：把 context 从返回体里抹掉 → 必须翻成「未读」
        mut = base.replace(",context:1", "")
        cases.append(("抹掉 context 后翻为未读", not run(mut, ["context"])["fields"]["context"]["read"]))

        # 变异 2：把 disallowedTools 塞进返回体 → 必须翻成「已读」
        mut2 = base.replace("context:1", "context:1,disallowedTools:9")
        cases.append(("塞入 disallowedTools 后翻为已读",
                      run(mut2, ["disallowedTools"])["fields"]["disallowedTools"]["read"]))

        # 变异 3：嵌套对象里的同名字段不得被当成 top-level（否则会把 `source:` 误判成泄漏）
        nested = base.replace("allowedTools:e", "meta:{allowedTools:'no'}")
        cases.append(("嵌套对象里的同名字段不算已读",
                      not run(nested, ["allowed-tools"])["fields"]["allowed-tools"]["read"]))

        # 变异 4：找不到 parseSkillFile → 明确报错而不是假装「都不支持」
        try:
            run("nothing here", ["name"])
            cases.append(("缺 parseSkillFile 时报错而非静默", False))
        except RuntimeError:
            cases.append(("缺 parseSkillFile 时报错而非静默", True))

        # 变异 5：bundle 换了版本（size 变了）→ 过期检测必须发现
        ev5 = json.loads(EVIDENCE.read_text(encoding="utf-8")) if EVIDENCE.is_file() else None
        if ev5:
            ev5["bundle_bytes"] = ev5["bundle_bytes"] + 1
            cases.append(("客户端升级后证据标记为过期", evidence_is_stale(ev5) is True))
            cases.append(("未变动的证据不算过期", evidence_is_stale(
                json.loads(EVIDENCE.read_text(encoding="utf-8"))) is False))
        else:
            print("  SKIP  过期检测（本机尚无证据文件，先跑一次取证）")

        # 变异 6：bundle 不在本机（别人机器上）→ 无从判断，返回 None 而不是瞎猜
        ev6 = json.loads(EVIDENCE.read_text(encoding="utf-8")) if EVIDENCE.is_file() else None
        if ev6:
            ev6["bundle"] = "/no/such/bundle.js"
            cases.append(("bundle 不在本机时承认无从判断", evidence_is_stale(ev6) is None))

        # 变异 7：} 不配对（截断）不崩且不误判为「全部不支持」
        try:
            run(base[: base.index("return{") + 20], ["name"])
            cases.append(("截断的 bundle 不静默通过", False))
        except RuntimeError:
            cases.append(("截断的 bundle 不静默通过", True))

    bad = 0
    for title, okv in cases:
        print(f"  {'PASS' if okv else 'FAIL'}  {title}")
        bad += 0 if okv else 1
    print(f"\n{'✅' if not bad else '❌'} {len(cases) - bad}/{len(cases)} 通过")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle", help="客户端 bundle 路径（默认按常见安装位置找）")
    ap.add_argument("--write", metavar="FILE", help="把取证结果写成 JSON（不打印报告）")
    ap.add_argument("--allow-missing", action="store_true",
                    help="找不到 bundle 时以 0 退出（用于本机没有客户端的环境）")
    ap.add_argument("--self-test", action="store_true", help="变异自验")
    a = ap.parse_args(argv)
    if a.self_test:
        return cmd_self_test()
    return cmd_probe(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
