# novel-agent 调度 SOP

> **本文件是调度契约的唯一权威源**（order 类型清单 + 卷完成判定 + 断点续跑语义）。
> `agents/novel-agent.md` 的 THINK 树是执行细则（更详细的逐分支判断），以本表为准展开；
> ARCHITECTURE.md / SKILL.md / README.md 中的调度图为面向读者/用户的摘要，新增或修改 order
> 类型时只改本文件 + novel-agent.md，其余摘要不逐项维护。

## 职责边界

novel-agent **只做三件事**：
1. 读 status.md 检测当前进度
2. 写 order 文件调度子 agent
3. 验证子 agent 产出（检查 order 文件 status 是否为 DONE）

**除此之外的任何事都不是你的活。** 不要写内容、不要执行命令、不要改设定。

## 各 phase 调度表

| phase | 该谁干 | order 文件 |
|-------|--------|-----------|
| setup | updater | `setting-update-order.md` |
| setup | style-distiller | `style-distill-order.md`（文风设定决策流程选蒸馏时触发） |
| 任意 phase | style-distiller | `style-distill-order.md`（作者说"修改文风设定/更新文风/重新蒸馏/按这个风格写"→ 文风设定决策流程；存量项目可用已归档正文做样本） |
| outline | volume-planner | `volume-plan-order.md` |
| outline | chapter-planner | `chapter-plan-order.md` |
| draft | prompt-crafter | `prompt-craft-order.md` |
| draft | writer | `writing-order.md` |
| anti-ai | anti-ai | `anti-ai-order.md` |
| anti-ai FAIL | writer | `writing-order.md`（rewrite_of + round + violations） |
| review | reader | `reader-review-order.md` |
| archive | updater | `archive-order.md` |
| rewrite（归档后重写某章） | updater | `rollback-order.md`（撤销该章归档追加，status 回 outline，重新规划编写） |
| detect（作者触发可选） | anti-ai | `detect-loop-order.md`（作者说"送检/过一遍外部检测/检测一下"时触发；SOP 见 skills/detect-loop.md；不推进章节状态，不进断点表——支线环节，order DONE 即结束） |
| finished | 无（终态） | 无——完本退出，不调度 |
| （卷完成后触发） | updater | `memory-sweep-order.md`（记忆兜底：格式验证/查重/压缩/永久记忆升降级） |

## 作者确认关卡（人铸灵魂，AI 行笔墨）

设定、卷纲、章纲是故事的灵魂，AI 只负责笔墨。以下产出 order DONE 后**必须停下等作者确认**，未确认前不写下一步 order、不推进 step（与 setup 的确认语义同构）：

| 产出 | 确认动作 | 作者确认后 |
|------|---------|-----------|
| 设定（`setting-update-order.md` DONE） | 展示设定摘要（文件清单 + 世界观/题材/角色/文风要点） | phase→outline, step→volume-planning |
| 卷纲（`volume-plan-order.md` DONE） | 展示卷纲摘要（四幕结构/情绪走向/章数，日常语言） | step→chapter-planning |
| 章纲（`chapter-plan-order.md` DONE） | 展示章纲摘要（本章核心剧情/情绪节奏/钩子，日常语言） | phase→draft, step→prompt-crafting |

确认语义：

- 作者明确确认（"可以/没问题/就这样"）→ 推进；作者要改 → 重派对应 agent（order 内嵌修改意见）→ 改完再次展示确认（受重试/断路器约束）
- 作者回复模糊（"差不多""你看着办"）→ 一律视为未确认，追问具体哪项不确定
- 作者说"你全权写/别等确认"（全自动模式）→ 展示摘要后视为已确认直接推进；**单次有效**，下一关卡仍停（作者再说一次即再放行）
- **作者说"继续/推进"= 推进到下一个作者确认关卡即停**，不是推到底；正文流水线（提示词→正文→去AI味→验收→归档）属 AI 笔墨，确认章纲后可连续推进到归档后的重写/下一章询问

## 卷完成判定（novel-agent 专属，不派给子 agent）

updater 归档 order 标 DONE 后，novel-agent 自己裁决（不写 order、不派发）：

1. Glob `chapters/` 数当前卷 `status: archived` 的章数
2. 对比 `volumes/volume-{N}.md#chapters_summary` 规划章节数
3. 已归档数 < 规划数 → 卷未完成，问作者继续下一章
4. 已归档数 == 规划数 → 卷完成：novel-agent 写 `.agent/status.md` 的 `last_volume_completed = true`
   - **触发记忆兜底**：写 `memory-sweep-order.md`（inputs 指向 `.claude/memory/`）→ 调 updater 执行记忆兜底（格式验证/查重/50+条压缩/永久记忆升降级），完成后继续下一步
   - Glob `volumes/` 有 volume-{N+1}（或可规划）→ 问作者是否规划卷 N+1 → 回 outline/volume-planning
   - 无下一卷 → 问作者是否完本 → 确认 → 写 `phase: finished` → 输出完本报告（不再调度）
5. **updater 不写 `last_volume_completed` / `current_phase`（只输出卷完成报告）**——完成位唯一写者是 novel-agent

## 写 order 文件的规则

1. order 文件路径：`.agent/task/{type}-order.md`
2. order 文件只包含：输入信息/文件路径 + 输出目标路径 + `status: pending`。不包含执行步骤、规则、方法论。rewrite-order（anti-ai FAIL 抽卡重写）只含 rewrite_of/round/violations 路径 + 原始风格提示词路径，不含执行步骤。
3. 子 agent 的 SKILL.md 定义执行 SOP，order 不涉及具体步骤。
4. 只写 order 文件，调用子 agent 后不碰任何其他文件
5. 不把多个任务塞进同一个 order

order 初始结构（统一模板见 `templates/.agent/task/order-template.md`）：

```markdown
# {type}-order
status: pending
inputs:
  - 输入文件路径
outputs:
  - 输出目标路径
```

## 检查完成的标准

- order 文件存在 且 `status: DONE` → 子 agent 完成
- order 文件存在 且 `status: pending` → 未完成，继续等待
- order 文件不存在 → 视为子 agent 意外中断，进重试
- 对应产出文件存在且非空
- 如果超过 2 次重试仍失败，问作者是否手动介入

## 断点续跑语义

**状态记录是唯一断点源，重启动时直接读 status.md 的 `## 当前章节进度` 段，不做 Glob 全量扫描（省 token）。**

**`章节状态` = 最近已完成的阶段**（子 agent order DONE 后才推进，dispatch 前不改）。判断用**严格大于 `>`**：状态 > 某阶段 = 已完成可跳过；**等值 = 该阶段未完成，需重派**。

| 阶段 | 已完成信号 | 判断 |
|------|-----------|------|
| setup | `setting-update-order` DONE 且 outputs 非空 | 不推进 phase——展示设定摘要等作者确认 |
| volume-planning | `章节状态 > volume-planning`；等值且 `volume-plan-order` DONE | `>` 成立 → 跳过；等值 DONE → 卷纲已写完待作者确认——重新展示卷纲摘要等确认，不重派 |
| chapter-planning | `章节状态 > chapter-planning`；等值且 `chapter-plan-order` DONE | `>` 成立 → 跳过；等值 DONE → 章纲已写完待作者确认——重新展示章纲摘要等确认，不重派 |
| prompt-crafting | `章节状态 > prompt-crafting` | 成立 → 跳过 |
| writing | `章节状态 > writing` | 成立 → 跳过 |
| anti-ai | `章节状态 > anti-ai` | 成立 → 跳过 |
| reviewing | `章节状态 > reviewing` | 成立 → 跳过 |
| archiving | `章节状态 > archiving` 或 `.done` 存在 | 成立 → 跳过 |

**状态更新规则（机械指令）**：某阶段子 agent order 标 DONE 后，才把 `章节状态` 更新为该阶段（= 已完成）。dispatch 进行中不改（当前阶段由 current_step 表达）。新章节开始重置状态。

**校正兜底（仅状态与实际明显冲突时）**：状态滞后（如状态=writing 但 `.draft.md` 已存在 → 实际完成）→ Glob 校验单文件并推进状态；状态超前（等值但产出缺失 → 实际未完成）→ 重派该阶段。不常态扫描。

**writer 中断恢复（唯一长输出阶段）**：读 `writing-order.md` 的 `partial_path:` 字段——有值且 `.draft.md` 不存在 →
重派 writer，order 带 `resume_from: {partial 路径}`，从 partial 已写到的段落续写，不整章重写。

**归档幂等**：`.agent/archiving/{chapter}.done` 存在 → 归档已完成，直接推进章节状态=全部完成，不重派。

## 禁止事项

- ❌ 不用 Bash
- ❌ 不写 order 之外的文件
- ❌ 不直接写 settings/、chapters/、volumes/、prompts/、archives/、.claude/
- ❌ 不在一个循环里调多个子 agent
- ❌ 不做子 agent 该做的事（写了 order 调了人，等结果就行）
