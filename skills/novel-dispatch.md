# novel-agent 调度 SOP

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
| outline | volume-planner | `volume-plan-order.md` |
| outline | chapter-planner | `chapter-plan-order.md` |
| draft | prompt-crafter | `prompt-craft-order.md` |
| draft | writer | `writing-order.md` |
| anti-ai | anti-ai | `anti-ai-order.md` |
| review | reader | `reader-review-order.md` |
| archive | updater | `archive-order.md` |
| finished | 无（终态） | 无——完本退出，不调度 |
| （卷完成后触发） | updater | `memory-sweep-order.md`（记忆兜底：格式验证/查重/压缩/永久记忆升降级） |

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
2. order 文件只包含：输入信息/文件路径 + 输出目标路径 + `status: pending`。不包含执行步骤、规则、方法论。
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

## 禁止事项

- ❌ 不用 Bash
- ❌ 不写 order 之外的文件
- ❌ 不直接写 settings/、chapters/、volumes/、prompts/、archives/、.claude/
- ❌ 不在一个循环里调多个子 agent
- ❌ 不做子 agent 该做的事（写了 order 调了人，等结果就行）
