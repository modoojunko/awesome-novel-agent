## 1. 结构热源知识文件

- [x] 1.1 写 `knowledge/anti-ai/structural-heat.md`：七条定律 + ≥13 种高风险结构，去书名化，逐条带实测分数，引用路径用部署后基座（验证：人工核对内容清单）
- [x] 1.2 对比包内模块 4 与 `knowledge/anti-ai/common-rules.md`/`anti-ai-writing.md`，列增量条目清单并合并（只增不删）（验证：git diff 仅新增行，逐条可追溯来源）
- [x] 1.3 跑 `python tools/check-agents.py` 与 `python tools/check-conflicts.py`（验证：双 0 退出）

## 2. 章节检查工具（先红后绿）

- [x] 2.1 写 `tools/test_check_chapter.py` 失败用例：各检查项正/反例、退出码 0/1/2、回归库与白名单缺失/命中、CRLF 输入（验证：当前实现不存在，测试红）
- [x] 2.2 实现 `tools/check-chapter.py`：硬性项（夹层标签式/嵌套双引号/半角引号/破折省略/字数逐字对账/回归串）+ 警告项（广义夹层/问答并段/弱化副词/字数待人工/尾随标签窄集）+ 平台口径字数统计 + 外置文件读取（验证：2.1 全绿）
- [x] 2.3 `python -m py_compile tools/*.py` 与 `python tools/test_check_chapter.py`（验证：编译零错、测试退出码 0）

## 3. 部署接入

- [x] 3.1 `tools/init.py` 与 `tools/sync-project.py` 部署清单加入 `check-chapter.py`（部署到 `<平台根>/tools/`，与 check-prose.py 同机制）（验证：临时目录 init 后文件存在）
- [x] 3.2 `tools/test_platforms.py` E2E 断言新工具在七平台输出中存在（验证：`python tools/test_platforms.py` 退出码 0）

## 4. 收尾与发版

- [x] 4.1 全量检查：`check-agents.py` + `check-conflicts.py` + `py_compile` + 两个测试脚本（验证：全绿）
- [x] 4.2 在至少一个 AI 终端实测初始化项目并跑一次 check-chapter（验证：按仓库提交指南）
  - 2026-08-31 claude 无头会话实测：init 临时项目→部署产物可运行；anti-ai 会话实际执行两个脚本，check-chapter exit 1 正确命中夹层硬伤、5 项警告逐条列出（详见 PR test/ai-terminal-verification）
- [x] 4.3 发版 `chore: bump version to v4.22.0`，更新 `VERSION` 与 `docs/releasenotes/releasenote-4.22.0.md`（验证：`check-version.py` 通过）
