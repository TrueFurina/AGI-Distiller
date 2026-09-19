#!/bin/bash
# ============================================================
# AGI-Distiller 项目初始化脚本（按 thinking.md 最佳实践）
# 用法: bash bootstrap.sh <项目名> [目标目录]
# 产出: AGENTS.md(薄) + plans/ 三件套 + docs/system-map.md
# ============================================================
set -euo pipefail

PROJECT="${1:?用法: bash bootstrap.sh <项目名> [目标目录]}"
TARGET="${2:-$PROJECT}"

if [ -e "$TARGET" ]; then
  echo "❌ 目标已存在: $TARGET"; exit 1
fi

mkdir -p "$TARGET/plans" "$TARGET/docs"

# 1. AGENTS.md —— 门禁，不是培训手册（无聊且短，100 行内）
cat > "$TARGET/AGENTS.md" <<EOF
# $PROJECT — 项目事实源

## 这是什么
[一句话：项目是啥、给谁用]

## 命令
- 启动: [命令]
- 测试: [命令]
- 构建: [命令]

## 目录
[关键目录一句话职责，5 行内]

## 禁区
- 不碰 .env / 密钥 / 生产数据库
- 破坏性操作必须二次确认
- [本项目特有禁区]

## 必须问人的事
- [资金/权限/登录/DDL 变更]
EOF

# 2. plans/ —— 计划外脑（换项目恢复上下文）
cat > "$TARGET/plans/current.md" <<'EOF'
# 当前计划

## 待办
- [ ]

## 进行中
- [ ]

## 系统理解任务（理解项目是第一类任务）
- [ ]

## 已完成
- [ ]
EOF

cat > "$TARGET/plans/decisions.md" <<'EOF'
# 技术决策记录

| 日期 | 决策 | 原因 | 备选方案 |
|------|------|------|----------|
|      |      |      |          |
EOF

# 3. docs/system-map.md —— 系统地图（你是作者，AI 只是助手）
cat > "$TARGET/docs/system-map.md" <<'EOF'
# 系统地图

## 核心领域
- [核心实体与状态机]

## 关键链路
- [入口 → 处理 → 出口]

## 已知雷区
- [历史原因导致的坑]

## 分层掌控清单（必须懂 / 知道就行 / 可以不懂）
- 必须懂: 核心领域模型、关键业务流程、外部集成
- 知道就行: 通用工具类
- 可以不懂: 交互细节、配置模板
EOF

# 4. git init（如果是全新目录）
if [ ! -d "$TARGET/.git" ]; then
  git -C "$TARGET" init -b main >/dev/null 2>&1 || git -C "$TARGET" init >/dev/null
fi

echo "✅ 项目 $PROJECT 初始化完成: $TARGET"
echo "   下一步: 填 AGENTS.md 的[占位符]，在 plans/current.md 写第一个任务"
