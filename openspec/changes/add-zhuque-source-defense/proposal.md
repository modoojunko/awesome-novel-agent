## Why

本项目 anti-ai 管线是开环：规则去味后直接交付，缺两层能力——①结构层热源知识（词句干净的文本照样被外部检测器判 AI，热源在结构：问答链密度、位置热值、微闭环等）；②章节交付级确定性检查（夹层引语、嵌套引号、字数表达错账等模型肉眼会漏的硬伤）。外部实测项目（连续 6 章 100% 人工特征攻防沉淀）已验证这两层有效，可通用化后从源头降低 AI 检出。

## What Changes

- 新增 `knowledge/anti-ai/structural-heat.md`：七条实测定律（问答链密度、位置热值、切片边界稳定、补字铁律、内容类型切换、语气词拉长法、整章重写边界）+ 13 种高风险结构，全部去书名化通用改写，保留实测分数作证据。
- 从 human-writing 系规则包（MIT）增量合并仓库缺失条目进 `knowledge/anti-ai/common-rules.md` / `anti-ai-writing.md`，不做文件级覆盖。
- 新增 `tools/check-chapter.py`：章节交付硬伤检查（通用正则项 + 平台口径字数统计），书专属回归模式库/白名单外置到项目文件。
- 新增 `tools/test_check_chapter.py` 测试。
- init/sync 将新工具部署到 `<平台根>/tools/`（与 check-prose.py 同机制）。

## Capabilities

### New Capabilities

- `structural-heat`: 结构热源知识——anti-ai/writer 写前可召回的结构级 AI 热源定律与高风险结构清单。
- `chapter-check`: 章节交付确定性检查工具——正则硬伤扫描、逐字对账、项目级回归库/白名单外置、部署与退出码契约。

### Modified Capabilities

（无——本 change 不改动既有 spec 级行为；common-rules.md 的合并是知识内容增量，不是行为契约变更。）

## Impact

- 新增：`knowledge/anti-ai/structural-heat.md`、`tools/check-chapter.py`、`tools/test_check_chapter.py`。
- 修改：`knowledge/anti-ai/common-rules.md`、`knowledge/anti-ai/anti-ai-writing.md`（增量条目）、`tools/init.py`、`tools/sync-project.py`（部署清单）、`tools/test_platforms.py`（E2E 断言）。
- 依赖：无新增（Python 仅标准库）；CI 无需改动（现有 static.yml 自动覆盖新测试）。
- 不改动：`tools/check-prose.py` 既有阈值与行为；`skills/`（管线挂接属后续 change）。
