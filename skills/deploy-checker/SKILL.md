---
name: deploy-checker
description: 上线检查清单 — 发布前按8项逐条检查：改动范围、diff审查、测试匹配、页面验证、回滚方案、发布备注、上线后观察、不自欺。触发词：上线、发布、部署、发版、release、上线检查、发布前检查、deploy、deployment
argument-hint: ["帮我做上线检查", "发布前检查", "准备上线", "部署检查"]
allowed-tools: bash, read_file, grep, glob
---

# 上线检查清单

用户请求: $ARGUMENTS

## 规则

1. 严格按 8 项逐条检查，不允许跳过。
2. 每一项必须写具体结论和证据，不允许写"已验证"这种空话。
3. 没有跑过的测试明确标注"未验证"，不确定的风险明确保留。
4. AI 交付最怕把不确定包装成确定——不自欺。

---

## ① 确认改动范围

```bash
# 获取变更统计
git diff --stat 2>/dev/null
echo "---"
# 查看具体变更
git diff 2>/dev/null | head -80
echo "---"
# 检查是否有未跟踪文件
git status --short 2>/dev/null
```

### 输出
```
- 改了哪些文件：
- 每个文件解决什么问题：
- 是否有超出原需求的修改：
- 高风险区域检查（配置/权限/数据库/支付/登录）：
```

---

## ② 审 diff，不听总结

```bash
# 重点看删除行、条件判断、默认值、配置文件
echo "=== 删除行 ==="
git diff 2>/dev/null | grep "^-" | grep -v "^---" | head -30
echo "=== 新增的条件判断 ==="
git diff 2>/dev/null | grep "^+.*if\|^+.*switch\|^+.*match\|^+.*else" | head -20
echo "=== 配置文件变更 ==="
git diff --name-only 2>/dev/null | grep -i "config\|\.env\|\.yml\|\.yaml\|\.json\|\.toml\|\.ini"
```

### 输出
```
- 删除行风险检查：
- 条件判断变更检查：
- 默认值变更检查：
- 配置文件变更检查：
- 权限校验变更检查：
```

---

## ③ 测试命令匹配改动类型

```bash
# 判断改动类型
CHANGED_FILES=$(git diff --name-only 2>/dev/null)

echo "=== 改动类型分析 ==="
echo "$CHANGED_FILES" | grep -q "\.css\|\.scss\|\.less\|style\|\.html\|\.vue\|\.tsx\|\.jsx" && echo "▶ 样式改动"
echo "$CHANGED_FILES" | grep -q "api\|route\|controller\|handler\|endpoint\|\.graphql" && echo "▶ 接口改动"
echo "$CHANGED_FILES" | grep -q "migration\|schema\|sql\|database\|db\|model" && echo "▶ 数据改动"
echo "$CHANGED_FILES" | grep -q "\.sh\|\.py\|\.js\|\.ts" && echo "▶ 脚本改动"
echo "$CHANGED_FILES" | grep -q "publish\|deploy\|release\|ci\|cd\|Dockerfile" && echo "▶ 发布流程改动"

# 运行项目检查
if [ -f "Cargo.toml" ]; then
  cargo check 2>&1 | tail -10
elif [ -f "package.json" ]; then
  npm run lint 2>/dev/null | tail -10
  npm test 2>/dev/null | tail -10
elif [ -f "pyproject.toml" ]; then
  python -m pytest --tb=short 2>/dev/null | tail -10
fi
```

### 输出
```
- 改动类型：
- 匹配的验证方式：
- 已运行命令及结果：
- 未验证项及原因：
```

---

## ④ 页面和流程必须打开看

### 输出
```
- 新增页面是否能访问：
- 移动端是否遮挡/换行/溢出：
- 按钮是否能点击：
- 表单提交后是否有正确提示：
- SEO 标题/描述/图片 alt 是否正常：
- 错误状态是否有兜底文案：
```

---

## ⑤ 准备回滚方案

```bash
# 获取当前提交信息
git log --oneline -3 2>/dev/null
echo "---"
# 检查是否有未提交的改动
git status --short 2>/dev/null
```

### 输出
```
- 代码能回退（对应提交/分支/补丁）：
- 数据能恢复（备份/dry-run）：
- 配置能撤销（API Key/环境变量/开关）：
```

---

## ⑥ 写发布备注

### 输出
```
- 本次上线解决的问题：
- 主要改动：
- 已执行的验证：
- 未覆盖的风险：
- 回滚方式：
- 上线后需要观察的指标：
```

---

## ⑦ 上线后观察

### 输出
```
- 观察点（错误日志/表单提交/转化/页面访问/用户反馈）：
- 观察期：
- 确认无异常的时间点：
```

---

## ⑧ 不自欺

### 输出
```
- 没有跑过的测试：_____（已明确标注）
- 不确定的风险：_____（已明确保留）
- 是否把不确定包装成确定：_____（已检查）
```

---

## 最终结论

```
✅ 可以上线 / ❌ 需要修复 / ⚠️ 有条件上线（风险说明）

决策依据：
1.
2.
3.
```