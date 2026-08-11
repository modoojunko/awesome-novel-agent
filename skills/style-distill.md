# style-distill skill

## 一、三段式蒸馏（主卡，style-distill-order）

### 段 1：脚本统计（确定性）
- 收集样本：作者提供的参考文本（.md/.txt）或已归档章节。少于 1500 字时向 novel-agent 说明质量不足，可挂起。
- Bash 调：`python tools/distill-style.py distill -o .agent/task/partial.yml -e .agent/task/evidence.md <样本...>`
- 读 partial.yml + evidence.md：拿到客观维度（lexicon/syntax/rhythm.dialogue_pct/cohesion/verb_style）与 few-shot 候选。

### 段 2：LLM 语义标注
- 读 `.claude/knowledge/style-distill/prompt-templates/distill-prompt.md`，按模板补：rhetoric / emotion_expression / narrative / dialogue_style / rhythm 非对话占比 / verb_style.strength / cohesion.paragraph_bridge_style，以及 banned_words 定稿、preferred_words 去噪、few-shot 精选。
- 语义维度参考：样本原文 + 客观维度 + 既有卡（保留 locked 项）。

### 段 3：合并写卡 + 备份
- 合并客观 + 语义 → 按 distilled-style-spec 写 `settings/writing-style.md`（新 frontmatter + 定性层）。
- 更新前把旧版备份到 `settings/.style-versions/v{N}_{YYYY-MM-DD}.md`（N 取现有最大 +1）。
- confidence 重算（脚本段已给）。覆盖 body 的 few-shot 例句。

## 二、场景卡蒸馏（style-distill-order 内）
1. 对样本按段落判定场景类型（对话/战斗/环境/心理/过渡/群像）。
2. 每类聚合出子样本（≥800 字才蒸馏该卡；不足则跳过该场景卡）。
3. 对每类子样本跑 `distill-style.py distill` → 得该场景客观维度。
4. 与主卡对比：差异显著（相对差 > 容差）的维度写进 `settings/style-profiles/{scene_type}.md` 的 override，其余留空。
5. 定性节（描写层次/技法）由 LLM 按该场景样本提炼；few-shot 取该场景标志句。

## 二点五、题材基线（无样本 / 低 confidence 兜底 + 混风格素材）
- 三层：`settings/style-profiles/genre-baselines/{genre}/base.md`（题材基础卡，P1 数值由标杆作品样本蒸馏填充）、`delta.md`（与基础卡的题材偏移，frontmatter 带 `baseline_for: {genre}`，只写偏移维度）、`benchmark.md`（作者认可的标杆卡，盲测正确率 ≥70%）。
- 何时用：作者无样本 → 用 `settings/style-profiles/genre-baselines/{genre}/base.md` 兜底（confidence=0，见主卡）；增量更新缺语义 → 参照 `benchmark.md` 校准；混风格 → 把 `delta.md` 偏移叠加到目标主卡（mix-style 组合）。
- 不写入：基线卡只读素材，蒸馏结果落到主卡/场景卡，不覆盖 `genre-baselines/` 目录。

## 三、防重复 / 防冲突
- banned_words 与 `.claude/knowledge/anti-ai.md` 禁用词合并去重。
- 场景卡 override 不与主卡同维度并列（override 即覆盖）。
- locked 维度：任何蒸馏/增量都跳过。

## 四、验收自检
1. frontmatter 含 9 大维度键，类型符合 schema
2. confidence 0-100；容差档标注正确
3. banned_words 与 anti-ai 禁用词无重复
4. 备份文件存在；幂等：重复跑同一样本不产生多余备份（以当日版本为准）

## 五、增量蒸馏（style-update-order）
1. 读 order inputs（当前主卡 + 最新归档章节列表）。
2. Bash 调：`python tools/distill-style.py update -c settings/writing-style.md -o settings/writing-style.md --project . <归档章节...>`
   （update 内部做：客观维度滑动平均、locked 跳过、备份到 .style-versions、置信度重算、.agent/style-update/{card}.{chapter}.done 幂等。）
3. 语义档重估条件（满足任一）：confidence < 60 / 距上次语义重估 ≥5 章 / order 标注语义重估。此时按蒸馏 prompt 段 2 跑语义维度并写卡。
4. 增量只动量化数值，不碰正文定性层（与 updater 的 [writer-preference] 学习分工：updater 继续写 .claude/knowledge/writer-style.md，style-distiller 不动它）。
5. 高频定性条目若作者确认升华，才写进卡片 banned_words / hard_constraints。
