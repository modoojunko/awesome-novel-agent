## Purpose

章节交付级确定性检查：在 anti-ai 统计检测（check-prose.py）之外，抓模型肉眼会漏的交付硬伤（引语夹层、嵌套引号、半角引号、字数表达错账等），并提供随项目成长的回归模式库与锁定台词白名单机制。

## ADDED Requirements

### Requirement: 检查工具命令契约

工具 MUST 以 `python3 check-chapter.py <稿件路径...>` 方式调用，接受一个或多个文件路径或目录；退出码 MUST 满足：0=全部通过（可有需人工裁定的警告项），1=存在硬性命中，2=文件读取失败。输出 MUST 逐条带 `[检查名] 行号: 上下文摘录`。

#### Scenario: 硬伤命中
- **WHEN** 稿件含硬性命中（引语夹层标签式、嵌套双引号、半角引号、破折号/省略号、字数表达不符）
- **THEN** 退出码为 1，输出逐条列出检查名、行号与上下文摘录

#### Scenario: 全部通过
- **WHEN** 稿件无硬性命中
- **THEN** 退出码为 0，仍输出平台口径字数统计（汉字/全角标点/引号/数字分项）与警告项

#### Scenario: 文件不可读
- **WHEN** 任一输入路径不存在或无法解码
- **THEN** 退出码为 2，不误报为检查失败

### Requirement: 检查项覆盖与分级

工具 MUST 覆盖以下通用检查项，并分为两级：硬性（命中即 exit 1）与警告（仅报告需人工裁定）。
硬性：引语夹层-标签式、嵌套双引号、半角引号、字数表达与引号内容逐字不符、回归库精确串命中。
警告：破折号/省略号（段落内 ≥3 处时提示逐处按 `common-rules.md` 用法判定，不做硬禁）、引语夹层-广义式、多轮问答并段、弱化副词密度超标、"X个字"待人工逐字核对、尾随标签（代词+说/问窄集）。
工具 MUST 输出平台口径字数但 MUST NOT 对字数设硬性阈值（字数要求属书级设定）；标点口径 MUST 与 `common-rules.md` 一致，MUST NOT 把书级硬禁（如"零破折号"）作为默认行为。

#### Scenario: 分级行为
- **WHEN** 稿件仅命中警告级检查项
- **THEN** 退出码为 0，警告项逐条列出并标注"需裁定"

### Requirement: 项目级回归库与白名单外置

回归模式库（曾翻车精确串）与锁定台词白名单 MUST 从项目文件读取（约定路径 `sandbox/prose-regressions.txt` 与 `sandbox/locked-lines.txt`，一行一条，UTF-8）；文件缺失时 MUST 跳过对应检查且不影响退出码；白名单命中行 MUST 跳过家族类检查并在输出中标注理由。

#### Scenario: 新项目无回归库
- **WHEN** 项目内不存在 `sandbox/prose-regressions.txt`
- **THEN** 回归库检查跳过，工具按其余检查项正常退出

#### Scenario: 回归串复发
- **WHEN** 稿件命中回归库中任一精确串
- **THEN** 该命中为硬性，退出码 1

#### Scenario: 白名单豁免
- **WHEN** 稿件某行完整匹配白名单中某条
- **THEN** 该行跳过句式家族类检查，输出标注白名单跳过

### Requirement: 部署与测试

init MUST 将工具部署到各平台根目录 `tools/`（与 check-prose.py 同机制），sync 的更新检测 MUST 覆盖该工具；测试 MUST 覆盖每个检查项的正例与反例、退出码契约、外置文件缺失/命中场景。

#### Scenario: 平台部署
- **WHEN** 运行 `python tools/init.py <项目路径> --platform claude`
- **THEN** 部署后项目内存在 `.claude/tools/check-chapter.py`，七平台 E2E 测试（`test_platforms.py`）通过

#### Scenario: 检查项回归
- **WHEN** 运行 `python tools/test_check_chapter.py`
- **THEN** 全部断言通过（stdout 打 ok，退出码 0）
