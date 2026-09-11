# Design: 2026-09-10-add-short-scan-analyze

## Context

短篇流水线（v4.25-v4.26）只有「写」。本 change 补扫榜与拆文两个独立工具——归档 change `2026-09-10-add-short-story-pipeline` 的 proposal「后续变更」明确记录的两项（跨文体检查工具移植不在本 change）。

约束（沿主线 spec 与仓库约定）：
- 独立工具部署到全部 7 平台，MUST NOT 进 short-agent 调度链、不占 phase（主线 spec `A5` 同类约定的扩展）
- 工具只用 Python 标准库 + pyyaml；Node 采集脚本不移植（design D8 既有裁定）
- 知识引用一律 `.claude/knowledge/...` 基座路径；版权标注照 D9
- 拆文方法论来自获赠包 story-short-analyze（SKILL.md 3.0 + material-decomposition 34K + output-templates 24K 等），按「压缩内联」策略进 SOP

## Goals / Non-Goals

**Goals:**
- 两个工具在 7 平台可被作者独立调用（不进调度链）
- 拆文产出与写作阶段消费打通：`_meta.json` 的题材识别 → 自动加载对应 short-genres 风格包；产出目录 `analysis/{书名}/` 项目级共享（跨篇复用，对齐 bootstrap 主 spec `A8.2` 的共享资源定位）
- 崩溃安全与三道闸门按既有 spec 设计落地

**Non-Goals:**
- 不做实时采集器（CDP / 爬虫）——实时采集依赖运行环境能力（如具备浏览器的 agent 用其自带工具），不可用走三级降级
- 不做拆文产出在写作阶段的**自动召回**接线（构思 agent 主动推荐对标）——那是 pipeline spec 的 `D2.5` 对标发现，等两工具合并后再接
- 不移植包内 JS 脚本（cdp-utils / dz-browse-scraper / heiyan-booklist-scraper）

## Decisions

### D1: 实现为自包含 SOP，方法论内联不外挂知识文件

包内拆文方法论 6 万+字（material-decomposition 34K / output-templates 24K / output-contract 9K）。全部外挂会新增知识目录（init/check/sync 三处接线）且大部分是模板细节。裁定：**把管道协议、五阶段模板、验收闸门压缩内联进 `skills/short-analyze.md`**（约 300 行），市场知识内联进 `skills/short-scan.md` 附录。工具是自包含单元，部署即完整。

- Alternative（新增 `knowledge/short/scan/` + `analyze/` 目录）被拒：三处接线成本换不来复用收益——这两个文件只有一个消费者（工具自身）。

### D2: 独立工具的部署形态——全平台统一「平台 skills 目录 + SKILL.md」

主线 v4.26 的短篇部署三类形态里，codex/grok 本就有独立工具 skills 目录；claude/opencode 有 skills_dir 约定但从未用；inline 三平台 skills 即一切。裁定：新增 `deploy_standalone_skills(project, skill_home, platform, names)` 通用助手，把 `SHORT_STANDALONE_SKILLS = ("short-scan", "short-analyze")` 以 `_convert_standalone_skill` + rewrite_refs 部署为 `<skills_dir>/<name>/SKILL.md`，7 平台统一走它；`deploy_inline_skills(short)` 内也调用它（inline 平台一次生成 6+2）。

- Alternative（只支持 inline + codex/grok，claude 靠仓库 skills/）被拒：claude 项目里没有仓库 skills/，工具不可达。

### D3: 扫榜的三级数据来源——采集能力归运行环境

「实时采集」在 SOP 中定义为：若当前 agent 环境具备浏览器/抓取工具则按附录的字段清单采集；否则跳到下一级。仓库不实现采集器（对齐 v4.23 detect-loop 的「平台无关」先例）。降级标注是硬要求：内置知识产物 MUST 带未校验声明，防止「像真的一样」。

### D4: 拆文的题材标尺用 short-genres 风格包，不新增对照文件

包内 genre-catalog.md（21K）与我们的 short-genres 高度重叠。裁定：题材识别后直接加载 `.claude/knowledge/short-genres/{题材}.md` 的「叙述腔调 / 钩子母题 / 节奏骨架」节作为「该篇是否合标」的对照标尺；识别不到记通用。产出 `_meta.json.genre` 与注册表 slug 对齐，写作阶段据此自动加载同包。

### D5: 拆文报告自身过短篇口径

包内用 banned-words+anti-ai-writing 双文件扫报告；我们只有一份 `.claude/knowledge/short-anti-ai.md`。裁定：闸门①按它扫（分析师措辞、跳过源文引用），语义等价。报告落 `.agent/task/` 之外——放 `analysis/{书名}/`（与产出同处，作者可直接读）。

### D6: 独立工具不进调度链，入口在 SKILL.md 与项目指令

作者触发方式：对话说「扫个榜」「拆这篇」。SKILL.md 短篇分支补一句可选工具说明；`templates/short` 项目级指令不加（避免三份文件同步负担，SKILL.md 一处声明即可被入口 skill 感知）。

## Risks / Trade-offs

- [拆文 SOP 内联后过长，模型执行到后期阶段遵守度下降] → 五阶段每阶段独立小步写盘 + order 无关（作者对话直接驱动），单阶段指令自包含；真机验证列为本 PR 后续事项
- [扫榜内置知识过期，报告误导] → 时效三件套（样本日期/可信度/复扫时间）为 MUST，降级标注为 MUST
- [拆文产出目录 `analysis/` 在 bootstrap spec 主线是 `A2.1` 骨架目录集之一吗？] → 是（v4.25 起 `templates/short` 已含 analysis/ 占位目录），本 change 恰好填实它，无骨架改动
- [独立 skill 部署新增 claude 的 `.claude/skills/` 目录，长篇项目没有此目录] → 仅 short 流程调用部署助手，长篇路径不变（测试断言兜住）

## Migration Plan

1. platforms.py：`SHORT_STANDALONE_SKILLS` + `deploy_standalone_skills` 助手；`deploy_inline_skills(short)` 内挂独立工具。
2. init.py：short 流程 Step 3.6 调用部署助手（全平台）。
3. sync-project.py：短篇 sync_skills 分支补独立工具再部署；find_changes 短篇分支补两文件比对。
4. SOP 内容：short-scan / short-analyze 自包含实现。
5. SKILL.md：短篇分支可选工具说明。
6. test_platforms：独立工具 E2E（7 平台 + inline 数量 6→8 + codex/grok skills 目录）。
7. 回归全绿后推 PR；评审；**不合入**（作者指定——合并时机待短篇主链路真机实测后决策）。

## Open Questions

（无。）
