# updater-archive-sop

归档时 lore-keeping 的标准操作流程。

## 一、输入检查

| 检查项 | 通过条件 | 失败处理 |
|--------|---------|---------|
| `.agent/task/archive-order.md` | 存在, 含 vol/chapter 号 | 报错给 novel-agent |
| `.agent/{chapter}-draft-ai.md` | 存在，或可从 `archives/*.draft.md` 创建 | 缺失 → 复制草稿创建（主路径，见 Step 1 ①） |
| `archives/vol-{N}-ch-{M}*`（`.md`/`.anti-ai.md`/`.draft.md` 任一） | 存在 | 报缺少正文；定稿 `.md` 由 Step 1 生成 |
| `settings/character-setting/` | 可读写 | 不存在则创建目录 |
| `settings/timeline.md` | 可读写 | 不存在则创建文件 |
| `.agent/status.md` | 存在 | 报错给 novel-agent |

## 二、归档前检查

| 检查项 | 操作 |
|--------|------|
| 正文草稿存在？ | `archives/vol-{N}-ch-{M}-*.draft.md` 存在？缺失→**STOP**，正文尚未生成 |
| chapter.md 完整？ | memo + emotional_design 有值？缺失→返回补章纲 |
| chapter.md#status 为 outline？ | 归档成功后改为 archived（见 Step 1 末尾）；已是 archived → 说明重复归档，进幂等模式 |
| `.agent/archiving/{chapter}.done` 存在？ | **存在 → 本章已归档过，进入幂等模式：跳过已完成步骤，只补缺失项**（见下"幂等规则"） |

### 幂等规则（防重放重复）

归档所有步骤都是**追加型**操作。如果本章曾归档到一半被中断，重派时必须先查重，不能整段重放：

| 追加目标 | 查重锚点 | 命中则 |
|---------|---------|--------|
| 角色状态 `settings/character-setting/{id}.md` | 已含 `## vol-{N}-ch-{M} 状态变更` | 跳过该角色 |
| 剧情履历 | 已含 `#### 第 {N} 卷第 {M} 章` | 跳过 |
| 情绪弧线 | 已含 `#### 第 {N} 卷第 {M} 章` | 跳过 |
| timeline `settings/timeline.md` | 已含 `vol-{N}-ch-{M}` 行 | 跳过 |
| 生物检测 world-setting | 已含该生物 | 跳过 |
| 记忆合并 writing-memory / chapter-memory | 已含同"原文+结论"条目 | 跳过 |
| 反 AI 规则 / 文风偏好 | 已含 `[writer-preference]` 同规则 | 跳过 |

全部步骤完成后写 `.agent/archiving/{chapter}.done`；已存在则说明归档完整，直接标记 order DONE。

## 三、存档流程

### Step 1: 正文定稿（定稿 = Write 生成 `archives/vol-{N}-ch-{M}-{slug}.md`；不重命名、不删除——S2 禁删）

1. **创建 AI 原版快照（主路径，updater 负责）**：若 `.agent/{chapter}-draft-ai.md` 不存在，从当前草稿
   `archives/vol-{N}-ch-{M}-*.draft.md` 复制一份作为 AI 原版快照（diff 基线）。快照创建必须先于任何
   diff/定稿动作。快照与保留的 `.draft.md` 职责不同：**快照 = 审计基线（此后不改）；`.draft.md` = 历史稿留档（可偏离基线）**
2. **判定并生成定稿**：只回答"哪个是最终内容"。任何分支都保留 `.draft.md` / `.anti-ai.md`，不删不改：
   - **`.md` 已存在**（此前归档已生成）：
     - 与 `.draft.md` / `.anti-ai.md` 内容一致 → `.md` 即定稿，跳过（幂等）
     - 与任一保留稿不一致（作者归档后重写过）→ **STOP**，将差异展示给作者确认：
       用新稿 Write 覆盖 `.md`，或维持旧 `.md`。不自动覆盖
   - **`.md` 不存在，`.anti-ai.md` 存在** → Write 其内容到定稿：`archives/vol-{N}-ch-{M}-{slug}.md`
   - **`.md` 不存在，仅 `.draft.md`** → Write 其内容到定稿：`archives/vol-{N}-ch-{M}-{slug}.md`
   - **正文不存在（`.md`/`.anti-ai.md`/`.draft.md` 均无）** → STOP 报错给 novel-agent
3. **复核**：定稿 `.md` 存在且非空；中间稿保留未删。归档后所有正文读取（diff、reader 回看、跨章一致性）
   一律以 `.md` 为权威，其他后缀为中间稿
4. **标记章纲已归档**：用 Edit 将 `chapters/vol-{N}-ch-{M}.md` 的 `status` 字段从 `outline` 改为 `archived`（只改该字段，不碰章纲正文）。此标记是 Step 10 卷边界检测的判断依据

### Step 2: 角色状态更新 + 情绪弧线

1. 读正文，提取本幕出场角色
2. 对每个出场角色：
   - 如果已有角色文件 → 追加本幕状态变化
   - 如果新角色（正文出现了但无设定文件）→ 创建角色文件，标注 `[auto-extracted]`
3. 追加状态历史格式：
   ```markdown
   ## vol-{N}-ch-{M} 状态变更
   - **位置:** 角色当前位置
   - **状态:** 角色当前状态简述
   - **人际关系变化:** xxx
   - **能力/状态变化:** xxx
   - **本幕关键台词/行为:** "..."
   ```
4. 追加剧情履历（跟在状态历史后面）：
   ```markdown
   ### 剧情履历
   #### 第 {N} 卷第 {M} 章
   - **行为:** {角色本幕实际做的事——击杀/选择/拯救/背叛等，含对象和结果}
   - **关系变化:** {与谁的关系发生了什么性质变化，无则空}
   ```
5. 追记情绪弧线（跟在剧情履历后面）：
   ```markdown
   ### 情绪弧线
   #### 第 {N} 卷第 {M} 章
   - **情绪状态:** 愤怒/压抑/释然/期待/恐惧/温情/决心
   - **触发事件:** 触发事件描述
   - **强度:** 7/10
   - **弧线方向:** 上升/回落/持平/转折
   - **表达方式:** 身体反应/行为/对话/环境互动
   ```

### Step 2.5: 生物/怪物检测

1. 读正文，提取本章出现或提及的动物、怪物、生物
2. 与 `settings/world-setting.md` 的「生物与怪物」节对比
3. 如发现不在列表中的生物 → 展示给作者确认：
   > "本章出现了【怪物名】，不在 world-setting.md 的生物列表中。要加进去吗？"
4. 作者确认 → 追加到 world-setting.md 的生物列表

### Step 3: timeline 追加

1. 提取本章关键事件（改变局势、角色认知、关系变化等）
2. 追加到 `settings/timeline.md`：
   ```markdown
   | 章节 | 事件 | 影响 |
   |------|------|------|
   | vol-{N}-ch-{M} | {一句话事件} | {对后续的影响} |
   ```

### Step 4: 持有物/经历更新

按需执行（正文中角色的持有物、财产、关键经历有实质变化才更新，无则跳过）：
- 角色持有物变化（获得/失去重要物品）→ 追加到对应 `settings/character-setting/{id}.md` 的状态历史
- 角色关键经历变化（身份/职业/立场变更）→ 同上
- 无变化 → 跳过本步（验收清单"持有物/经历已更新"勾选"无变化跳过"）

### Step 5: 正文一致性检查（L2 合规）

归档时对最终正文做内容合规验证：

1. **设定合规**
   - 世界观一致（无矛盾）
   - 无 OOC（角色行为符合设定）
   - 无题材禁忌内容
   - 与前文连续性无断裂

2. **章纲兑现**
   - required_changes 每条是否在正文中发生
   - payoff 是否兑现
   - prohibitions 是否遵守

3. **钩子兑现**
   - 新埋钩子有 seed_text 可提取
   - 收束钩子有明确段落
   - 钩子分量与 payoff_plan 一致

如有违规 → 标注到 status.md 供作者下次修正，不阻断归档。

### Step 6: 写作反馈收集

先问作者（或从对话中提取）：

> "这次写这一章，你有没有什么写作上的要求、修改习惯，或者发现章纲没考虑到的地方？分几类说就行。"

引导作者回顾三类反馈：

1. **写作要求** — 你对文风、节奏、描写、对话的具体偏好（"对话太啰嗦了""动作描写不够细"）
2. **反 AI 修改** — 你改掉了哪些 AI 味的表达（疲劳词、句式模板、元叙事）
3. **章纲遗漏** — 实际写作时发现章纲没覆盖到的内容或方向偏差

反馈来源（三路，**合并**而非互斥）：
- **作者直接反馈**（上面对话）— 优先，有则收录
- **reader 评审留档**：若 `.agent/review/vol-{N}-ch-{M}.md` 存在，读入并把可沉淀点并入三类（reader 不分类，分类由 updater 在此步完成）— 与作者反馈**并存**，都应收录
- **AI 快照 vs 定稿 diff**：始终执行，从 diff 自动提取作者改掉的 AI 味表达（无论作者是否反馈）。与作者反馈、reader 留档三路合并，去重后写入记忆——记录不依赖"作者在场回答"

三类反馈合并前展示给作者确认分类（与 Step 7 的确认门禁复用）。

### Step 6.5: AI 味等级记录

在写作反馈之后，记录本章的反 AI 质量数据供后续趋势追踪：

```markdown
## AI 味等级记录
- **等级:** 轻/中/重
- **禁用词密度:** X 次/千字
- **排比段落数:** X 段
- **心理词占比:** X%
- **对话标签密度:** X%
- **平均段落句数:** X 句
- **重复描写密度:** X 次/千字
- **原文字数:** XXXX
- **修改后字数:** XXXX（增减 ±X%）
```

数据来源：读 `.agent/review/vol-{N}-ch-{M}.md`（reader 评审留档）的终局判决与 AI 味维度，或从 anti-ai.md 的 Phase 4 报告提取。如两者都无，则跳过不自行计算。

### Step 7: 动态记忆合并（分类写入）

将 Step 6 收集的反馈分三类处理：

**① 写作要求** → 追加到 `.claude/memory/writing-memory.md`
```markdown
- **原文:** {作者原话关键词}
- **结论:** {可操作的写作指引}
- **场景:** {什么情境下适用}
- **use_count:** 1
```

**② 反 AI 修改** → 语义合并到 `.claude/knowledge/anti-ai.md`
- 读取 AI 快照 vs 最终正文，提取修改模式
- 与已有规则做语义合并：
  - 完全相同 → 跳过
  - 语义重复 → 合并为一条，保留更优表述
  - 场景重叠 → 扩展已有条目的场景范围
  - 冲突 → STOP，展示给作者确认
- 追加内容标注 `[writer-preference]`

**③ 章纲遗漏** → 追加到 `.claude/memory/chapter-memory.md`
```markdown
- **原文:** {作者原话或 diff 发现的遗漏}
- **结论:** {下次章纲要注意什么}
- **场景:** {适用环节}
- **use_count:** 1
```

合并前展示给作者确认分类是否准确。

### Step 7.5: 报告学习结果

输出本次记忆合并摘要：
- ✏️ 写作要求：新增 N 条
- 🤖 反 AI 规则：新增 N 条 / 合并 M 条 / 跳过 N 条
- 📋 章纲遗漏：记录 N 条

### Step 8: Hooks 健康检查 + 伏笔台账维护

归档本章后：

1. **更新 `settings/foreshadowing.md`（全局伏笔台账）**：读本章 `chapters/vol-{N}-ch-{M}.md#payoff_plan` 的钩子操作，追加/更新台账——
   - **台账不存在（升级/既有项目兜底）→ 先 Write 创建**：参照 `templates/settings/foreshadowing.md` 结构生成空台账（「未收束钩子」「已收束钩子」两表 + 头部说明），再按本章内容填充。updater 的 Write 白名单含 `settings/foreshadowing.md` 创建权限
   - 本章新埋的钩子 → 加入「未收束钩子」表（埋设位置 = 本章）
   - 本章收束的钩子 → 从「未收束」移到「已收束」（记录收束位置与方式）
   - 已存在的钩子 → 更新「最近提及」为本章
   这是跨卷伏笔的权威记录（M2 原则：真相源，非派生缓存），volume-planner/chapter-planner/reader 都读它做跨卷检查
2. **健康检查**，对有钩子引用的角色执行：
   - 高优先级钩子是否超过 5 章未被提及
   - 普通钩子是否超过 3 章未被提及
   - 是否连续 weak 钩子超过 3 章
   - 是否每 5 章至少有 1 个 strong 钩子

如有异常 → 在 status.md 或对话中提示作者。

### Step 9: 停滞检测

检查最近 3 章是否有实质性推进：
- 核心冲突是否推进
- 角色关系是否变化
- 有无新信息/新悬念

连续 3 章无实质推进 → 提示作者"最近 3 章推进较缓，是否需要调整节奏？"

### Step 10: 卷边界检测

读 `chapters/` 目录，筛选当前卷的章节文件，按 `status: archived` 标记判断完成度（Step 1 ④ 写入）：
- 未全部完成 → 更新 status.md，`current_chapter` 前移
- 全部完成 → **只输出卷完成报告**（不写 `last_volume_completed`、不写 `current_phase`——完成位由 novel-agent 裁决，见 novel-agent THINK）：

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  卷 {N} 《{title}》全部 {M} 章已完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

已归档章节：{逐章列出}

下一步选项：
1. 规划卷 {N+1}
2. 回顾整卷
3. 修改某章
```

### Step 11: Status 推进 + 清理

- 更新 `.agent/status.md`：phase→`archive`, current_step→`archiving`, last_archived→当前章号
- **保留** `.agent/{chapter}-draft-ai.md`（AI 原版快照审计留档；不删除——S2 禁删，靠 `.done` 标记区分过期）
- 写 `.agent/archiving/{chapter}.done` 完成标记（幂等 checkpoint）
- 将 `.agent/task/archive-order.md` 覆盖为 `status: DONE`（不删除文件）

## 四、验收清单

- [ ] 写作反馈已收集（作者确认或从 diff 自动提取）
- [ ] 定稿 `archives/*.md` 已 Write 生成，中间稿（`.draft.md`/`.anti-ai.md`）保留未删
- [ ] 所有出场角色的状态 + 情绪弧线已更新
- [ ] 生物/怪物检测已完成 + 作者确认
- [ ] 持有物/经历已更新（如有变化）
- [ ] timeline 已追加本章事件
- [ ] 正文一致性检查完成（设定/章纲/钩子）
- [ ] 三类记忆已分类合并：写作要求 / 反 AI / 章纲遗漏
- [ ] 合并前已展示给作者确认分类
- [ ] 学习结果报告已输出
- [ ] hooks 健康检查已执行
- [ ] 停滞检测已执行
- [ ] 卷边界检测已执行 + 报告已输出
- [ ] status.md 已推进
- [ ] chapter.md#status 已改为 archived
- [ ] AI 快照已创建并保留（审计留档）
- [ ] `.agent/archiving/{chapter}.done` 已写入
- [ ] order 已标记 DONE
