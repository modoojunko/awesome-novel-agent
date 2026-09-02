## Purpose

为 writer 与 anti-ai 提供结构级 AI 热源知识：外部 AI 检测器的热源常在段落结构而非用词，本能力让 agent 在写前与修文前按可验证的定律规避/识别高风险结构，从源头降低检出。

## ADDED Requirements

### Requirement: 结构热源知识文件必须存在且按部署路径可达

知识文件 `knowledge/anti-ai/structural-heat.md` MUST 存在于仓库；init MUST 将其并入 anti-ai 知识合并清单，随部署产物 `.claude/knowledge/anti-ai.md`（各平台对应知识目录）下发；对它的引用 MUST 指向该合并产物路径，通过 `tools/check-agents.py` 校验。

#### Scenario: agent 写前召回
- **WHEN** writer 或 anti-ai agent 读取部署后的 anti-ai 知识
- **THEN** 合并产物中包含结构热源定律内容，`check-agents.py` 对引用路径校验通过（exit 0）

#### Scenario: 仓库静态检查
- **WHEN** CI 运行 `check-agents.py` 与 `check-conflicts.py`
- **THEN** 均以 0 退出，无路径断链、无阈值冲突

### Requirement: 知识内容必须通用化且可溯源

文件内容 MUST 满足：①覆盖问答链密度、位置热值、切片边界稳定、补字铁律、内容类型切换、语气词拉长法、整章重写边界七条定律；②覆盖高风险结构清单（不少于 13 种：工作汇报体、取证结案体、经营验收体、协作示范体、前置准备体、数字讲解体、微闭环递归体、连续验收叠加体、固定位置换皮体、标准悬念搭台体、过桥链前缀体、私人回忆证明链、固定章首完整小戏）；③不含任何具体书名、人物名、章节号；④每条定律 MUST 附带实测数据作证据。

#### Scenario: 内容完整性验收
- **WHEN** 人工或脚本核对文件内容
- **THEN** 七条定律与不少于 13 种高风险结构齐备，全文无特定书目专有名词，定律条目附实测分数

#### Scenario: 阈值体系不冲突
- **WHEN** 运行 `check-conflicts.py`
- **THEN** 新增定律中的数量表述与既有 anti-ai 规则阈值无冲突

### Requirement: human-writing 系规则增量合并不得覆盖既有体系

从 human-writing 系规则包合并条目时 MUST 只增不删：不修改 `common-rules.md` / `anti-ai-writing.md` 既有阈值与方法论框架，新增条目 MUST 能逐条追溯到来源文件；不得以包内旧分叉文件整文件替换仓库重构版。

#### Scenario: 合并后回归
- **WHEN** 合并完成并运行 anti-ai 相关检查与测试
- **THEN** 既有规则条目与阈值不变（git diff 仅见新增行），无重复定义同一名词的冲突条目

### Requirement: 适用范围与冲突裁决顺序必须声明

知识文件 MUST 声明：①实测来源与适用边界（经验来自现实题材单书实测，数量阈值为默认值，按文风/题材校准）；②冲突裁决顺序——作者设定与章纲 > 题材知识 > 结构默认值 > 检测优化。数量表述 MUST 标注为默认值；与既有规则覆盖同一现象时 MUST 写明关系（新刻度并行或引用既有规则），MUST NOT 重复定义同一数值口径（如对话密度、标点用法）。

#### Scenario: 与既有规则同题
- **WHEN** 结构默认值与既有规则（如 Gate E5 对话句数、common-rules 破折号判定）覆盖相近现象
- **THEN** 文件明确两者为不同刻度或直接引用既有口径，无方向相反的指令

#### Scenario: 优先级落文
- **WHEN** writer 或 anti-ai 引用该文件做判定且与作者设定/章纲冲突
- **THEN** 按声明的裁决顺序执行，作者设定与章纲始终优先于检测优化
