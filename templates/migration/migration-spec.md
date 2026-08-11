# 迁移规范 — 从 2.x 迁移到 4.0

> Agent 按此规范执行设定迁移。每份文件的字段映射表定义旧版字段 → 新版模板位置的对应关系。
> 验收标准：新版模板的每个必需字段都能在旧版中找到来源，迁移后内容完整。

## 字段状态标记

| 标记 | 含义 |
|------|------|
| ✅ 直接填 | 旧字段值可直接填入新位置 |
| 🔄 归纳 | Agent 读旧字段内容后归纳提炼填入新子字段 |
| ⚠️ 待推断 | 旧版无直接对应字段，Agent 从上下文推断 |
| ❌ 新增 | 旧版完全不存在，需作者补充 |

---

## §1 story.yaml → story.md

**旧路径：** `story.yaml`
**新路径：** `story.md`
**模板：** `templates/migration/story.md.template`

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| `# {title}` | `story.yaml → title` | ✅ 直接填 | 标题一致 |
| 元信息 → skill_version | — | ❌ 新增 | 写 `4.13.0` |
| 元信息 → 题材 | `writing-style.yaml → genre_profile` | ✅ 直接填 | 有值则填，无值标"待确认" |
| 元信息 → 标签 | 无直接字段 | ⚠️ 从 story.yaml 内容推断 | 允许空 |
| 元信息 → 状态 | — | ❌ 新增 | 写"写作中" |
| 引用路径表 → 世界观概要 | `story.yaml → world_setting.summary` | ✅ 直接填 | 非空 |
| 引用路径表 → 题材概要 | — | ❌ 新增 | 标"待确认" |
| 引用路径表 → 角色概要 | `story.yaml → characters.summary` | ✅ 直接填 | 非空 |
| 引用路径表 → 写作风格概要 | `story.yaml → writing_style.summary` | ✅ 直接填 | 非空 |
| 故事主线 → 结构类型 | 无直接字段 | ⚠️ 从 volumes 数量 + 内容推断 | 至少填一个 |
| 故事主线 → 总卷数 | `volumes/*.yaml` 文件数 | ✅ 直接填 | 数字正确 |
| 故事主线 → 全书核心冲突 | 各卷 `core_conflict` | 🔄 归纳各卷核心冲突为一句话 | 非空 |
| 分卷规划 → 卷N 标题 | `volume-{N}.yaml → title` | ✅ 直接填 | 每卷都有 |
| 分卷规划 → 卷N 弧线位置 | 无直接字段 | ⚠️ 从 `volume-{N}.yaml → summary` 推断 | 标"待确认" |
| 分卷规划 → 卷N 核心冲突 | `volume-{N}.yaml → core_conflict` | ✅ 直接填 | 每卷都有 |
| 分卷规划 → 卷N 预估章节 | `volume-{N}.yaml → chapters_summary` 数量 | ✅ 直接填 | 数字正确 |

### 验收

- `story.md` 标题行正确
- 元信息三字段至少题材有值
- 引用路径表 4 行全部非空（题材行标"待确认"）
- 故事主线段：结构类型 + 总卷数 + 核心冲突 三项齐全
- 分卷规划：卷数正确，每卷至少有标题和核心冲突
- 没有旧版 story.yaml 残留

---

## §2 world-setting.yaml → settings/world-setting.md

**旧路径：** `settings/world-setting.yaml`
**新路径：** `settings/world-setting.md`
**模板：** `templates/migration/world-setting.md.template`

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| 地理 → 主要场景 | `world-setting.yaml → details.geography` | 🔄 从整体描述中提取关键地名/场景 | 至少有 1 个主要场景 |
| 地理 → 气候 | `world-setting.yaml → details.geography` | 🔄 从描述中提取气候特征 | 非空 |
| 地理 → 地理限制 | `world-setting.yaml → details.geography` | 🔄 从描述中提取地理限制（如交通/地形） | 非空 |
| 政治 → 统治形式 | `world-setting.yaml → details.politics` | 🔄 从描述中提取统治结构 | 非空 |
| 政治 → 主要势力 | `world-setting.yaml → details.politics` | 🔄 从描述中提取至少 2 个势力 | 至少 2 个 |
| 政治 → 社会分层 | `world-setting.yaml → details.politics` + `sociology` | 🔄 从描述中提取社会层级 | 非空 |
| 政治 → 不服从的代价 | `world-setting.yaml → details.politics` + `rules` | 🔄 从描述中提取 | 非空 |
| 规则 → 世界级 | `world-setting.yaml → details.rules` + `physics` + `biology` | 🔄 从底层物理/生物规则中提取 | 非空 |
| 规则 → 社会级 | `world-setting.yaml → details.rules` + `culture` + `sociology` | 🔄 从社会/文化规则中提取 | 非空 |
| 规则 → 个人级 | 旧版无此子字段 | ⚠️ 从其他段推断或标"待确认" | 标"待补充" |

**说明：** 新版模板比旧版更结构化（有子字段）。Agent 读旧版的自由文本段落，理解后按新版子字段分类填入。旧版 `culture`、`history`、`sociology` 等字段的内容分散到地理/政治/规则三节中。

### 验收

- 地理三子字段全部有实质内容
- 政治四子字段全部有实质内容
- 规则三子字段：世界级、社会级有内容，个人级允许空缺但标"待补充"
- 对比旧文件确认重要设定点没有丢失

---

## §3 writing-style.yaml → settings/writing-style.md

**旧路径：** `settings/writing-style.yaml`
**新路径：** `settings/writing-style.md`
**模板：** `templates/migration/writing-style.md.template`

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| `## role` | `writing-style.yaml → role` | ✅ 直接填 | 非空 |
| `## role`（合并 personality） | `writing-style.yaml → personality` | 🔄 合并到 role 段末尾 | 非空 |
| `## core_principles` | `writing-style.yaml → core_principles.*` | 🔄 所有子字段合并为一个列表 | 非空，无重复 |
| `## possible_mistakes` | `writing-style.yaml → possible_mistakes` | ✅ 直接填 | 非空 |
| `## depiction_techniques` | `writing-style.yaml → depiction_techniques` | ✅ 直接填 | 非空 |

**说明：** 新版使用 markdown 格式（非 YAML）。旧版 `core_principles` 的 5 个子字段（global_rules / natural_expression / description_vs_depiction / character_building / pov_consistency）合并为一个列表写入 `## core_principles`。`personality` 合并到 `## role` 段末尾。`genre_profile` → 写入 §8 genre-setting.md。`workflow` / `writing_model` → 新版无对应位置，迁移时跳过。

### 验收

- ## role 段已合并 personality，内容非空
- ## core_principles 包含旧版所有子字段的内容
- ## possible_mistakes 完整迁移
- ## depiction_techniques 完整迁移
- 与旧文件对比确认无遗漏

---

## §4 anti-ai.yaml → settings/anti-ai.md

**旧路径：** `settings/anti-ai.yaml`
**新路径：** `settings/anti-ai.md`
**模板：** `templates/migration/anti-ai.md.template`

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| 疲劳词 → 副词类 | `anti-ai.yaml → fatigue_words_zh` 中副词类词 + `fatigue_words_en` | ✅ 直接填 | 至少有收录 |
| 疲劳词 → 动词类 | `anti-ai.yaml → fatigue_words_zh` 中动词类 | ✅ 直接填 | 非空 |
| 疲劳词 → 形容词类 | `anti-ai.yaml → fatigue_words_zh` 中形容词类 | ✅ 直接填 | 非空 |
| 疲劳词 → 连接词类 | `anti-ai.yaml → fatigue_words_zh` 中连接词类 | ✅ 直接填 | 非空 |
| 疲劳词 → 身体反应模板 | `anti-ai.yaml → fatigue_words_zh` 中 cliche_action/cliche_environment | ✅ 直接填 | 非空 |
| 句式规则 | `anti-ai.yaml` + `tic-patterns.yaml` | ✅ 直接填 | 引用路径正确 |
| 改写算法 → 感知词移除 | `anti-ai.yaml` 感知词相关规则 | 🔄 Agent 归纳旧版规则 | 非空 |
| 改写算法 → "了"字净化 | `anti-ai.yaml` 中"了"相关规则 | 🔄 Agent 归纳旧版规则 | 非空 |

**说明：** 新版分类更清晰，旧版分 `fatigue_words_zh` 的子类别按新版类别填入。

### 验收

- 疲劳词各分类有实质内容
- 句式规则引用路径正确
- 改写算法有具体描述

---

## §5 hooks.yaml → settings/foreshadowing.md

**旧路径：** `settings/hooks.yaml`
**新路径：** `settings/foreshadowing.md`
**模板：** `templates/migration/foreshadowing.md.template`

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| 活跃伏笔表 | `hooks.yaml → hooks[]` 中 `status=pending/mentioned` | 🔄 提取为表格行：description→伏笔, introduced_in→引入章, payoff_timing→预期收束, last_mentioned_chapter→最近提及 | 旧版中所有未收束钩子都出现 |
| 已收束伏笔表 | `hooks.yaml → hooks[]` 中 `status=resolved` | 🔄 提取为表格行：description→伏笔, introduced_in→引入章, resolution_chapter→收束章 | 旧版中所有已收束钩子都出现 |
| 废弃伏笔表 | `hooks.yaml → hooks[]` 中 `status=abandoned` | 🔄 提取为表格行 | 旧版中所有废弃钩子都出现 |

**说明：** 旧版 hooks.yaml 有几十个详细字段（hook_type、priority、hook_strength 等），新版只保留核心摘要信息。详细元数据不在此维护——已分散到各章 chapter.md 的 memo 中。

### 验收

- 三张表覆盖旧版 hooks.yaml 中所有钩子，无一遗漏
- 活跃/已收束/废弃 分类与旧版一致
- 每条至少有描述和所在章节

---

## §6 character yaml → settings/character-setting/*.md

**旧路径：** `settings/character-setting/{id}.yaml`
**新路径：** `settings/character-setting/{id}.md`
**模板：** `templates/migration/character.md.template`

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| 基本信息 → id | 文件名（不含扩展名） | ✅ 直接填 | 非空 |
| 基本信息 → 名称 | `{character}.yaml → name` | ✅ 直接填 | 非空 |
| 基本信息 → 故事角色 | `{character}.yaml → story_role` | ✅ 直接填 | 非空 |
| 基本信息 → 外貌 | `{character}.yaml → appearance` | ✅ 直接填 | 非空 |
| 基本信息 → 背景 | `{character}.yaml → background` + `summary` + `age` + `occupation` | 🔄 合并多个字段 | 非空 |
| 基本信息 → 语言特征 | 旧版无此字段 | ❌ 新增 | 标"待补充" |
| 务虚层 → 世界观 | `{character}.yaml → cognition.l1_worldview` | ✅ 直接填 | 非空 |
| 务虚层 → 自我定位 | `{character}.yaml → cognition.l2_self_identity` | ✅ 直接填 | 非空 |
| 务虚层 → 价值观 | `{character}.yaml → cognition.l3_values` | ✅ 直接填 | 非空 |
| 务实层 → 能力 | `{character}.yaml → cognition.l4_core_abilities` | ✅ 直接填 | 非空 |
| 务实层 → 技能 | `{character}.yaml → cognition.l5_skills` | ✅ 直接填 | 非空 |
| 务实层 → 环境 | `{character}.yaml → cognition.l6_environment` | ✅ 直接填 | 非空 |
| 关系 | `{character}.yaml → relationships` | 🔄 逐条格式转换 | 原有关系统计正确 |
| 状态历史 | `{character}.yaml → state_history` | ✅ 直接填 | 非空（已有历史的话） |
| 情绪弧线 | 旧版无此字段 | ❌ 新增 | 标"待补充" |

### 验收

- 每个旧角色 yaml 对应一个新角色 md，数量一致，无一遗漏
- 认知 6 层模型完整迁移（旧版有 6 个字段，新版 6 个位置）
- 关系逐条转换完毕
- 背景已合并旧版多个字段
- 语言特征和情绪弧线标"待补充"

---

## §7 volume yaml → volumes/volume-{N}.md

**旧路径：** `volumes/volume-{N}.yaml`
**新路径：** `volumes/volume-{N}.md`
**模板：** `templates/migration/volume.md.template`

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| `# 卷 {N}：{标题}` | `volume-{N}.yaml → title` | ✅ 直接填 | 非空 |
| 核心冲突 | `volume-{N}.yaml → core_conflict` | ✅ 直接填 | 非空 |
| 预估章节 | `volume-{N}.yaml → chapters_summary` 数量 | ✅ 直接填 | 数字正确 |
| 章节列表 → 各章标题 | `volume-{N}.yaml → chapters_summary[].title` | ✅ 直接填 | 每章都有 |
| 章节列表 → 冲突事件 | `volume-{N}.yaml → chapters_summary[].summary` | ✅ 直接填 | 每章都有 |

**说明：** 旧版 `summary` 和 `main_events` 字段无新模板的直接位置，Agent 可将其核心内容融入卷的引言段落。

### 验收

- 卷数与旧版一致
- 每卷核心冲突完整迁移
- 章节列表条数与旧版 chapters_summary 一致
- 未标注"待补充"

---

## §8 genre-setting.md（新建）

**旧版无此文件。** 旧版 `writing-style.yaml` 的 `genre_profile` 字段记录了题材 ID。

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| 选定类型 | `writing-style.yaml → genre_profile` | ✅ 直接填 | 有值则填，无值标"待确认" |
| 满足类型 | 旧版无此字段 | ⚠️ 从 genre-example 库提取 | 标"待确认" |
| 节奏规则 | 旧版无此字段 | ⚠️ 从 genre-example 库提取 | 标"待确认" |
| 避免套路 | 旧版无此字段 | ⚠️ 从 genre-example 库提取 | 标"待确认" |
| 类型禁忌 | 旧版无此字段 | ⚠️ 从 genre-example 库提取 | 标"待确认" |

**说明：** 此文件是 3.0 新增的。如果旧版有 `genre_profile`，Agent 从 `knowledge/genre-example/` 下对应类型的配置预填；如果无，全部标"待讨论"。

---

## §9 chapter yaml → chapters/vol-{N}-ch-{M}.md（仅 archived）

**旧路径：** `chapters/vol-{N}-ch-{M}.yaml`（仅 `status: archived`）
**新路径：** `chapters/vol-{N}-ch-{M}.md`
**模板：** `templates/migration/chapter.md.template`

### 字段映射

| 新模板位置 | 旧版来源 | 迁移方式 | 验收 |
|-----------|---------|---------|------|
| `# 卷{N}第{M}章：{标题}` | `volume` + `chapter` + `title` | ✅ 直接填 | 非空 |
| 状态 | `status` | ✅ 直接填 | `archived` |
| 大纲 → 概要 | `outline.summary` | ✅ 直接填 | 非空 |
| 大纲 → 关键点 | `outline.key_points` | ✅ 直接填 | 非空 |
| 大纲 → 出场角色 | `outline.characters` | ✅ 直接填 | 非空 |
| 大纲 → 场景地点 | `outline.location` | ✅ 直接填 | 非空 |
| 大纲 → 时间 | `outline.time` | ✅ 直接填 | 非空 |
| Memo → 当前任务 | `memo.current_task` | ✅ 直接填 | 非空 |
| Memo → 读者期待 → 情绪状态 | `memo.reader_expectation.state` | ✅ 直接填 | 非空 |
| Memo → 读者期待 → 策略 | `memo.reader_expectation.strategy` | ✅ 直接填 | 非空 |
| Memo → 读者期待 → 具体说明 | `memo.reader_expectation.detail` | ✅ 直接填 | 非空 |
| Memo → 兑现计划 → 必须了结 | `memo.payoff_plan.must_resolve` | ✅ 直接填 | 非空 |
| Memo → 兑现计划 → 必须压住 | `memo.payoff_plan.must_hold` | ✅ 直接填 | 非空 |
| Memo → 兑现计划 → 推进不收束 | `memo.payoff_plan.partial_advance` | ✅ 直接填 | 非空 |
| Memo → 过渡功能 | `memo.downtime_functions` | ✅ 直接填 | 非空 |
| Memo → 关键抉择 | `memo.key_choices` | ✅ 直接填 | 非空 |
| Memo → 角色信息状态 | 旧版无此子节 | ❌ 新增 | 标"待补充" |
| Memo → 章尾改变 | `memo.required_changes` | ✅ 直接填 | 非空 |
| Memo → 硬约束 | `memo.prohibitions` | ✅ 直接填 | 非空 |
| 情绪设计 → 主情绪 | `emotional_design.primary_mood` | ✅ 直接填 | 非空 |
| 情绪设计 → 情绪走向 | `emotional_design.mood_progression` | ✅ 直接填 | 非空 |
| 情绪设计 → 强度峰值 | `emotional_design.intensity_peak` | ✅ 直接填 | 非空 |
| 情绪设计 → 强度等级 | `emotional_design.intensity_level` | ✅ 直接填 | 非空 |
| 情绪设计 → 情绪钩子 | `emotional_design.emotional_hook` | ✅ 直接填 | 非空 |
| 情绪设计 → 读者获得 | `emotional_design.satisfaction_beat` + `micro_payoffs` | 🔄 从两种信息归纳 | 非空 |

### 迁移说明

**narrative_pov / narrative_style：** 旧版章节 YAML 根层级可能有此字段（如 `narrative_pov: "林默第三人称有限视角"`），新版 chapter.md 模板无独立位置。Agent 将其内容写入 Memo → 当前任务的末尾，标记为 `[视角]`。

**segments 段：** 旧版部分章节有 `segments:` 段级拆分——新版已弃用，段级拆分转移到提示词层。迁移时跳过。

**cycle_position / suppression_stack：** InkOS 特有的情绪周期字段，新版不存在。迁移时跳过。

**prompt_path / prompt_variant / archive_path：** 旧版章节文件的元数据字段，新版通过命名约定管理文件间关系。迁移时跳过。

### 验收

- 所有 archived 章节都已迁移，无一遗漏
- ✅ 标记的字段全部有内容
- ❌ 标记的字段标"待补充"
- 总章节数与旧版一致
- 被跳过的 non-archived 章节在汇报中列出

---

## §10 timeline 文件（新建）

**旧版无此文件。** 时间线由 updater 在归档时自动追加，迁移时只需创建空文件。

**模板：** `templates/migration/timeline.md.template`

### 验收

- `settings/timeline.md` 存在，表头正确

---

## 总体验收清单

执行完所有迁移步骤后，Agent 逐项检查：

### 结构验收

- [ ] `story.md` 存在，元信息已填充
- [ ] `settings/world-setting.md` 存在
- [ ] `settings/writing-style.md` 存在
- [ ] `settings/genre-setting.md` 存在
- [ ] `settings/anti-ai.md` 存在
- [ ] `settings/foreshadowing.md` 存在
- [ ] `settings/timeline.md` 存在
- [ ] `settings/character-setting/` 下角色文件与旧版一致
- [ ] `volumes/volume-{N}.md` 卷数与旧版一致
- [ ] `chapters/` 下已归档章节全部迁移
- [ ] `archives/` 正文完整复制
- [ ] `prompts/` 提示词完整复制
- [ ] 旧 `.yaml` 已移入 `old/`，无残留
- [ ] 废弃文件（author-intent.md, current-focus.md, drafts/ 等）已清理

### 字段完整性验收

对每个迁移过的文件，按其 § 节验收条件逐项检查：

- [ ] ✅ 标记字段 → 全部有内容
- [ ] 🔄 标记字段 → Agent 归纳的内容合理、不丢信息
- [ ] ⚠️ 标记字段 → 已标记"待确认"或"待推断"
- [ ] ❌ 标记字段 → 已标"待补充"

### 升级后记

> 完成迁移后，`old/` 目录保留旧文件。确认无误可手动 `rm -rf old/` 删除。
> 标记为"待讨论""待确认""待补充"的字段，在后续创作中逐步完善。
