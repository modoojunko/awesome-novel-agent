## 1. writer 写前反闭环卡

- [x] 1.1 `skills/writing-execution.md` 起草节前加"每场五行反闭环卡"步骤与不开写条件（验证：步骤可执行、话术过 author-communication 对照表）
- [x] 1.2 引用 `.claude/knowledge/anti-ai/structural-heat.md` 作为卡的判定依据（验证：`check-agents.py` exit 0）

## 2. prompt 结构禁令注入

- [x] 2.1 `skills/prompt-crafting.md` 写前约束清单加结构禁令段：问答回合拍数默认上限（新刻度，注明与 Gate E5 句数刻度并行）、章首冷开场、禁同场连续多套回执叠加（单回执爽点兑现场豁免）、过桥链/证明链禁令、章尾禁总结/升华/预告（引用 Gate F + 章纲落点优先），整段带裁决顺序声明（验证：条目齐备、不整段复制知识文件）
- [x] 2.2 冲突对照核查：逐条对照既有口径（Gate A-F、common-rules 数值、既有提示词节奏规则），确认禁令段无重复定义、无方向相反指令（验证：对照清单零矛盾，含标点/对话频率/章尾三处专项）
- [x] 2.3 `knowledge/format-specs/author-communication.md` 对照表补新增内部名词（验证：作者可见文本无未翻译内部名词）

## 3. anti-ai 结构扫描与双脚本初筛

- [x] 3.1 `skills/anti-ai.md` Phase 1 前加结构热源扫描步骤，报告格式加"结构命中"单列节（验证：Gate A-F 编号不变）
- [x] 3.2 Phase 2 机器初筛并列调用 `check-chapter.py`，沿用既有降级语义（验证：与 check-prose 的调用/降级描述一致）
- [x] 3.3 `python tools/check-agents.py`（验证：exit 0）

## 4. 骨架模板与部署

- [x] 4.1 新增 `templates/sandbox/detect-battles.md`、`templates/sandbox/prose-regressions.txt`、`templates/sandbox/locked-lines.txt`（验证：模板含使用说明与示例，语言为作者可读）
- [x] 4.2 `tools/init.py` 生成三个骨架；`tools/sync-project.py` 覆盖检测（验证：临时目录 init 后文件存在，sync --check 行为正确）
- [x] 4.3 `tools/test_platforms.py` E2E 断言三文件（验证：七平台测试退出码 0）

## 5. 收尾与发版

- [x] 5.1 全量检查：`check-agents.py` + `check-conflicts.py` + `py_compile` + `test_platforms.py`（验证：全绿）
- [ ] 5.2 至少一个 AI 终端实测：初始化新项目→走一遍 writer/prompt/anti-ai 挂接点（验证：按仓库提交指南）
- [x] 5.3 发版 `chore: bump version to v4.23.0`，更新 `VERSION` 与 `docs/releasenotes/releasenote-4.23.0.md`（验证：`check-version.py` 通过）
