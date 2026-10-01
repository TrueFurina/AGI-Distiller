<!--
  本仓库的唯一卖点是「可溯源」。所以这份模板的第一屏不是代码风格，
  而是三问：你解决什么痛点、来自哪里、不写会怎样。
  答不上来的 PR 会被要求补，不是刁难 —— 是防止单次踩坑被写成铁律。
-->

## 一、溯源三问（必答）

| 问题 | 回答 |
|---|---|
| **解决什么痛点？** | <!-- 一句话：不装这个 skill 会出什么事 --> |
| **来自哪里？** | <!-- 文章链接 + `sources/` 笔记文件名，或「本机实战：哪次、什么现象」 --> |
| **不写会怎样？** | <!-- 不装的话 Agent 会犯什么错 --> |

> 三者缺一，说明这个 skill 还没想清楚。先去 `DISTILLER.md` 走一遍蒸馏流程。

## 二、改动类型

- [ ] 📝 **新 skill**（走完下方第三节 6 条）
- [ ] 🔧 **改进现有 skill**（说明改了哪条规则、依据是什么）
- [ ] 🐛 **修复机验 / CI**
- [ ] 📚 **文档**（README / NEXT / ROADMAP / DISTILLER）

## 三、新 skill 投稿：6 条硬要求

> 来源：`CONTRIBUTING.md` 第三节。不满足会被 CI 的 `skill-tags` / `doc-consistency` job 拦下。

- [ ] **1. frontmatter 四字段齐全**：`name` / `description` / `argument-hint` / `allowed-tools`
- [ ] **2. `description` 带触发词**：写进用户会说的自然语言（如「调试、debug、修Bug」），否则 skill 不会被调用
- [ ] **3. 规则句带溯源标记**：含「必须/禁止/不许/绝不/一定要/严禁」的一级 bullet，必须标 `[R<N>]` / `[实测]` / `[设计]` / `[复现:2+]` 之一
- [ ] **4. 命名 `<动词>-<名词>`**：全小写加连字符，如 `debug-flow`、`cli-safety`
- [ ] **5. 中英文描述都有**：正文可中文，但 `description` 要让不读中文的 Agent 也能判断该不该触发
- [ ] **6. 不是凑数**：宁可少一个 skill，也不要一个没有出处的 skill

## 四、本地自检（四条必须全绿）

```bash
python scripts/check_doc_consistency.py        # 无第三方依赖
python tools/check_skill_tags.py               # 无第三方依赖
python tools/sync_counts.py                    # 计数同步：数字必须等于工作区事实（无第三方依赖）
python golden/graders.py --self-test           # 需要 PyYAML：pip install pyyaml
```

四条都退出 `0` 才提 PR。前三条是纯标准库；第四条**要 PyYAML**——本机装了不等于 CI 有，见 `CONTRIBUTING.md` 第四节。

## 五、文档是否需要同步

改动 skill 数量 / 规则节数 / 数字口径时，**不要手敲数字**：

```bash
python tools/sync_counts.py --fix   # 从 skills/ 与 sources/ 的实际内容改回去
python tools/sync_counts.py         # 复核
```

它只改**计数**，不碰**历史/实测记录**（如 README 里那次 `Skills (19)` 的安装实测值）——那些追改等于伪造验证。
skill 表的**一句话摘要**工具不代写，只把待办列出来。若仍有漂移，逐项确认：

- [ ] `README.md` + `README.zh.md`（**两份都要改**，机验 D1/D2 盯着中英一致）
- [ ] `HEARTBEAT.md`
- [ ] `NEXT.md`
- [ ] 不需要同步

## 六、本机 pre-commit 门禁

提交时本地还有 4 道门禁：密钥扫描 / 诚实口径 / 口径数字 / 结构守卫。
如果其中一道拦下你，**先看它报的是不是真问题**——放宽白名单前请说明理由。
