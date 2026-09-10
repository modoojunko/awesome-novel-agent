# Tasks: 2026-09-04-enhance-generation-prompt-antiai

## 1. 分支与知识层

- [ ] 1.1 从 main 新建分支（worktree 隔离，仓库惯例禁直接改 main），验证：`git worktree list` 可见新 worktree
- [ ] 1.2 新建 `knowledge/anti-ai/statistical-anchor.md`：五类锚全部以区间定义（句长节奏约每 4-7 句 1 个 ≤5 字碎句 / 段落节奏约每 6-10 段 1 个一句话段 / 每段逗号 0-4 不固定 / 起句类型连续 3 段不重复 / 关键名词不换说法），附情绪段→节奏倾向映射表（紧张/爆发→密端、舒缓/铺垫→疏端）与「参数是本章情绪曲线因变量、防均匀化下限保护而非写作目标」原则声明；禁用「必须/不得低于/占比不低于/全局固定值」式硬配额；剔除视角混用与省略号/破折号建议；文件头标注改写来源与「公开/商用前需原作者确认」、单书实测默认值按书校准声明。验证：`grep -rn "朱雀\|检测器平台名"` 无命中、`grep -n "占比不低于\|不得低于"` 无命中，人工核对五类锚与映射表齐备
- [ ] 1.3 `knowledge/anti-ai/common-rules.md` T1 新增华美空洞家族（单句形容词 >3 个拆句 / 开篇环境外貌描写砍到两三笔 / 意象必须真实可发生 + 细腻文笔低级错误组合警示），每条带「为什么禁 + 改成什么」。验证：`python tools/check-conflicts.py` exit 0
- [ ] 1.4 `knowledge/anti-ai/living-voice.md` 新增三节：情绪清单禁 / 偏差表达（反应属于此人）/ 描写显形判据（删掉它人物还成立吗），不定义数量线。验证：`git diff` 仅新增行，无「N次/章」式数量线
- [ ] 1.5 `knowledge/anti-ai/structural-heat.md` 定律 2 增补对话密度线达标区（句句带货时对白行占比 50-70% 为达标区）、定律 3 增补中段位置实测（约 60-85% 内容对修改免疫、地板 0.55-0.68、纯对话段置中段参考），嵌入既有定律不新增编号，标注外部单书实测。验证：定律标题数仍为 7，`python tools/check-conflicts.py` exit 0
- [ ] 1.6 `knowledge/anti-ai/README.md` 目录表加入 `statistical-anchor.md` 行。验证：目录与实际文件一致

## 2. 部署链（先红后绿）

- [ ] 2.1 先红：`tools/test_platforms.py` 在既有「anti-ai.md 合并结构热源定律」断言旁新增「合并产物含统计节奏锚」断言，运行确认 FAIL（此时合并清单未含新文件）。验证：退出码非 0 且失败项为新断言
- [ ] 2.2 转绿：`tools/init.py` L402 anti-ai 合并清单元组加入 `statistical-anchor.md` 并同步注释。验证：`python tools/test_platforms.py` 全绿
- [ ] 2.3 E2E 部署抽查：临时目录跑 `python tools/init.py`（任一平台），确认 `.claude/knowledge/anti-ai.md` 同时含统计锚、华美空洞、正向三节、对话密度线增补。验证：四处内容 grep 全命中

## 3. 生成层（prompt-crafting）

- [ ] 3.1 `skills/prompt-crafting.md` 反 AI 注入范围扩充：①Step 1.6 活人感正向要点覆盖情绪清单禁/偏差表达/描写显形（各 1-2 句精炼注入）、T1 简表覆盖华美空洞家族；②新增「本章节奏参数实例化」步骤——从统计锚区间按本章情绪曲线与场景权重取一组具体参数（读上一章 prompt 文件核对、与上章参数错开、禁止跨章同参），注入「质感要求」子节（带「与红线/字数/T1/认知动词/感官冲突时让步、压缩段豁免、情绪段变速优先」声明）；③关键名词不换说法注入「输出·写作规范」（对象限定核心名词/术语/人名）；节奏参数 MUST NOT 进不可违反规则区，不重复既有「叙事节奏交替」语义。验证：`python tools/check-agents.py` exit 0
- [ ] 3.2 同文件 Step 4 验收自检表同步：「反AI注入范围」项含本章节奏参数（归宿正确、与上章不同参、无占比下限）与正向要点新增条目，「组装后去重检查」提示含节奏参数与既有节奏规则的口径；T2/T3 与疲劳词阈值仍标注不注入。验证：自检表条目与 Step 1.6 一一对应

## 4. 全链回归与收尾

- [ ] 4.1 全链回归：`python -m py_compile tools/*.py`、`python tools/test_platforms.py`、`python tools/check-agents.py`、`python tools/check-conflicts.py` 全部 exit 0。验证：四条命令输出无 FAIL
- [ ] 4.2 AI 终端实测（仓库提交前要求）：至少一种终端实测 prompt 组装，确认生成的 `prompts/*.md` 写作规范段含统计锚与新增正向要点、读感无自我引用痕迹。验证：实测记录附入 PR 描述
- [ ] 4.3 提交并建 PR（`feat: 生成提示词反AI注入增量`，关联本 change），PR 合并后按发版流程决定是否 bump VERSION 与写 releasenotes。验证：CI 绿、review 通过
