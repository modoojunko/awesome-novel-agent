## Purpose

把结构热源知识接到写作管线的关键节点，让 AI 热源在生成前被规避、在扫描时被优先识别，并为每本书提供"检测战役→规则沉淀"的文件载体。目标是把外部检测的修复轮次从源头压到最少。

## ADDED Requirements

### Requirement: writer 写前反闭环卡

writing-execution 流程 MUST 在起草每个场景前产出五行反闭环卡：人物此刻要办成什么/阻力从谁的即时反应产生/本场只演到哪一步停/哪些结果不解释/哪条信息留到下一场；第 3-5 项答不出时 MUST NOT 开始写该场正文。

#### Scenario: 约束先行
- **WHEN** writer 按流程起草任一场景
- **THEN** 约束速记中存在该场的五行反闭环卡，且卡内第 3-5 项均有明确答案

#### Scenario: 话术合规
- **WHEN** 检查 writing-execution.md 的新增文本
- **THEN** 作者可见表述使用日常语言，不含内部名词（对照 author-communication.md）

### Requirement: 写前提示词注入结构禁令（单一权威源、零语义冲突）

prompt-crafting 生成的写作提示词 MUST 包含结构禁令段，且 MUST 满足防冲突约束：

- 条目仅限既有规则未覆盖的新刻度：问答回合拍数上限（与 Gate E5 的"连续纯对话句数"刻度并行、互不替代，不重复写插动作频率）、章首冷开场、禁同场连续多套回执叠加（单场单回执的爽点兑现场明确豁免）、过桥链/证明链禁令；
- 章尾条目仅保留"禁总结/升华/预告"（与 Gate F 同向，引用不复述），MUST 显式声明"章纲落点优先"；"钩子搭台打断"为按需深度项，默认不写入提示词；
- 禁令段 MUST 带裁决顺序声明：作者设定与章纲 > 题材知识 > 结构默认值 > 检测优化；
- 判定细则 MUST 引用 `.claude/knowledge/anti-ai/structural-heat.md`，不整段复制知识文件；
- 禁令段 MUST NOT 与既有提示词规则产生数值或语义矛盾（标点、对话频率等既有口径一律引用，不重定义）。

#### Scenario: 提示词含禁令
- **WHEN** prompt-crafter 为任一章生成写作提示词
- **THEN** 提示词含结构禁令段，带知识文件引用路径与裁决顺序声明，`check-agents.py` 校验该路径有效

#### Scenario: 无矛盾注入
- **WHEN** 对照既有规则清单（Gate A-F、common-rules 数值口径、既有提示词节奏规则）核对禁令段
- **THEN** 无同一现象的双重数值口径、无方向相反的指令（如标点硬禁对用法判定）

### Requirement: anti-ai 先扫结构后清句子

anti-ai Phase 1 MUST 在 Gate A-F 词句扫描之前先做结构热源扫描（对照 structural-heat.md 的高风险结构清单）；结构命中项 MUST 优先进入修改范围（先改结构，再清句子）。同一问题同时命中结构与词句规则时 MUST 只计一次，按更优先生效的类别归类，避免双重计分。Phase 2 机器初筛 MUST 与 `check-prose.py` 并列调用 `check-chapter.py`（`check-chapter` 硬性命中并入 Gate A/B 清单；`check-prose` 行为不变）。

#### Scenario: 结构优先定级
- **WHEN** 稿件同时存在结构热源命中与 Gate A 词句命中
- **THEN** 修改顺序为先结构后词句，报告中结构命中单列

#### Scenario: 双脚本初筛
- **WHEN** anti-ai Phase 2 执行机器初筛
- **THEN** 两个脚本都被调用；`check-chapter` 硬性命中按硬失败处理，缺失或不可执行时按既有降级语义标注（不阻塞）

### Requirement: 项目骨架含进化机制文件

init 生成的项目 MUST 包含 `sandbox/detect-battles.md`（战役记录模板）、`sandbox/prose-regressions.txt`（回归模式库，空库+使用说明）、`sandbox/locked-lines.txt`（锁定台词白名单示例）；三者 MUST 被 sync 的更新检测与 `test_platforms.py` E2E 覆盖。

#### Scenario: 初始化产出
- **WHEN** 运行 `python tools/init.py <项目路径> --platform <任一平台>`
- **THEN** 三个骨架文件存在于项目 `sandbox/`，E2E 测试断言通过

#### Scenario: 战役记录可用
- **WHEN** 打开 `sandbox/detect-battles.md`
- **THEN** 模板含逐轮记录表（轮次/改动/逐片结果/结论）与"规律沉淀"节，使用说明为作者可读语言
