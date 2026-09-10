# short-story-bootstrap Delta

## Purpose

让短篇成为一种独立的项目类型：作者说「写短篇」即得到一套短篇专属的骨架、agent 组、题材体系与知识库，四者共同构成短篇自己的运行环境，不依赖也不污染任何其他写作类型的资产。

## ADDED Requirements

### Requirement: A1 初始化入口必须按长度分流

`tools/init.py` MUST 接受 `--length short|long`。入口 skill（仓库根 `SKILL.md`）的检测流程 MUST 在作者表达短篇意图时走短篇分支，并在边界条件表中列出短篇各场景的处理方式。长度一旦确定 MUST 写入项目 `story.md`，作为后续同步工具判断同步对象的依据。

短篇 MUST NOT 成为缺省：不显式指定长度时，`init.py` MUST 沿用既有行为（不启用短篇）。

#### Scenario: A1.1 短篇意图进入短篇分支
- **WHEN** 作者在项目目录说出「写短篇」「写个盐言故事」「写个短故事」等短篇意图，且当前目录无 `story.md`
- **THEN** 入口 skill 询问是否在此目录创建**短篇**项目，确认后以 `--length short` 运行 `init.py`，完成后加载短篇总指挥

#### Scenario: A1.2 已有项目按长度标记识别
- **WHEN** 项目目录已存在 `story.md`，且其中标记 `length: short`
- **THEN** 入口 skill 直接加载短篇总指挥，不进入任何非短篇流程

#### Scenario: A1.3 短篇不是缺省
- **WHEN** 运行 `python tools/init.py <path>` 不带 `--length`
- **THEN** 初始化不启用短篇，`story.md` 中不含短篇标记

#### Scenario: A1.4 非法长度值被拒绝
- **WHEN** 传入 `--length medium` 或其他非 `short`/`long` 的值
- **THEN** `init.py` 打印可选值提示并非零退出，不创建任何文件

### Requirement: A2 短篇骨架必须自成一套

新增模板树承载短篇骨架。`--length short` 时 MUST 只生成短篇骨架：项目索引、篇目目录、沙箱、调度目录、题材设定与平台目录。

短篇 MUST 生成短篇版的项目级指令文件与短篇形态的状态机；短篇骨架 MUST NOT 包含短篇流程不使用的目录。

#### Scenario: A2.1 短篇骨架目录集
- **WHEN** 以 `--length short` 初始化项目
- **THEN** 项目含项目索引（含长度标记）、篇目目录、沙箱、`.agent/task/`、`tools/`、题材设定与平台目录

#### Scenario: A2.2 骨架只含短篇资产
- **WHEN** 检查 `--length short` 初始化后的项目根
- **THEN** 顶层目录全部属于短篇流程所需，不存在短篇流程不使用的目录

#### Scenario: A2.3 项目级指令为短篇版
- **WHEN** 读短篇项目根的项目级指令文件
- **THEN** 其中描述的 agent 构成、写作流程（情绪 → 构思 → 契约 → 写作 → 精修 → 兑现度核对 → 验收）与目录地图均为短篇形态

#### Scenario: A2.4 状态机为短篇形态
- **WHEN** 读短篇项目的 `.agent/status.md`
- **THEN** 含 `phase`（覆盖 setup / planning / contract / writing / polishing / verifying / delivered）、当前篇目标识、篇状态字段，不含卷章相关字段

### Requirement: A3 短篇题材体系必须独立编号

短篇 MUST 有独立的题材注册表与题材风格包集合。`--length short` 时题材参数的编号空间 MUST 为短篇题材，编号越界 MUST 报出短篇的可选范围。

#### Scenario: A3.1 短篇题材注册表齐备
- **WHEN** 核对短篇题材注册表
- **THEN** 注册表列出全部短篇题材，每条含编号、标识、中文名，且编号与风格包文件一一对应、全部存在

#### Scenario: A3.2 题材编号切换到短篇空间
- **WHEN** 以 `--length short --genre 1` 初始化
- **THEN** 部署的题材为短篇注册表第 1 号题材，且知识产物中的题材参考来自短篇风格包

#### Scenario: A3.3 编号越界提示短篇范围
- **WHEN** 以 `--length short` 传入超出短篇题材数量的编号
- **THEN** 报错并提示短篇可选编号范围，非零退出

### Requirement: A4 短篇 agent 组必须职责独立且全平台可部署

短篇 agent 组 MUST 由 5 个短篇专属 agent 与 1 个复用的体验验收 agent 组成：

| agent | 职责 | 独立性要求 |
|---|---|---|
| 总指挥 | phase 路由与调度 | 不写内容文件 |
| 构思 | 框架 / 大纲 / 写作契约组装 | — |
| 写手 | 正文写作 | 不组装契约 |
| 编辑 | 去 AI 味与精修 | 不参与契约组装与写作 |
| 验收 | 契约审计 + 定稿兑现度核对 | 不参与契约组装、写作、清创 |
| 体验验收（复用） | 苛刻读者体验验收 | 不参与结构核对 |

任一职责 MUST NOT 由承担其他职责的执行兼任。全部 7 个平台 MUST 支持短篇 agent 组部署，且短篇项目 MUST NOT 部署任何非短篇 agent。

#### Scenario: A4.1 短篇 agent 定义齐备
- **WHEN** 核对仓库 agent 目录
- **THEN** 存在短篇总指挥、构思、写手、编辑、验收五个 agent 定义，每个的 frontmatter 结构（含 name/description/role/tools/skills/knowledge）与既有 agent 同构

#### Scenario: A4.2 职责独立性可追溯
- **WHEN** 对照短篇各 agent 定义的输入输出契约
- **THEN** 契约审计与兑现度核对由验收 agent 执行、契约组装由构思 agent 执行、两者非同一 agent；验收 agent 不写任何内容文件

#### Scenario: A4.3 claude 与 opencode 平台部署到 agents 目录
- **WHEN** 以 `--length short --platform claude`（或 `opencode`）初始化
- **THEN** 平台 agents 目录下含短篇 agent 组

#### Scenario: A4.4 codex 平台部署为 TOML
- **WHEN** 以 `--length short --platform codex` 初始化
- **THEN** 平台 agents 目录下生成短篇 agent 组的 TOML 产物，含名称、描述与内联的 SOP 全文

#### Scenario: A4.5 grok 平台部署为 markdown
- **WHEN** 以 `--length short --platform grok` 初始化
- **THEN** 平台 agents 目录下生成短篇 agent 组的 markdown 产物，子 agent 带禁止再派生的约束

#### Scenario: A4.6 reasonix 与 zcode 与 dsh 平台部署为内联 skill
- **WHEN** 以 `--length short --platform zcode`（或 `reasonix`、`dsh`）初始化
- **THEN** 平台 skills 目录下生成短篇 agent 组对应的 `SKILL.md`，数量与短篇 agent 组一致，总指挥的 SKILL.md 含该平台的调度适配段

#### Scenario: A4.7 不部署非短篇 agent
- **WHEN** 检查短篇项目任一平台产物
- **THEN** 不存在任何非短篇的写作 agent

### Requirement: A5 短篇知识库必须独立部署

短篇知识库 MUST 部署为短篇自己的产物集合：语法与格式规范、写作参考、题材风格包、以及短篇自己的去 AI 口径产物。短篇反 AI 口径 MUST 单独合并为一个独立产物文件。

#### Scenario: A5.1 短篇反 AI 产物独立
- **WHEN** 以 `--length short` 初始化后检查平台知识目录
- **THEN** 存在独立的短篇反 AI 合并产物，其内容来自短篇自己的去 AI 口径文件

#### Scenario: A5.2 三类写作资产落位
- **WHEN** 以 `--length short` 初始化后检查平台知识目录
- **THEN** 短篇格式规范、短篇写作参考、短篇题材风格包三类内容均可通过部署后路径访问

#### Scenario: A5.3 引用路径可解析
- **WHEN** 运行静态校验
- **THEN** 短篇 agent 对知识文件的引用全部解析成功

#### Scenario: A5.4 题材风格包内容完整
- **WHEN** 检查短篇题材风格包
- **THEN** 每个题材包至少含：叙述腔调、开篇范式、钩子母题、情绪烈度、对话风格、**情绪链库**、招式库、节奏骨架、收尾范式；其中情绪链库给出若干条命名情绪弧（每条 4-6 个阶段，阶段有名称），招式库的每条为可套用的公式加一个具体示例，MUST NOT 只列招式名称

### Requirement: A6 同步工具必须按项目长度同步

同步工具 MUST 从项目索引读取长度标记，并按长度选择同步对象。对短篇项目的同步 MUST NOT 引入任何非短篇骨架或非短篇 agent。

#### Scenario: A6.1 短篇项目同步保持短篇形态
- **WHEN** 对短篇项目运行同步工具
- **THEN** 同步后的 agent 组、知识库、项目级指令仍为短篇形态

#### Scenario: A6.2 变更检测覆盖短篇资产
- **WHEN** 仓库侧短篇 agent 或短篇知识文件发生变化
- **THEN** 同步检查报告有更新并非零退出

### Requirement: A7 静态校验链必须覆盖短篇资产

仓库静态校验 MUST 覆盖短篇 agent 与短篇知识：引用路径 MUST 可解析，短篇知识文件 MUST NOT 被判为孤儿，短篇部署路径 MUST 在部署后路径白名单内，短篇量化阈值 MUST 与本仓既有阈值体系无冲突（冲突时 MUST 走显式豁免并记录理由）。

#### Scenario: A7.1 引用校验通过
- **WHEN** 运行 agent 引用校验
- **THEN** 短篇 agent 的引用全部解析成功，退出码 0

#### Scenario: A7.2 短篇知识不被判为孤儿
- **WHEN** 运行孤儿知识检查
- **THEN** 每个被部署的短篇知识文件都被短篇 agent 或入口 skill 引用，或属于显式的作者参考豁免清单

#### Scenario: A7.3 规则冲突检查通过
- **WHEN** 运行规则冲突检查
- **THEN** 退出码 0；若短篇阈值与本仓既有阈值存在同对象不同数字，则必须已加入显式豁免并说明理由，不得静默通过

#### Scenario: A7.4 平台 E2E 断言通过
- **WHEN** 运行平台测试套件
- **THEN** 短篇初始化在各平台的产物断言全部通过

### Requirement: A8 一个短篇项目必须容纳多篇且篇目互相隔离

短篇项目 MUST 以「一篇一目录」组织成品，篇目之间 MUST 在文件层面隔离（各自的设定、大纲、契约、正文互不覆盖），共享资源（题材风格包、项目级指令、状态文件）MUST 位于项目级。同一项目内开始新一篇 MUST NOT 影响已交付篇目的文件。

#### Scenario: A8.1 篇目目录隔离
- **WHEN** 在同一短篇项目内先后写两篇
- **THEN** 两篇各占独立的篇目目录，各含自己的设定、大纲、契约与正文，任一篇的文件不覆盖另一篇

#### Scenario: A8.2 共享资源位于项目级
- **WHEN** 检查短篇项目结构
- **THEN** 项目级指令、状态文件与题材知识位于项目级路径，不被复制进各篇目录

#### Scenario: A8.3 新篇不影响旧篇
- **WHEN** 已交付一篇后开始下一篇
- **THEN** 已交付篇目的正文文件字节不变
