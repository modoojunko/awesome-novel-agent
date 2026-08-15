# awesome-novel-agent 架构文档

> 面向开发者理解实现细节。面向使用者的内容见 [README.md](./README.md)。
> 当前版本：v4.13.0

---

## 1. 系统架构

### 1.1 总体：状态驱动的 ReAct 循环

核心架构是**状态驱动循环**。每个 agent（含 novel-agent 与所有子 agent）都按 ReAct 模式运行：`OBSERVE → THINK → ACT → VERIFY → LOOP`。

- **OBSERVE**：从文件系统重建状态，不依赖上一次运行的上下文缓存（Context Isolation）
- **THINK**：读 `.agent/status.md` 的 `phase` 字段，判断当前该做什么、该谁做
- **ACT**：写 order 文件 → 通过 Agent 工具调度子 agent（novel-agent）；或直接执行本环节任务（子 agent）
- **VERIFY**：检查产出文件存在、order 文件 `status` 是否为 `DONE`
- **LOOP**：回到 OBSERVE，直到当前阶段完成

**路由依据是 `.agent/status.md#phase`**（setup/outline/draft/anti-ai/review/archive/finished），不是 `chapter.md#status`。`chapter.md#status`（outline→draft→archived）只表示章节自身的生命周期，不影响 agent 调度路由。

卷完成判定与完本终态：updater 归档后**只输出卷完成报告**，不写完成位；`last_volume_completed` 与 `phase: finished` 由 **novel-agent 裁决写入**（比对已归档章数 vs 卷规划章数）。phase=finished 为终态，不再调度。

### 1.2 入口检测（SKILL.md）

Skill 入口（主 agent 加载 SKILL.md 后）先做项目状态检测，之后才交棒给 novel-agent：

```
检测项目状态
├─ story.yaml 存在 → 旧版 2.x → 执行自动迁移（备份 → init.py → 按 templates/migration 映射转换）
├─ story.md 不存在 → 询问作者 → python tools/init.py [path] [--genre N] → @novel-agent
└─ story.md 存在 → 已有项目
    ├─ python tools/sync-project.py . --check → exit 1 → 询问作者是否同步更新
    └─ → @novel-agent 继续写作
```

同步新鲜度由 `.agent/.sync-fingerprint` 记录，用于检测 skill 仓库更新是否需要同步进项目。

### 1.3 主 Agent 与子 Agent

| 角色 | 职责 |
|-----|------|
| **novel-agent** | 顶层总指挥（`@novel-agent` 加载进主 AI）。检测 phase、写 order 文件、通过 Agent 工具调度子 agent。**不直接代劳子 agent 的工作，不用 Bash，不写任何内容文件** |
| **子 Agent × 8** | volume-planner / chapter-planner / prompt-crafter / writer / anti-ai / reader / updater / style-distiller。各自负责一个环节，由 novel-agent 调度，完成后将 order 标记 `status: DONE` |

> **写作基底规范**（`knowledge/format-specs/writing-base.md`，部署为 `.claude/knowledge/writing-base.md`，非 agent，不可调度）——永久加载、不可篡改。
> writer 的写作 sub-agent 动笔前先加载此基底，再叠加章节提示词；与基底冲突时以基底为准。

### 1.4 Agent 分工

| Agent | 职责 | 由谁调度 |
|-------|------|----------|
| `volume-planner` | 主线拆纲 + 卷纲规划（四维方法论） | novel-agent |
| `chapter-planner` | 章纲生成（memo + 情绪设计 + 场景卡 + hooks） | novel-agent |
| `prompt-crafter` | 6 元素提示词组装（冲突优先级 + 四步转化 + 稀疏注入） | novel-agent |
| `writer` | 正文生成 + AI 味自检（写作 sub-agent 先经 writing-base 基底） | novel-agent |
| `anti-ai` | Gate A-F 管线检测 + 量化评分定级 + 逐项清除 | novel-agent |
| `reader` | 深度评审（可选，作者需要时调度） | novel-agent |
| `updater` | 归档 lore-keeping + 设定变更 + 记忆兜底 | novel-agent |
| `style-distiller` | 风格蒸馏（LLM 双态：脚本统计引擎已退役 → 蒸馏主卡/场景卡/版本快照） | novel-agent |

### 1.5 调度架构

```
主 AI（加载 @novel-agent）
  │
  ├── 读 status.md → 判断当前 phase
  ├── 写 order 文件到 .agent/task/{type}-order.md（只含输入/输出路径，不含执行步骤）
  ├── 通过 Agent 工具调度子 agent
  │     ├── setup   → updater          （setting-update-order.md）
  │     ├── setup   → style-distiller  （style-distill-order.md，作者提供风格样本时）
  │     ├── outline → volume-planner   （volume-plan-order.md）
  │     ├── outline → chapter-planner  （chapter-plan-order.md）
  │     ├── draft   → prompt-crafter   （prompt-craft-order.md）
  │     ├── draft   → writer           （writing-order.md）
  │     ├── anti-ai → anti-ai          （anti-ai-order.md）
  │     ├── review  → reader           （reader-review-order.md，可选）
  │     ├── archive → updater          （archive-order.md / memory-sweep-order.md）
  │     └── # 卡冻结：归档后无风格增量更新
  ├── 子 agent 完成后将 order 覆盖为 status: DONE
  └── 检测到 order 标记 DONE → 推进下一阶段（setup 例外：setting-update-order DONE 后需作者确认设定，再推进 phase）
```

**关键规则：**
- novel-agent 是唯一调度者，**一次只 dispatch 一个任务**，等完成再调下一个
- order 文件只写输入文件路径 + 输出目标路径 + `status: pending`，**不包含执行步骤、规则、方法论**（SOP 在子 agent 的 skill 定义里）
- 子 agent 完成任务后用 Write 覆盖 order 的 `status: pending` 为 `status: DONE`（**不删除文件**——子 agent 无删除权限，删除会导致完成信号永不触发）
- novel-agent 完成判定：order 存在且 `status: DONE` 且 outputs 全部存在非空 → 完成；order 不存在 → 子 agent 意外中断，进重试
- 归档幂等：updater 追加前按章节锚点查重，整章完成后写 `.agent/archiving/{chapter}.done`，重派从断点继续（见 §2 数据流）
- novel-agent 不得被 Agent 工具作为 subagent 调度（否则失去 Agent 工具权限，调度链断裂）

---

## 2. 数据流

```
[入口] 检测 → init.py 初始化 / 2.x 迁移 / sync 同步
  │
[setup] 与作者讨论设定 → updater 写 settings/
  │
[outline] story.md → volumes/volume-{N}.md（情绪走向 / 冲突阶梯 / 信息差 / 场景卡）
  │        volume → chapters/vol-{N}-ch-{M}.md（章内微弧线 / 场景卡 / hooks）
  │
[draft]  chapter.md → prompt-crafting（6 元素组装）→ prompts/vol-{N}-ch-{M}-prompt.md
  │        → writer（写作 sub-agent 先读 writing-base 基底 + prompt）→ archives/*.draft.md
  │
[anti-ai] draft → Phase 1-4 管线 → archives/*.anti-ai.md
  │
[review] reader 深度评审（可选）
  │
[archive] updater 归档（**幂等**，见 §1.5 关键规则）：
  │        先建快照 `.agent/{chapter}-draft-ai.md`（从 .draft.md 复制，审计基线）→ 查 `.agent/archiving/{chapter}.done`，存在则只补缺失项
  │        判定定稿并 Write 生成 archives/*.md（中间稿 .draft.md/.anti-ai.md 保留不删）
  │        chapter.md#status → archived
  │        character-setting 追加角色状态（按 `## vol-N-ch-M` 锚点查重）→ timeline 追加事件（查重）
  │        快照 vs 定稿 diff → 语义合并到 .claude/knowledge/anti-ai.md + 动态记忆（writing-memory.md）（查重）
  │        写 {chapter}.done → 推进 status.md → order 标记 DONE
```

---

## 3. 文件结构

```
{project-name}/
├── story.md              # 项目索引（元信息 + 主线拆纲）
├── settings/
│   ├── world-setting.md  # 世界观
│   ├── writing-style.md  # 写作风格（蒸馏后含量化层主卡）
│   ├── genre-setting.md  # 题材设定
│   ├── foreshadowing.md  # 跨卷伏笔全局台账（init 生成空台账 / updater Step 8 维护，从 chapter.md#payoff_plan 汇总）
│   ├── timeline.md       # 时间线（归档时追加）
│   ├── character-setting/
│   │   └── <id>.md       # 每角色一个
│   ├── style-profiles/   # 分场景风格卡（style-distiller 蒸馏产出：dialogue/fight/group-scene/…）
│   │   └── genre-baselines/  # 题材风格基线（base/benchmark/delta）
│   └── .style-versions/  # 蒸馏版本快照（style-distiller 蒸馏时生成）
├── volumes/
│   └── volume-{N}.md     # 卷纲
├── chapters/
│   └── vol-{N}-ch-{M}.md # 章纲（status: outline → draft → archived）
├── prompts/
│   └── vol-{N}-ch-{M}-prompt.md  # 6 元素提示词
├── sandbox/              # 推演沙盘记录（可选，roleplay-sandbox 产出）
├── novel-samples/        # 文风蒸馏样本（作者把待学文风的文章放这里，style-distiller 专用）
├── archives/
│   ├── *.draft.md        # 草稿（writer 输出，历史留档）
│   ├── *.anti-ai.md      # 去 AI 味后版本（历史留档）
│   └── *.md              # 定稿（updater 归档时 Write 生成；归档后正文读取一律以此为准，中间稿不删）
├── .agent/
│   ├── status.md         # ★ phase 路由依据（唯一持久状态）
│   ├── task/             # order 文件（临时，完成后 status→DONE 留存待删）
│   ├── archiving/        # 归档 checkpoint（{chapter}.done，防重放重复）
│   └── {chapter}-draft-ai.md  # AI 原版快照（审计基线，归档后保留，靠 .done 标记区分过期）
├── .claude/ 或 .opencode/ 或 .zcode/ 或 .dsh/
│   ├── agents/           # Agent 定义（init.py 部署；zcode/dsh 无 agents，agents 即 .zcode/skills/ / .dsh/skills/）
│   ├── knowledge/        # 反 AI 规则 / 文风偏好 / 场景方法论 / 永久记忆 / 格式规范
│   └── memory/           # 动态写作记忆（volume/chapter/prompt/writing）
```

---

## 4. Skill 仓库结构与部署

### 4.1 仓库目录

```
agents/          # Agent 定义（frontmatter: role / react / skills / knowledge）
skills/          # 子 agent 的 SOP（anti-ai、prompt-crafting、memory-recording、volume-arc 等）
knowledge/       # 静态参考知识 → 部署到项目 .claude/knowledge/
templates/       # 项目骨架模板（settings/volumes/chapters/migration/…）
tools/           # init.py（初始化）、sync-project.py（同步更新）
```

### 4.2 knowledge/ 两层分类（按用途）

| 目录 | 用途 | 决策者 |
|------|------|--------|
| `scene-craft/` | 场景写作方法论——按场景类型匹配，四步转化后自动注入 prompt | **AI 自动** |
| `format-specs/` | 格式规范——章纲/卷纲/提示词/记忆格式 | 系统固定 |
| `genre-example/` | 题材案例——初始化后继承到项目 | 题材决定后自动 |
| `plot-craft/` | 剧情设计方法论（冲突升级/钩子/反转/悲剧） | **作者决策** |
| `character-craft/` | 角色设定方法论（认知 6 层模型/反派模板） | **作者决策** |
| `title-craft/` | 取书名方法论 | **作者决策** |
| `anti-ai/` | 反 AI 规则（common-rules / boundary-cases / {genre} 正反例） | **AI 自动** |

**场景方法论目录**：`scene-craft/{类型}/universal.md` + `{题材}.md` 特化，含 `prose/`、`pov/`（始终加载，稀疏注入）与 `dialogue/`、`fight/`、`appearance/`、`inner-mono/`、`death-scene/`、`environment/`、`group-scene/`、`transition/`（按场景类型触发）。

### 4.3 部署

- **Claude Code**：init.py 部署 agent 定义到 `.claude/agents/`，知识到 `.claude/knowledge/`，建 `.claude/memory/` 动态记忆桩
- **OpenCode**：init.py 同时部署到 `.opencode/agents/`，OpenCode 自动发现 `@novel-agent` 等
- **Codex**：init.py 部署 9 个自定义 agent 为 `.codex/agents/*.toml`（TOML 转换产物，引用改写为 `.codex/knowledge|memory`），独立工具为 `.codex/skills/<name>/SKILL.md`；novel-agent 用 `spawn_agent` 调度子 agent
- **ZCode**：init.py 部署 9 个 agent 为 `.zcode/skills/<name>/SKILL.md`（skill 转换产物，引用改写为 `.zcode/knowledge|memory`；ZCode 无项目级 agents 目录，agents 即 skills，与 Reasonix 同构）；novel-agent 用 `Agent` 工具按 skill 名调度子 agent
- **dsh（DeepSeek Harness）**：init.py 部署 9 个 agent 为 `.dsh/skills/<name>/SKILL.md`（skill 转换产物，frontmatter 只保留 dsh 识别的 `name`/`description`，引用改写为 `.dsh/knowledge|memory`；dsh 无项目级 agents 目录，agents 即 skills，与 ZCode 同构）；novel-agent 用 `subagent` 工具调度子 agent（prompt 要求子 agent 先 `skill(name=...)` 加载自身指令）
- **安装**：`install.sh` / `install.ps1` 将 skill 装到用户级 skills 目录

---

## 5. prompt-crafting 提示词组装管线

### 5.1 流程

```
Step 1  读取输入源（writing-style / volume / chapter / 涉及角色设定 / genre-example / anti-ai 规则）
Step 1.5 加载全局冲突裁定优先级（裁决后续规则冲突，不产出到 prompt 文本）
Step 2  按 6 元素结构填充：角色 / 任务指示 / 背景信息 / 案例 / 输入 / 输出
Step 3  冲突检测（前后一致性核对）
Step 4  验收自检 → 写入 prompts/vol-{N}-ch-{M}-prompt.md
```

### 5.2 冲突裁定优先级（从高到低）

| 优先级 | 规则 | 说明 |
|--------|------|------|
| 1 | 约束红线 | 情节红线 / 角色禁区 / 边界禁止，任何压缩不得删红线 |
| 2 | 字数 | 目标字数硬性约束，超限按"压缩低权重场景 > 高权重场景次要元素"策略 |
| 3 | T1 词（修饰类） | 仿佛/一丝/不禁/不由得等（突然/忽然/猛然 属语境敏感类，≤4次/章，红线段落从宽），超阈值时保留有叙事功能的 |
| 4 | 认知动词 | 意识到/发现/明白/感到，换外部动作或直接感知；关键情绪节点可简要使用（≤2次/章，见 narrative-rules.md 规则 2），其余不让步 |
| 5 | 感官/X了一下 | 每场景 ≤2 种感官细化（声音线索若为红线关键信息可豁免） |
| 6 | 写作规范 | 其余写作规范与技法，与以上冲突时自动让步 |

### 5.3 场景方法论加载（四步转化法）

场景方法论不能整段复制进 prompt，必须**稀疏抽取**（每类型最多 2 条）后经四步转化：

1. **锚定角色**——把"角色A/角色B"套到具体的人（性格、微习惯）
2. **锚定信息差**——谁在瞒、瞒什么、为什么（决定"不说真话"的方向）
3. **锚定情绪节奏**——紧张/压抑/舒缓对应不同句式与动作穿插频率
4. **融合输出**——生成可直接写入"输出·写作规范"的具体写法指引

### 5.4 输出结构（扁平化）

- **不可违反规则**：约束红线 + 字数 + T1词/认知动词/感官 + 叙事规则 + 写作规范，合成一个列表减少嵌套
- **场景写作指引**：四步转化后的场景写法（独立子节）
- **质感要求**：不完美约束（无用细节 / 半截话 / 段落精度分层）

---

## 6. 记忆系统

### 6.1 两级架构

```
.claude/memory/               动态记忆（各环节实时记录，updater 兜底维护）
  ├── volume-memory.md         卷纲反馈
  ├── chapter-memory.md        章纲反馈
  ├── prompt-memory.md         提示词反馈
  └── writing-memory.md        正文写作反馈（writer/reader 记录）
         │ use_count >= 4 晋升
         ▼
.claude/knowledge/permanent-memory.md   永久记忆（高频条目沉淀）
         │ 连续 3 次 sweep 未引用 → 作者确认后降级删除
```

### 6.2 捕获时机（memory-recording）

以下情况视为需要记录的反馈，各 agent 在对话中直接追加到对应 memory 文件：

| 时机 | 判断标准 |
|------|---------|
| 作者明确否定 | 说"不对""不好""不是这样"并给出替代方向 |
| 作者主动提出规则 | 说"以后都这样""记住这个" |
| 作者修正已接受内容 | 回头修改已确认的产出 |
| 作者提供正例 | 说"这就对""就是这样"或指参考材料 |

**不作为记忆：** 临时随口反问、纯功能性操作确认、明确说"先这样后面再说"。

### 6.3 生命周期

```
写入 memory/ → 被 agent 引用（use_count++）→ use_count >= 4
→ 晋升到 permanent-memory.md（保留全部字段 + [promoted YYYY-MM-DD]）
→ 连续 3 次 sweep 未引用 → 展示给作者确认 → 删除
```

- 单文件 >50 条 → updater 压缩：保留最近 30 条，其余按（领域+类型）分组摘要
- 追加前查重：结论 + 场景一致则跳过

### 6.4 归档语义合并（updater diff）

归档时对比 AI 原版快照（`.agent/{chapter}-draft-ai.md`）vs 定稿（`archives/*.md`）：

1. 完全相同 → 跳过
2. 语义重复 → 合并为一条，用更好的表述
3. 场景重叠 → 扩展已有条目场景范围
4. 冲突 → 询问作家确认

结果写入 `.claude/knowledge/anti-ai.md` 和写作记忆（`.claude/memory/writing-memory.md`），标注 `[writer-preference]`。

---

## 7. 去 AI 味管线（anti-ai）

anti-ai 是独立子 agent，输入 `archives/*.draft.md`，输出 `archives/*.anti-ai.md`。**不改剧情，只改表达。**

```
Phase 1  扫描   按 Gate A-F 分类标记 AI 味位置
         A 禁用词 / B 句式套路 / C 心理描写 / D 节奏 / E 对话 / F 结尾
Phase 2  诊断   6 项量化指标打分，定级（轻 / 中 / 重）
Phase 3  清除   按定级范围逐 Gate 修改，多轮收敛（同段连续两轮无改动跳过，全文上限 3 轮）
Phase 4  报告   字数变化 + 修改统计 + 前后对比
```

- **误杀防护**：修改前读 `knowledge/anti-ai/boundary-cases.md` 做豁免判定，命中则跳过标 `[SKIP: 误杀防护]`
- **删除量上限**：轻 ≤15% / 中 ≤25% / 重 ≤35%
- **白名单**：同级目录存在 `.anti-ai-whitelist` 时，其中段落跳过所有 Gate

---

## 8. 工具与工程

| 工具 | 用途 | 何时运行 |
|------|------|---------|
| `tools/init.py` | 项目初始化（选题材 → 建骨架 → 部署 agent/知识 → 建记忆桩 → 生成 CLAUDE.md/AGENTS.md → 写 status.md），共 9 步 | 全新项目 / 2.x 迁移后 |
| `tools/sync-project.py` | 将 skill 仓库更新同步进已有项目（`--check` 只检测） | 入口检测到指纹过期时 |
| `install.sh` / `install.ps1` | 安装 skill 到用户级目录 | 首次安装 |
| `.github/workflows/static.yml` | CI 静态检查 | 推送时 |

---

## 9. 扩展点

### 贡献社区 defaults

1. 作家在 `.claude/memory/` 积累自己的模式
2. 说"贡献这个模式"
3. 生成 community-ready 格式
4. 提 PR 到 `knowledge/anti-ai/`

### 新增题材类型

1. 在 `knowledge/genre-example/` 添加题材填充案例
2. 在 `knowledge/anti-ai/` 添加反 AI 默认模式
3. 添加 `scene-craft/{类型}/{题材}.md` 题材特化方法论

---

## 10. 关键约束

- **`.agent/status.md#phase`** — agent 调度路由依据，唯一持久状态
- **`chapters/*.md#status`** — 章节生命周期 `outline → draft → archived`
- **order 文件** — `.agent/task/*-order.md`，子 agent 完成后覆盖 `status: pending → DONE`（不删除），novel-agent 以 `status: DONE` 确认完成
- **`archives/*.md`** — 正文唯一存放处；`.draft.md` = 草稿；`.anti-ai.md` = 去 AI 味后；归档后定稿一律读 `.md`，`.draft.md`/`.anti-ai.md` 为历史留档（不删）
- **`.agent/{chapter}-draft-ai.md`** — AI 原版快照，归档 diff 基线；归档后保留（审计留档，靠 `.agent/archiving/{chapter}.done` 标记区分过期）
- **`.agent/archiving/{chapter}.done`** — 归档完成 checkpoint，重派时从断点继续，防 append 重放重复
- **`.claude/memory/*.md`** — 追加写入，不覆盖
- **novel-agent** — 不用 Bash、不写内容文件、不越权代劳、绝不访问项目外路径
- **设定写入** — settings/ 必须经 updater（setting-update 模式），novel-agent 不得直接写。例外：style-distiller 拥有 settings/writing-style.md、settings/style-profiles/、settings/.style-versions/ 专属写白名单，其余 settings 仍归 updater
- **作家本地记录优先于 references defaults**
