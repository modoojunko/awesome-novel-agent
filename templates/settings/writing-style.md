---
profile_version: "1.0"
scene_type: general
source_sample_length: 0
confidence: 0
last_updated: ""
locked: []

# 9 大维度（PRD 定义；0/空 = 未蒸馏，首次蒸馏后由 style-distiller 填充）
lexicon: { adj_density_per_100: 0, adv_density_per_100: 0, four_phrase_freq_per_100: 0, preferred_words: [], banned_words: [], name_pronoun_ratio: 0 }
syntax: { avg_sentence_length: 0, sentence_length_dist: {}, single_sentence_paragraph_pct: 0, avg_sentences_per_paragraph: 0, question_ratio: 0, exclamation_ratio: 0 }
rhythm: { dialogue_pct: 0, action_pct: 0, environment_pct: 0, inner_thought_pct: 0, narration_pct: 0 }
rhetoric: { metaphor_density_per_100: 0, metaphor_preference: "", sensory_dist: "" }
emotion_expression: { direct_pct: 0, action_physiology_pct: 0, environment_projection_pct: 0 }
narrative: { perspective: "", focal_character: "", inner_monologue_style: "" }
dialogue_style: { tag_style: "", avg_dialogue_length: 0, interrupt_freq_per_100: 0, subtext_ratio: 0 }
cohesion: { conjunction_freq_per_100: 0, transition_sentence_ratio: 0, paragraph_bridge_style: "" }
verb_style: { action_verb_ratio: 0, mental_verb_ratio: 0, state_verb_ratio: 0, strength: "" }
---

# 写作风格

## 叙事身份（原 role）

{role}

## 硬约束（原 core_principles）

- {principle_1}

## AI 易犯错误（原 possible_mistakes）

- {mistake_1}

## 描写层次和手法（原 depiction_techniques）

{depiction_techniques}

## few-shot 例句

- （蒸馏后由 style-distiller 填入标志性例句）
