# short-agent 调度 SOP

> **本文件是短篇调度契约的唯一权威源**（order 类型清单 + 作者确认关卡 + 断点续跑语义）。
> `agents/short-agent.md` 的流程树是执行细则，以本表为准展开。

## 职责边界

short-agent **只做三件事**：
1. 读 status 检测当前 phase 与篇状态
2. 写 order 文件调度子 agent
3. 验证子 agent 产出（order DONE + 产出文件非空）

**除此之外的任何事都不是你的活。** 不写内容文件、不执行命令、不改设定。

## 各 phase 调度表

| phase | 该谁干 | order 文件 | 产出 |
|-------|--------|-----------|------|
| setup | short-planner | `short-setting-order.md` | `stories/{slug}/setting.md` |
| planning | short-planner | `short-outline-order.md` | `stories/{slug}/outline.md` |
| contract | short-planner | `short-contract-order.md` | `stories/{slug}/prompt.md` |
| contract | short-verifier | `short-contract-audit-order.md` | `.agent/task/audit-report-{slug}.md` |
| writing | short-writer | `short-writing-order.md`（每批一个） | `stories/{slug}/manuscript.md`（追加） |
| polishing | short-editor | `short-polish-order.md` | 精修后的 manuscript.md |
| verifying | short-verifier | `short-verify-order.md` | `.agent/task/verify-report-{slug}.md` |
| verifying | reader（体验验收） | `short-reader-order.md` | `.agent/review/short-{slug}.md` |
| delivered | short-planner | `short-revision-order.md`（改稿：构思层） | 更新 setting/outline/prompt |
| delivered | short-writer | `short-revision-order.md`（改稿：重写某几节） | 更新 manuscript.md |
| delivered | short-editor | `short-revision-order.md`（改稿：表达层） | 更新 manuscript.md |

## 作者确认关卡（两道）

框架、大纲是故事的灵魂，AI 只负责笔墨：

| 产出 | 确认动作 | 作者确认后 |
|------|---------|-----------|
| 框架（setting-order DONE） | 展示摘要：读者读完什么感觉 / 写了件什么事 / 反转在哪 / 谁和谁 | phase → planning |
| 大纲（outline-order DONE，两道验证已过） | 展示摘要：这节讲什么 / 情绪怎么走 / 卡在哪断点 | phase → contract |

确认语义（与长篇同构）：
- 明确确认（可以/没问题）→ 推进；要改 → 重派对应 agent（order 内嵌修改意见）→ 改完再展示
- 模糊回复（差不多/你看着办）→ 一律视为未确认，追问具体哪项
- 「你全权写」全自动模式 → 展示摘要后视为已确认直接推进，**单次有效**
- 「继续/推进」→ 只推进到下一个确认关卡即停

**契约审计通过后不停等确认**（契约是 AI 笔墨的一部分）；正文流水线（契约→审计→写作→精修→核对→验收）确认大纲后可连续推进到交付。

## 写 order 文件的规则

1. 路径：`.agent/task/{type}-order.md`
2. 只含：输入路径 + 输出路径 + `status: pending`（改稿 order 另含定位结论与改动范围）
3. **writing-order 必须含重注入块**：本批的契约硬规则区完整内容（或等价摘录）——每批开始时由总指挥把契约硬规则区全文写入 order，写手不自行回溯
4. 不把多个任务塞进同一个 order；一次只调度一个子 agent

```markdown
# {type}-order
status: pending
story: {slug}
inputs:
  - 输入文件路径
outputs:
  - 输出目标路径
```

## 检查完成的标准

- order 存在且 `status: DONE` → 完成
- order 存在且 pending → 等待
- order 不存在 → 意外中断，进重试（≤2 次，超过问作者）

## 断点续跑语义

**状态记录是唯一断点源，重启直接读 `.agent/status.md` 的 `## 当前篇进度` 段，不做全量扫描。**

**篇状态 = 最近已完成的阶段**（order DONE 后才推进）。判断用**严格大于 `>`**：状态 > 某阶段 = 已完成可跳过；**等值 = 未完成，需重派**。

| 阶段 | 已完成信号 |
|------|-----------|
| setting | setting-order DONE 且 setting.md 非空 → 停下展示框架摘要等确认 |
| outline | `篇状态 > outline`；等值且 DONE → 重新展示大纲摘要等确认，不重派 |
| contract-audit | 审计报告存在且结论为通过 |
| batch-writing | 按批推进：writing_order_id + current_batch 记录断批位置 |
| polishing | polish-order DONE |
| verification | verify 报告通过且 reader 评审已产出 → 交付摘要 |

**改稿回退**：改稿定位结论决定回退目标（构思 → setting 重做连带大纲契约；大纲 → outline 重做连带重组契约并重新审计；写法 → 只重写指定节），状态机回退到对应阶段，**保留未受影响部分的进度**。

**改稿不夹带校验**：改稿 order DONE 后，总指挥比对差异范围（改了哪些文件哪些节）——越出作者要求范围（改走向/删冲突/加人物/改人设/改视角/动未要求的节）→ 判本次改稿失败，回退重做。

## 交付后：跨篇偏好记忆

每篇交付（作者确认）时，short-agent 追问一句「这篇有什么想固定下来的偏好（写法/节奏/忌讳）」；
把作者的明确反馈以「原文 → 结论」一行追加到 `<平台>/memory/author-feedback.md`（已存在的条目去重，
不改写）。short-planner 组装契约的「作者偏好记忆」字段从这里取用——跨篇不丢作者口味。
只在作者明确说了偏好时追加，MUST NOT 自己总结臆造。

## 禁止事项

- ❌ 不写 order 与 status 之外的文件
- ❌ 不直接写 stories/ 下任何内容
- ❌ 不在一个循环里调多个子 agent
- ❌ 不做子 agent 该做的事
