# Proposal: 2026-09-04-enhance-generation-prompt-antiai

## Why

去 AI 味资产包（2026-09-03 获赠，`~/Downloads/去AI味资产包_20260903/`）与本仓库反 AI 体系同源，逐件对比后确认：清创侧（anti-ai 管线）与结构热源知识约七成已有等价实现，但**生成侧（prompt-crafting 组装提示词）存在五处真实增量**——现有生成提示词的节奏约束全为定性表述（「句式长短交替」「禁止通篇等长段落」），无统计分布锚；同义词循环已在 anti-ai-writing.md 识别为 AI 指纹（1.4 节）但生成侧没有正向解法；描写密度与物理真实性无约束线；情绪清单与通用反应无禁令；场景排序缺对话位置密度知识。本次只引入对生成提示词有直接提升的部分，清创侧词表增量不在本 change 范围。

## What Changes

- `skills/prompt-crafting.md` 反 AI 注入范围扩充 5 类，注入通道（活人感正向要点 + T1 简表 + 元叙事禁止 + 题材正反例）与稀疏注入原则、生成与清创分离原则不变：
  1. **统计节奏锚（每章实例化）**：锚以区间定义——碎句约每 4-7 句 1 个、一句话段约每 6-10 段 1 个、逗号 0-4 不固定、起句类型连续 3 段不重复；prompt-crafter 按本章情绪曲线从区间取一组「本章节奏参数」注入，参数章章不同（紧张章碎句密、舒缓章长句慢），禁止跨章同参
  2. **关键名词不换说法**：核心名词/术语重复使用同一说法，禁止同义词轮换
  3. **华美空洞防护**：开篇环境/外貌描写砍到两三笔、意象必须真实可发生、细腻文笔+低级常识错误组合是 AI 铁证
  4. **情绪清单禁 + 偏差表达**：禁止把复杂情绪列成清单，反应必须属于「此人」（偏差表达，非安全表达）
  5. **描写让人显形**：判据「删掉这段描写，人物还成立吗」
- `knowledge/anti-ai/` 新增 `statistical-anchor.md`（通用化改写：去书名/去检测器专名/去省略号破折号建议/去视角混用条目，标注单书实测来源与按书校准声明）
- `knowledge/anti-ai/common-rules.md` T1 新增华美空洞家族（形容词堆叠 / 开篇描写堆砌 / 物理不通意象），使清创侧与注入侧同源
- `knowledge/anti-ai/living-voice.md` 新增情绪清单禁、偏差表达原则、描写显形判据（正向原则，不定义新阈值）
- `knowledge/anti-ai/structural-heat.md` 定律 2/3 增补对话密度线达标区（句句带货时对白行占比 50-70% 为达标区）与中段位置实测（60-85% 内容免疫、地板 0.55-0.68），沿用「单书实测默认值、按书校准」框架
- `tools/init.py` anti-ai 合并清单加入 `statistical-anchor.md`

## Capabilities

### New Capabilities

- `generation-prompt-antiai`: prompt-crafter 生成提示词的反 AI 注入增量——统计分布锚、关键名词不换说法、华美空洞防护、情绪清单禁与偏差表达、描写显形判据、对话位置排序参考，以及注入范围约束（统计锚按分布倾向表述不写成配额、负面清单只进 T1 简表通道、生成与清创分离不变）

### Modified Capabilities

（无——structural-heat.md 为定律内数据增补，不新增定律、不修改既有 requirement，不列 spec delta。）

## Impact

- **代码/文档**：`skills/prompt-crafting.md`（Step 1.6 注入范围 + Step 4 验收自检表「反AI注入范围」检查项）、`knowledge/anti-ai/`（1 新文件 + 3 文件增补 + README 目录）、`tools/init.py`（合并清单）
- **部署产物**：`.claude/knowledge/anti-ai.md` 体积增加约 4-6KB，无新失效路径（仍单文件合并产物）；每章生成提示词固定注入增量约 300 字（统计锚 4 条 + 正向三节 + 华美空洞简表行）
- **检查链**：`check-agents.py`（prompt-crafting 引用路径校验）、`check-conflicts.py`（新量化表述与既有阈值体系无冲突）、`test_platforms.py`（E2E 断言合并产物内容如有需同步）
- **无**新第三方依赖、无平台适配（platforms.py）改动、无破坏性变更
