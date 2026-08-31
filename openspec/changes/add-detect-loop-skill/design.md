## Context

- 前置：`add-zhuque-source-defense`（知识+工具）与 `wire-source-constraints-into-pipeline`（管线挂接+骨架）已合入；`sandbox/detect-battles.md`、`sandbox/prose-regressions.txt`、`sandbox/locked-lines.txt` 已是项目骨架文件。
- 来源包的闭环经验（逐片结果→修最高窗→锁版→沉淀）已验证有效，但其工程载体（CDP 脚本、验证码求解、指纹农场、接口逆向文档）不可入库。
- 调度契约在 `skills/novel-dispatch.md`（order 类型清单 + 断点续跑语义），agent 细则在 `agents/novel-agent.md` 的 THINK 树。

## Goals / Non-Goals

**Goals:**

- 把闭环的"流程知识"入库、"工程载体"留本地：skill 教方法，不携带工具。
- 与既有调度/降级/锁版语义无缝衔接。

**Non-Goals:**

- 不实现任何检测平台对接代码。
- 不把 detect-loop 设为默认管线环节。
- 不做自动修文到满分（修文动作仍由 anti-ai 语义执行，本 skill 只给修复纪律）。

## Decisions

1. **order 类型最小扩展。**
   `detect-loop-order.md` 一个新 order 类型，调度表加一行"作者触发"；`agents/novel-agent.md` THINK 树同步一个分支。备选"并入 anti-ai phase 作 Phase 5"被否：会把可选环节变成默认路径，且 anti-ai 的退出码/报告契约会被稀释。
2. **平台无关的适配器接口。**
   skill 只约定三件事：送检入口（本地命令或作者手动网页送检）、结果文件（逐片：起止位置/分数/文本）、判定阈值参数。来源包的 CDP/验证码/额度经验写进本地文档（`~/tools/zhuque/`，不入库），仓库 skill 引用"若本地有对接工具按结果文件格式提供"。
3. **修复纪律独立成节，复用 anti-ai 的执行语义。**
   "只修最高分片段/边界稳定/等长微调/止损"是修文纪律，写进 skill 供任何执行者（anti-ai agent 或作者手改后的 agent 协助）遵循；具体 Gate 改法仍按 anti-ai.md。
4. **锁版语义复用 archives 的快照惯例。**
   锁版快照落 `archives/`（或作者指定位置），哈希记录进战役记录文件；不新增锁版基础设施。
5. **合规声明写进 skill 正文。**
   用途限定（作者自稿自愿校准）、资产隔离（无自动化脚本入仓）作为验收项，防止后续贡献者把本地工具误提交。

## Risks / Trade-offs

- 平台无关化会让 skill 对"具体怎么送检"语焉不详，首次使用者可能觉得抽象 → skill 内给一个"本地对接工具的最小结果文件示例"（纯格式示例，非任何真实平台协议）。
- "连续两轮 <0.05 止损"等数值纪律来自单一实测项目，其他检测器未必适用 → 阈值参数化并在 skill 标注来源与适用范围。
- 作者触发语义依赖调度层准确识别自然语言 → 与既有"作者确认关卡"同机制，风险可控。
