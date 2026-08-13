# v4.8.4 版本说明

> **关键词：** OpenCode 支持、双平台（Claude Code / OpenCode）、B站社区贡献合入

---

## 一句话

**awesome-novel-skill 现在也能在 OpenCode 上跑了。**

---

## 这版做了什么

OpenCode 是社区开源的一款 AI 编程 CLI 工具，和 Claude Code 是同类产品。有 B站的小伙伴基于 v4.8.2 做了 OpenCode 适配，我们花时间对比了他改的所有代码，在最新 v4.8.3 main 上重新整理了适配逻辑，合入了主线。

---

## 怎么做到的

花了很多时间对比两个版本的差异，意外发现了一个好消息：

**main 分支的 Agent 定义格式天然兼容 OpenCode。**

之前 v4.8 大重构时把 agent 定义改成了 `name:` / `role:` / `react:` / `skills:` / `knowledge:` 的结构化格式，这恰好也是 OpenCode 能直接读的格式。所以 **agent 文件本身一行不用改**——改的全是工具脚本、安装脚本和文档。

---

## 具体改了什么（7 个文件）

| 改动 | 文件 | 说明 |
|------|------|------|
| 平台检测 + 定向部署 | `tools/init.py` | 根据 `SKILL_HOME` 路径自动判断当前平台，agent 定义只部署到对应目录 |
| 同步路径自动切换 | `tools/sync-project.py` | 新增 `AGENT_TARGET` 常量，同步时自动走 `.opencode/` 或 `.claude/` |
| 项目模板 | `templates/AGENTS.md`（新） | OpenCode 项目初始化时生成的指引文件 |
| 集成说明 | `SKILL.md` | 新增 OpenCode 集成说明章节，路径引用全部更新 |
| 安装脚本 | `install.ps1` / `install.sh` | 新增 `opencode` 平台选项 |
| 文档 | `README.md` | 标题、徽章、安装命令、项目结构、FAQ 全面更新，新增独立集成章节 |

---

## 设计原则：纯粹的"或"关系

Claude Code 和 OpenCode 是 **或** 的关系，不是 **与**：

- 用 `./install.sh opencode` 安装 → agent 部署到 `.opencode/agents/`
- 用 `./install.sh claude-code` 安装 → agent 部署到 `.claude/agents/`
- 部署时通过 `SKILL_HOME` 路径判断平台，两个工具装在不同路径，互不干扰

**不会**出现项目里两个目录都有的情况。你的项目只会有当前平台需要的那一套。

---

## 兼容性保证

- ✅ 所有现有 Claude Code 项目零影响——安装路径不变、agent 路径不变、工作流不变
- ✅ 两种平台共享同一套写作流程——设定→卷纲→章纲→提示词→正文→验收→归档，一模一样
- ✅ 两种平台共享同一套知识库和记忆系统——`.claude/knowledge/` 和 `.claude/memory/` 通用

---

## 适合视频呈现的亮点

1. **社区贡献故事** — B站小伙伴自发适配，我们 review 后合入主线。前后对比了 20+ 个文件的差异，发现 main 的格式天然兼容，最终只改了 7 个文件 100 多行代码。

2. **"或"关系的设计取舍** — 不是简单地在两个目录都写一遍，而是通过 `SKILL_HOME` 路径检测平台，只部署当前平台需要的目录。代码量不大但设计思路清晰。

3. **向后兼容的范本** — 所有改动加在一起没有动过一行 agent 定义、没有改过一条写作流程、没有影响一个现有项目。纯粹的增量改动。
