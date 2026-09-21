#!/bin/bash
# ============================================================
# 分桶模板：web-app（前后端全栈类项目）
# 来源：通用 Web 项目最佳实践（Vue/React + FastAPI/Node 均适用）
# 用法：由统一入口 bootstrap.sh 调用：bash web-app.sh <名称> <目录>
# ============================================================
set -euo pipefail

PROJECT="${1:?用法: web-app.sh <项目名> <目标目录>}"
TARGET="${2:?缺少目标目录}"

mkdir -p "$TARGET/plans" "$TARGET/docs" "$TARGET/.agents/skills"

# ── AGENTS.md（Web 全栈特化版）──
cat > "$TARGET/AGENTS.md" <<EOF
# $PROJECT — 项目事实源（Web 全栈）

## 这是什么
[一句话：产品是啥、给谁用、前端框架 + 后端框架 + 数据层]

## 命令
- 前端: npm run dev / npm run build / npm run test（写明包管理器）
- 后端: [启动命令 + 端口]
- 测试: [前端 + 后端各自的测试命令；标注已知坑]

## 目录
- frontend/: [框架与状态管理]
- backend/: [框架与数据库]
- [部署方式：本地 / Docker / 云]

## 禁区
- 不碰 .env / 密钥 / 生产数据库
- 破坏性操作必须二次确认
- API 变更必须同步前端类型定义与文档
- 数据库 DDL 变更必须先说迁移方案再动手
- [SEO/移动端适配是验收项时写明]

## 必须问人的事
- [资金/支付/登录/权限变更]
- [生产部署与数据迁移]
EOF

# ── plans/ ──
cat > "$TARGET/plans/current.md" <<'EOF'
# 当前计划

## 待办
- [ ]

## 进行中
- [ ]

## 系统理解任务
- [ ] 能画出核心页面流与 API 清单
- [ ] 搞清前后端契约（类型定义/接口文档的位置与同步方式）

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

## 页面流
[入口 → 核心页面 → 关键交互 → 出口]

## API 契约
[认证方式、错误码约定、分页约定]

## 已知雷区
- [环境差异（dev/prod 配置来源）]
- [浏览器兼容/移动端已知问题]

## 分层掌控清单
- 必须懂: 页面流、API 契约、数据模型
- 知道就行: 通用组件库
- 可以不懂: 构建/部署细节
EOF

# ── 项目级 skill 四件套 ──
mkdir -p "$TARGET/.agents/skills"/{project-context,arch-rules,test-gate,debug-playbook}
cat > "$TARGET/.agents/skills/project-context/SKILL.md" <<'EOF'
---
name: project-context
description: 项目上下文入口——技术栈、页面流、API 契约；触发词：项目上下文、这个项目是什么
---
# 项目上下文
[填：产品一句话、前后端栈、真值文件、启动命令、页面流速览]
EOF
cat > "$TARGET/.agents/skills/arch-rules/SKILL.md" <<'EOF'
---
name: arch-rules
description: 架构红线——API 契约同步、DDL 迁移先行、SEO/移动端验收；触发词：架构红线、API、迁移
---
# 架构红线
1. API 变更必须同步前端类型定义（契约先行，禁止后端先改前端后追）
2. 数据库 DDL 变更：先说迁移方案（备份/回滚/历史数据兼容）再动手
3. 页面验收三件套：桌面布局 / 移动端不遮挡换行 / 错误状态有兜底文案
4. SEO 三件套（如适用）：标题、描述、图片 alt
EOF
cat > "$TARGET/.agents/skills/test-gate/SKILL.md" <<'EOF'
---
name: test-gate
description: 测试闸门——前端/后端测试命令、改动类型→验证映射；触发词：测试、验证、跑测试
---
# 测试闸门
## 标准命令
- 前端: [test 命令]
- 后端: [test 命令]
## 改动类型 → 验证方式
| 改动 | 必须跑 |
|------|--------|
| 样式/布局 | 浏览器打开看（桌面 + 移动端视口） |
| 接口 | 接口测试（正常/错误输入/权限场景/返回结构） |
| 数据 | 迁移 + 备份 + 历史数据兼容 |
| 表单/按钮 | 提交后提示是否正确 |
## 汇报纪律
改样式的验证不是跑测试，是打开页面看；没打开过页面不说"已验证"。
EOF
cat > "$TARGET/.agents/skills/debug-playbook/SKILL.md" <<'EOF'
---
name: debug-playbook
description: 排障流程——启动失败/接口报错/样式异常；触发词：排障、报错、白屏、接口错
---
# 排障手册
[填：前端启动失败路径、后端启动失败路径、接口联调错位排查、样式问题先查视口/层级]
EOF

echo "✅ [web-app] $PROJECT 模板生成完成: $TARGET"
echo "   下一步: 填占位符（命令/目录/API 契约），审核 skill 四件套"