## Why

源头约束（前两个 change）能把外部 AI 检测的修复轮次压到最少，但无法保证归零：切片边界由全文分布决定、检测器持续升级、同文本复测有波动。需要一个作者手动触发的可选校准环节——送外部检测、按逐片结果定向修、达标锁版，并把每轮经验沉淀进项目的战役记录与回归库。

## What Changes

- 新增 `skills/detect-loop.md`：平台无关的外部检测校准闭环 SOP（送外部 AI 检测器→读逐片结果→只修最高分片段→边界稳定/等长微调→达标锁版→沉淀战役记录与回归串）。
- `skills/novel-dispatch.md` 调度表增加作者触发可选 phase（作者说"送检/过一遍检测"才启动，不进默认管线）。
- 工程对接以适配器形式描述：仓库内不含任何检测平台自动化脚本、逆向协议与密钥；本地工具的对接方式见 skill 内说明。
- 明确合规边界：SOP 只面向作者对自己稿件的自愿校准，不包装检测器对抗、不绕平台风控。

## Capabilities

### New Capabilities

- `detect-loop`: 作者触发的外部检测校准闭环——送检、逐片修复、锁版与经验沉淀的流程契约。

### Modified Capabilities

（无既有 spec。）

## Impact

- 新增：`skills/detect-loop.md`。
- 修改：`skills/novel-dispatch.md`（可选 phase 行 + 断点续跑语义备注）。
- 依赖：依赖 `wire-source-constraints-into-pipeline` 先合入（复用 `sandbox/detect-battles.md` 与 `sandbox/prose-regressions.txt`、check-chapter 复跑）。
- 明确不入库：检测平台自动化脚本、接口逆向文档、密钥模板、浏览器指纹方案。
