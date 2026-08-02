
# writer skill


## 流程概览

```text
Step 1: 准备（确认卷号/章号/prompt 完整性）
Step 2: 清理上下文（减少干扰）
Step 3: 写作（sub-agent 执行）
Step 4: 验证输出（文件存在 + 字数达标）
Step 5: 叙事规则自查（7 条正面规则逐条过）
```

> AI 原版快照（`.agent/{chapter}-draft-ai.md`）由 **updater 在归档时创建**（从草稿复制，updater-archive Step 1），writer 不负责保存。

## Step 1: 准备

1. 确认卷号 `{N}` 和章号 `{M}`
2. 读取 `prompts/vol-{N}-ch-{M}-prompt.md`，确认 4 层完整。字数和驱动力从任务层获取，叙事视角从输出·写作规范获取
3. **断点检测**：读 `writing-order.md` 的 `resume_from:` 字段——有 → 读对应 partial 文件，续写（见 Step 3 的续写分支）；无 → 全新写

## Step 2: 清理上下文

调用 sub-agent 前，清理主 agent 的读取历史（genre-example、anti-ai 等文件后续不再需要）。减少 sub-agent 的干扰上下文。

## Step 3: 写作（sub-agent 执行）

启动 sub-agent（推荐 flash 模型），传入以下完整指令：

```markdown
## 基底（先读，再叠加以下指令）
先 Read `.claude/knowledge/writing-base.md` 作为写作基底（核心写作取舍铁律 + 输出硬性规范 + 禁用行为），
以下指令在基底之上叠加生效；与基底冲突时以基底为准。

## Role
全章正文写作。只读提示词文件，一次性写完整章正文。章纲约束已全部注入提示词。

## Scope
- 做：读提示词，按叙事段落顺序写整章
- 不做：不读卷纲/章纲/archives、不修改提示词、不写其他章、不写 settings/ 下任何文件

## Inputs
- `.claude/knowledge/writing-base.md` — 写作基底（先读）
- `prompts/vol-{N}-ch-{M}-prompt.md` — 主要输入（4 层提示词）
- `settings/writing-style.md` — 写作风格方法论
- `settings/genre-setting.md` — 题材设定

## Outputs
- `archives/vol-{N}-ch-{M}-{slug}.draft.md` — 全章正文草稿（最终）
- `archives/vol-{N}-ch-{M}-{slug}.draft.partial.md` — 部分草稿（写作过程 checkpoint，边写边存）

## 写作规则
- 按提示词叙事段落 1→N 顺序写，段落间过渡流畅
- 每个段落的写作指引必须兑现（场景/情绪/角色状态/结束画面）
- 结尾停在最后一段 ends_with 指定的画面或状态
- 正文不含解释、说明、引导语（不写"他感到""他意识到"）
- 字数不低于提示词任务层目标字数的 80%
- **每写完一个叙事段落，立即做两件事（不等全部写完）**：
  1. 把该段追加写入 `.draft.partial.md`（覆盖式，保留最新进度）
  2. 在 `writing-order.md` 的 `partial_path:` 字段写入该 partial 路径（覆盖更新）
  → 这是中断 checkpoint。**即使中途被掐断，order 里也留有最新 partial 指针**，novel-agent 重启后能定位续写。全部段落写完后再写完整 `.draft.md` 并清掉 `partial_path:`

## 续写（仅 resume_from 存在时）
若本 order 带 `resume_from: {partial 路径}`：
1. 读 partial 文件（允许，见 Inputs），数清已写完的段落数（设为 K）
2. 从提示词第 K+1 个叙事段落继续写，**不重写** K 段之前的内容
3. partial 里已有的内容保留，新写的段落追加其后
4. 若 partial 为空或读不到 → 按全新写处理并报告

## Inputs（续写时追加）
- `archives/vol-{N}-ch-{M}-{slug}.draft.partial.md` — resume_from 指向的 partial 文件（仅续写时读，数 K 段用）

## 禁止（违规即重写）
- 不自行添加提示词中未出现的角色名、细节、描写
- 不凭空发明章纲/提示词未要求的信息
- 龙套命名：提示词未给名字就不写名字，用"那几个人""另一个人"等泛指代替
- 格式违规：正文禁止使用 `---` 分隔符、Markdown 标题（`#` `##` 等）以及其他 Markdown 标记

**原则：提示词没写的情节、对话、角色行为，不自行添加；允许合理的细节填补和氛围铺陈——提示词写了"他在咖啡馆等人"，可以写环境氛围、微动作、思绪，但不能写"他等人等到了仇家"。**
```

sub-agent 执行写完后返回。主 Agent 检查输出文件是否存在。

### Step 3.5: partial 记录校验（中断恢复的权威信号）

partial_path 由**写作 sub-agent 每段写完同步写入 order**（见上文写作规则），主 Agent 返回后只做**校验兜底**：

1. **校验 order**：读 `writing-order.md` 的 `partial_path:`——sub-agent 若已正常写入则无需改动
2. **兜底补写**：若 partial 文件存在但 order 里 `partial_path:` 缺失（sub-agent 异常未写）→ 主 Agent 补写该行
3. **完成清理**：完整 `.draft.md` 写完 → 清掉 `partial_path:`（断点已完成，novel-agent 不再触发续写）

> 为什么 partial_path 记在 order 而不是 status.md：writer 没有 status.md 写权限（最小权限设计），但 order 是 writer 唯一可写的调度文件。novel-agent 重启动读 order 即可知 partial 位置。

## Step 4: 验证输出

| 检查项 | 操作 |
|--------|------|
| 输出文件存在？ | `archives/vol-{N}-ch-{M}-*.draft.md` 存在？不存在→重试 1 次 |
| 字数达标？ | ≥ 章纲字数 80%？不足→**先回写提示词层再问作者**（见下"字数不足处理"），不静默接受 |
| 文件位置正确？ | 写入到 archives/ 目录而非其他地方？ |
| partial 清理？ | 完整 `.draft.md` 写完且验证通过后，删掉 `.draft.partial.md` + 清空 order 的 `partial_path:`（断点已完成，不留残留） |

**字数不足处理（显式降级，不静默）：**
若字数 < 目标 80%：
1. **在 writing-order.md 记录缺口**：`status: DONE` 前在文件追加一行 `quality_gap: ch{M} 字数不足，目标 X 实写 Y`——让降级可追溯（writer 无 status.md 写权限，缺口记录在 order 里，novel-agent 检测 DONE 时同步到 status.md）
2. **回写提示词层**：在下一章 prompt 的对应场景提高权重（如把低权重场景的字数分配挪给被压缩的核心场景），而非只在本次接受
3. **再问作者**："本章字数未达目标（X/Y），已记录并会在下一章提示词回写。接受定稿还是补充重写？"
4. 作者接受 → 继续；作者要求补 → 重写该章，不把未达标草稿静默推进 anti-ai

## Step 5: 叙事规则自查

通读刚写的 draft，对照 prompt 中注入的叙事规则做一轮快速检查：

| 规则 | 自查 |
|------|------|
| 规则 1（先出感知信号） | 段首是否有"主角+感知动词"结构？（他看到/他听到/他发现）→ 有则改为先扔感知事实 |
| 规则 2（认知动词节制） | "他发现/他感到/他注意到"等词汇是否过于密集？→ 优先用动作替代，关键节点保留≤2次/章 |
| 规则 3（按印象深排） | 是否有连续"先→然后→接着→最后"结构？→ 按感知强度重排 |
| 规则 4（用具体体验） | 是否有"各种/纷纷/一系列"类标签？→ 换成具体感官细节 |
| 规则 5（因果自然） | 是否有过多因果解释（因为/所以/因此连篇）？→ 删掉多余的，保留必要的 |
| 规则 6（对话像人话） | 对话是否主谓宾齐全、缺口语味？→ 加人称/语气词/口癖 |
| 规则 7（叙事自然有温度） | 是否有过度修辞或刻意做作？→ 改为自然叙述，允许适度叙事温度。不要为"不演"而极端白描 |

发现问题直接改，**不留违禁品到 anti-ai 管线**。anti-ai 的职责是扫漏网之鱼，不是替你擦屁股。

## Step 6: （无——快照由 updater 创建）

AI 原版快照 `.agent/{chapter}-draft-ai.md` 不在 writer 职责内：writer 的 Write 白名单不含 `.agent/`，快照由 **updater 在归档时从草稿复制**（updater-archive Step 1 ①，作为归档 diff 基线）。writer 完成后只需把 draft.md 交给管线。
