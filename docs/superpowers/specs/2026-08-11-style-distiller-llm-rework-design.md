# 设计文档：style-distiller 重构——LLM 特征提取 + 生成验收抽卡循环（双态卡 + 向前兼容）

**状态：已获作者确认（2026-08-11）；2026-08-12 修正：双态卡 + 向前兼容（无样本项目保持旧流程不变）**

## 1. 背景与目标

原模块采用「脚本统计（jieba POS）+ LLM 语义」两段式蒸馏。验收暴露根因问题：jieba 词性打标对文学词汇不可靠（「死寂→v、空旷→nr、安静→nr、刺骨→l、冰冷→z」，7 个形容词只认 2 个），导致核心测量失真、C1 手工口径被迫迁就机器。

核心使用场景（作者确认）：拿作者 1-3 章（约 1 万字）正文 → 蒸馏出**特征卡** → 特征卡被渲染成**生成提示词** → 生成 agent 按提示词写出接近作者文风的正文 → 生成正文被**验收**，不符则带反馈重写（抽卡）。

**双用户场景（2026-08-12 作者确认，向前兼容前提）：**

- **场景 A「无样本蒸馏」**：作者没有可蒸馏的原文 → 卡保持**旧结构原样**（`confidence: 0` + 正文定性四字段 + 9 维零值 + `locked`），prompt 注入走旧定性路径（正文四字段），**现状不变、零改动**。此类项目不触发 style-distiller。
- **场景 B「有样本蒸馏」**：作者提供 1-3 章样本 → 三阶段 13 模板蒸馏 → **蒸馏卡**（9 维填充 + 声音层 + `profile_name` + `confidence > 0`），prompt 注入**蒸馏输出**（量化区间 + 硬性规则/整体基调/风格参考例句）。
- **状态开关 = 卡内 `confidence`**（0 = 未蒸馏/手动；> 0 = 已蒸馏）——与旧 prompt-crafting Step 1.1 既有判定（「confidence=0 → 只注入定性层」）一致，**不新增标记字段**。旧卡（含旧 jieba 蒸馏卡）在两种状态下均可继续使用（回退见 §6.0b）。

**目标**：改用 LLM 直接做特征提取（弃 jieba），蒸馏方法论 = **三阶段 13 模板逆向工程**（拆解 1-4 → 量化 5-8 → 建模 9-13，作者提供），产出量化表 + 建模规则并收敛为特征卡；把「验收」从脚本数值对比改为「用生成提示词逐条指令遵循检查」，并新增「验收不过 → 反馈重写」的抽卡闭环。卡片一旦蒸馏即冻结，机器生成内容永不回写卡片。

**不做**：确定性统计引擎（jieba POS 计数）、增量滑动平均更新、题材基线、compare/mix 工具、C1 人工计数对照验收。**不做**：批量 schema 迁移（双态共存取代迁移，见 §9）。

## 2. 核心决策（已与作者确认）

| 决策点 | 结论 |
|--------|------|
| 测量层 | **纯 LLM 特征提取**，无 jieba、无脚本统计引擎 |
| 卡片格式 | **双态**：未蒸馏 = 旧模板原样（confidence=0，正文定性四字段）；蒸馏后 = 案例 1 结构（9 维填充 + 可选三维 name_pronoun / inner_monologue_pct / strength + 声音层）。增强字段全部可选，旧卡零改动 |
| 卡状态开关 | **`confidence`**（0=未蒸馏/手动 → 定性注入；>0=已蒸馏 → 蒸馏输出注入），复用旧判定，无新字段 |
| 生成提示词格式 | 双态注入：未蒸馏 = 正文定性四字段（现状不变）；蒸馏后 = 案例 2（数值渲染成范围指令 + 声音层透传 + 剧情上下文） |
| 验收 | **anti-ai 用生成提示词（案例 2）逐条做指令遵循检查**，不用独立特征再提取；对 prompt 实际注入内容验收（双态通用） |
| 抽卡 | 验收违反 → 违反报告喂回 writer 带反馈重写，novel-agent 调度级，≤3 次 |
| 卡生命周期 | **冻结**：一次蒸馏到位；归档后不动卡；机器生成章永不回写；重蒸馏仅作者主动触发 |
| 场景卡 | 保留：通用卡 + 分场景卡（战斗/对话等），LLM 按段落类型聚合提取，inherits/override |
| 蒸馏方法论 | 三阶段 13 模板（拆解 1-4 → 量化 5-8 → 建模 9-13）；模板 1-4 为 LLM 分析过程稿不落盘 |
| 分析稿持久化 | 白名单内扩 `settings/style-profiles/analysis/`（量化表 + 建模规则全文），卡保持收敛精简 |
| 退役 | compare-style、mix-style、题材基线、F5 增量更新、check 退出码契约、C1；**不退役**旧定性注入路径（正文四字段 + confidence=0 分支）与旧模板/init seed |
| 验收主标准 | C6 作者盲测正确率 ≥ 70% |

## 3. 架构

### 3.1 角色分工（产卡/注入/生成/验收四分离）

| 角色 | 职责 | 产物 |
|------|------|------|
| **style-distiller** | 产卡：LLM 读样本 → 三阶段 13 模板（拆解/量化/建模）→ 特征卡（主卡 + 场景卡）+ 分析稿 | `settings/writing-style.md` + `settings/style-profiles/*` + `settings/style-profiles/analysis/` + 备份 `.style-versions/` |
| **prompt-crafter** | 注入：卡 → 生成提示词（案例 2 格式） | 渲染后的风格参数提示词（写入 `prompts/` 或随 order 传递） |
| **writer** | 生成：按风格参数提示词写正文 | `*.draft.md` |
| **anti-ai** | 验收：用同一份风格参数提示词逐条检查正文 → 违反报告 | `archives/*.anti-ai.md` 报告 |
| **novel-agent** | 调度：writer 生成 → anti-ai 验收 → 违反则派 writer 重写（≤3）→ 全过进 review/archive | order 流转 |

**关键约束**：生成提示词（案例 2）是**唯一操作规格**——writer 生成与 anti-ai 验收用同一份文字，天然同源，避免「提取→对比数值」的两次测量噪声。

**卡可见性（数据流）**：卡 = 项目相对路径，已声明在各 agent 定义的 `knowledge:` 清单（prompt-crafter 现有 `settings/writing-style.md` + `settings/style-profiles/`）。流转：novel-agent 下发 `prompt-craft-order.md`（目标章节 + scene_type）→ prompt-crafter 按 scene_type 用 Read 加载主卡 + 对应场景卡（inherits/override 叠加）→ **按卡态分支渲染**（§6.0：confidence=0 走定性注入；confidence>0 走渲染规则）→ 产提示词写 `prompts/vol-{N}-ch-{M}-prompt.md` → writer 生成与 anti-ai 验收读取**同一份**。分析稿（§5.4）不进任何 agent 的加载清单，仅留档，不参与运行时读取。场景 A（未蒸馏）项目卡为旧结构，prompt-crafter 走旧定性路径，与现状完全一致。

### 3.2 主循环

**双态注记**：循环结构对两场景相同（prompt-crafter → writer → anti-ai），差异仅在 prompt-crafter 注入的内容——场景 A（未蒸馏）注入正文定性四字段（§6.0 上支，现状不变）；场景 B（蒸馏）注入蒸馏输出（量化区间 + 声音层，§6.0 下支）。writer 与 anti-ai 始终读同一份提示词，与卡态无关。

```
① style-distiller（仅场景 B，作者触发）：样本(1-3章) → 三阶段 13 模板（拆解→量化→建模）→ 蒸馏卡（案例1 收敛格式 + 声音层）+ 分析稿
② prompt-crafter：卡 → 渲染 → 风格参数提示词（未蒸馏=定性四字段；蒸馏=案例2 蒸馏输出）
③ writer：用提示词写正文
④ anti-ai：用同一份提示词逐条验收正文
      ├─ 违反 → 违反报告（条号/如何违反/建议）→ novel-agent 派 writer 带报告重写 → 回④（≤3 次）
      ├─ 3 次仍违反 → 取最优稿，报告留作者人工裁决
      └─ 全过 → review(reader) → archive(updater) → 卡不动
```

### 3.3 调度点

| 触发 | 动作 |
|------|------|
| setup / 手动「重蒸馏」 | novel-agent 派 style-distiller（`style-distill-order.md`）→ 写主卡 + 场景卡 |
| draft | prompt-crafter 读卡渲染提示词，writer 生成 |
| 生成后 | novel-agent 派 anti-ai 验收；违反派 writer 重写（≤3） |
| 归档后 | **不触发任何风格增量更新**（卡冻结） |

## 4. F1：卡片数据结构（双态，2026-08-12 修正）

卡分双态，状态由 frontmatter `confidence` 判定（0 = 未蒸馏/手动；> 0 = 已蒸馏）：

- **未蒸馏态（场景 A / 旧项目）**：现有旧模板**原样不动**（`templates/settings/writing-style.md` 当前版本）——`confidence: 0`、9 维零值、`name_pronoun_ratio` 单值、`emotion_expression` 三字段（无 inner_monologue_pct）、`locked` 保留、正文定性四字段 + few-shot。此态卡 = 作者手动配置，prompt 注入走定性路径（§6.0 上支）。**本仓库不改模板、init 不改 seed、旧项目零改动**。场景卡同理（`inherits`/`override` + 正文定性节，旧样）。
- **蒸馏态（场景 B）**：由 style-distiller 三阶段 13 模板蒸馏产出，下方案例 1 结构。9 维填充 + 声音层（`hard_constraints`/`soft_guidance`/`few_shot_examples`）+ `profile_name` + `confidence > 0`。**结构增强字段可选**：`name_pronoun_ratio` 三维、`emotion_expression.inner_monologue_pct`、`verb_style.strength`——存在时校验（§4.1）、渲染用增强格式；缺省（旧 jieba 蒸馏卡 / 未蒸馏卡）时渲染回退（§6.0b）。`locked` 保留可接受（新流程无增量更新，为 no-op）。

蒸馏卡 = **量化维（模板 5-8 收敛）** + **声音层（模板 9-13 建模规则收敛）**。主卡 `scene_type: general`；场景卡同结构 + `inherits` + `override`。完整推导档（量化表 + 建模规则全文）见 §5.4 分析稿。

```yaml
profile_version: "1.0"
profile_name: "都市校园轻小说-贺天然视角"     # 新增：人类可读的卡名
scene_type: "general"                        # general | dialogue | fight | environment | inner-mono | transition | group-scene
source_sample_length: 5000
confidence: 75
last_updated: "2026-08-11"

# ==================== 词汇层 ====================
lexicon:
  adj_density_per_100: 5.8                   # 客观数值（LLM 提取）
  adv_density_per_100: 3.5
  four_phrase_freq_per_100: 1.8
  preferred_words: [贺天然, 温凉, 重生, ...]  # 高频偏好词（≤10）
  banned_words: []                            # 禁用词
  name_pronoun_ratio:                         # 三维分布（旧单值改为分布）
    name: 45                                  # 人名占比 %
    he_she: 50                                # 他/她占比 %
    i_you: 5                                  # 我/你占比 %

# ==================== 句式层 ====================
syntax:
  avg_sentence_length: 16
  sentence_length_dist:                       # 客观阈值桶
    short_le_8: 38
    medium_9_20: 45
    long_21_35: 14
    xlong_gt_35: 3
  single_sentence_paragraph_pct: 38
  avg_sentences_per_paragraph: 2.2
  question_ratio: 13
  exclamation_ratio: 7

# ==================== 节奏层 ====================
rhythm:
  dialogue_pct: 48
  action_pct: 16
  environment_pct: 6
  inner_thought_pct: 25
  narration_pct: 5

# ==================== 修辞层 ====================
rhetoric:
  metaphor_density_per_100: 1.2
  metaphor_preference:                        # 类别分布 %
    weapon_metal: 5
    nature: 10
    body: 20
    abstract: 30
    other: 35
  sensory_dist:                               # 类别分布 %
    visual: 72
    auditory: 15
    tactile: 10
    olfactory: 2
    gustatory: 1

# ==================== 情绪表达层 ====================
emotion_expression:
  direct_pct: 15
  action_physiology_pct: 45
  environment_projection_pct: 5
  inner_monologue_pct: 35                     # 作者特有：内心吐槽直接呈现情绪

# ==================== 叙事视角层 ====================
narrative:
  perspective: "third_limited"                # 类别枚举
  focal_character: "贺天然"
  inner_monologue_style: "direct"             # 类别枚举

# ==================== 对话风格层 ====================
dialogue_style:
  tag_style: "mixed"                          # 类别枚举
  avg_dialogue_length: 12
  interrupt_freq_per_100: 6
  subtext_ratio: 22
  direct_address_freq_per_100: 8

# ==================== 衔接层 ====================
cohesion:
  conjunction_freq_per_100: 2.6
  transition_sentence_ratio: 0.04
  paragraph_bridge_style: "action"            # 类别枚举

# ==================== 动词风格层 ====================
verb_style:
  action_verb_ratio: 35
  mental_verb_ratio: 40
  state_verb_ratio: 25
  strength: "medium"                          # 类别枚举（力度：weak/medium/strong）

# ==================== 硬约束（声音层，LLM 提炼）====================
hard_constraints:
  - "内心独白必须用引号包裹，呈现为角色直接的心理活动"
  - "禁止使用'宛如''宛若'等过于文艺的明喻词"
  # …

# ==================== 软引导（声音层）====================
soft_guidance:
  - "整体基调：轻松吐槽向，带点日式轻小说的脱线感"
  # …

# ==================== Few-shot 示例（声音层）====================
few_shot_examples:
  - type: "inner_thought"
    text: "…"
    reason: "…"
  # …
```

### 4.1 类型规则

- **客观数值**：密度/占比/长度（`5.8`、`48`），LLM 按字段客观定义输出精确值。
- **类别枚举**：有限集合取值（`tag_style: mixed`、`strength: medium`、`perspective: third_limited`、`paragraph_bridge_style: action`、`inner_monologue_style: direct`）。枚举是分类不是打分，属客观。
- **分布**：`sentence_length_dist` / `metaphor_preference` / `sensory_dist` / `name_pronoun_ratio`（三维时）为百分比分布，和应为 100（±1 容忍）。
- **可选增强字段（蒸馏卡）**：`name_pronoun_ratio` 三维（`name`/`he_she`/`i_you`）与单值（旧结构）均可，存在即校验；`emotion_expression.inner_monologue_pct` **蒸馏阶段**缺省时由 style-distiller 按余量推断补值（100 − 其他三项），**渲染阶段**缺省则不注入该子项（§6.0b，不凭空补 0）；`verb_style.strength` 缺省时渲染不注入力度描述（存在时注入力度描述）。**校验规则：字段存在才校验，缺失不报错**（向前兼容，旧卡零改动）。
- **声音层**：`hard_constraints` / `soft_guidance` / `few_shot_examples` 由阶段三建模规则（模板 9-13：句式卡/行为树/对话模式/节奏模型/锚点）收敛而来，自由文本，不进验收数值对比。已蒸馏卡建议含声音层；缺失（旧 jieba 蒸馏卡）时渲染回退正文定性四字段（§6.0b）。

## 5. F2：LLM 特征提取（蒸馏方法论：三阶段 13 模板）

蒸馏 = 三阶段 13 模板逆向工程（作者提供，方法论锁定）：

| 阶段 | 模板 | 产出 | 归属 |
|------|------|------|------|
| 一 拆解 | 1 文本分层 / 2 段落节奏 / 3 句子级结构 / 4 情绪表达 | 逐段/逐句/逐情绪标注表 | LLM 分析过程稿（不落盘） |
| 二 量化 | 5 频次 / 6 五层占比 / 7 情绪通道 / 8 词汇 | 量化数据表 | 持久化分析稿 + 收敛进卡量化维 |
| 三 建模 | 9 句式卡 / 10 行为树 / 11 对话模式 / 12 节奏模型 / 13 结构锚点 | 建模规则卡 | 持久化分析稿 + 收敛进卡声音层 |

### 5.1 方法论模板

新建 `knowledge/style-distill/prompt-templates/feature-extract.md`（取代旧 distill-prompt.md），内容 = 13 个模板的完整定义：

- 模板 1-4：分层/段落节奏/句子结构/情绪表达的标注口径 + 封闭取值集合（句型/主语/动词/情绪通道选项，按作者模板原样）。
- 模板 5-8：频次/五层占比/情绪通道/词汇的统计口径 + 每项客观定义；分布约束（五层占比总计 ≤110% 容忍、情绪通道和 =100%）。
- 模板 9-13：句式卡（S-01 内心独白起手式）/行为树/对话模式（D-01 直球-语塞）/节奏模型（循环单元 + 关键参数）/结构锚点模型的**结构公式与规则格式**（作者示例为格式范本）。
- 输出格式：量化表（模板 5-8）+ 建模规则卡（模板 9-13）+ 收敛卡（案例 1 格式）。

### 5.2 主卡提取流程

```
样本(.md/.txt，≥1500 字，不足向 novel-agent 说明)
 → 阶段一 拆解（模板 1-4）：逐段分层/段落节奏/逐句结构/情绪通道标注（LLM 内部推理，不落盘）
 → 阶段二 量化（模板 5-8）：频次/五层占比/情绪通道/词汇 → 量化表
 → 阶段三 建模（模板 9-13）：句式卡/行为树/对话模式/节奏模型/锚点 → 建模规则
 → 收敛：量化表 → 卡量化维（案例 1 九维）；建模规则 → 卡声音层（hard_constraints/soft_guidance/few_shot_examples）
 → 校验 schema → 写 settings/writing-style.md（蒸馏卡）
 → 写 settings/style-profiles/analysis/general.md（量化表 + 建模规则全文，推导档留痕）
 → 备份旧卡到 settings/.style-versions/v{N}_{YYYY-MM-DD}.md
 → confidence 由 LLM 按样本质量/一致性给（1-100；蒸馏卡必须 >0，0 只留给手动配置的未蒸馏卡）
```

**覆盖旧卡（结构保持，2026-08-12 修正）**：蒸馏输出写到 `settings/writing-style.md`——9 维结构不变（只填值），**新增**声音层三字段 + `profile_name`，`confidence` 置 >0，`locked` 保留（新流程无增量更新，为 no-op）。正文定性四字段保留为遗留内容，不再参与注入（蒸馏后渲染走声音层，§6.0）；未蒸馏项目不触发本流程。

### 5.3 场景卡提取流程

```
样本按段落分类场景（复用 6 类）→ 每类聚合子样本
 → 子样本 ≥ 阈值（800 字）才产该场景卡；不足跳过
 → 同 5.2 三阶段跑该场景子样本（阶段三侧重场景差异规则：战斗句式/对话模式等）
 → 收敛为 override（只写差异维度）+ 场景声音层
 → 写 settings/style-profiles/{scene_type}.md（inherits: writing-style.md + override）
     + settings/style-profiles/analysis/{scene_type}.md（该场景量化表 + 建模规则）
```

### 5.4 存储布局（白名单内扩）

```
settings/
  writing-style.md                    # 主卡（收敛：量化维 + 声音层）
  style-profiles/
    dialogue.md fight.md …            # 场景卡（差异维 + 声音层）
    analysis/                         # 新增：蒸馏分析稿
      general.md                      # 主卡推导档（量化表 + 建模规则全文）
      dialogue.md fight.md …          # 各场景推导档
  .style-versions/                    # 版本备份（卡 + 对应分析稿同版本备份）
```

- 分析稿 = 完整推导档；卡 = 收敛参考物。**生成/验收从卡出发渲染案例 2，不直接读分析稿**。
- 白名单扩展：写入面从「卡三处」扩为「卡三处 + `settings/style-profiles/analysis/`」，蒸馏流程只写这四处。

### 5.5 幂等与备份

- 重复蒸馏同一样本不产生多余备份（以当日版本为准）。
- 卡与对应分析稿同版本备份到 `.style-versions/`；卡内 `last_updated` 写当日日期。

## 6. F3：生成注入（prompt-crafter，双态）

### 6.0 双态注入（状态开关 = `confidence`，2026-08-12 修正）

| 卡态 | 判定 | prompt-crafter 注入 | 实现位置 |
|------|------|--------------------|----------|
| 未蒸馏（场景 A） | `confidence == 0` | 正文定性四字段（role→叙事身份 / core_principles→硬约束 / possible_mistakes→AI易犯错误 / depiction_techniques→描写层次）+ few-shot 例句 | prompt-crafting Step 1.1 既有分支，**不改** |
| 已蒸馏（场景 B） | `confidence > 0` | 量化维渲染（区间/占比/分布/枚举，§6.1）+ 声音层透传（硬性规则/整体基调/风格参考例句，§6.1） | `rendering-rules.md`（取代 `injection-template.md`） |

**6.0a 声音层透传（已蒸馏）：** `hard_constraints` →「硬性规则」逐条不删改；`soft_guidance` →「整体基调」；`few_shot_examples` →「风格参考例句」按 type 分组。

**6.0b 回退（向前兼容）：** 已蒸馏但声音层缺失（旧 jieba 蒸馏卡）→ 量化维照常渲染 + 声音层回退为正文定性四字段 + few-shot；`name_pronoun_ratio` 单值 → 渲染为「人名/代词使用比例 X%」，三维 → 逐桶；`emotion_expression` 无 `inner_monologue_pct` → 该子项不注入。

### 6.1 渲染规则（卡 → 案例 2 提示词，仅已蒸馏态）

| 卡内容 | 渲染 |
|--------|------|
| 数值密度类（`adj_density_per_100: 5.8`） | 「形容词密度：每百字 5-6 个」（按 confidence 定区间，见 6.1a） |
| 占比类（`dialogue_pct: 48`） | 「对话约 48%（近一半是对话）」 |
| 分布类（`sentence_length_dist`） | 「短句（≤8字）占比 ≥ 35%」等分条 |
| 类别枚举（`tag_style: mixed`） | 中文短语（「对话标签混合使用」），映射表见 6.2 |
| `preferred_words` | 「允许使用：网络用语、动漫梗、口语化表达」等聚合表述 |
| `hard_constraints` | 「硬性规则」逐条透传（不删改） |
| `soft_guidance` | 「整体基调」透传 |
| `few_shot_examples` | 「风格参考例句」按 type 分组透传 |
| — | prompt 固定含「严格匹配上述风格参数，偏差不超过 20%」生成目标 |
| — | prompt 固定含「剧情上下文」「写作要求（直接写正文/字数）」占位 |

建模规则（模板 9-13）先收敛进卡声音层（§4），渲染时从卡读取，不直接读分析稿：句式卡 → few_shot_examples；节奏参数/锚点 → hard_constraints；对话模式/行为树 → hard_constraints + soft_guidance。结构化全文留档在分析稿（§5.4）。**本表与下述 6.2/6.1a 仅已蒸馏态（confidence>0）生效**；未蒸馏态（confidence=0）不渲染本表，走 §6.0 上支定性注入。

### 6.2 类别枚举 → 中文映射表（渲染用，仅已蒸馏态）

```
tag_style: pure_tags → "标签用'XX说'为主" / mixed → "标签混合使用" / no_tags → "不用标签，动作替代"
strength: weak → "动词力度轻" / medium → "动词力度中等" / strong → "动词力度烈"
paragraph_bridge_style: action → "段落靠动作衔接" / dialogue → "靠对话衔接" / transition → "少用过渡句"
inner_monologue_style: direct → "内心独白用引号直接呈现" / indirect → "间接转述"
perspective: first_person / second_person / third_limited / third_omniscient
```

### 6.1a 密度类区间规则（confidence → 区间宽度，仅已蒸馏态）

仅密度类数值（`*_density_per_100`、`*_freq_per_100`、`avg_sentence_length`、`avg_dialogue_length` 等单值度量）渲染为「约 X，区间 [L, U]」：

| confidence | 区间 |
|------------|------|
| ≥ 70 | X × (1±10%)，取整 |
| 50-69 | X × (1±20%)，取整 |
| < 50 | X × (1±30%)，取整 |

占比类（`dialogue_pct` 等）渲染为「约 X%」+ 中文定性（近一半/大部分/少量）；分布类（`sentence_length_dist` 等）渲染为逐桶阈值。两类不套区间公式，由 anti-ai 做定性贴近判定。注：置信度档位沿用旧 injection-template 的容差思想，但区间宽度按本表（≥70±10% / 50-69±20% / <50±30%）取代旧四档（21-50→30 / 51-70→20 / 71-90→15 / 91-100→10）。

### 6.3 稀疏注入

- 主卡兜底；按 scene_type 选场景卡（override 叠加主卡）。
- 场景差异维度才额外注入，全量注入挤 prompt 空间时优先保声音层 + 差异维。

## 7. 验收与抽卡（Gate G 重构 + 新闭环）

### 7.1 anti-ai 验收（指令遵循检查）

**双态注记（2026-08-12 修正）**：验收对象 = 提示词**实际注入**的风格要求，与卡态无关——已蒸馏态 prompt 含量化区间 + 硬性规则/整体基调/例句，逐类检查；未蒸馏态 prompt 只有定性四字段，则只验收定性要求（数值/占比/建模规则条不适用则跳过）。同一份 checklist、按 prompt 实际内容取子集。

```
输入：风格参数提示词（prompt-crafter 渲染的那份，未蒸馏=定性四字段 / 已蒸馏=案例 2）+ 生成正文
过程：LLM 逐条对照提示词中实际存在的风格要求检查正文
  · 数值/占比条（已蒸馏）：「对话约 48%」→ 本章对话是否明显偏离（偏离即违反，不要求数值）
  · 硬性规则条：逐条判定（如「禁止'宛如'」→ 查是否出现）
  · 建模规则条（已蒸馏）：节奏参数（「对话密集区≥4轮后必须独白缓冲」「纯叙述≤3句」）、对话模式（D-01~）、锚点（章首/章尾语义闭环）逐条判定
  · 软引导条：整体基调是否吻合
  · 定性条（未蒸馏）：叙事身份/硬约束/AI易犯错误/描写层次四字段逐条判定
输出：违反报告（.anti-ai.md）
  · 逐条：条号 + 原文要求 + 正文表现 + 违反与否 + 建议
  · 汇总：违反条数 / 总条数；结论 PASS / FAIL
```

### 7.2 抽卡循环（novel-agent 调度级）

```
writer 生成一版
 → novel-agent 派 anti-ai 验收
 → PASS → 进 review(reader) → archive(updater)
 → FAIL → 违反报告随重写 order 喂 writer：
        提示词 = 原风格参数提示词 + 「本次验收违反：[逐条]，重写时向 [建议] 靠拢」
       → writer 重写 → 再验收（round ≤ 3）
 → 3 次仍 FAIL → 取最优稿（违反最少），报告留作者人工裁决
```

### 7.3 反馈装配

重写提示词由 novel-agent 在 order 中装配：原始渲染提示词（含剧情上下文）+ 最新违反报告全文 + 「仅重写上述违反项，其余保持」。

## 8. 退役清单

| 组件 | 处理 |
|------|------|
| `tools/distill-style.py` | 删除（distill/update/check 三子命令 + 统计引擎） |
| `tools/compare-style.py`、`tools/mix-style.py` | 删除 |
| jieba 依赖 | requirements、`static.yml` 的 `pip install jieba`、venv 说明删除 |
| F5 增量更新 | `skills/style-distill.md` 增量节、novel-agent/novel-dispatch 的 style-update-order 调度点删除 |
| 题材基线 | `genre-baselines/` 三层机制退役（模板可留作纯参照） |
| check 退出码契约 | `skills/anti-ai.md` Gate G 的 0/1/2 语义替换为指令遵循验收 |
| `injection-template.md` | 删除，由 `rendering-rules.md` 取代（已蒸馏态渲染规格） |
| C1 验收 | 退休（无可参照物） |
| 旧 `tools/test_style_distill.py` 数字断言 | 重写为模板/流程/schema 断言（见 §10） |

**不退役（2026-08-12 修正，向前兼容核心）**：旧定性注入路径（prompt-crafting 正文四字段提取 + confidence=0 分支，场景 A 主路径）、旧卡模板（`templates/settings/writing-style.md` 当前结构）、init 的旧模板 seed（`_write_new_style_card` 原样保留）。场景 A 项目不感知任何行为变化。

**保留**：`tools/init.py`、`tools/sync-project.py`（模板部署；旧模板 seed 不变，无 schema 迁移）、`tools/check-agents.py`（双态卡校验更新）、`tools/check-conflicts.py`、`tools/test_platforms.py`。

## 9. 双态共存与升级（2026-08-12 修正，取代原「迁移」）

- **无批量迁移**：旧卡（未蒸馏态）零改动、零迁移，直接沿用（定性注入路径不变，§6.0 上支）。init 新建项目仍产旧模板（未蒸馏态 seed）。
- **升级只发生在作者主动蒸馏时**：有样本 → 作者触发 `style-distill-order.md` → style-distiller 三阶段 13 模板蒸馏 → 旧卡被**蒸馏卡**覆盖（9 维结构保持、只填值；新增声音层 + `profile_name`；`confidence` 置 >0）。卡冻结模型下无自动迁移。
- **旧 jieba 蒸馏卡**（`confidence>0`、无声音层、旧结构）：继续可用——量化维照常渲染，声音层回退正文定性四字段（§6.0b）；建议作者重蒸馏获得声音层。
- 声音层（建模规则收敛）零损失：蒸馏时保留在卡内 + 分析稿留档（§5.4）。

## 10. 测试

| 测试 | 内容 |
|------|------|
| schema 合法性（双态） | **旧模板（未蒸馏态）过校验 + 蒸馏卡（案例 1 结构）过校验**；增强字段存在才校验、缺失不报错（向前兼容） |
| 13 模板方法论 schema | 量化表（模板 5-8）键完整；建模规则（模板 9-13）格式正确（句式卡含结构公式、对话模式含轮次结构、节奏模型含关键参数） |
| 渲染正确性（双态注入） | 已蒸馏卡 → 区间/中文映射正确（5.8 → "5-6 个"；mixed → "标签混合使用"）；未蒸馏卡（confidence=0）→ 走定性四字段分支（技能文本含双态分支） |
| 建模规则渲染 | 句式卡 →【风格参考例句】、节奏参数/锚点 →【硬性规则】、对话模式 →【对话风格】映射正确 |
| 验收判定 | 构造卡 + 构造正文 → 违反报告正确（PASS/FAIL、逐条判定，含数值/占比/建模规则/软引导四类检查项） |
| 抽卡装配 | 违反报告正确装配进重写提示词；round 计数上限 3；超限取最优 |
| 场景卡 | 段落分类 → 聚合 → 场景卡 override 叠加主卡正确 |
| 双态共存 | 旧卡（未蒸馏）零改动可用（过校验 + 定性注入路径未删）；蒸馏卡结构合法 |
| init/sync | 旧模板 seed 不变（回归；保留在 test_platforms） |

LLM 输出的非确定性由「schema 校验 + 模板一致性」兜底，不依赖精确数值断言。

## 11. 验收标准（PRD 十，重定义）

1. ~~C1 工具计数 vs 人工计数 ≤15%~~ → **退休**
2. **C2' 生成验收**：同场景提示词生成正文，anti-ai 指令遵循验收 PASS 率 ≥ 90%（流程级）
3. **C3' 场景区分**：战斗卡 vs 对话卡生成的正文，验收在差异维度显著区分
4. ~~C4 5 章置信度 ≥70~~ → 由卡冻结模型取代（卡不再随归档更新）
5. **C5 双态共存**：未蒸馏项目零改动可用（旧卡过校验 + 定性注入不变）；蒸馏升级无报错
6. **C6 作者盲测（主验收）**：三套标杆卡（或作者真实样本），作者盲测生成文风像不像原作者，正确率 ≥ 70%

## 12. 实施顺序

1. **Phase 1**：13 模板方法论（feature-extract 模板，含蒸馏卡 schema 定义）+ style-distiller 三阶段产卡（主卡 + 场景卡 + 分析稿）+ 双态卡 schema 校验（旧模板 + 蒸馏卡都过）
2. **Phase 2**：prompt-crafter 双态渲染（confidence=0 定性分支保留；confidence>0 走 rendering-rules 案例 2）+ 枚举映射表
3. **Phase 3**：anti-ai 验收（双态，按 prompt 实际注入内容）+ 违反报告 + 抽卡闭环（novel-agent 调度）
4. **Phase 4**：退役清理（distill/compare/mix/jieba/增量/题材基线/injection-template）+ 测试重写 + CI 更新
5. **Phase 5**：双态共存回归（旧卡零改动可用 + 蒸馏升级无报错）+ 全量回归 + C6 作者盲测

## 13. 风险与应对

| 风险 | 应对 |
|------|------|
| LLM 提取噪声 | 客观字段定义写死在模板；容差在渲染层（区间化）；验收为指令遵循判定 |
| LLM 自造枚举值 | 模板封闭枚举集合 + schema 校验兜底 |
| 验收误判 | 验收用与生成同一份提示词（同源）；违反报告逐条可人工复核 |
| 抽卡不收敛 | round ≤3 + 超限取最优 + 报告留人工裁决 |
| 声音层信息丢失 | 硬约束/软引导/few-shot 原样透传，渲染不压缩 |
| 成本 | 模板 1-4 拆解全量标注 token 大 → 定为 LLM 内部推理不落盘；量化/建模各 1 次调用；抽卡 ≤3 |
