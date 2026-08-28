# {project-name}

## OpenCode 指引

本项目的小说写作流程由 9 个 agent 协作完成，定义在 `.opencode/agents/` 下。

**开始写作：** 在 OpenCode 中通过 `@novel-agent` 或 Task 工具调用 novel-agent 进入写作循环。

**写作流程：** 设定 →（作者确认）→ 卷纲 →（作者确认）→ 章纲 →（作者确认）→ 提示词 → 正文 → 去AI味 → 验收 → 归档 → 下一章

**灵魂与笔墨：** 设定、卷纲、章纲是故事的灵魂，每一步都先给作者看摘要、等作者点头才继续；提示词之后的正文与打磨是 AI 的笔墨。

**项目结构：**
- `story.md` — 项目索引 + 主线拆纲
- `settings/` — 世界观、角色、写作风格、时间线
- `volumes/` — 卷纲
- `chapters/` — 章纲
- `prompts/` — 提示词
- `archives/` — 正文
- `.agent/` — 状态追踪 + agent 通信（order 文件）
- `.opencode/agents/` — 各 agent 定义（novel-agent, volume-planner, chapter-planner 等）
- `.claude/memory/` — 写作动态记忆（各环节作者反馈，持续积累）
- `.claude/knowledge/` — 反 AI 规则、文风偏好、永久记忆、题材参考材料
