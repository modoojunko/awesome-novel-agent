# v4.12.0 版本说明

> **关键词：** Codex 平台支持、四平台适配、安装/检视修复、landing page

---

## 一句话

**新增 Codex 平台支持，与 Claude Code / OpenCode / Reasonix 并列成为第四平台：skill 用户级安装到 `~/.codex/skills/awesome-novel/`，初始化时把 8 个自定义 agent 以 Codex 官方 TOML 部署到项目 `.codex/agents/`，novel-agent 用 `spawn_agent` 调度子 agent。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **平台适配层**（`tools/platforms.py`） | 新增 codex 平台条目；`convert_to_codex()` 把 8 个 Claude agent frontmatter 转换为 Codex 官方 TOML（`name`/`description`/`developer_instructions`），SOP 内联、`Agent`→`spawn_agent`、`.claude/` 引用改写；`ensure_yaml()` 依赖预检 |
| **初始化/同步** | `init.py --platform codex` 项目级部署 `.codex/agents/*.toml` + `.codex/skills/`（memory-recording、roleplay-sandbox）+ knowledge/memory；生成 Codex 版 `AGENTS.md`；`sync-project.py` 按源指纹重新生成派生产物 |
| **安装** | `install.sh codex` / `install.ps1 codex` 装到用户级 `~/.codex/skills/awesome-novel/`；修复全新 HOME 首次安装被安全校验误拒（F1） |
| **检视修复** | `rewrite_refs` 清除部署产物裸 `.claude/` 残留（F2）；`memory-format-spec.md` 改平台无关表述（F3）；CI 增加平台测试步骤（F4）；缺 pyyaml 时明确报错而非静默产出损坏 TOML（F5）；install.sh 先校验后建目录、codex 检测改 `.codex` 路径段匹配 |
| **文档与 landing page** | README（中/英）、SKILL.md、ARCHITECTURE.md、skill.json、根 AGENTS.md、平台适配 spec 同步；`index.html` 补充 Codex/OpenCode/Reasonix 安装说明 |
| **CI** | `test_platforms.py` 纳入检查；`pull_request` 触发；Pages 部署仅限 main 推送 |

---

## 验证方法

- `tools/test_platforms.py`：90/90 通过（四平台回归 + codex 单元/E2E/负向用例 + F1/P2/P3 回归）
- `py_compile`、`check-agents.py`、`check-conflicts.py`、`bash -n install.sh` 全过
- Codex 实测 demo：init → 设定 → 卷纲 → 章纲 → 提示词 → 正文 → 去 AI 味 → 归档，第一章完成

---

## 兼容性保证

- 新增平台不改变既有三平台行为；四平台共享同一套写作流程与知识库
- `opencode` / `reasonix` / `codex` 的 agent 转换需要 pyyaml（`tools/requirements.txt` 已声明，CI 自动安装；缺失时 init/sync 明确报错）
