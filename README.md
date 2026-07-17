# 🧪 AGI Distiller

> **Knowledge Distillation System for AI Coding Agents**
> **AI 编程知识蒸馏系统**
>
> Read. Distill. Evolve. Repeat. / 阅读. 蒸馏. 进化. 循环.

[![Agent Skills](https://img.shields.io/badge/spec-agentskills.io-7dd3fc)](https://agentskills.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-marketplace-a78bfa)](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-compatible-10A37F)](https://github.com/openai/codex)

---

## 🌟 Vision / 愿景

**AGI Distiller** is not just another skill collection. It is a **living knowledge distillation system** that:

**AGI Distiller** 不只是另一个 skill 集合。它是一个**活的知识蒸馏系统**：

1. **Reads** high-quality technical content (articles, blogs, papers, WeChat posts) / **阅读**高质量技术内容
2. **Extracts** pain points, solutions, and actionable rules / **提取**痛点、解法和可执行规则
3. **Precipitates** them into cross-platform agent skills, behavioral rules, and collaboration protocols / **沉淀**为跨平台 agent skill、行为规范和协作协议
4. **Evolves** itself — the more it reads, the more capable it becomes / **自我进化**——读得越多，能力越强

> **The ultimate goal: An AI agent that continuously self-improves by reading, distilling, and applying knowledge — one article at a time.**
> **终极目标：一个通过阅读、蒸馏和应用知识持续自我进化的 AI 代理——一次一篇文章。**

---

## 🔬 What Makes This Different / 差异化

| Dimension / 维度 | Traditional Skill Repos / 传统 Skill 仓库 | AGI Distiller |
|-----------|----------------------|---------------|
| **Source / 来源** | Developer experience | **High-quality technical content** / 高质量技术内容 |
| **Creation / 创建方式** | Hand-written | **Distilled from content** / 从内容中蒸馏 |
| **Evolution / 进化方式** | Manual PRs | **Self-evolving** / 自我进化 |
| **Focus / 聚焦** | General coding | **Terminal AI agent efficiency** / 终端 AI 代理效率 |
| **Language / 语言** | English only | **Bilingual** / 中英双语 |
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
| `SOUL.md` | Agent personality (name, character, service targets) | ~905 chars |
| `AGENTS.md` | Permission matrix + red line rules (core security) | ~2016 chars |
| `USER.md` | Current user identity and role | ~359 chars |
| `TOOLS.md` | Tool usage guide | ~1013 chars |
| `IDENTITY.md` | Agent identity metadata | ~753 chars |
| `HEARTBEAT.md` | Session / health tracking | ~235 chars |
| **Total** | | **~5281 chars** |

### Skills (Cross-Platform)

| Skill | Description | Status |
|-------|-------------|--------|
| `acceptance-checker` | 7-item acceptance checklist for every task | ✅ Live |
| `debug-flow` | 5-step debugging workflow (reproduce → locate → fix → test → regression) | ✅ Live |
| `deploy-checker` | 8-item pre-release checklist (scope, diff, test, UI, rollback, notes, observe, honesty) | ✅ Live |
| `task-briefer` | Structured task brief template (background, goal, scope, limits,验收) | 🚧 Next |
| `code-review-p0` | P0/P1/P2 graded code review | 🚧 Next |
| `cli-safety` | Agent-friendly CLI execution rules | 🚧 Next |

### Knowledge Base

- `sources/` — Index of all distilled content with extraction metadata
- `rules/ATOMCODE.md` — Comprehensive behavioral specification (12 sections)
- `DISTILLER.md` — Distillation pipeline specification
- `ROADMAP.md` — 4-phase development roadmap

---

## 🔧 Installation

### Claude Code

```bash
/plugin marketplace add agi-distiller/agi-distiller
/plugin install agi-distiller@agi-distiller
```

### Codex CLI

```bash
npx skills add agi-distiller/agi-distiller
```

### Manual (Any Agent)

```bash
git clone https://github.com/agi-distiller/agi-distiller.git
# Copy skills/ to your agent's skills directory
cp -r agi-distiller/skills/* ~/.claude/skills/
```

### Platform Compatibility

| Platform | Path | Status |
|----------|------|--------|
| Claude Code | `~/.claude/skills/` | ✅ |
| Codex CLI | `~/.codex/skills/` | ✅ |
| Cursor | `.cursor/skills/` | ✅ |
| Gemini CLI | `.gemini/skills/` | ✅ |
| GitHub Copilot | `.github/skills/` | ✅ |
| OpenCode | `~/.config/opencode/skills/` | ✅ |
| Windsurf | `.windsurf/skills/` | ✅ |

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
- [x] 2 production skills (acceptance-checker, debug-flow)
- [x] 11-section behavioral specification (ATOMCODE.md)
- [x] 8 persistent memory entries
- [x] 20+ articles distilled from laodad.com

### Phase 2: Growth (Next 30 days)
- [ ] 20 skills total
- [ ] GitHub repository with CI
- [ ] Bilingual README (中文 + English)
- [ ] Marketplace registration
- [ ] Automated distillation pipeline

### Phase 3: Ecosystem (3 months)
- [ ] 50+ skills
- [ ] Multi-source distillation (laodad.com, WeChat, Medium, arXiv)
- [ ] Community contributions
- [ ] Web catalog for browsing skills

### Phase 4: Scale (6 months)
- [ ] 100+ skills
- [ ] Multi-agent collaboration workflows
- [ ] Self-evolution dashboard
- [ ] 10,000+ GitHub stars

---

## 🤝 Contributing

We welcome contributions of all kinds:

- **📝 New sources**: Suggest a high-quality article/blog to distill
- **🔧 New skills**: Submit a skill based on the distillation template
- **🌐 Translations**: Help translate skills to other languages
- **🐛 Bug fixes**: Improve existing skills
- **💡 Ideas**: Share your vision for the distillation pipeline

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📚 Sources Distilled

| Source | Articles | Category | Status |
|--------|----------|----------|--------|
| [laodad.com](https://laodad.com) | 19 | AI programming efficiency | ✅ |
| 卡码大模型 (WeChat) | 1 | CLI & Agent | ✅ |
| More coming... | | | 🚧 |

---

## 📄 License

MIT — use these skills in your projects, teams, and tools. Full credit to the original authors of the articles that inspired each skill.

---

## ⭐ Star History

If this project resonates with you, give it a star ⭐ — it helps more people find this vision of self-evolving AI agents.

---

> **"The endgame is not CLI. The endgame is every piece of software growing a set of interfaces that an Agent can call, verify, audit, and be safely confined by. CLI is just the first one ready."**
> — 卡码大模型