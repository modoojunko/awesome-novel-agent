# v4.15.0 版本说明

> **关键词：** 支持 DeepSeek Harness（dsh）平台

---

## 一句话

**新增 deepseek-harness（dsh）平台支持：项目级 skill 部署到 `.dsh/skills/`（agents 即 skills，与 ZCode 同构），`--platform dsh` 全链路打通（init / sync / install / 测试 / 文档）。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **dsh 平台定义** | `platforms.py` 新增 `dsh` Platform（根目录 `.dsh/`，agents=None，skill 根 `.dsh/skills/`）与路径自动识别（SKILL_HOME 含 `.dsh` 即判定） |
| **dsh skill 生成** | 新增 `_convert_to_dsh` / `_convert_dsh_inline_skill` / `deploy_dsh_skills`：9 个 agent + memory-recording / roleplay-sandbox 共 11 个 SKILL.md；frontmatter 只保留 dsh 识别的 `name`/`description`（无 allowed-tools/runAs 噪音）；novel-agent 内联「DeepSeek Harness 调度适配」段（用 `subagent` 工具调度，子 agent 先 `skill(name=...)` 加载自身指令） |
| **init / sync 接线** | `init.py --platform dsh` 项目级部署到 `.dsh/`（模板路径改写 `.claude/agents/` → `.dsh/skills/`）；`sync-project.py` 的 skills 派生产物检测与同步分支覆盖 dsh |
| **install 脚本** | `install.sh` / `install.ps1` 新增 `dsh` 平台（用户级安装到 `~/.dsh/skills/awesome-novel/`），pyyaml 门槛同步覆盖 |
| **测试** | `test_platforms.py` 新增 28 项检查：detect 路径识别、frontmatter 纯净性、引用改写、E2E init/sync 无 `.claude` 残留 |
| **文档** | README / README-en 新增 badge、安装表行与 dsh 集成章节（安装 / 初始化 / 开始写作 / 项目结构差异） |

---

## 兼容性

- 存量项目：无迁移。dsh 是新平台，不影响既有 claude / opencode / reasonix / codex / zcode 项目。
- dsh 项目升级用 `python tools/sync-project.py <项目路径> --platform dsh`，skill 派生产物由同步重新生成。

---

## 验证方法

- `python tools/test_platforms.py`：187/187 通过（新增 dsh 28 项检查）
- `python -m py_compile tools/*.py` 通过
- 实测 `init.py --platform dsh`：11 个 SKILL.md 正确生成（frontmatter 只 name/description、引用改写为 `.dsh/`、novel-agent 含调度适配段）；`sync-project.py --platform dsh` 正常同步、`--check` 正确报告最新
