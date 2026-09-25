---
name: hook-safety-checker
description: hook 安全检查器——写/接/验收任何 hook（pre-commit、PostToolUse、PreToolUse、CI gate）前过一遍：设计三原则、接线检查单、双向验收用例模板。防哑巴 hook。触发词：写个 hook、加个钩子、hook 失效、门禁不拦、pre-commit、接线
argument-hint: ["帮我写个 hook", "检查这个 hook 安全吗", "hook 不生效排查"]
allowed-tools: read_file, grep, glob, write_file, edit_file, bash
---

# hook-safety-checker — 写/接/验收 hook 的强制检查

## 设计三原则（写 hook 前必答，答不上来就别写）
1. **fail-open**：hook 自身异常时返回 0 放行主流程——门禁挂了不能把所有人都堵死；真正的防线在 git 层/CI 层兜底。
2. **错误必须浮出**：hook 内严禁 `2>/dev/null || true` 包住检查逻辑——那会把拦截信号吞掉变成**哑巴 hook**（比没有 hook 更危险：你以为有防护，实际是裸奔）。stderr 是反馈通道，不是日志垃圾桶。
3. **状态写失败不阻主流程**：快照/状态文件的写入失败只记日志，不返回非零——hook 是检查者，不是数据 Owner。

## 接线检查单（接入前逐项确认）
- [ ] **先查 `git config core.hooksPath`**——hooksPath 存在时 `.git/hooks/` 是死的（西湖论剑教训：hooksPath=ctf_agent/git_hooks）
- [ ] settings.json / hook 配置**只放指针**（`python "<绝对路径>/hook.py"`），逻辑在独立脚本——可版本管理、可独立测试
- [ ] stdin 解析失败 → 返回 0 放行（fail-open），不 crash 工具链
- [ ] Windows 下测试路径用**正斜杠原生路径**——MSYS 的 `/tmp` Windows Python 读不到（假阴性会误导验收）
- [ ] 每次改动配置前备份旧文件（`settings.json.bak-<tag>`），回滚 = copy 回去
- [ ] 接线后**立刻双向实测**（见下），没有实测记录的 hook 视为未安装

## 双向验收用例模板（最少 3 个）
```
① 应放行（正常操作）      → 退出码 0，无输出/通过提示
② 应拦截（违规操作）      → 退出码 1，stderr 给出原因 + 修复建议
③ 应放行（边界情况）      → 退出码 0（如非目标文件、无暂存文件、-F 替代方式）
```
用例 ② 的输出必须包含**可执行的修复建议**（"改用 git commit -F"而非"格式错误"）——拦截不带出口 = 逼用户绕过门禁。

## 反模式清单（出现即返工）
- 哑巴 hook：错误被吞，永远退出 0，看起来"已安装"
- 误报轰炸：正常操作频繁被拦 → 用户学会 `--no-verify` 绕过 → 门禁名存实亡
- 无备份直改 hook 配置
- 状态文件写失败导致主流程中断（hook 抢了数据 Owner 的活）
- 只装不测（没跑过 ② 用例的 hook 不算生效）

## "Skills = model decides, hooks = system enforces"
必须发生的行为（密钥扫描、编译检查、覆盖检测）做成 hook；通常发生的行为（流程指引）做成 skill。skill 触发是概率性的，hook 是确定性——按"不发生的后果严重度"选层级。
