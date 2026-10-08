---
name: wechat-distill
description: 微信公众号文章蒸馏流程——处理 sources/wechat/pending/ 里的已抓取推文：逐篇提炼可执行规则、R3 门槛裁决、广告检测、归档 done/。触发词：蒸馏微信、pending、公众号文章、微信文章蒸馏、处理待蒸馏
argument-hint: ["蒸馏 pending 里的微信文章", "处理微信推文", "微信蒸馏状态"]
allowed-tools: bash, read_file, grep, glob, write_file, edit_file
---

# wechat-distill — 微信推文蒸馏流程

## 管道位置
抓取（tools/fetch_wechat.py，确定性脚本）→ **本 skill（蒸馏）** → 记忆体系（notes/memory/skill 按 R3 门槛分）。
本 skill 只负责中间一跳；抓取失败/验证码页不归本 skill 管（见抓取脚本自述）。

## 执行步骤

### 1. 盘点 pending
```bash
python tools/fetch_wechat.py --status
```
逐篇读 `sources/wechat/pending/*.txt`（meta 头含 url/title/account/chars）。

### 2. 广告/软文检测（[实测] 先于蒸馏）
正文若以产品推销、课程售卖、活动报名为主（特征：价格/二维码口播/限时/私域引导占正文主体）→ 标记 `status: AD` 直接移 done/，不蒸馏。诚实口径：宁漏一篇软文，不往记忆里注水。

### 3. 逐篇蒸馏（[R1·设计] 溯源格式）
每篇产出蒸馏块，追加到 `~/.atomcode/notes/wechat-distilled.md`（不存在则创建）：
- `## <标题>（<公众号名>，<日期>）` + 原文 URL 一行（[源:URL]，R1 纪律——没有 URL 的蒸馏块不许入库）
- 痛点 1-3 条：作者指出的具体问题（不复述营销叙事）
- 解法/规则 1-5 条：**只收可执行的**（有动作、有判据），拒绝"要重视/很关键"类口号
- 与现有体系的接口：命中既有规则（重复/矛盾/补强）必须显式标注——重复→增量补充；矛盾→以可验证方为准并记录
- 单篇蒸馏 ≤2000 字；未提取的部分（案例细节/背景故事）一行说明"未提取"（[R5·实测] 覆盖率诚实）

### 4. R3 门槛裁决（[R3·实测] 每条规则必答）
- 首次出现 → 留在 notes（本步产出即归宿）
- 第 2 个独立来源复现 → 升 memory（action=remember，注明"第二次复现"）
- ≥2 独立来源且值得独立流程 → 立项 skill（挂账带触发条件）
- 禁止跳级：单篇文章的惊艳观点 ≠ 铁律。

### 5. 归档
蒸馏完成后：`pending/<file>.txt` → `done/`（bash mv）；notes 里该篇标题后加 ✅。
失败篇（captcha/error）留在 pending，下次重跑 `fetch_wechat.py` 重抓。

## 质量门（G1-G4，[实测]）
| 门 | 检查 |
|----|------|
| G1 | 每个蒸馏块有 [源:URL] |
| G2 | 每条规则过 R3 裁决（notes/memory/skill 三选一，不悬空） |
| G3 | AD 检测先于蒸馏执行 |
| G4 | done/ 与 notes 索引一致（无蒸了没记、记了没移） |
