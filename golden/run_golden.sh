#!/bin/bash
# ============================================================
# Golden Test Set 跑分脚本（落盘判成功）
# 用法:
#   bash run_golden.sh <replies_dir> [model_name]
#   replies_dir 结构: replies/<case_id>.txt（每场景一份 Agent 回复）
# 产出:
#   golden/results/<timestamp>.json — 判分报告（落盘即成功判据）
# ============================================================
set -euo pipefail

GOLDEN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$GOLDEN_DIR")"
REPLIES="${1:?用法: bash run_golden.sh <replies_dir> [model_name]}"
MODEL="${2:-unknown}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$GOLDEN_DIR/results/$STAMP.json"

mkdir -p "$GOLDEN_DIR/results"

# 依赖检查
python -c "import yaml" 2>/dev/null || { echo "❌ 需要 PyYAML: pip install pyyaml"; exit 1; }

# 场景完整性预检：每个 case 必须有对应回复文件
MISSING=0
for f in "$GOLDEN_DIR"/cases/*.yaml; do
  id=$(grep -m1 '^id:' "$f" | sed 's/id:[[:space:]]*//')
  if [ ! -f "$REPLIES/$id.txt" ]; then
    echo "⚠️ 缺回复: $REPLIES/$id.txt"
    MISSING=$((MISSING+1))
  fi
done

# 判分（落盘报告是唯一成功判据）
cd "$REPO_ROOT"
if python golden/graders.py --cases golden/cases --replies "$REPLIES" --out "$OUT" --model "$MODEL"; then
  test -f "$OUT" || { echo "❌ 报告未落盘"; exit 1; }
  echo ""
  echo "✅ 跑分完成: $OUT"
  echo "   对比: python golden/compare.py golden/results/<旧>.json $OUT"
  [ "$MISSING" -gt 0 ] && echo "   ⚠️ 有 $MISSING 个场景缺回复，未计入总分"
else
  echo "❌ 判分失败"
  exit 1
fi