## Context

- 依赖 change `add-zhuque-source-defense`：知识文件（`knowledge/anti-ai/structural-heat.md`）与 `tools/check-chapter.py` 已存在。
- 现有管线：novel-agent 调度 → prompt-crafter（写提示词）→ writer（起稿）→ anti-ai（Phase 1-4 + Gate G）→ reader → archive；skills 是各 agent 的 SOP 指令，frontmatter 引用路径按部署布局由 `check-agents.py` 校验。
- 项目骨架由 `templates/` + `tools/init.py` 生成，E2E 由 `tools/test_platforms.py` 断言七平台输出。

## Goals / Non-Goals

**Goals:**

- 三个挂接点（writer/prompt/anti-ai）改动最小化：只加引用与步骤，不重写既有 SOP 结构。
- 进化机制文件开箱即用：新项目初始化即带骨架，老项目 sync 可补。
- 作者可见话术合规。

**Non-Goals:**

- 不改调度契约（novel-dispatch.md 的 phase 表不动；detect-loop 的可选 phase 属 `add-detect-loop-skill`）。
- 不做自动送检（本 change 全部离线）。
- 不给老项目写迁移脚本（存量项目由作者按 README 手动补 `sandbox/` 文件即可，sync 只补骨架）。

## Decisions

1. **反闭环卡放 writing-execution（writer 的 SOP），不放 prompt-crafting。**
   卡是写作过程中的自查动作，属执行环节；prompt-crafting 只负责把禁令写进提示词。两处各司其职，避免同一内容双源头维护。
2. **结构禁令以"引用+条目"形式注入提示词，不整段复制知识文件。**
   知识文件会持续修订，整段复制会产生两份漂移副本；提示词列禁令条目（短），判定细则指向知识文件。
3. **anti-ai 结构扫描作为 Phase 1 的前置步骤而非新 Gate。**
   保持 Gate A-F 编号稳定（其他文档大量引用），结构命中在报告中单列一节。备选"新增 Gate H"被否：Gate 是词句级分类，结构命中是整段/整场级，混排会破坏报告格式。
4. **check-chapter 的失败语义并入既有降级体系。**
   anti-ai Phase 2 对 check-prose 已有"缺失/无 python 降级"语义，check-chapter 沿用同一套，不新增阻塞条件。
5. **骨架文件放 `templates/sandbox/`。**
   `sandbox/` 是项目已有目录（试写/沙盒），进化机制文件同属项目工作区，不污染 `settings/`（设定）与 `archives/`（归档）。
6. **skill 文本双轨命名。**
   skills 内部描述用"结构热源/回归库"等内部名词，凡作者可见示例与说明改用日常语言（"容易一眼像 AI 写的段落结构"），对照表同步补词。
7. **提示词注入的三条防冲突纪律（防止污染生成质量）。**
   大模型对矛盾与重复指令敏感：两套口径并行会让 writer 在执行间摇摆，重复条目会放大错误阈值的影响。因此：①**单一权威源**——知识文件是唯一细则源，提示词只放短条目加引用，不整段复制；②**新刻度不重复定义**——只注入既有规则未覆盖的刻度（问答回合拍数），既有口径（Gate E5 句数、common-rules 破折号用法判定、Gate F 章尾）一律引用不重述；③**显式裁决顺序**——作者设定/章纲 > 题材知识 > 结构默认值 > 检测优化写进禁令段，冲突时 writer 无需自行猜优先级。来源包的"章尾极简/钩子搭台打断"与网文钩子文化直接冲突，降为按需深度项默认不启用。

## Risks / Trade-offs

- 三个 skill 是被所有题材共用的，结构禁令若写死数量（如"每 300 字≤8 拍"）可能不适配部分题材 → 禁令写成"默认值+按文风调整"，默认值来自实测数据。
- prompt 变长增加 token 消耗 → 禁令段控制在十余行内，细则外置知识文件。
- init 骨架新增文件会让存量项目 `sync-project --check` 报"有更新" → 属预期行为，发版说明中提示。
