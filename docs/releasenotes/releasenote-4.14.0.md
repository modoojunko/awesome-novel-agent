# v4.14.0 版本说明

> **关键词：** ZCode 平台支持、agents 即 skills、五平台、install 门槛扩展

---

## 一句话

**新增第 5 个平台 ZCode（skill 约定与 Claude Code 同源，天然兼容；无项目级 agents 目录，agents 即 skills，与 Reasonix 同构部署），init/sync/install 全链路支持，平台从四选一变为五选一。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **ZCode 平台**（`platforms.py`） | 新增 zcode 平台（`.zcode/`，agents=None）+ `_convert_to_zcode` / `deploy_zcode_skills`：Claude agent frontmatter → ZCode skill frontmatter（`allowed-tools` 裸名保留、Agent 剔除），novel-agent 追加「Agent 工具按 skill 名调度子 agent」适配段，引用改写为 `.zcode/` |
| **项目级部署**（`init.py` / `sync-project.py`） | `--platform zcode` 生成 11 个 SKILL.md（9 个 agent + memory-recording / roleplay-sandbox），知识/记忆落 `.zcode/knowledge/`、`.zcode/memory/`；模板引用改写（AGENTS.md / CLAUDE.md → `.zcode/skills/`）；同步/指纹/`--check` 全链路 |
| **安装**（`install.sh` / `install.ps1`） | 新增 `zcode` 安装目标 `~/.zcode/skills/awesome-novel/`，pyyaml fail-fast 门槛同步扩展（zcode 转换依赖 pyyaml） |
| **文档** | README / README-en / SKILL.md / ARCHITECTURE.md / AGENTS.md 平台列表五选一、ZCode 集成章节、badge |
| **测试** | `test_platforms.py` 新增 zcode 单元（检测/配置/引用改写/pyyaml 预检）+ E2E（init 布局、11 skill、模板改写、sync 保持格式） |

---

## 兼容性

- 存量项目：不变。ZCode 是全新平台，不影响 claude/opencode/reasonix/codex 既有项目。
- ZCode 用户：skill 本体需 `./install.sh zcode` 用户级安装；项目内容由 `init.py --platform zcode` 项目级部署，升级时用 `sync-project.py --platform zcode`。
- 非 claude 平台转换统一走 `style_common.split_frontmatter` 单源解析（review #38 口径），frontmatter 含 `---` 分隔线的正文不再错位。

---

## 验证方法

- `python tools/test_platforms.py`：154/154 通过（含 35 个 zcode 用例）
- `python tools/test_style_rules.py`：125/125 通过
- `python tools/test_style_distill.py`：84/84 通过
- `python tools/check-agents.py` / `check-conflicts.py` / `py_compile` / `bash -n install.sh` 全部通过
