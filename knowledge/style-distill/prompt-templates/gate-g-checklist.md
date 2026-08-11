# Gate G 风格偏差检查清单（anti-ai 用）

## 触发
Phase 1 扫描阶段，对每章正文跑 `python tools/distill-style.py check -c settings/writing-style.md <正文>`
（客观维度）。语义维度（rhetoric/emotion_expression/narrative/dialogue_style 等）由 anti-ai LLM 按风格卡估算对比。

## 分级
- **通过**：客观维度全在容差内，语义维度无明显偏离。
- **警告（作者确认）**：1-3 个客观维度 warn，或语义维度轻微偏离 → 列出，作者确认后放行。
- **不通过（局部重写建议）**：≥1 个客观维度 FAIL（偏差 > 2×容差）或语义维度显著偏离 → 建议对偏离段落局部重写（只改表达，不改剧情）。

## 报告行
风格偏差：X 处（维度：avg_sentence_length 偏差 +18% …；定级：警告/不通过）

## 豁免（读 boundary-cases Gate G 组）
- 特定场景类型刻意偏离（战斗场景短句、对话场景长对话）命中豁免列表 → SKIP
