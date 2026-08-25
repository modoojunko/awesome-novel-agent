# v4.20.0 版本说明

> **关键词：** 第 7 平台 —— 接入 Grok Build：原生 agents 部署 + spawn_subagent 调度 + 子代理权限硬约束

---

## 一句话

接入 [Grok Build](https://docs.x.ai/build/overview)（SpaceXAI 的编码 agent TUI，PR #118，作者 @BillChenIDY）：skill 本体用户级安装到 `~/.grok/skills/awesome-novel/`，9 个自定义 agent 以 Grok 原生发现路径 `.grok/agents/*.md` 项目级部署，novel-agent 用 `spawn_subagent` 调度子 agent（必须在主会话运行，Grok 子代理深度上限为 1），order 文件协议与其余六平台完全一致。

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **平台接入** | `install.sh` / `install.ps1` 新增 `grok`（skill 装到 `~/.grok/skills/awesome-novel/`）；`init.py --platform grok` 初始化、`sync-project.py --platform grok` 升级同步；pyyaml 安装门槛与运行时检查同步覆盖（grok 的 agent 转换依赖 frontmatter 解析） |
| **agent 转换（convert_to_grok）** | Claude Code agent frontmatter → Grok agent Markdown：工具名映射 `Read→read_file` / `Write→write` / `Edit→search_replace` / `Glob→list_dir` / `Grep→grep` / `Bash→run_terminal_command`，`Agent` 保留指令拼写（授权派发工具族）；Claude 私有字段（role/react/memory/knowledge）丢弃；SOP 内联正文（两边的 skills 字段格式不兼容）；引用改写为 `.grok/knowledge|memory` |
| **调度模型** | novel-agent 注入 Grok 调度适配段：用 `spawn_subagent(subagent_type=<子agent名>, isolation="none")` 调度（共享工作区，子 agent 写回同一项目），一次一个任务、等 `status: DONE` 再派下一个；novel-agent 必须在主会话运行——Grok 子代理不能再派子代理（深度上限 1），把 novel-agent 当 subagent 会让调度链断裂 |
| **子代理权限硬约束** | 子 agent 的 `tools` 剔除 `Agent` 指令 + `disallowedTools: [Agent]`（按指令拼写 deny，剥离派发工具族）+ `agentsMd: false`；正文置顶注入调度禁令：禁止任何形式的派生/递归，禁止越权写 order 与进度字段，需要协作时在回复中告知 novel-agent |
| **独立工具** | memory-recording、roleplay-sandbox 部署为 `.grok/skills/<name>/SKILL.md`（不进调度链，与 codex 同构） |
| **文档与口径** | README / README-en / SKILL.md / ARCHITECTURE.md / AGENTS.md / install 脚本 / memory-format-spec 全部同步为七平台口径 |

---

## 兼容性

- 纯新增平台，存量六平台（claude/opencode/reasonix/codex/zcode/dsh）行为不变；已初始化项目无需任何操作。
- Grok Build 新用户：`./install.sh grok`（Windows 用 `install.ps1 grok`）装本体，再 `python ~/.grok/skills/awesome-novel/tools/init.py <项目路径> --platform grok` 初始化。
- grok 平台与其他转换平台一样需要 pyyaml（缺依赖时安装/初始化均 fail-fast 报错，不产出损坏产物）。
- 升级已有 grok 项目用 `python tools/sync-project.py <项目路径> --platform grok`；skill_version 将更新为 4.20.0。

---

## 验证方法

- `test_platforms.py` 新增 grok 全链路断言：init/sync E2E（9 个 agent Markdown + 独立工具 skill + 引用改写 + 无 .claude 残留）、frontmatter 用 `yaml.safe_load` 解析断言（子 agent 未授权且 deny `Agent`、novel-agent 授权 `Agent`、anti-ai 保留 `run_terminal_command`）——**253 通过 0 失败**。
- 静态检查全绿：check-agents / check-conflicts / check-version / py_compile。
- review-agent 三轮评审闭环：2 个问题合并前修复——P1（tools 写调用名 `spawn_subagent` 匹配不到任何工具，novel-agent 失去派发能力，改回 `Agent` 指令拼写）、P3（子 agent 同时输出授权与 deny 的矛盾配置，守卫条件同步修正）。工具授权语义均对照 xai-org/grok-build 源码逐条核实。
- 待作者侧：真机 Grok Build 实测「安装 → novel-agent 派 updater」一环（全部语义经源码静态验证，尚未真机跑过）。
