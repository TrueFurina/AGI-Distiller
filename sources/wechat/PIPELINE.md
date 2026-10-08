# 微信公众号蒸馏管道（WeChat Distill Pipeline）

> 2026-10-08 落地 ｜ 自动发现 → 自动抓取 → 预蒸馏草稿 → 人工复核 → R3 升格

## 架构

```
[常驻] we-mp-rss 桥接服务（E:\Program\we-mp-rss，:8001，微信扫码授权）
        后台定时同步订阅号文章 → /rss 全量源
   ↓
[常驻] tools/distill_loop.py（每日 09:30，startup 自启）
   ├─ tools/wechat_poller.py    RSS → 新链接去重 → fetch_wechat → sources/wechat/pending/
   └─ tools/wechat_predistill.py pending → AD 检测 → Spark 预蒸馏 → notes/wechat-drafts/*.draft.md（DRAFT）
   ↓
[人工] 会话里"复核微信草稿" → wechat-distill 流程按 R3 门槛升格 → pending/done 归档
```

## 成本实测

| 项 | 数值 |
|----|------|
| 预蒸馏单篇消耗 | ≤4000 字输入 + ≤1200 tokens 输出 ≈ 3K tokens/篇 |
| 每日上限 | 3 篇/日（--max 可调）≈ 9K tokens/日 ≈ 0.3 元/日（lite 档） |
| 轮询消耗 | 0（RSS 本地读取） |
| 模型 | lite（默认；4.0Ultra 2026-10-08 实测 500，恢复后可切回提升草稿质量） |

## 已知局限（诚实清单）

1. **预蒸馏质量依赖模型档位**：lite 草稿结构合规但规则偏泛——所以草稿带 `DRAFT` 状态，必须人工复核才入库，禁自动升格。
2. **桥接服务依赖微信读书登录态**：过期需重新扫码（打开 http://127.0.0.1:8001 授权页）；接口非官方，可能随微信更新失效（we-mp-rss 社区跟进）。
3. **发现范围 = 已订阅号**：不做"全网宝藏文章"发现（那需要推荐源，属于 P2 长线）。订阅哪些号由用户在服务里添加。
4. **单篇抓取成功率 ~2/3**：微信反爬验证码；失败篇留 pending 可重试。
5. **草稿幻觉风险**：LLM 预蒸馏可能改写/脑补原文——复核时对照 `[源:URL]` 原文抽查（done/ 里留有全文）。

## 运维命令

```bash
# 状态总览
python tools/fetch_wechat.py --status
tail -5 sources/wechat/distill_loop.log

# 手动触发一轮
python tools/distill_loop.py --once

# 重启桥接服务（进程死亡时）
explorer.exe "E:\Program\we-mp-rss\start_server.bat"

# 重启蒸馏循环
explorer.exe "E:\Program\AGI-Distiller\start_distill_loop.bat"
```
