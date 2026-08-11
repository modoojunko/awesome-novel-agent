# 蒸馏 LLM 语义标注 Prompt（style-distiller 段 2 用）

你是文风标注器。基于样本原文与脚本客观维度，补齐风格卡 9 大维度中脚本算不出的部分。

## 输入
- 样本原文（若干段）
- 客观维度 partial（脚本输出）
- 既有卡（如有，保留 locked 项）

## 只补下列维度（脚本已算的不要重写）
- **rhetoric**：metaphor_density_per_100（每百字比喻数）、metaphor_preference（常用喻体类型，1 句）、sensory_dist（主要感官通道，1 句）
- **emotion_expression**：direct_pct（直接情绪词比例，估算）、action_physiology_pct（动作/生理描写比例）、environment_projection_pct（移情环境比例），三者合计约 100
- **narrative**：perspective（视角，1 词）、focal_character（聚焦角色）、inner_monologue_style（内心独白风格，1 句）
- **dialogue_style**：tag_style（"说"字风格/动作代替，1 句）、avg_dialogue_length（估字数）、interrupt_freq_per_100、subtext_ratio（潜台词比例）、direct_address_freq_per_100（称呼频率）
- **rhythm**：action_pct / environment_pct / inner_thought_pct / narration_pct（估算，与 dialogue_pct 合计约 100）
- **verb_style.strength**：动词力度（1-5）
- **cohesion.paragraph_bridge_style**：段间衔接方式（1 句）
- **lexicon.banned_words**：从 preferred_words 高频词里筛出"显得廉价/滥用"的词；**lexicon.preferred_words**：去噪保留 5-10 个
- **few-shot**：从样本挑 3-5 句标志性句子（短、有辨识度）

## 输出
按 distilled-style-spec 的 9 大维度结构输出补全后的 frontmatter YAML 片段（只含你补的字段），以及正文 few-shot 例句列表。数值给整数/一位小数，文字描述≤1 句。
