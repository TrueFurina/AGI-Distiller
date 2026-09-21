#!/bin/bash
# ============================================================
# 分桶模板：agent-project（LangGraph/多智能体/Agent 类项目）
# 来源：study-help-pro (MARS-408) 落地经验提炼
# 用法：由统一入口 bootstrap.sh 调用：bash agent-project.sh <名称> <目录>
# ============================================================
set -euo pipefail

PROJECT="${1:?用法: agent-project.sh <项目名> <目标目录>}"
TARGET="${2:?缺少目标目录}"

mkdir -p "$TARGET/plans" "$TARGET/docs" "$TARGET/.agents/skills"

# ── AGENTS.md（Agent 项目特化版）──
cat > "$TARGET/AGENTS.md" <<EOF
# $PROJECT — 项目事实源（Agent 类）

## 这是什么
[一句话：多智能体系统是啥、解决什么问题、架构分层（路由/编排/策略/评审）]

## 命令
- 启动后端: cd py-server && pip install -e . && python main.py
- 测试: [⚠️ 若全量 pytest 有已知兼容坑，写明分文件/分标记的正确姿势]
- 功能验证: [绕过框架问题的直接调用方式]

## 目录
- agents/ 各智能体职责（一行一个）
- 核心链路: [入口 → 路由 → 智能体 → 评审 → 出口]

## 禁区
- 不碰 .env / 密钥 / 生产数据库
- 破坏性操作必须二次确认
- LLM 调用必须有白名单/token 预算/墙钟止损（确定性优先，LLM 兜底）
- [多分支项目写明：分支同步方向唯一，前缀隔离纪律]

## 必须问人的事
- [资金/权限/登录/DDL 变更]
- [LLM provider 换用/配额消耗策略]
EOF

# ── plans/ ──
cat > "$TARGET/plans/current.md" <<'EOF'
# 当前计划

## 待办
- [ ]

## 进行中
- [ ]

## 系统理解任务
- [ ] 能复述核心链路（路由/编排/评审的判定顺序）
- [ ] 搞清确定性层与 LLM 层的升级边界

## 已完成
- [ ]
EOF

cat > "$TARGET/plans/decisions.md" <<'EOF'
# 技术决策记录

| 日期 | 决策 | 原因 | 备选方案 |
|------|------|------|----------|
|      |      |      |          |
EOF

# ── docs/system-map.md ──
cat > "$TARGET/docs/system-map.md" <<'EOF'
# 系统地图

## 核心链路
[入口 → Triage 路由 → 智能体执行 → 评审/校验 → 提交闸门]

## 分层原则
- 确定性优先：能枚举的套路走静态/规则层，不调 LLM
- LLM 兜底：白名单 + token 预算 + 墙钟止损，请求出错即硬失败

## 已知雷区
- [框架版本兼容坑（如全量 pytest 失败的正确绕法）]
- [外部模型/依赖的会话级资产（模型文件不入库的恢复方式）]

## 分层掌控清单
- 必须懂: 核心链路、智能体间协议、奖励/评分机制
- 知道就行: 通用工具类
- 可以不懂: 具体智能体内部实现细节
EOF

# ── 项目级 skill 四件套 ──
mkdir -p "$TARGET/.agents/skills"/{project-context,arch-rules,test-gate,debug-playbook}
cat > "$TARGET/.agents/skills/project-context/SKILL.md" <<'EOF'
---
name: project-context
description: 项目上下文入口——架构分层、命令、真值文件；触发词：项目上下文、这个项目是什么
---
# 项目上下文

[填：项目一句话、架构分层、真值文件清单、关键命令、禁区速览]
EOF
cat > "$TARGET/.agents/skills/arch-rules/SKILL.md" <<'EOF'
---
name: arch-rules
description: 架构红线——确定性优先/LLM 约束/分支纪律；触发词：架构红线、LLM 约束、分支
---
# 架构红线
1. 确定性优先：静态/规则层能解决的禁止调 LLM
2. LLM 调用三重约束：白名单 + token 预算 + 墙钟止损
3. [分支纪律：同步方向唯一 / 前缀隔离]
4. 叙事结论不可信：唯一可信 = 可复现命令 + 落盘工件
EOF
cat > "$TARGET/.agents/skills/test-gate/SKILL.md" <<'EOF'
---
name: test-gate
description: 测试闸门——分文件/分标记的正确姿势；触发词：测试、pytest、验证
---
# 测试闸门
[填：全量测试的已知坑、分文件命令、功能级验证方式、汇报纪律]
EOF
cat > "$TARGET/.agents/skills/debug-playbook/SKILL.md" <<'EOF'
---
name: debug-playbook
description: 排障流程——启动失败/依赖未就绪/分支冲突；触发词：排障、报错、启动失败
---
# 排障手册
[填：按故障类型分节的排查路径]
EOF

echo "✅ [agent-project] $PROJECT 模板生成完成: $TARGET"
echo "   下一步: 填 AGENTS.md/system-map 的[占位符]，审核 .agents/skills/ 四件套"