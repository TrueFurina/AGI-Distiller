---
name: acceptance-checker
description: 验收清单自动输出 — 每次任务完成后按7项结构输出验收结果：目标是否完成、改动范围、测试验证、旧功能回归、异常边界处理、回滚方式、剩余风险。触发词：验收、检查、清单、checklist、7项、交付检查、验收清单
argument-hint: ["验收本次改动", "检查交付物", "输出验收清单", "checklist"]
allowed-tools: bash, read_file, grep, glob
---

# 验收清单

用户请求: $ARGUMENTS

## 规则

1. 严格按 7 项结构输出，不允许跳过任何一项。
2. 每一项必须写具体结论，不允许写"已完成"这种空话。
3. 没有证据的结论不写，无法验证的明确标注"未验证"。
4. 风险项必须给出具体表现和影响，不写模糊提醒。

## 输出格式

### 1. 核心目标是否完成
目标是什么，用户结果是否已出现。

### 2. 改动范围
- 修改了哪些文件：
- 每个文件的核心变化：
- 是否包含任务外文件（如有，说明原因）：

### 3. 测试验证
- 已运行命令及结果：
- 人工检查了什么：
- 未验证项及原因：

### 4. 旧功能回归
- 高风险相邻功能是否正常：
- 低风险抽查结果：

### 5. 异常/边界处理
- 空数据时表现：
- 接口失败/超时表现：
- 权限不足时表现：
- 执行失败时是否留下脏数据：

### 6. 回滚方式
- 是否有独立提交或清晰 diff：
- 回滚命令或步骤：

### 7. 剩余风险
- 未验证的假设：
- 需要人工判断的地方：
- 后续待办：

## 执行步骤

### 步骤 1：收集信息

```bash
# 获取当前 git diff 了解改动范围
git diff --stat 2>/dev/null
echo "---"
git diff 2>/dev/null | head -100

# 获取最近提交信息
git log --oneline -5 2>/dev/null

# 检查是否有未提交的改动
git status --short 2>/dev/null
```

### 步骤 2：检查测试状态

```bash
# 检查项目类型并运行对应检查
if [ -f "Cargo.toml" ]; then
  cargo check 2>&1 | tail -20
elif [ -f "package.json" ]; then
  npm run lint 2>/dev/null && npm test 2>/dev/null || echo "无可用测试命令"
elif [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
  python -m pytest --version 2>/dev/null && python -m pytest --tb=short 2>/dev/null || echo "无可用测试命令"
fi
```

### 步骤 3：输出验收报告

按上述 7 项结构输出完整报告。