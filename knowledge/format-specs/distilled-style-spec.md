# 蒸馏风格卡格式规范（distilled-style-spec）

风格卡分两种：主卡 `settings/writing-style.md`（scene_type: general，全局默认）与
场景卡 `settings/style-profiles/{scene_type}.md`（分场景差异）。两者共用同一 frontmatter schema。

## 一、frontmatter 量化层

必需字段：`profile_version`（"1.0"）、`scene_type`、`source_sample_length`（蒸馏样本总字数）、
`confidence`（0-100，0=手动设定/未蒸馏）、`last_updated`（YYYY-MM-DD）。
场景卡另有：`inherits`（继承主卡路径）、`override`（只写差异维度）、`locked`（手动锁定维度，F5 增量跳过）。

9 大维度（PRD 定义，键名唯一，不可改名）：

| 维度 | 字段 | 说明 |
|------|------|------|
| lexicon | adj_density_per_100 / adv_density_per_100 / four_phrase_freq_per_100 / preferred_words[] / banned_words[] / name_pronoun_ratio | 词法：脚本统计 |
| syntax | avg_sentence_length / sentence_length_dist{} / single_sentence_paragraph_pct / avg_sentences_per_paragraph / question_ratio / exclamation_ratio | 句法：脚本统计 |
| rhythm | dialogue_pct / action_pct / environment_pct / inner_thought_pct / narration_pct | 节奏占比：dialogue_pct 脚本统计，其余 LLM 估算 |
| rhetoric | metaphor_density_per_100 / metaphor_preference / sensory_dist | 修辞：LLM |
| emotion_expression | direct_pct / action_physiology_pct / environment_projection_pct | 情绪表达：LLM |
| narrative | perspective / focal_character / inner_monologue_style | 叙事：LLM |
| dialogue_style | tag_style / avg_dialogue_length / interrupt_freq_per_100 / subtext_ratio / direct_address_freq_per_100 | 对话：LLM |
| cohesion | conjunction_freq_per_100 / transition_sentence_ratio / paragraph_bridge_style | 衔接：前两项脚本，bridge LLM |
| verb_style | action_verb_ratio / mental_verb_ratio / state_verb_ratio / strength | 动词：前三项脚本，strength LLM |

## 二、正文定性层

主卡正文保留旧 4 字段映射（迁移零损失）：

| 旧字段 | 新位置 |
|--------|--------|
| role | 正文「叙事身份」节 |
| core_principles | 正文「硬约束」节（注入时视为红线级） |
| possible_mistakes | 正文「AI 易犯错误」节（与 banned_words 互补） |
| depiction_techniques | 正文「描写层次和手法」节（原样保留） |

正文另含 `few-shot 例句`：蒸馏选出的标志性例句（按场景类型分组）。

## 三、继承与合成

- 场景卡 `inherits` 指向主卡，`override` 只覆盖差异维度；prompt-crafter 读卡时合并 override（继承链解析放 Step 1 内，不引入新解析器）。
- 主卡兜底：某场景无场景卡时只用主卡。

## 四、置信度与容差

`confidence = min(100, 20 + min(40, sample_length/50) + min(40, chapter_count*5))`
容差档：0-20 手动 / 21-50 ±30% / 51-70 ±20% / 71-90 ±15% / 91-100 ±10%。
confidence=0 时量化层不注入，提示词只走定性层，直到首次蒸馏。

## 五、验收自检

1. frontmatter 含全部 9 大维度键，字段类型与 schema 一致
2. scene_type 在 6 类枚举内（主卡 general）
3. confidence 0-100 整数；locked 只含已定义维度键
4. 场景卡 inherits 指向存在的卡（主卡或其他场景卡）
5. 量化值以「约 X（±Y%）」表述注入，不写死
