# 案例 2 风格提示词渲染规格（prompt-crafter 已蒸馏态用）

## 适用范围（双态）
- 本规格仅用于**已蒸馏卡**（confidence>0）。未蒸馏态（confidence=0）由 prompt-crafting Step 1.1
  既有分支走正文定性四字段注入（现状不变，不读本文件）。

## 数据源
- 只读卡（settings/writing-style.md 主卡 + 按 scene_type 叠加 settings/style-profiles/{scene}.md override），
  **不读分析稿**（settings/style-profiles/analysis/）。
- 渲染规则本文自含（精确值见下），不依赖任何 tools/*.py（那些不部署到项目空间）。

## 精确渲染值（与 tools/style_render.py 对齐）

### 数值密度类区间（RANGE_TIERS）
按卡 confidence 定档，数值维度渲染为「每百字 L-U 个」：`L = round(X×(1−t))`，`U = round(X×(1+t))`
（四舍五入 half-up，非银行家舍入；U≤L 时渲染单值 `L`——如零值 →「0」，不虚构 0-1 区间）。

| confidence 档 | 容差 t |
|---------------|--------|
| ≥70 | ±10% |
| ≥50 | ±20% |
| <50（含 0） | ±30% |

### 占比类中文定性（pct_zh）
占比值 → 中文定性词：

| 占比 | 定性 |
|------|------|
| ≥80% | 绝大多数 |
| ≥60% | 大部分 |
| ≥40% | 近一半 |
| ≥20% | 一部分 |
| <20% | 少量 |

### 类别枚举 → 中文（ENUM_ZH）

| 键 | 值 | 渲染 |
|----|----|------|
| tag_style | pure_tags | 标签用'XX说'为主 |
| tag_style | mixed | 标签混合使用 |
| tag_style | no_tags | 不用标签，动作替代 |
| strength | weak | 动词力度轻 |
| strength | medium | 动词力度中等 |
| strength | strong | 动词力度烈 |
| paragraph_bridge_style | action | 段落靠动作衔接 |
| paragraph_bridge_style | dialogue | 靠对话衔接 |
| paragraph_bridge_style | transition | 少用过渡句 |
| inner_monologue_style | direct | 内心独白用引号直接呈现 |
| inner_monologue_style | indirect | 间接转述 |
| perspective | first_person | 第一人称 |
| perspective | second_person | 第二人称 |
| perspective | third_limited | 第三人称有限视角 |
| perspective | third_omniscient | 第三人称全知视角 |

### 场景稀疏注入矩阵（SCENE_INJECTION）
按本章 scene_type 只注入对应维度；未知 scene_type 兜底 general。

| scene_type | 注入维度 |
|------------|----------|
| general（兜底） | lexicon、syntax、rhythm、rhetoric、emotion_expression、narrative、dialogue_style、cohesion、verb_style |
| dialogue | lexicon、dialogue_style |
| fight | verb_style、syntax |
| environment | rhetoric、rhythm |
| inner-mono | emotion_expression、narrative |
| transition | cohesion、rhythm |
| group-scene | rhythm、dialogue_style |

### 分布类桶名中文
- 句长分布：short_le_8→短句（≤8字）、medium_9_20→中句（9-20字）、long_21_35→长句（21-35字）、xlong_gt_35→超长句（>35字）
- 喻体：weapon_metal→兵器金属、nature→自然、body→身体、abstract→抽象、other→其他
- 感官：visual→视觉、auditory→听觉、tactile→触觉、olfactory→嗅觉、gustatory→味觉
- 人名/代词：name→人名、he_she→他/她、i_you→我/你

## 渲染步骤
0. 回退守卫（§6.0b）：已蒸馏卡缺声音层（遗留 jieba 蒸馏卡，confidence>0 无 hard_constraints 等）→
   量化节照常渲染；声音层节【硬性规则】/【整体基调】/【风格参考例句】回退读卡正文定性四字段注入，
   逐键独立回退（缺哪个键回退哪个）：【硬性规则】←正文「硬约束」+「AI 易犯错误」小节条目、
   【整体基调】←正文「叙事身份」小节、【风格参考例句】←正文「描写层次和手法」小节示例。
1. 数值密度类（adj_density_per_100 等）：按 confidence 用 RANGE_TIERS 定区间 →「每百字 L-U 个」。
2. 占比类（dialogue_pct 等）：「约 X%（中文定性：近一半/大部分/…）」；缺键/未测/越界（<0 或 >100）
   → 不渲染该行（不伪造 0%）。
3. 分布类（sentence_length_dist / metaphor_preference / sensory_dist / name_pronoun_ratio）：
   逐桶「{中文桶名}占比 X%」。
4. 类别枚举：按 ENUM_ZH 映射为中文短语（如 mixed → 「对话标签混合使用」）。
5. 稀疏注入：按本章 scene_type 用 SCENE_INJECTION 只注入相关维度；主卡兜底 general。
6. 声音层透传：hard_constraints →「硬性规则」逐条不删改；soft_guidance →「整体基调」；
   few_shot_examples →「风格参考例句」按 type 分组。
7. 固定注入（**prompt-crafter 附加，非渲染节**）：在 11 个风格节外追加生成目标「严格匹配上述风格参数，
   偏差不超过 20%」+ 占位「剧情上下文」+「写作要求（直接写正文/字数）」。渲染模块（style_render.py）只产出
   下述 11 个风格节，不产出这两节。

## 输出结构（11 风格节 + 2 固定注入节 = 完整案例 2 提示词）

渲染模块产出（11 节）：
【词汇】【句式】【节奏】【修辞与感官】【情绪表达】【对话风格】【衔接】【视角】
【硬性规则】【整体基调】【风格参考例句】

prompt-crafter 固定注入（2 节）：
【剧情上下文】【写作要求】
