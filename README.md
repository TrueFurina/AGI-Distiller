# 🧪 AGI Distiller

> **版权声明 Copyright**：© 2026 All Rights Reserved. 未经作者书面许可，禁止复制、修改、分发、商用、用于各类学科竞赛。
>
> **Knowledge Distillation System for AI Coding Agents**
>
> Read. Distill. Evolve. Repeat.

[![Agent Skills](https://img.shields.io/badge/spec-agentskills.io-7dd3fc)](https://agentskills.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-marketplace-a78bfa)](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-compatible-10A37F)](https://github.com/openai/codex)

> **🌐 [中文版 README](README.zh.md)**

---

## 🌟 Vision

**AGI Distiller** is not just another skill collection. It is a **living knowledge distillation system** that:

1. **Reads** high-quality technical content (articles, blogs, papers, WeChat posts)
2. **Extracts** pain points, solutions, and actionable rules
3. **Precipitates** them into cross-platform agent skills, behavioral rules, and collaboration protocols
4. **Evolves** itself — the more it reads, the more capable it becomes

> **The ultimate goal: An AI agent that continuously self-improves by reading, distilling, and applying knowledge — one article at a time.**

---

## 🔬 What Makes This Different

| Dimension | Traditional Skill Repos | AGI Distiller |
|-----------|----------------------|---------------|
| **Source** | Developer experience | **High-quality technical content** |
| **Creation** | Hand-written | **Distilled from content** |
| **Evolution** | Manual PRs | **Self-evolving** |
| **Focus** | General coding | **Terminal AI agent efficiency** |
| **Language** | English only | **Bilingual (EN + CN)** |
| **Philosophy** | "Here are the skills" | **"Here is the distillery that produces skills"** |

---

## 🏗️ System Architecture

```
                    ┌─────────────────────────────┐
                    │     Knowledge Sources        │
                    │  laodad.com · WeChat · Blogs │
                    │  arXiv · GitHub Issues · More │
                    └─────────────┬───────────────┘
                                  │ Read
                    ┌─────────────▼───────────────┐
                    │     Distillation Pipeline    │
                    │                              │
                    │  ① Extract Pain Points      │
                    │  ② Extract Solutions        │
                    │  ③ Derive Actionable Rules  │
                    │  ④ Precipitate into Skills  │
                    │  ⑤ Update Behavior Rules    │
                    └─────────────┬───────────────┘
                                  │ Output
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  Agent Skills  │       │  Rules & Specs │       │  Memory &     │
│  (SKILL.md)    │       │  (ATOMCODE.md) │       │  Knowledge    │
│  Cross-platform│       │  Best practices│       │  (notes/)     │
└───────────────┘       └───────────────┘       └───────────────┘
```

---

## 📦 What's Inside

### Agent Spec Files (OpenAI Open Standard)

| File | Purpose | Size |
|------|---------|------|
| `SOUL.md` | Agent personality (name, character, service targets) | ~1187 chars |
| `AGENTS.md` | Permission matrix + red line rules (core security) | ~2320 chars |
| `USER.md` | Current user identity and role | ~639 chars |
| `TOOLS.md` | Tool usage guide | ~1497 chars |
| `IDENTITY.md` | Agent identity metadata | ~1064 chars |
| `HEARTBEAT.md` | Session / health tracking | ~825 chars |
| **Total** | | **~7532 chars** |

### Skills (Cross-Platform)

| Skill | Description | Status |
|-------|-------------|--------|
| `acceptance-checker` | 7-item acceptance checklist for every task | ✅ Live |
| `automation-gray-release` | Gray-release discipline for scheduled automations — manual trial first, verify on-disk artifact, then schedule; cost control and silent-failure guards | ✅ Live |
| `cli-safety` | Agent-friendly CLI execution rules (structured output, exit code, non-interactive, idempotent, audit, file-based success) | ✅ Live |
| `code-review-p0` | P0/P1/P2 graded code review with file location + cause + impact + suggestion | ✅ Live |
| `debug-flow` | 5-step debugging workflow (reproduce → locate → fix → test → regression), with 5-step localization method | ✅ Live |
| `dependency-verify` | Dependency-change verification — installed ≠ works: a successful install or import does not prove the native library loads | ✅ Live |
| `deploy-checker` | 8-item pre-release checklist (scope, diff, test, UI, rollback, notes, observe, honesty) | ✅ Live |
| `doc-freshness-check` | Doc-rot detection — keep README/docs in sync with code; stale-marker and terminology-change propagation | ✅ Live |
| `hook-safety-checker` | Pre-flight for writing, wiring and accepting any hook (pre-commit, PreToolUse, PostToolUse, CI gate); prevents silent hooks | ✅ Live |
| `learning-accelerator` | Use AI tooling to learn a new field fast — new framework, concept, interview prep, technology survey | ✅ Live |
| `long-task-resume` | Resumable long-running jobs — checkpoint first, idempotent reruns, sentinel-based success, explicit recovery command | ✅ Live |
| `memory-layer-router` | Five-layer memory routing decision tree — which layer (SOUL / IDENTITY / USER / MEMORY / daily log / skills) new information belongs to | ✅ Live |
| `rule-migrator` | Rule-file migration and multi-tool sync (Cursor Rules / CLAUDE.md / AGENTS.md) | ✅ Live |
| `session-handoff` | Session-handoff artifact — write an evidence-linked, fail-closed handoff file instead of a chat summary | ✅ Live |
| `skill-authoring-check` | Skill authoring compliance baseline — frontmatter field limits (name/description/compatibility), description formula, progressive disclosure budgets, degrees of freedom, anti-patterns, pre-submit checklist | ✅ Live |
| `task-automator` | Automation task writer — write repeatable, verifiable automation workflows | ✅ Live |
| `task-briefer` | Structured task brief template (background, goal, scope, limits, acceptance, delivery) — probe for missing context | ✅ Live |
| `tdd-discipline` | AI pair-programming TDD discipline — red/green cycle constraints, read the diff instead of trusting summaries | ✅ Live |
| `untrusted-content-boundary` | Trust boundary when an agent consumes untrusted external content (webpages, issues/PRs, comments, downloads) — treat it as data not instructions, segregate and label it, least-privilege tools, human approval before high-impact actions | ✅ Live |
| `version-guard` | Version management and rollback for workflows, configs and apps (Dify, n8n, CI config) | ✅ Live |
| `workspace-isolation` | Multi-workspace context isolation — locate the workspace first, identify foreign files, always use explicit paths | ✅ Live |

### Knowledge Base

- `sources/` — Index of all distilled content with extraction metadata
- `rules/ATOMCODE.md` — Comprehensive behavioral specification (14 sections)
- `DISTILLER.md` — Distillation pipeline specification
- `ROADMAP.md` — 4-phase development roadmap

---

## 🔧 Installation

### Claude Code

```bash
/plugin marketplace add TrueFurina/AGI-Distiller
/plugin install agi-distiller@agi-distiller
```

> ✅ **实测通过**：本机 Claude Code v2.1.251 跑通 `claude plugin validate` → `marketplace add` → `plugin install` → `plugin details`
> 全链路，`Component inventory: Skills (19)` 全部加载。
> ⚠️ 该记录是**当次运行的观测值**（运行时 19 个 skill）；后续新增 skill 后**未复跑**安装链路——数字保持原样，不追改成新计数。
> ✅ **Verified end-to-end** on Claude Code v2.1.251 — all 19 skills load (that run had 19 skills; the chain has **not** been re-run since the skill count changed).

### Codex CLI

```bash
npx skills add TrueFurina/AGI-Distiller
```

> CLI 存在（`skills@1.7.0`，`add <owner/repo>` 语法已核对）。本机无 Codex CLI，**未实装验证**。
> CLI exists (`skills@1.7.0`, `add <owner/repo>` syntax confirmed). No Codex CLI on this machine — **install not actually verified**.

### Manual (Any Agent)

```bash
git clone https://github.com/TrueFurina/AGI-Distiller.git
cp -r AGI-Distiller/skills/* ~/.claude/skills/
```

### Platform Compatibility

> **Verified** — ✅ 实测 = ran the full chain on this machine: `claude plugin validate` → `marketplace add` → `plugin install` → `plugin details`, all 19 skills loaded (Claude Code v2.1.251 — the run predates the current skill count; **not re-run** since). ⚠️ 未实测 / unverified = path follows that platform's public docs; no CLI available here, never actually run.

| Platform | Path | Status |
|----------|------|--------|
| Claude Code | `~/.claude/skills/` | ✅ 实测 |
| Codex CLI | `~/.codex/skills/` | ⚠️ 未实测 |
| Cursor | `.cursor/skills/` | ⚠️ 未实测 |
| Gemini CLI | `~/.gemini/skills/` | ⚠️ 未实测 |
| GitHub Copilot | `.github/skills/` | ⚠️ 未实测 |
| OpenCode | `~/.config/opencode/skills/` | ⚠️ 未实测 |
| Windsurf | `.windsurf/skills/` | ⚠️ 未实测 |

---

## 🧪 The Distillation Pipeline

Every skill in this repository is born from a structured process:

```
1. READ  an article
2. EXTRACT:
   - Pain point: What problem does this solve?
   - Solution: How does it solve it?
   - Actionable rule: What should the agent do differently?
   - Trap: What should the agent avoid?
3. CLASSIFY: Does this fit an existing skill? Or need a new one?
4. PRECIPITATE:
   - If new rule → update ATOMCODE.md
   - If cross-session value → write to memory
   - If high-frequency pattern → create/update skill
5. VERIFY: Is the skill usable? Does it solve the original pain point?
```

See [DISTILLER.md](DISTILLER.md) for the complete pipeline specification.

---

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- [x] Core distillation pipeline design
- [x] 21 production skills
- [x] 14-section behavioral specification (ATOMCODE.md)
- [x] 14 persistent memory entries
- [x] 10 distilled source notes on disk in `sources/` (laodad 4 / wechat 2 / anthropic 1 / comment-distillery 1 / owasp 1 / tencent 1)
- [x] GitHub repository live

### Phase 2: Growth (Next 30 days)
- [x] 21 skills total
- [x] CI pipeline (`.github/workflows/golden-regression.yml`)
- [ ] Marketplace registration
- [ ] Automated distillation pipeline
- [ ] Community contributions

### Phase 3: Ecosystem (3 months)
- [ ] 50+ skills
- [ ] Multi-source distillation (laodad.com, WeChat, Medium, arXiv)
- [ ] Web catalog for browsing skills
- [ ] 10,000+ GitHub stars

---

## 🤝 Contributing

We welcome contributions of all kinds:

- **📝 New sources**: Suggest a high-quality article to distill
- **🔧 New skills**: Submit a skill based on the distillation template
- **🌐 Translations**: Help translate skills to other languages
- **🐛 Bug fixes**: Improve existing skills

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📚 Sources Distilled

| Source | Notes on disk | Category | Status |
|--------|---------------|----------|--------|
| [laodad.com](https://laodad.com) | 4 | AI programming efficiency | ✅ |
| WeChat (personal AI OS, 10x learning) | 2 | Learning & agent workflow | ✅ |
| 卡码大模型 (Tencent) | 1 | CLI & Agent | ✅ |
| [comment-distillery](https://github.com/TrueFurina/comment-distillery) | 1 | Skill engineering (sibling project) | ✅ |
| More coming... | | | 🚧 |

**10 distilled source notes on disk** (`sources/**/*.md`). The count above is verified against the working tree by `scripts/check_doc_consistency.py`.

---

## 📄 License

MIT — use these skills in your projects, teams, and tools. Full credit to the original authors of the articles that inspired each skill.

---

## ⭐ Star History

If this project resonates with you, give it a star ⭐ — it helps more people find this vision of self-evolving AI agents.

---

> *"The endgame is not CLI. The endgame is every piece of software growing a set of interfaces that an Agent can call, verify, audit, and be safely confined by. CLI is just the first one ready."*
> — 卡码大模型

---

## License & Usage Notice

**Source-Available · All Rights Reserved**

This project is source-available and all rights are reserved by the author. The code is provided for **viewing and evaluation purposes only** — access does not grant any right to copy, modify, redistribute, use commercially, or create derivative works. Unauthorized reuse may carry legal risk. Contact the author for explicit written permission before any other use.

**本仓库为「源码可查、权利保留」项目（source-available / all-rights-reserved）。代码仅供查看与评估，未授权任何复制、再分发、修改、商用或衍生创作。擅自借用代码存在法律风险；如有需要请先联系作者获取明确书面许可。**

