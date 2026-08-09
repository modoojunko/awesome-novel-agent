# {project-name}

## Codex 指引

本项目的小说写作流程由 8 个 agent 协作完成，定义在 `.codex/agents/` 下（TOML 自定义 agent）。

**开始写作：** 在 Codex 中通过 `@novel-agent` 或 `spawn_agent` 调用 novel-agent 进入写作循环。

**写作流程：** 设定 → 卷纲 → 章纲 → 提示词 → 正文 → 去AI味 → 验收 → 归档 → 下一章

**项目结构：**
- `story.md` — 项目索引 + 主线拆纲
- `settings/` — 世界观、角色、写作风格、时间线
- `volumes/` — 卷纲
- `chapters/` — 章纲
- `prompts/` — 提示词
- `archives/` — 正文
- `.agent/` — 状态追踪 + agent 通信（order 文件）
- `.codex/agents/` — 8 个自定义 agent 定义（novel-agent, volume-planner, chapter-planner 等）
- `.codex/skills/` — 独立交互工具（memory-recording、roleplay-sandbox）
- `.codex/memory/` — 写作动态记忆（各环节作者反馈，持续积累）
- `.codex/knowledge/` — 反 AI 规则、文风偏好、永久记忆、题材参考材料
