#!/bin/bash
# ============================================================
# AGI-Distiller 项目初始化统一入口（分桶模板调度器）
# 用法: bash bootstrap.sh --type <generic|agent|competition|web> <项目名> [目标目录]
#       bash bootstrap.sh <项目名> [目标目录]          # 默认 generic
# 产出: AGENTS.md(薄) + plans/ 外脑 + docs/system-map.md + .agents/skills/（按桶）
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/templates"

TYPE="generic"
PROJECT=""
TARGET=""

# 参数解析：--type <t> <name> [dir] 或 <name> [dir]
if [ "${1:-}" = "--type" ]; then
  TYPE="${2:?--type 需要 generic|agent|competition|web}"
  shift 2
fi
PROJECT="${1:?用法: bash bootstrap.sh [--type generic|agent|competition|web] <项目名> [目标目录]}"
TARGET="${2:-$PROJECT}"

if [ -e "$TARGET" ]; then
  echo "❌ 目标已存在: $TARGET"; exit 1
fi

case "$TYPE" in
  agent)
    bash "$TEMPLATE_DIR/agent-project.sh" "$PROJECT" "$TARGET"
    ;;
  competition)
    bash "$TEMPLATE_DIR/competition.sh" "$PROJECT" "$TARGET"
    ;;
  web)
    bash "$TEMPLATE_DIR/web-app.sh" "$PROJECT" "$TARGET"
    ;;
  generic)
    # ── 通用版（原 bootstrap 逻辑）──
    mkdir -p "$TARGET/plans" "$TARGET/docs"
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
    echo "✅ [generic] $PROJECT 初始化完成: $TARGET"
    echo "   下一步: 填 AGENTS.md 的[占位符]，在 plans/current.md 写第一个任务"
    ;;
  *)
    echo "❌ 未知类型: $TYPE（可选 generic|agent|competition|web）"; exit 1
    ;;
esac

# 全部桶统一：git init（全新目录）
if [ ! -d "$TARGET/.git" ]; then
  git -C "$TARGET" init -b main >/dev/null 2>&1 || git -C "$TARGET" init >/dev/null
fi