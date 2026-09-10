# {project-name}

## OpenCode 指引（短篇项目）

本项目的短篇写作流程由 6 个 agent 协作完成，定义在 `.opencode/agents/` 下。

**开始写作：** 在 OpenCode 中通过 `@short-agent` 或 Task 工具调用 short-agent 进入写作循环，或直接说「帮我写个短篇」。

**写作流程：** 定情绪与定方向 →（作者确认）→ 构思与排纲 →（作者确认）→ 写作契约组装 → 契约独立审计 → 分批写正文 → 去AI味与精修 → 兑现度核对 → 验收交付 →（作者可改稿或写下一篇）

**灵魂与笔墨：** 情绪目标、框架、大纲是故事的灵魂，每一步先给作者看摘要、等作者点头才继续；契约之后的正文与打磨是 AI 的笔墨。

**项目结构：**
- `story.md` — 项目索引 + 篇目清单（含 `length: short` 标记）
- `stories/{slug}/` — 一篇一个目录：`setting.md`（框架）、`outline.md`（大纲）、`prompt.md`（写作契约）、`manuscript.md`（成品正文）
- `sandbox/` — 检查资产（回归模式库、锁定台词白名单）
- `.agent/` — 状态追踪 + agent 通信（order 文件）
- `.opencode/agents/` — 各 agent 定义（short-agent, short-planner, short-writer 等）
- `.opencode/knowledge/` — 短篇去AI口径、短篇格式规范、短篇写作参考、题材风格包
- `.opencode/memory/` — 写作动态记忆（各环节作者反馈，持续积累）
