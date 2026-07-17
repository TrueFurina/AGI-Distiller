# 🧪 AGI Distiller

> **AI 编程知识蒸馏系统**
>
> 阅读. 蒸馏. 进化. 循环.

[![Agent Skills](https://img.shields.io/badge/spec-agentskills.io-7dd3fc)](https://agentskills.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-marketplace-a78bfa)](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
[![Codex CLI](https://img.shields.io/badge/Codex_CLI-compatible-10A37F)](https://github.com/openai/codex)

---

## 🌟 愿景

**AGI Distiller** 不只是另一个 skill 集合。它是一个**活的知识蒸馏系统**：

1. **阅读**高质量技术内容（文章、博客、论文、公众号）
2. **提取**痛点、解法和可执行规则
3. **沉淀**为跨平台 agent skill、行为规范和协作协议
4. **自我进化**——读得越多，能力越强

> **终极目标：一个通过阅读、蒸馏和应用知识持续自我进化的 AI 代理——一次一篇文章。**

---

## 🔬 差异化

| 维度 | 传统 Skill 仓库 | AGI Distiller |
|-----------|----------------------|---------------|
| **来源** | 开发者经验 | **高质量技术内容** |
| **创建方式** | 手工编写 | **从内容中蒸馏** |
| **进化方式** | 手动 PR | **自我进化** |
| **聚焦** | 通用编码 | **终端 AI 代理效率** |
| **语言** | 仅英文 | **中英双语** |
| **理念** | "这里是 skill" | **"这里是生产 skill 的蒸馏器"** |

---

## 🏗️ 系统架构

```
                    ┌─────────────────────────────┐
                    │        知识来源              │
                    │  laodad.com · 公众号 · 博客  │
                    │  arXiv · GitHub Issues · 更多 │
                    └─────────────┬───────────────┘
                                  │ 阅读
                    ┌─────────────▼───────────────┐
                    │        蒸馏管道              │
                    │                              │
                    │  ① 提取痛点                 │
                    │  ② 提取解法                 │
                    │  ③ 推导可执行规则           │
                    │  ④ 沉淀为 skill             │
                    │  ⑤ 更新行为规范             │
                    └─────────────┬───────────────┘
                                  │ 输出
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  Agent Skill  │       │  规则与规范    │       │  记忆与知识    │
│  (SKILL.md)   │       │  (ATOMCODE.md) │       │  (notes/)     │
│  跨平台       │       │  最佳实践     │       │  知识库       │
└───────────────┘       └───────────────┘       └───────────────┘
```

---

## 📦 仓库内容

### Agent 规范文件（OpenAI 开源标准）

| 文件 | 用途 | 大小 |
|------|------|------|
| `SOUL.md` | Agent 人格设定（名字、性格、服务对象） | ~905 字符 |
| `AGENTS.md` | 权限矩阵 + 红线规则（核心安全约束） | ~2016 字符 |
| `USER.md` | 当前用户身份和角色 | ~359 字符 |
| `TOOLS.md` | 工具使用指南 | ~1013 字符 |
| `IDENTITY.md` | Agent 身份元数据 | ~753 字符 |
| `HEARTBEAT.md` | 会话/健康跟踪 | ~235 字符 |
| **总计** | | **~5281 字符** |

### Skill（跨平台）

| Skill | 描述 | 状态 |
|-------|------|------|
| `acceptance-checker` | 7 项验收清单：每次任务完成时自动输出 | ✅ 已发布 |
| `debug-flow` | 5 步调试流程：复现→定位→最小改动→测试→回归 | ✅ 已发布 |
| `deploy-checker` | 8 项上线检查清单：范围、diff、测试、页面、回滚、备注、观察、不自欺 | ✅ 已发布 |
| `task-automator` | 自动化任务编写器：把重复工作写成可稳定执行的自动化流程 | ✅ 已发布 |
| `task-briefer` | 结构化任务说明模板（背景、目标、范围、限制、验收） | 🚧 待写 |
| `code-review-p0` | P0/P1/P2 分级代码审查 | 🚧 待写 |
| `cli-safety` | Agent 友好 CLI 安全执行规则 | 🚧 待写 |

### 知识库

- `sources/` — 已蒸馏文章索引
- `rules/ATOMCODE.md` — 完整行为规范（12 节）
- `DISTILLER.md` — 蒸馏管道规范
- `ROADMAP.md` — 4 阶段发展路线图

---

## 🔧 安装方式

### Claude Code

```bash
/plugin marketplace add agi-distiller/agi-distiller
/plugin install agi-distiller@agi-distiller
```

### Codex CLI

```bash
npx skills add agi-distiller/agi-distiller
```

### 手动安装（任意 Agent）

```bash
git clone https://github.com/TrueFurina/AGI-Distiller.git
cp -r AGI-Distiller/skills/* ~/.claude/skills/
```

### 平台兼容性

| 平台 | 路径 | 状态 |
|----------|------|--------|
| Claude Code | `~/.claude/skills/` | ✅ |
| Codex CLI | `~/.codex/skills/` | ✅ |
| Cursor | `.cursor/skills/` | ✅ |
| Gemini CLI | `.gemini/skills/` | ✅ |
| GitHub Copilot | `.github/skills/` | ✅ |
| OpenCode | `~/.config/opencode/skills/` | ✅ |
| Windsurf | `.windsurf/skills/` | ✅ |

---

## 🧪 蒸馏管道

仓库中的每个 skill 都来自结构化流程：

```
1. 阅读文章
2. 提取：
   - 痛点：解决什么问题
   - 解法：如何解决
   - 可执行规则：Agent 应该怎么做
   - 陷阱：Agent 应该避免什么
3. 分类：适合现有 skill 还是需要新建
4. 沉淀：
   - 新规则 → 更新 ATOMCODE.md
   - 跨会话价值 → 写入 memory
   - 高频模式 → 创建/更新 skill
5. 验证：skill 是否可用，是否解决原始痛点
```

详见 [DISTILLER.md](DISTILLER.md) 完整管道规范。

---

## 🗺️ 路线图

### Phase 1：筑基期（当前）
- [x] 核心蒸馏管道设计
- [x] 4 个生产级 skill
- [x] 12 节行为规范（ATOMCODE.md）
- [x] 14 条持久化记忆
- [x] 22 篇 laodad.com 文章蒸馏
- [x] GitHub 仓库上线

### Phase 2：成长期（未来 30 天）
- [ ] 20 个 skill
- [ ] CI 流水线
- [ ] 注册 marketplace
- [ ] 自动化蒸馏管道
- [ ] 社区贡献

### Phase 3：生态期（3 个月）
- [ ] 50+ skill
- [ ] 多源蒸馏（laodad.com、公众号、Medium、arXiv）
- [ ] Web 目录
- [ ] 10,000+ GitHub stars

---

## 🤝 贡献指南

欢迎各种形式的贡献：

- **📝 新来源**：推荐高质量文章
- **🔧 新 skill**：基于蒸馏模板提交 skill
- **🌐 翻译**：帮助翻译 skill 到其他语言
- **🐛 Bug 修复**：改进现有 skill

---

## 📚 已蒸馏来源

| 来源 | 文章数 | 分类 | 状态 |
|--------|----------|----------|--------|
| [laodad.com](https://laodad.com) | 22 | AI 编程效率 | ✅ |
| 卡码大模型（微信） | 1 | CLI & Agent | ✅ |
| 持续扩展中... | | | 🚧 |

---

## 📄 许可证

MIT — 你可以在自己的项目、团队和工具中自由使用这些 skill。每篇文章的原始作者保留完整署名权。

---

## ⭐ Star 历史

如果这个项目对你有帮助，请点一个 star ⭐——让更多人看到自我进化 AI 代理的愿景。

---

> *"终局不是 CLI。终局是所有软件都长出一套 Agent 能调用、能验证、能审计、也能被安全关住的接口。CLI 只是最早准备好的那一个。"*
> — 卡码大模型