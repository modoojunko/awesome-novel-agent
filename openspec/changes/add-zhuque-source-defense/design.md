## Context

- `tools/check-prose.py` 已存在：移植自 human-writing（MIT），管 AI 味硬禁令与统计形态，只报告不改文，anti-ai Phase 2/4 调用。
- 来源包的 `check_chapter.py` 是单书硬编码：29 条家族正则里混着书专属回归串（人物名、情节句）、台账路径（`参考资料/连续性数字台账.md`）、书名关键词表；本项目是多书多题材的通用工具库，不能直接搬运。
- 知识侧：包内 `anti-ai-writing.md` 是 human-writing 的旧分叉（36KB，带"同名副本×5"同步注记），仓库版是重构版（13KB，阈值下沉到 common-rules.md），两版不能文件级覆盖。

## Goals / Non-Goals

**Goals:**

- 结构热源知识入库且通用化（任何题材/书籍可用）。
- 章节交付检查工具可部署到七平台，书专属资产外置为项目文件。
- 与 check-prose.py 职责清晰互不重复。

**Non-Goals:**

- 不改动 check-prose.py 既有阈值。
- 不在本 change 挂接 skills 管线（writing/prompt/anti-ai 的挂接属 `wire-source-constraints-into-pipeline`）。
- 不入库任何书专属回归串、人物名、台账。
- 不引入朱雀自动化脚本与协议文档（属本地工具，永不入 git）。

## Decisions

1. **新工具 `check-chapter.py`，不并入 check-prose.py。**
   理由：职责不同（AI 味统计形态 vs 交付硬伤逐行定位），合并会让单脚本膨胀且退出码语义打架；anti-ai 流程里两个脚本可先后跑。备选"并入"被否：check-prose 移植自上游，保持与上游结构对应便于未来同步。
2. **书专属资产外置到项目 `sandbox/`。**
   回归模式库 `sandbox/prose-regressions.txt`、白名单 `sandbox/locked-lines.txt` 一行一条 UTF-8；工具只实现读取逻辑，文件缺失跳过。骨架文件由 `wire-source-constraints-into-pipeline`（templates 层）生成，本 change 先保证"无文件也能跑"。
3. **检查项只收通用正则，分级硬性/警告，标点口径对齐 common-rules。**
   硬性=客观错误（夹层标签式、嵌套引号、半角引号、字数对账不符、回归串命中）；警告=需语义裁定（破折号/省略号按 common-rules 用法判定、广义夹层、问答并段、副词密度、尾随标签）。来源包的"零破折/零省略"是单书铁律，与仓库既有口径（允许用法性保留、段内 ≥3 处才提示）冲突，不作默认行为；个别书需要时走书级白名单/开关。来源包中依赖书名词表的检查（㊵短词双引号、台账常量扫描）不收；尾随标签检查依赖人物名表，通用化为"代词+说/问"窄集并设为警告级。
4. **平台口径字数只统计不设阈值。**
   来源包 ≥3010 是单书平台要求；本项目多平台多书，字数门槛属书级设定，工具只输出分项统计。
5. **纯标准库 + Windows 编码防护。**
   与仓库 Python 惯例一致：snake_case、`reconfigure(encoding="utf-8")`、docstring 写明用法与退出码。
6. **知识文件通用化改写而非原文挂载。**
   去书名/人名/章节号，保留结构形状与实测分数；引用路径按仓库规范写部署后路径（`.claude/knowledge/anti-ai/...` 基座）。

## Risks / Trade-offs

- 通用化改写会丢失来源包的部分语境细节 → 以"保留实测数据 + 仓库外保留原包"缓解（原包在用户本地，不入库）。
- 警告级检查（广义夹层等）误报率高于硬性项 → 输出明确标注"需裁定"，不阻塞交付；误报模式后续由各书回归库兜底。
- 正则族在 Python `re` 与来源包一致，但跨平台行尾（CRLF）差异 → 测试用例覆盖 CRLF 输入。
