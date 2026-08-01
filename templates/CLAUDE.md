# {project-name}

## AI 指引

本项目的写作流程由 8 个 agent 协作完成，定义在 `.claude/agents/` 下。

**开始写作：** 输入 `@novel-agent` 进入写作循环。

**写作流程：** 设定 → 卷纲 → 章纲 → 提示词 → 正文 → 验收 → 归档 → 下一章

**项目结构：**
- `story.md` — 项目索引 + 主线拆纲
- `settings/` — 世界观、角色、写作风格、时间线
- `volumes/` — 卷纲
- `chapters/` — 章纲
- `prompts/` — 提示词
- `archives/` — 正文
- `.agent/` — 状态追踪 + agent 通信
- `.claude/memory/` — 写作动态记忆（各环节作者反馈，持续积累）
- `.claude/knowledge/` — 反 AI 规则、文风偏好、永久记忆、题材参考材料
