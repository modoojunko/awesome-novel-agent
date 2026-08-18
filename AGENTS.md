# Repository Guidelines

## 工作原则

减少常见 LLM 编码错误的行为准则。权衡：这些准则倾向于谨慎而非速度。对于简单任务，请自行判断。

### 1. 编码前先思考
不要假设。不要隐藏困惑。显化权衡。

在实现之前：
- 明确陈述你的假设。如果不确定，请提问。
- 如果存在多种解读，请全部呈现——不要默默选择。
- 如果存在更简单的方案，请说出来。必要时坚持己见。
- 如果有不清楚的地方，停下来。指出哪里令人困惑。提问。

### 2. 简洁优先
用最少的代码解决问题。不做任何推测性的设计。

- 不添加超出需求的功能。
- 不为只用一次的代码做抽象。
- 不引入未被要求的"灵活性"或"可配置性"。
- 不处理不可能发生的场景的错误。
- 如果你写了 200 行但 50 行就能搞定，重写它。
- 问自己："资深工程师会说这过度设计了吗？"如果答案是肯定的，简化它。

### 3. 精准修改
只碰你必须碰的。只清理你自己留下的混乱。

编辑现有代码时：
- 不要"改进"相邻的代码、注释或格式。
- 不要重构没坏的东西。
- 匹配现有风格，即使你自己不会那样写。
- 如果你注意到无关的废弃代码，提出来——不要删除它。

当你的变更产生孤儿代码时：
- 删除你的变更导致不再使用的 import/变量/函数。
- 不要删除既有的废弃代码，除非被要求。
- 检验标准：每一行变更都应能直接追溯到用户的请求。

### 4. 目标驱动执行
定义成功标准。循环验证直到通过。

将任务转化为可验证的目标：
- "添加校验" → "为无效输入编写测试，然后让它们通过"
- "修复 Bug" → "编写一个能复现它的测试，然后让它通过"
- "重构 X" → "确保重构前后测试都通过"

对于多步骤任务，简要列出计划：
1. [步骤] → 验证：[检查点]
2. [步骤] → 验证：[检查点]
3. [步骤] → 验证：[检查点]

强有力的成功标准让你能独立循环。弱标准（"让它跑起来"）需要不断澄清。

## 面向作者沟通

agent 与作家对话、提问、展示、确认一律用日常大白话。铁律与"内部名词 → 作者用语"对照表见 `knowledge/format-specs/author-communication.md`（部署后为 `.claude/knowledge/author-communication.md`，与作者对话的 agent 均已挂引用）：内部字段名、自创术语、流程词不得出现在作者可见文本；给作者看结构用摘要模板，不展示原文结构；网文通用词（爽点/打脸/钩子/金手指/卷纲/章纲等）保留不翻译。修改 agent 话术时先查对照表；新增内部名词同步补表。

## 项目结构与模块组织

- `agents/` — 9 个写作 agent 定义（novel-agent 总指挥 + 8 个子 agent），Markdown + frontmatter。
- `skills/` — 各 agent 的 SOP 指令，按 `{环节}-{动作}.md` 命名。
- `knowledge/` — 知识库：`genre-example/` 题材档案、`anti-ai/` 反 AI 规则、`format-specs/` 格式规范、`{plot|scene|character|title}-craft/` 创作方法论。
- `templates/` — 项目初始化模板（`settings/`、`migration/` 旧项目迁移）。
- `tools/` — Python 工具：`init.py`（初始化）、`sync-project.py`（同步）、`platforms.py`（平台适配）、`check-agents.py` / `check-conflicts.py` / `check-version.py` / `check-python.py` / `check-yaml.py`（静态检查）、`check-prose.py`（正文 AI 味机器检测，anti-ai Phase 2 初筛/Phase 4 复跑用，init/sync 部署到 `<平台根>/tools/`）、`style_render.py` / `style_verify.py` / `style_common.py`（style-distill 渲染/验收/共享）、`test_platforms.py` / `test_style_rules.py` / `test_style_distill.py` / `test_check_prose.py`（测试）、`test_util.py`（测试共享）。
- 根目录：`README.md` / `README-en.md`、`SKILL.md`、`skill.json`、`ARCHITECTURE.md`、`CONTRIBUTING.md`、`install.sh` / `install.ps1`；图片素材在 `reference/images/`。

## 构建、测试与开发命令

无构建步骤。Python 主体仅用标准库；pyyaml 例外：`--platform opencode|reasonix|codex|zcode|dsh` 的 agent 转换（platforms.py）与 style-distill 卡 frontmatter 解析/校验（style_common.py / style_render.py / check-agents.py）（见 `tools/requirements.txt`，CI 自动安装）：
- `python tools/init.py <项目路径> [--genre N] [--platform claude|opencode|reasonix|codex|zcode|dsh]` — 初始化小说项目骨架
- `python tools/sync-project.py <项目路径> --check` — 检查项目是否需要同步（0=最新，1=有更新，2=无效）
- `python tools/test_platforms.py` — 运行测试（退出码 0=通过）
- `python tools/check-agents.py` — 校验 agent frontmatter 引用路径
- `python tools/check-conflicts.py` — 检查反 AI 规则阈值冲突
- `python -m py_compile tools/*.py` — 语法检查

CI：`.github/workflows/static.yml`，push main 时运行语法/agent/规则检查 + 平台测试套件，并部署 GitHub Pages。

## 编码风格与命名约定

- Python：snake_case 文件名；仅标准库；入口脚本顶部用 `reconfigure(encoding="utf-8")` 防 Windows 中文乱码；docstring 写明用法与退出码。
- Markdown：中文正文、UTF-8；frontmatter 与正文中引用的项目内文件一律写**部署后路径**——knowledge 用 `.claude/knowledge/...` 基座（format-specs 拍平/合并后仓库相对路径会断链，check-agents.py 按部署布局校验），skills/ 引用用 `skills/xxx.md`（仓库内路径，必存在），settings/ 等项目生成文件用相对项目根的路径。部署后路径由 init.py 的 rewrite_refs 按平台改写前缀。
- 命名：agent 定义 `{role}-agent.md`；章节 `vol-{N}-ch-{M}.md`、卷纲 `volume-{N}.md`；知识文件按 `knowledge/<分类>/<题材或主题>.md` 组织。
- 改动贴合项目定位（AI 辅助小说创作），不引入无关功能或依赖。

## 测试指南

- 无第三方测试框架；`tools/test_platforms.py` 自写断言，stdout 打印 `ok/FAIL`，非 0 退出码表示失败。
- 测试函数以 `test_` 开头；E2E 用临时目录验证 init/sync 在 claude/opencode/reasonix/codex/zcode/dsh 六平台的输出。
- 涉及 agent 定义跑 `check-agents.py`，涉及反 AI 规则跑 `check-conflicts.py`。
- 行为变更遵循先红后绿：先加失败用例，再实现。

## 提交与 PR 指南

- 提交信息遵循 Conventional Commits + 中文描述：`feat:` / `fix:` / `docs:` / `test:` / `refactor:` / `chore:`，如 `fix: sync-project --platform 值守卫防吞 --check`。
- 发版时 `chore: bump version to vX.Y.Z`，同步更新 `VERSION` 与 `docs/releasenote-*`。
- PR：从 main 新建分支，禁止直接改 main；单个 PR 聚焦一项改动并关联 issue；提交前至少在一种 AI 终端实测（claude/opencode/reasonix/codex/zcode/dsh）。

## 安全与配置提示

- 平台适配逻辑集中在 `tools/platforms.py`，新增平台或修改目录约定时先改这里，再同步 init/sync。
- 遵守 GPLv3，不提交无版权素材、侵权文案或用户小说内容。
