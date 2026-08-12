# 案例 2 风格提示词渲染规格（prompt-crafter 已蒸馏态用）

## 适用范围（双态）
- 本规格仅用于**已蒸馏卡**（confidence>0）。未蒸馏态（confidence=0）由 prompt-crafting Step 1.1
  既有分支走正文定性四字段注入（现状不变，不读本文件）。

## 数据源
- 只读卡（settings/writing-style.md 主卡 + 按 scene_type 叠加 settings/style-profiles/{scene}.md override），
  **不读分析稿**（settings/style-profiles/analysis/）。
- 区间/枚举/注入矩阵规则：`tools/style_render.py`（读其 RANGE_TIERS / ENUM_ZH / SCENE_INJECTION 常量）。

## 渲染步骤
0. 回退守卫（§6.0b）：已蒸馏卡缺声音层（遗留 jieba 蒸馏卡，confidence>0 无 hard_constraints 等）→
   量化节照常渲染；声音层节【硬性规则】/【整体基调】/【风格参考例句】回退读卡正文定性四字段
   （叙事身份/硬约束/AI易犯错误/描写层次）注入，其中【风格参考例句】以正文的描写层次示例充当。
1. 数值密度类（adj_density_per_100 等）：按 confidence 用 RANGE_TIERS 定区间 →「每百字 L-U 个」。
2. 占比类（dialogue_pct 等）：「约 X%（中文定性：近一半/大部分/…）」。
3. 分布类（sentence_length_dist / metaphor_preference / sensory_dist / name_pronoun_ratio）：
   逐桶「{中文桶名}占比 X%」。
4. 类别枚举：按 ENUM_ZH 映射为中文短语（如 mixed → 「对话标签混合使用」）。
5. 稀疏注入：按本章 scene_type 用 SCENE_INJECTION 只注入相关维度；主卡兜底 general。
6. 声音层透传：hard_constraints →「硬性规则」逐条不删改；soft_guidance →「整体基调」；
   few_shot_examples →「风格参考例句」按 type 分组。
7. 固定注入：生成目标「严格匹配上述风格参数，偏差不超过 20%」+ 占位「剧情上下文」+「写作要求（直接写正文/字数）」。

## 输出结构
【词汇】【句式】【节奏】【修辞与感官】【情绪表达】【对话风格】【衔接】【视角】
【硬性规则】【整体基调】【风格参考例句】【剧情上下文】【写作要求】
