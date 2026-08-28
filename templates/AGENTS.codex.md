# {project-name}

## Codex 指引

本项目的小说写作流程由 9 个 agent 协作完成，定义在 `.codex/agents/` 下（TOML 自定义 agent）。

**开始写作：** 在 Codex 中通过 `@novel-agent` 或 `spawn_agent` 调用 novel-agent 进入写作循环。

**写作流程：** 设定 →（作者确认）→ 卷纲 →（作者确认）→ 章纲 →（作者确认）→ 提示词 → 正文 → 去AI味 → 验收 → 归档 → 下一章

**灵魂与笔墨：** 设定、卷纲、章纲是故事的灵魂，每一步都先给作者看摘要、等作者点头才继续；提示词之后的正文与打磨是 AI 的笔墨。

## 调度边界（最高优先级）

- **唯一调度者：** novel-agent 是唯一允许派生子 agent 的 agent；任何被 spawn 的子 agent 禁止再派生（包括派发同名 agent 的递归派生）。
- 子 agent 即使持有 spawn_agent 工具也不得使用；需要协作时向 novel-agent 报告，由 novel-agent 调度。
- novel-agent 每次 spawn 后留意 agent 树，发现子 agent 递归派生立即中断并重派。

**项目结构：**
- `story.md` — 项目索引 + 主线拆纲
- `settings/` — 世界观、角色、写作风格、时间线
- `volumes/` — 卷纲
- `chapters/` — 章纲
- `prompts/` — 提示词
- `archives/` — 正文
- `.agent/` — 状态追踪 + agent 通信（order 文件）
- `.codex/agents/` — 9 个自定义 agent 定义（novel-agent, volume-planner, chapter-planner 等）
- `.codex/skills/` — 独立交互工具（memory-recording、roleplay-sandbox）
- `.codex/memory/` — 写作动态记忆（各环节作者反馈，持续积累）
- `.codex/knowledge/` — 反 AI 规则、文风偏好、永久记忆、题材参考材料
