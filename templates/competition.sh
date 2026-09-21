#!/bin/bash
# ============================================================
# 分桶模板：competition（竞赛交付类：诚实口径 + 提交包 + 测试基线）
# 来源：marl-ecdsa-consensus-chain (CCF) + 西湖论剑 落地经验提炼
# 用法：由统一入口 bootstrap.sh 调用：bash competition.sh <名称> <目录>
# ============================================================
set -euo pipefail

PROJECT="${1:?用法: competition.sh <项目名> <目标目录>}"
TARGET="${2:?缺少目标目录}"

mkdir -p "$TARGET/plans" "$TARGET/docs" "$TARGET/.agents/skills"

# ── AGENTS.md（竞赛特化版）──
cat > "$TARGET/AGENTS.md" <<EOF
# $PROJECT — 项目事实源（竞赛类）

## 这是什么
[一句话：参赛赛道、核心创新点、当前阶段（开发/提交/答辩）]

## 命令
- 测试: [命令 + 测试基线数字（如 1603 passed），跌破必须解释]
- 主实验: [可复现命令]
- 提交包生成: [唯一打包脚本路径，禁止手工整理提交树]

## 目录
- 核心代码目录: [一行说明]
- 提交包: [路径，唯一口径源]
- 实验与分析: [脚本路径]

## 禁区
- 诚实口径：实验结论不得夸大显著性，Nash/证明类表述不得写成 formailly proven
- 提交包禁止手工编辑，只走打包脚本；旧包副本只读
- 密钥/私钥材料永不入库
- 数字必须能追溯到代码真值（分析脚本输出），文档禁止自造数字

## 必须问人的事
- 提交包内容变更（截止前冻结）
- 实验 seed 数/统计口径变更
EOF

# ── plans/ ──
cat > "$TARGET/plans/current.md" <<'EOF'
# 当前计划

## 待办
- [ ]

## 进行中
- [ ]

## 系统理解任务
- [ ] 理解核心机制的判定链路
- [ ] 掌握测试基线与实验复现命令

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

## 核心机制
[核心创新点的判定链路，一段话 + 简图]

## 诚实口径基线
- 实验结论原文：[如 n=22 seeds, p=0.126 方向一致但不显著]
- 禁止的过度声明：[如 formally proven / 只报最好 seed]

## 已知雷区
- [多份提交包副本的一致性问题：以最新 _提交包 为准]
- [外层工作区 vs 核心代码目录的关系]

## 分层掌控清单
- 必须懂: 核心机制、实验统计口径、提交规范
- 知道就行: 工具脚本
- 可以不懂: 具体实验内部实现
EOF

# ── 项目级 skill 四件套 ──
mkdir -p "$TARGET/.agents/skills"/{project-context,arch-rules,test-gate,debug-playbook}
cat > "$TARGET/.agents/skills/project-context/SKILL.md" <<'EOF'
---
name: project-context
description: 项目上下文入口——赛道、核心机制、提交包、命令；触发词：项目上下文、竞赛、提交
---
# 项目上下文
[填：赛道/版本、核心机制速览、真值文件、关键命令、仓库布局（核心代码 vs 提交包副本）]
EOF
cat > "$TARGET/.agents/skills/arch-rules/SKILL.md" <<'EOF'
---
name: arch-rules
description: 诚实口径红线——实验结论/证明强度/数字对齐；触发词：诚实口径、红线、口径
---
# 架构红线（诚实口径为最高红线）
1. 实验结论保留完整统计表述（seed 数 + p 值），禁止夸大显著性
2. 证明强度如实标注（数值验证 ≠ 形式化证明）
3. 文档数字必须可追溯到代码真值
4. 提交包只走打包脚本，旧副本只读
5. 密钥/私钥永不入库
EOF
cat > "$TARGET/.agents/skills/test-gate/SKILL.md" <<'EOF'
---
name: test-gate
description: 测试闸门——基线数字、改动类型→验证方式映射；触发词：测试、验证、基线
---
# 测试闸门
## 标准命令
[命令 + 基线数字（如 1603 passed 应全绿）]
## 改动类型 → 验证方式
| 改动 | 必须跑 |
|------|--------|
| [核心机制] | 全量测试 + 短跑冒烟 |
| [安全/加密层] | 全量测试 + 演示目录冒烟 |
| [实验/统计] | 全量测试 + 小参数实验确认环路 |
| [文档数字] | 与分析脚本输出对账 |
## 汇报纪律
基线跌破必须解释；结论引用必须带统计量。
EOF
cat > "$TARGET/.agents/skills/debug-playbook/SKILL.md" <<'EOF'
---
name: debug-playbook
description: 排障流程——测试失败/机制异常/提交包不一致；触发词：排障、报错、提交包
---
# 排障手册
[填：测试失败三分类（本次/既有/环境）、核心机制异常排查、提交包以最新为准的核对流程]
EOF

echo "✅ [competition] $PROJECT 模板生成完成: $TARGET"
echo "   下一步: 填占位符（尤其诚实口径基线原文），审核 skill 四件套"