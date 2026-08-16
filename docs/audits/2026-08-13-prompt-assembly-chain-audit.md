# 提示词组装链路审计报告

- **日期：** 2026-08-13
- **审计人：** multi-agent-systems-architect
- **范围：** 「写正文之前」的提示词组装链路——从 6 元素 prompt 每个字段反推输入源，核对 agent 定义 / skill SOP / 知识库格式规范 / 模板对同一契约的定义一致性
- **方法：** 逐文件交叉比对 + 全库 grep 取证 + 运行项目自带检查工具
- **自带工具运行结果：** `check-agents.py` ✅、`check-conflicts.py` ✅——但两者都不覆盖本报告发现的问题（见 §6）
- **状态：** 已移交 prompt-engineer 修复（P0/P1/P2-9，决策见 §8 批注）

---

## 0. 修复状态复核（2026-08-16）

逐条核对仓库现状（grep 取证 + 全库引用校验），**15/18 已修复**，3 项按决策留待下批：

| 编号 | 发现 | 状态 |
|------|------|------|
| B1 | 记忆闭环断裂（3/4 只写不读） | ✅ 已修复——volume/chapter/prompt 三个记忆文件读者已补齐（volume-planner / chapter-planner / prompt-crafter 各自 skill 的 Step 1） |
| B2 | writer-style.md 死链 | ✅ 已修复——文件已删除，init.py 占位与 3 份契约引用一并清理（2026-08-16 孤儿知识检查无此文件） |
| B3 | 前情上下文三源冲突 | ✅ 已修复——唯一来源=上一章章纲 emotional_design + required_changes（prompt-crafting.md:19,28），archives 仍禁读 |
| B4 | 场景卡契约缺口 | ✅ 已修复——chapter-setting-style.md 补「场景卡对应关系」节（卷纲场景卡 ↔ 章纲关键点） |
| B5 | 字数死值 vs 章纲目标 | ✅ 已修复——checklist 裁定改为「以章纲 memo 目标字数为准（±10%）」，2200±300 已删除 |
| B6 | 提示词结构术语三套并存 | ✅ 已修复——「4 层/9 层/Goals/任务层」等遗留词已清理，统一「6 元素」 |
| B7 | 两套规则优先级体系并存 | ⚠️ 未修——writing-base 铁律 vs prompt 六层优先级的跨文档裁定规则仍未定义（无决策批注） |
| B8 | novel-agent.md 重复块 | ✅ 已修复——重复块已清理 |
| C1 | 感官上限 2 vs 2-3 | ✅ 已修复——统一「2 种为主、氛围允许可至 3」；优先级表/执行细则/写作方法论/格式规范四处同口径 |
| C2 | 声音例外双标准 | ✅ 已修复——统一「红线关键信息 + 简短白描（1-2 句）」；「叙事线延伸」旧措辞已清零 |
| C3 | 认知动词例外冲突 | ✅ 已修复——二义性表例外已删，与优先级 4 对齐（关键情绪节点 ≤2 次/章） |
| C4 | T1 词档位漂移 | ✅ 已修复——突然/忽然/猛然已按 common-rules 改为语境敏感类口径 |
| C5 | 修正以反模式存在（无静态检查） | ⏸ 未修——术语/断言类 CI 见 P2-10（下批） |
| D1 | 6 元素骨架整份双定义 | ✅ 已修复——骨架定义收敛到 prompt-crafting，prompt-setting-style 不再重复定义 |
| D2 | 冲突裁定优先级表三份副本 | ✅ 已修复——收敛为 prompt-crafting + chapter-quality-checklist 两份且口径已同步 |
| D3 | 写作方法论四条三份副本 | ✅ 已修复——prompt-setting-style 与 prompt-audit 已改同口径/审计探针化 |
| D4 | 情绪外化速查表双份维护 | ⏸ 未修——anti-ai skill Gate C 速查与 common-rules 仍双份（决策：留待下批合并） |
| D5 | 叙事规则 7 条无单一权威源 | ✅ 已修复——narrative-rules.md 独立单源，注入/自查两侧引用 |

> 复核方法：逐条 grep 证据 + check-agents/check-conflicts/check-version 全绿 + test_platforms 187 通过。
> 未修 3 项（B7/C5/D4）已列入后续工作交接（handoff.md）。

---

## 1. 链路全貌（现状溯源图）

```
settings/writing-style.md（主卡，双态）─┐
settings/style-profiles/*.md（场景卡）──┤──rendering-rules.md 渲染（confidence>0）
settings/genre-setting.md               │
volumes/volume-{N}.md（卷纲/摘要）──────┐│
chapters/vol-{N}-ch-{M}.md（章纲）─────┤│
settings/character-setting/             ├┤
.claude/knowledge/anti-ai.md            ├┼─→ prompt-crafter ─→ prompts/vol-N-ch-M-prompt.md
.claude/knowledge/genre-example.md      ││      │                （6 元素）
.knowledge/scene-craft/*（方法论）──────┤│      │ 二轮：prompt-audit（9 维度，FAIL 打回）
.knowledge/permanent-memory.md          ││      ↓
.claude/memory/writing-memory.md ───────┘│   writer（writing-base 基底 + prompt）
                                          └→ anti-ai Gate G 读同章 prompt 逐条验收（同源闭环）
```

设计本身是对的：**单一组装者 + 纯净上下文 writer + 同源验收 + 双态风格 + 确定性渲染值**（rendering-rules 自含精确值、不依赖 tools 部署）。**架构层面达到要求。**

但溯源链路的**契约一致性没有达到要求**——同一契约在多份规范性文档中重复定义，演进不同步，产生了 8 处断裂、5 处冲突、5 处重复。

---

## 2. 断裂（链路断点）

### B1 记忆闭环断裂：4 个记忆文件 3 个只写不读 ⚠️ 最严重

[memory-recording.md:30-37](../skills/memory-recording.md#L30-L37) 定义四个记忆文件各有写者；但全仓库检索显示，**只有 `writing-memory.md` 有读者**（[prompt-crafting.md:24](../skills/prompt-crafting.md#L24)）：

| 文件 | 写者 | 读者 |
|------|------|------|
| volume-memory.md | volume-planner | **无** |
| chapter-memory.md | chapter-planner + updater-archive（[199](../skills/updater-archive.md#L199)「章纲遗漏」） | **无** |
| prompt-memory.md | prompt-crafter | **无** |
| writing-memory.md | updater（writer/reader 反馈） | prompt-crafter ✅ |

后果：memory-recording 的晋升机制要求 `use_count >= 4`（[memory-recording.md:94](../skills/memory-recording.md#L94)），没人读就没有引用计数——**3/4 的记忆文件永远无法晋升永久记忆，作者反馈闭环在三个环节是断的**。

### B2 `writer-style.md` 是死链

四份文档互相矛盾：
- [init.py:361-367](../../tools/init.py#L361-L367) 创建占位文件，注释称「由 updater 首次归档时填充」
- [updater.md:55,100](../agents/updater.md#L55) 契约仍声称合并写入它；[ARCHITECTURE.md:116](../ARCHITECTURE.md#L116) 也声称如此
- 但实际 SOP [updater-archive.md Step 7](../skills/updater-archive.md#L178-L205) 只写 `writing-memory.md` / `anti-ai.md` / `chapter-memory.md`，**没有 writer-style.md**
- [prompt-crafting.md Step 1](../skills/prompt-crafting.md#L14-L26) 的 9 类输入源里**没有它**，而 [prompt-crafter.md:77](../agents/prompt-crafter.md#L77) 的契约仍把它列为输入源

即：文件存在、3 份契约引用、**无写入方、无消费方**。作家的文风偏好沉淀（updater 语义合并）实际流向了 writing-memory，writer-style.md 只是残留。

### B3 前情上下文三源冲突，且每个源都有问题

「上章结尾画面」这一个字段，三个文档各指一个来源：
1. [prompt-setting-style.md:197](../../knowledge/format-specs/prompt-setting-style.md#L197)：**上章 archives/*.md 最后 100 字**
2. [prompt-crafting.md:19](../skills/prompt-crafting.md#L19)：**volume.md 前章摘要**（「只读卷纲中的前章摘要，不读上一章全文」）
3. [prompt-crafter.md:164](../agents/prompt-crafter.md#L164)：Read 权限**明令禁止读 archives/**

再核对卷纲格式规范——[volume-setting-style.md 产出模板](../../knowledge/format-specs/volume-setting-style.md#L611-L633)的章节列表只有「冲突事件 / 情绪锚点 / 信息差」，**根本没有「结尾画面」字段**。也就是说：来源 1 被权限禁止，来源 2 在格式规范里不存在。这个字段实际无合法输入源，prompt-crafter 只能临场发挥。

### B4 场景卡契约缺口

[prompt-crafting.md:126-132](../skills/prompt-crafting.md#L126-L132) 要求「从 **chapter.md 场景卡**的三要素提取核心事件，**不从 outline.key_points 提取**」。但：
- [chapter-setting-style.md](../../knowledge/format-specs/chapter-setting-style.md)（章纲格式规范）的内容清单是 7 节，**没有「场景卡」节**，完整示例里也没有
- [chapter-outline.md:112](../skills/chapter-outline.md#L112) 说「每条关键点对应一个场景卡」——场景卡与 key_points 是一一对应的
- [volume-setting-style.md:480](../../knowledge/format-specs/volume-setting-style.md#L480) 说「章纲→场景卡」

四份文档对 chapter.md 里到底有没有场景卡、场景卡和 key_points 什么关系，**各说各话**。prompt-crafter 的「不从 key_points 提取」指令指向一个格式规范里不存在的字段。

### B5 字数死值 vs 章纲目标

[chapter-quality-checklist.md:30,50](../../knowledge/format-specs/chapter-quality-checklist.md#L30) 的全局冲突裁定表硬编码「目标字数 **2200±300**（1900-2500 字）」，而全链路的目标字数是章纲级动态值（[chapter-setting-style.md](../../knowledge/format-specs/chapter-setting-style.md#L149-L161) 的例值 4000-6000；[prompt-setting-style.md:30](../../knowledge/format-specs/prompt-setting-style.md#L30) 明确「从章纲读取，不重复定义」）。裁定表自称「已预加载到 prompt 的任务指示」，writer/auditor 按它验收——4500 字的目标章会被判「超限」。

### B6 提示词结构术语三套并存：4 层 / 6 元素 / 9 层

| 叫法 | 出处 |
|------|------|
| **4 层** | [prompt-crafter.md:3,10,25,50,80](../agents/prompt-crafter.md#L3)（description/Purpose/Output 全用）、[writing-execution.md:27,52](../skills/writing-execution.md#L27)（「确认 4 层完整」） |
| **6 元素** | [prompt-crafting.md:9](../skills/prompt-crafting.md#L9)、[prompt-setting-style.md](../../knowledge/format-specs/prompt-setting-style.md#L17)、[ARCHITECTURE.md:103](../ARCHITECTURE.md#L103)（现状实际结构） |
| **9 层** | [writing-base.md:10](../../knowledge/format-specs/writing-base.md#L10)（「仅执行上层 9 层结构化提示词」） |

连带遗留词：「任务层」（[writing-execution.md:27,64](../skills/writing-execution.md#L27)、[prompt-audit.md:115](../skills/prompt-audit.md#L115)）、「**Goals**」（[writing-base.md:20,25](../../knowledge/format-specs/writing-base.md#L20)——现在的结构里这个字段已改名「叙事目标」，writer 的基底文件却还引用旧字段名）、「prompt 模块 5」「genre_profile」「hooks.md」（[chapter-quality-checklist.md:498,613,657](../../knowledge/format-specs/chapter-quality-checklist.md#L657)）。writer 和 auditor 按这些文档执行时，字段名对不上就是执行歧义。

### B7 两套规则优先级体系并存

[writing-base.md:14-20](../../knowledge/format-specs/writing-base.md#L14-L20) 自称「核心写作取舍铁律（优先级高于所有技法规则）」，且 [writing-execution.md:41](../skills/writing-execution.md#L41) 规定「与基底冲突时以基底为准」；而 prompt 内部带六层「不可违反规则」优先级（红线 > 字数 > T1/认知/感官 > 叙事规则 > 写作规范）。当「字数硬约束（prompt 第 2 层）」与「情绪优先于文笔（基底铁律）」冲突时，writer 没有明确的跨文档裁定规则。

### B8 novel-agent.md 存在重复块（合并残留）

[novel-agent.md:107-112](../agents/novel-agent.md#L107-L112) 原样重复了 [65-72 行](../agents/novel-agent.md#L65-L72) 的 Out of Scope / Decision Rights 内容——「推演沙盘评估逻辑」节后粘连了一段旧版块。

---

## 3. 冲突（同一规则，多个版本）

### C1 感官上限：2 种 vs 2-3 种（skill 内部自相矛盾）

- [prompt-crafting.md:43](../skills/prompt-crafting.md#L43) 优先级 5：**「每场景不超过 2 种感官细化」**
- [prompt-crafting.md:253](../skills/prompt-crafting.md#L253) 写作方法论：**「以 2 种为主，氛围允许时增至 3 种」**
- [prompt-setting-style.md:43](../../knowledge/format-specs/prompt-setting-style.md#L43)：2-3 种
- [chapter-quality-checklist.md:33](../../knowledge/format-specs/chapter-quality-checklist.md#L33)：建议 ≤2、可至 3

同一份 skill 文件里两个数字并存，而「写作方法论」是**照抄模板不做调整**（[prompt-setting-style.md:188](../../knowledge/format-specs/prompt-setting-style.md#L188)）——两个数字会同时进入 prompt，writer 和 auditor 各自挑一个执行。

### C2 声音例外双标准

- 注入模板版：[prompt-crafting.md:253](../skills/prompt-crafting.md#L253)：「仅当声音线索被**明确标记为『叙事线延伸』**时…例外**仅限红线关键信息**」
- 裁定细则版：[prompt-crafting.md:57-60](../skills/prompt-crafting.md#L57-L60) 与 [checklist:85-92](../../knowledge/format-specs/chapter-quality-checklist.md#L85-L92)：「**红线关键信息 + 简短白描（1-2 句）**」

「叙事线延伸」（旧设计的碾药声/露珠例）和「红线关键信息」是两个不同判定条件，在 prompt 里并存，auditor 按哪个判都是对的、也是错的。

### C3 认知动词例外：允许 vs 不允许

- [prompt-crafting.md:42](../skills/prompt-crafting.md#L42) 优先级 4 + [checklist:33](../../knowledge/format-specs/chapter-quality-checklist.md#L33)：「必须替换，**不因其他规则让步**」
- [prompt-crafting.md:71](../skills/prompt-crafting.md#L71) 二义性表：「认知动词承载不可替代的情节信息且替换后导致字数超限而红线内容被挤占」→ **适用例外**

同一 skill 内一条规则同时有「无例外」和「有例外」两个版本。

### C4 T1 词档位漂移

[prompt-crafting.md:41](../skills/prompt-crafting.md#L41) 优先级 3 举例「T1 词（修饰类）：**突然**、竟然、默默、微微」；而权威源 [common-rules.md:46](../../knowledge/anti-ai/common-rules.md#L46) 已把「突然/忽然/猛然」**移出 T1**、改为语境敏感类（≤4 次/章，红线段落从宽）。prompt 组装的优先级表引用的是旧档位。

### C5 「叙事规则优先级高于所有约束」已修正但以反模式形式存在

[prompt-crafting.md:44](../skills/prompt-crafting.md#L44) 记录了修正（「原有『叙事规则优先级高于所有约束』修正为…」），[prompt-audit.md:162](../skills/prompt-audit.md#L162) 也把旧表述列为 FAIL 信号——但修正只写在文档里，没有任何静态检查保证旧表述不会再被注入。

---

## 4. 重复（同一定义多份维护，已产生漂移）

### D1 最核心：6 元素骨架整份双定义

[prompt-setting-style.md](../../knowledge/format-specs/prompt-setting-style.md)（知识库格式规范）与 [prompt-crafting.md](../skills/prompt-crafting.md)（agent skill SOP）**各自完整定义了骨架 + 填充规则 + 检查清单**，重叠约 80%，且已经漂移：前情来源不同（B3）、感官数字不同（C1）、验收表和二义性表只在 skill、第一章规则表述不同。**这是全链路重复-漂移的总根源。**

### D2 冲突裁定优先级表三份副本

[prompt-crafting.md:37-44](../skills/prompt-crafting.md#L37-L44) / [prompt-setting-style.md:91-96](../../knowledge/format-specs/prompt-setting-style.md#L91-L96) / [checklist:27-34](../../knowledge/format-specs/chapter-quality-checklist.md#L27-L34)——感官行已经漂移（C1 证据）。

### D3 写作方法论四条三份副本

[prompt-crafting.md:250-258](../skills/prompt-crafting.md#L250-L258) / [prompt-setting-style.md:41-45](../../knowledge/format-specs/prompt-setting-style.md#L41-L45)（模板）/ [prompt-audit.md:134](../skills/prompt-audit.md#L134)（审计探针）——声音例外措辞在三份间漂移（C2 证据）。

### D4 情绪外化速查表双份维护

[common-rules.md:253-264](../../knowledge/anti-ai/common-rules.md#L253-L264)（情绪外化 8 行）与 [anti-ai.md:189-200](../skills/anti-ai.md#L189-L200)（Gate C 速查 8 行）几乎逐行一致（紧张→手抖、愤怒→青筋…），两处独立维护，改一处漏一处是必然。

### D5 叙事规则 7 条无单一权威源

规则 1-7 的定义散落在 [prompt-crafting.md:158-208](../skills/prompt-crafting.md#L158-L208)（注入侧）和 [writing-execution.md:121-129](../skills/writing-execution.md#L121-L129)（自查侧）两处各自列出，没有独立定义文件。

---

## 5. 对「提示词溯源」要求的专项评估

- **产物级溯源是有的**：prompt-audit 维度 B「知识点溯源」逐条核对场景写法指引的来源与转化质量，无源指引 ≥2 条触发 WARN。
- **但溯源范围只覆盖 scene-craft**：anti-ai 规则、genre-example 注入段、作者记忆、风格卡渲染四路来源的注入**没有任何溯源检查**——维度 B 的输入清单（[prompt-audit.md:12-18](../skills/prompt-audit.md#L12-L18)）只有 prompt + chapter + genre-setting + scene-craft。
- **「无来源标注」设计本身是对的**（[prompt-crafting.md:549](../skills/prompt-crafting.md#L549)：writer 不需要知道规则出处），与溯源不冲突——溯源是组装过程的事，不是 writer 的事。但组装过程的溯源目前是不完整的。

---

## 6. 检查工具盲区

| 工具 | 实际覆盖 | 漏掉什么 |
|------|---------|---------|
| check-conflicts.py | 数值阈值 vs common-rules + 2 个方法论文件的数量线越界 | 语义冲突（感官 2/3、字数死值）、术语漂移（4 层/Goals）、链路死链（writer-style、记忆只写不读）、字段来源冲突（前情/场景卡）——**本次全部发现都漏掉** |
| check-agents.py | agent 定义结构校验 | 跨 agent 契约一致性（B2、B3 正是跨文件问题） |

两个工具都通过 ≠ 链路无问题。当前 CI 给的是**结构绿灯，语义红灯不亮**。

---

## 7. 总体结论

**架构设计：达到要求。** 组装单点化、writer 上下文纯净、anti-ai 同源验收、双态风格渲染、确定性数值——设计层没有根本缺陷。

**提示词溯源链路的完整性：未达到要求。** 存在 2 处死链、1 处契约三源冲突、1 处格式规范缺口、5 组规则多版本并存。根因是一个模式：**同一契约在 agent 定义 / skill SOP / 知识库规范 / 模板四层重复定义，演进时只改一处**（本次分支新增 style-distiller 双态、决策 A/B 后尤其明显）。

---

## 8. 建议（按优先级，已定决策批注）

### P0 — 先止血（契约唯一化）

1. **术语统一**：锁定「6 元素」为唯一名称，全局清理「4 层」（5 处）、「9 层」（writing-base）、「任务层」「Goals」「prompt 模块 5」「genre_profile」「hooks.md」遗留词；在 check-conflicts.py 加术语断言（这些词在 agents/skills/knowledge 中禁现），防止回潮。
   > ✅ 已决策：术语断言进 P2-10，本批只做替换。
2. **前情上下文定唯一来源**：允许 prompt-crafter 读上一章 `chapters/vol-N-ch-M-1.md` 的 `emotional_design`（权限已含 chapters/），prompt-setting-style / prompt-crafting / prompt-crafter 权限三处同步。
   > ✅ 已决策：采用「上一章章纲 emotional_design + 卷纲摘要辅助」，archives 仍禁读。
3. **writer-style.md 决定去留**：**删除**（init.py 占位 + 3 份契约引用 + ARCHITECTURE 声明一并清理）——其功能已被 writing-memory + permanent-memory 完整覆盖。
   > ✅ 已决策：删。
4. **三处规则冲突归一**：感官上限（2-3 种口径）、声音例外（红线关键信息 + 简短白描）、认知动词例外（删掉二义性表的例外，与优先级 4 对齐）——每处保留一份权威定义，其余引用。
   > ✅ 已决策：感官=2 为主可至 3；声音例外=红线关键信息+简短白描；认知动词一律替换。
5. **字数死值删除**：checklist 的「2200±300」改为「以章纲 memo 目标为准（±10%）」。
   > ✅ 已决策。

### P1 — 补闭环

6. **场景卡进格式规范**：在 chapter-setting-style.md 补「场景卡」节（或明确「场景卡 ≡ key_points 的章级映射」），让 prompt-crafting Step 1.3 的读取契约有落点。
   > ✅ 已决策：补节，口径按 chapter-outline.md L112-115。
7. **记忆闭环补读者**：chapter-planner 读 chapter-memory、prompt-crafter 读 prompt-memory、volume-planner 读 volume-memory（写入各自 skill 的 Step 1），否则晋升机制对 3/4 文件永远失效。
   > ✅ 已决策。
8. **novel-agent.md 去重块清理**（107-112 行）。
   > ✅ 已决策。

### P2 — 防回潮（把本次发现固化为 CI）

9. **单一权威源模式推广**：叙事规则 7 条独立成 `knowledge/format-specs/narrative-rules.md`，注入侧与自查侧引用；合并情绪外化速查（anti-ai skill 引用 common-rules）。
   > ✅ 已决策：本批只做 narrative-rules 单源化；情绪速查合并留待下批。
10. **扩展检查工具**：给 check-conflicts.py（或新增 check-chain.py）加三类断言——术语禁现、关键字段来源唯一性（前情/场景卡/字数）、契约死链（引用文件必有写者+读者）。本次报告的每一条发现都可以写成一条断言，从此可回归。
    > ⏸ 下批。
11. **溯源扩展**：prompt-audit 维度 B 的溯源从仅 scene-craft 扩展到 anti-ai/genre-example/记忆/风格卡四路注入（至少抽查）。
    > ⏸ 下批。
12. **本地 skill 副本同步**：`~/.claude/skills/awesome-novel` 仍写「8 个 agent」，仓库已是 9 个（style-distiller 新增后未同步），需重装/同步。
    > ⏸ 下批。
