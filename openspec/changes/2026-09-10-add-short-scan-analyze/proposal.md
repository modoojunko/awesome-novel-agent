# Proposal: 2026-09-10-add-short-scan-analyze

## Why

短篇流水线（v4.25/v4.26）只覆盖「写」——作者不知道**现在什么情绪在火**（选题凭感觉），也没有**对标爆款的拆解管道**（模仿凭印象）。获赠短篇包原带扫榜（story-short-scan）与拆文（story-short-analyze）两个独立工具，v4.25 收窄时移出。本 change 补上这两块：选题有市场数据、对标有结构资产，短篇链路闭环为「选题 → 对标 → 写作」。

## What Changes

### 主流程 S：扫榜（独立工具，不进调度链）

- 新增 `skills/short-scan.md`：确认平台与方向 → 三级数据来源（运行环境实时采集 / 作者提供截图文字链接 / 内置知识，逐级降级且降级必须标注「未实时校验」）→ 七维分析（情绪类型分布 / 题材热点 / 篇幅分布 / 开头模式 / 结尾类型 / 标题模式 / 人设模型）→ 报告（样本日期 / 趋势可信度 / 下次复扫时间 / 风口预警三级）→ 选题匹配（复杂度分级 + 传播风险兜底：无反转方向必须以强共鸣/强话题/强余韵补足）
- 内置市场知识（跨平台调性对照、各平台简介公式、题材爆款公式）内联进 SOP 附录，不依赖 Node 采集脚本

### 主流程 A：拆文（独立工具，不进调度链）

- 新增 `skills/short-analyze.md`：五阶段串行管道——①结构+情节节点（≥4 段含开端/发展/高潮/结局）②情感曲线（≥5 节点）+爆点六维 ③反转机制（铺垫 ≥2 条）+写作手法（≥5 项）④人物功能+开头结尾 ⑤综合评估+结构计数；每阶段有完成标志
- **崩溃安全写盘**：阶段前置标记 → 完成后非空+最小长度校验 → 通过才清标记并记入已完成；续跑时未完成阶段整段重跑
- **三道验收闸门**：报告自身 AI 腔自检（按 `.claude/knowledge/short-anti-ai.md`，只扫分析师措辞、跳过源文引用）/ 结构计数数值校验 / 强阻断项扫描
- 产出落盘 `analysis/{书名}/`：原文备份 + 拆解报告 + 情节节点 + 写作手法 + `_meta.json`（题材识别 + 结构计数，供写作阶段自动加载对应题材风格包）
- 题材标尺：识别题材后按 `.claude/knowledge/short-genres/{题材}.md` 的对照节做「该篇是否合标」比对

### 部署与接线

- 两个工具以**独立 skill** 部署到全部 7 平台（claude/opencode 的 `.平台/skills/`、codex/grok 的独立工具 skills 目录、reasonix/zcode/dsh 的内联 skills 目录），MUST NOT 进 short-agent 调度链、不占 phase
- 入口 SKILL.md 短篇分支补充可选工具说明

## Capabilities

### New Capabilities

- `short-story-scan`: 短篇扫榜——平台方向确认、三级数据来源与降级标注、单平台失败不中断、七维分析、含时效与风口预警的报告、选题复杂度分级与传播风险兜底
- `short-story-analyze`: 短篇拆文——字数路由、题材标尺与续跑检查、原文备份先行、五阶段串行管道与逐阶段完成标志、崩溃安全写盘、固定文件树产出、三道验收闸门

### Modified Capabilities

（无——两个工具均为新增独立工具，不改动既有 spec 的 requirement。）

## Impact

- **新增**：`skills/short-scan.md`、`skills/short-analyze.md`；`tools/platforms.py`（短篇独立工具部署清单 + 全平台独立 skill 部署助手）；`tools/init.py`（短篇独立工具部署步）；`tools/sync-project.py`（短篇独立工具同步）；`SKILL.md`（可选工具说明）；`tools/test_platforms.py`（独立工具 E2E 断言）
- **openspec**：change 归档后新增两个主线 spec
- **无**新依赖（仍为 Python 标准库 + pyyaml；扫榜实时采集依赖运行环境能力，不可用走降级）
- **PR 状态**：按作者要求**评审后不合入**——实现已可用，合并时机待真机实测短篇主链路后统一决策
