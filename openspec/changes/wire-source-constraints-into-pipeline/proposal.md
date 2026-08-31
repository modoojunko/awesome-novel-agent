## Why

Change `add-zhuque-source-defense` 落地了结构热源知识与章节检查工具，但管线不引用它们就没有效果：writer 起稿仍无结构约束，anti-ai 仍从句子级开始扫，项目也没有承载"战役记录→规则"进化机制的文件骨架。源头降检的主菜是生成期约束，本 change 把知识接进管线并模板化记忆机制。

## What Changes

- `skills/writing-execution.md`：写前增加"每场五行反闭环卡"（人物要办什么/阻力来自谁/演到哪步停/什么不解释/什么留到下场），答不出第 3-5 项不开写。
- `skills/prompt-crafting.md`：写前约束注入结构禁令（问答链拍数上限、章首冷开场、章尾极简不总结、微闭环/过桥链/证明链禁令），引用 `structural-heat.md`。
- `skills/anti-ai.md`：Phase 1 扫描前增加结构热源扫描步骤（读 structural-heat.md，命中先改结构再清句子），并在 Phase 2 机器初筛中并列调用 `check-chapter.py`。
- `templates/sandbox/` 新增三个骨架：检测战役记录（`detect-battles.md`）、回归模式库（`prose-regressions.txt`）、锁定台词白名单（`locked-lines.txt`）。
- `tools/init.py` 初始化项目时生成上述骨架文件；`tools/sync-project.py`/`test_platforms.py` 覆盖。

## Capabilities

### New Capabilities

- `source-constraint-pipeline`: 源头结构约束管线——writer 写前反闭环卡、prompt 结构禁令注入、anti-ai 结构热源扫描的挂接契约。

### Modified Capabilities

（无既有 spec——本仓库尚无已归档 specs，全部为本批新建。）

## Impact

- 修改：`skills/writing-execution.md`、`skills/prompt-crafting.md`、`skills/anti-ai.md`、`tools/init.py`、`tools/test_platforms.py`。
- 新增：`templates/sandbox/detect-battles.md`、`templates/sandbox/prose-regressions.txt`、`templates/sandbox/locked-lines.txt`。
- 依赖：依赖 change `add-zhuque-source-defense` 先合入（引用其知识文件与工具）。
- 话术约束：skills 中作者可见文本不得出现内部名词（切片/热窗/回归库等），须过 `knowledge/format-specs/author-communication.md` 对照表。
