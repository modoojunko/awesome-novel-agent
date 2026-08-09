# Repository Guidelines

## 项目结构与模块组织

- `agents/` — 8 个写作 agent 定义（novel-agent 总指挥 + 7 个子 agent），Markdown + frontmatter。
- `skills/` — 各 agent 的 SOP 指令，按 `{环节}-{动作}.md` 命名。
- `knowledge/` — 知识库：`genre-example/` 题材档案、`anti-ai/` 反 AI 规则、`format-specs/` 格式规范、`{plot|scene|character|title}-craft/` 创作方法论。
- `templates/` — 项目初始化模板（`settings/`、`migration/` 旧项目迁移）。
- `tools/` — Python 工具：`init.py`（初始化）、`sync-project.py`（同步）、`platforms.py`（平台适配）、`check-agents.py` / `check-conflicts.py`（静态检查）、`test_platforms.py`（测试）。
- 根目录：`README.md` / `README-en.md`、`SKILL.md`、`skill.json`、`ARCHITECTURE.md`、`CONTRIBUTING.md`、`install.sh` / `install.ps1`；图片素材在 `reference/images/`。

## 构建、测试与开发命令

无构建步骤。Python 主体仅用标准库；`--platform opencode|reasonix|codex` 的 agent 转换需要 pyyaml（见 `tools/requirements.txt`，CI 自动安装）：

- `python tools/init.py <项目路径> [--genre N] [--platform claude|opencode|reasonix|codex]` — 初始化小说项目骨架
- `python tools/sync-project.py <项目路径> --check` — 检查项目是否需要同步（0=最新，1=有更新，2=无效）
- `python tools/test_platforms.py` — 运行测试（退出码 0=通过）
- `python tools/check-agents.py` — 校验 agent frontmatter 引用路径
- `python tools/check-conflicts.py` — 检查反 AI 规则阈值冲突
- `python -m py_compile tools/*.py` — 语法检查

CI：`.github/workflows/static.yml`，push main 时运行语法/agent/规则检查 + 平台测试套件，并部署 GitHub Pages。

## 编码风格与命名约定

- Python：snake_case 文件名；仅标准库；入口脚本顶部用 `reconfigure(encoding="utf-8")` 防 Windows 中文乱码；docstring 写明用法与退出码。
- Markdown：中文正文、UTF-8；frontmatter 引用路径相对仓库根解析。
- 命名：agent 定义 `{role}-agent.md`；章节 `vol-{N}-ch-{M}.md`、卷纲 `volume-{N}.md`；知识文件按 `knowledge/<分类>/<题材或主题>.md` 组织。
- 改动贴合项目定位（AI 辅助小说创作），不引入无关功能或依赖。

## 测试指南

- 无第三方测试框架；`tools/test_platforms.py` 自写断言，stdout 打印 `ok/FAIL`，非 0 退出码表示失败。
- 测试函数以 `test_` 开头；E2E 用临时目录验证 init/sync 在 claude/opencode/reasonix/codex 四平台的输出。
- 涉及 agent 定义跑 `check-agents.py`，涉及反 AI 规则跑 `check-conflicts.py`。
- 行为变更遵循先红后绿：先加失败用例，再实现（见 `docs/superpowers/` 计划）。

## 提交与 PR 指南

- 提交信息遵循 Conventional Commits + 中文描述：`feat:` / `fix:` / `docs:` / `test:` / `refactor:` / `chore:`，如 `fix: sync-project --platform 值守卫防吞 --check`。
- 发版时 `chore: bump version to vX.Y.Z`，同步更新 `VERSION` 与 `docs/releasenote-*`。
- PR：从 main 新建分支，禁止直接改 main；单个 PR 聚焦一项改动并关联 issue；提交前至少在一种 AI 终端实测（claude/opencode/reasonix/codex）。

## 安全与配置提示

- 平台适配逻辑集中在 `tools/platforms.py`，新增平台或修改目录约定时先改这里，再同步 init/sync。
- 遵守 GPLv3，不提交无版权素材、侵权文案或用户小说内容。
