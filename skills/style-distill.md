# style-distill skill

## 一、三段式蒸馏（主卡，style-distill-order）

### 段 1：脚本统计（确定性）
- 收集样本：作者提供的参考文本（.md/.txt）或已归档章节。少于 1500 字时向 novel-agent 说明质量不足，可挂起。
- Bash 调：`python tools/distill-style.py distill -o .agent/task/partial.yml -e .agent/task/evidence.md <样本...>`
- 读 partial.yml + evidence.md：拿到客观维度（lexicon/syntax/rhythm.dialogue_pct/cohesion/verb_style）与 few-shot 候选。

### 段 2：LLM 语义标注
- 读 `knowledge/style-distill/prompt-templates/distill-prompt.md`，按模板补：rhetoric / emotion_expression / narrative / dialogue_style / rhythm 非对话占比 / verb_style.strength / cohesion.paragraph_bridge_style，以及 banned_words 定稿、preferred_words 去噪、few-shot 精选。
- 语义维度参考：样本原文 + 客观维度 + 既有卡（保留 locked 项）。

### 段 3：合并写卡 + 备份
- 合并客观 + 语义 → 按 distilled-style-spec 写 `settings/writing-style.md`（新 frontmatter + 定性层）。
- 更新前把旧版备份到 `settings/.style-versions/v{N}_{YYYY-MM-DD}.md`（N 取现有最大 +1）。
- confidence 重算（脚本段已给）。覆盖 body 的 few-shot 例句。

## 二、场景卡蒸馏（style-distill-order 内，可选）
- 按样本的段落场景类型归属（对话/战斗/环境/心理/过渡/群像），对每类子样本跑 distill → 差异维度写 `settings/style-profiles/{scene_type}.md`（override 只写该场景与主卡显著不同的维度，confidence 与 source_sample_length 用该子样本的值）。

## 三、防重复 / 防冲突
- banned_words 与 `.claude/knowledge/anti-ai.md` 禁用词合并去重。
- 场景卡 override 不与主卡同维度并列（override 即覆盖）。
- locked 维度：任何蒸馏/增量都跳过。

## 四、验收自检
1. frontmatter 含 9 大维度键，类型符合 schema
2. confidence 0-100；容差档标注正确
3. banned_words 与 anti-ai 禁用词无重复
4. 备份文件存在；幂等：重复跑同一样本不产生多余备份（以当日版本为准）
