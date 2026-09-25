---
name: dependency-verify
description: 依赖变更验证纪律——installed ≠ works：pip/npm install 成功≠可用，import 成功≠原生库能加载。装完必跑真实初始化。触发词：装依赖、pip install、npm install、装好了吗、环境验证、import 成功但报错
argument-hint: ["验证新装依赖", "装完依赖怎么确认", "环境坏了排查"]
allowed-tools: bash, read_file, grep, glob
---

# Dependency Verify — installed ≠ works

## 铁律
`pip install` 成功、`import` 成功，都**不等于**可用。环境探测必须做一次**真实初始化**——否则环境问题会伪装成代码缺陷，浪费排查时间（实证：weasyprint import 成功但渲染抛 libgobject 缺失；ladybug import 成功但 Database() 抛原生库缺失）。

## 验证四步（宣称"环境可用"前必跑）
1. **import**：`python -c "import X"`——只证明元数据在
2. **真实初始化**：构造核心对象 / 跑最小渲染 / 最小查询——证明底层可用
   - 渲染库 → 渲染一个最小文档
   - 数据库客户端 → 打开连接跑 `SELECT 1`
   - 编译工具链 → `printf 'int main(){return 0;}' > t.cpp && g++ t.cpp`（本机 conda g++ 前端静默失败即此法查出）
3. **只读检查落盘**：版本号、可执行文件路径写入验证记录——后续会话可复核
4. **才可宣称"环境可用"**——没跑过 ② 就说"装好了" = 把不确定包装成确定

## 前置检查（装之前）
- **磁盘空间**：C 盘常年紧张，装大包前 `df -h`；必要时 `export TEMP=<D盘路径>` `TMPDIR` 同值（三条独立 export，不能 `A=B=C` 连写）
- **pip 报 `from versions: none`** → 加 `--isolated --no-cache-dir`（关键在 `--isolated`）
- **网络**：代理端口会漂移（7890/7891/7897），Python urllib 还会读注册表系统代理——判定网络挂之前先绕开系统代理复测

## 脚本化验证（CI/多机）
学 OpenSeed 的 `## Verification` 段：为每个环境写只读验证脚本（`verify_env.sh`），结构性检查 + 纯退出码——"anyone can fork the checks"，验证与安装同样重要。

## 汇报口径
- "已安装" = ①通过
- "已安装且可用" = ①②③全部通过，附验证命令与输出位置
- 只跑过 ① 就汇报"能用" = 违反诚实红线
