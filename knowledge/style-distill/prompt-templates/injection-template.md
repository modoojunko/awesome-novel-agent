# 写作风格约束块渲染模板（prompt-crafter 用）

## 何时注入
- confidence=0 → 本块不注入（只走正文定性层注入）。
- 主卡兜底：本章每个场景类型查 `settings/style-profiles/{scene_type}.md`，有则合成（主卡数值被场景卡 override 覆盖），无则只用主卡。

## 渲染规则
1. 数值一律「约 X（±Y%）」——Y 按主卡 confidence 容差档：21-50→30 / 51-70→20 / 71-90→15 / 91-100→10。
2. 按场景类型稀疏注入（本章无该场景的维度不注入）：

| 场景类型 | 重点注入 | 不注入 |
|---------|---------|--------|
| dialogue | dialogue_style + dialogue_pct + lexicon | verb_style、environment_pct |
| fight | verb_style + syntax（短句）+ rhythm.action_pct | subtext_ratio、sensory_dist |
| environment | rhetoric.sensory_dist + rhythm.environment_pct | interrupt_freq |
| inner-mono | emotion_expression + narrative.inner_monologue_style | dialogue_style |
| transition | cohesion + rhythm | rhetoric |
| group-scene | rhythm + dialogue_style | verb_style |

3. 红线级（置于约束红线区，任何压缩不得删改）：卡内 banned_words、硬约束节。
4. few-shot：每场景类型 1-2 句标志性例句（无则省略）。

## 输出块示例
```
【写作风格约束】（本场景：dialogue）
- 对话占比约 40%（±20%）；对话多短句，平均约 12 字（±20%）
- 对话标签以动作代替为主，禁用"说"字赘述
- banned_words：{…}（红线，不得出现）
- few-shot：{例句 1}；{例句 2}
```
