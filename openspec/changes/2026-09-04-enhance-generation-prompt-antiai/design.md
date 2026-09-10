# Design: 2026-09-04-enhance-generation-prompt-antiai

## Context

仓库反 AI 体系分三层：知识层（`knowledge/anti-ai/*.md`，init.py 按固定清单合并为部署产物 `anti-ai.md`）、生成层（`skills/prompt-crafting.md`，prompt-crafter 按它组装提示词，从 anti-ai.md 只取生成期需要的部分注入）、清创层（`skills/anti-ai.md` 管线 + check-prose.py）。资产包对比结论见 proposal Why；本 change 只动生成层入口与它引用的知识层文件。

关键既有约束（实现时不可破坏）：
- 生成与清创分离：writer 不对照负面清单写作，T2/T3 与疲劳词阈值不进提示词（prompt-crafting Step 1.6 + Step 4 自检）。
- living-voice.md 职责声明「不定义阈值与档位」。
- structural-heat spec 枚举七条定律 + 不少于 13 种结构，增补必须嵌入既有定律。
- check-conflicts.py 双闸：SCAN_GLOBS 跨文件阈值冲突 + METHODOLOGY_FILES（anti-ai-writing / boundary-cases）越界数量线检测（`N次/章` 式）。
- 部署引用一律写 `.claude/knowledge/...` 基座路径（check-agents.py 校验）。

## Goals / Non-Goals

**Goals:**
- 五项生成侧增量全部落地且可通过现有检查链（check-agents / check-conflicts / test_platforms）验证。
- 新增知识可溯源（文件头标注来源与许可约束）、可校准（数字声明为单书实测默认值）。
- 生成注入与清创扫描同源（华美空洞家族在 T1 一处定义、两侧使用）。

**Non-Goals:**
- 不引入资产包清创侧词表增量（无情绪声线家族、顿号罗列、冒号空转、段首零主语评论、翻译腔四族等）——留待后续 change。
- 不引入 `_precheck.py` / `check_chapter.py` / 检测战史 / 朱雀送检运营内容。
- 不改 anti-ai 管线（skills/anti-ai.md）与 check-prose.py。
- 不引入 3-gram 重复检测（与「关键名词不换说法」存在口径张力，检测侧裁决另行 change，见 Decisions D5）。

## Decisions

### D1: 统计锚落独立知识文件 `knowledge/anti-ai/statistical-anchor.md`

Alternative A（写进 prompt-crafting.md）被拒：skill 是流程 SOP，知识应留 knowledge 层，且流程文件不应承载可校准的数字。Alternative B（并入 living-voice.md）被拒：统计锚是量化阈值，与该文件「不定义阈值与档位」职责声明冲突。独立文件便于整体溯源到资产包、将来按书校准时只改一处。init.py 合并清单（L402 元组）加入该文件并更新注释。

### D2: 统计锚归宿分离——节奏锚进质感要求，关键名词条进写作规范

提示词审计维度 F（去 AI 校验·温感平衡）的 PASS 标准是「无独句段占比硬性指标」，维度 I 要求建议性技法沉底不进硬规则区；而 prompt-crafting 输出为扁平结构，「写作规范」会并入「不可违反规则」列表。因此四类节奏锚（句长/段落/逗号/起句）注入「质感要求」子节——那里本来就是半截话/不完美约束等倾向性要求的家；表述全部用分布倾向（「约每 5 句」「0-4 个不等」），无占比下限，并带让步声明（与红线/字数压缩/T1/认知动词/感官冲突时先让步，低权重场景压缩段豁免）。关键名词不换说法性质不同——它是禁止性硬约束（禁同义词轮换），进「输出·写作规范」，对象限定核心名词/术语/人名，与 common-rules 的情绪词上限、比喻复用条目对象不相交，避免 writer 把「重复好」与「重复≤3次」读成矛盾。Alternative（五类全进写作规范）被拒：会触发维度 F 温感平衡 FAIL 与电报体风险（资产包自警的删过头模式 9）。

去重口径：提示词已有「叙事节奏交替」（禁止通篇等长段落）与质感要求「段落精度分层」，统计锚只补句长/逗号/起句三类微观分布对象，不重复段落交替语义（维度 H 同格式重复即 FAIL）；prompt-crafting「组装后去重检查」同步提示。

### D3: 华美空洞进 common-rules T1，正向原则进 living-voice

「单句形容词 >3 个」「开篇描写砍到两三笔」是阈值，按仓库规矩阈值只能定义在 common-rules.md（check-conflicts 双闸）——放 T1 家族（带「为什么禁 + 改成什么」），生成侧经既有 T1 简表注入通道取用，清创侧直接扫描，两侧同源。「情绪清单禁 / 偏差表达 / 描写显形」无数字线，按「只增不删」加进 living-voice（git diff 仅新增行），prompt-crafter 经活人感正向要点通道各注入 1-2 句。

### D4: structural-heat 数据嵌入定律 2/3，不新增定律编号

structural-heat spec（`openspec/specs/structural-heat/spec.md`）枚举「七条定律」为 MUST 内容；新增第八条定律需要改该 spec。对话密度线达标区与中段位置实测是对既有定律 2/3 的数据增补，嵌入原文即可保持 spec 不动。沿用文件头「单书实测默认值、按文风与题材校准」「作者侧优先于检测优化」既有声明；prompt-crafter 场景排序仅参考，不作硬性配额（作者章纲顺序优先）。

### D5: 资产包剔除清单（并记录理由）

| 剔除项 | 理由 |
|---|---|
| 视角混用锚（第一人称为主偶尔切第二人称） | 与章纲 `outline.pov` 决定的视角体系直接冲突 |
| 插入省略号/破折号建议 | 与 common-rules 现行破折号用法判定口径冲突 |
| 3-gram 重复零容忍 | 与「关键名词不换说法」存在口径张力；裁决口径（功能性锚词重复=人味，非功能短语复用=指纹）需单独设计检测实现，留后续 change |
| 人味弹药库、翻译腔、高频词库等清创侧内容 | 与质感要求/living-voice/common-rules 重复或属清创范围，见 proposal Why |

### D6: 节奏参数每章实例化——区间 + 情绪曲线派生 + 跨章错开

固定参数本身就是新指纹：章内防了均匀，跨章全用同一组值，检测器做跨章统计时每章节奏特征一致；且真人写作的节奏不是常量——紧张戏碎句密、舒缓戏长句慢，参数本质是内容的因变量。因此：知识文件把锚定义为**区间**（碎句约每 4-7 句 1 个、一句话段约每 6-10 段 1 个），prompt-crafter 组装时按本章情绪曲线与场景权重从区间取一组「本章节奏参数」写进质感要求。取值规则三条：①由情绪曲线派生（映射表：紧张/爆发→区间密端，舒缓/铺垫→疏端），不搞无依据随机——LLM 自行「随机」会收敛到中庸点，而情绪曲线章章不同，把变化托付给内容比托付给骰子可靠；②与上一章提示词参数错开（prompt-crafter 读上一章 prompt 文件核对，prompts/ 本就是可读产物）；③参数只约束全章倾向，局部情绪段按既有「叙事节奏交替」反向变速时以情绪段为准——真人味的核心是节奏跟内容走，参数只是防均匀化的下限保护，不是写作目标（真正的人味来源仍是 living-voice 三层：眼下要办的事/细节跟视角/对白在做事）。

### D7: 来源与许可标注

资产包 README 约定「十九/二十六等实战规则为个人积累，引用请注明出处；公开或商用前请先征得原作者同意」。`statistical-anchor.md` 文件头 MUST 标注改写来源；structural-heat 增补数据同源，在定律内标注「外部单书实测」即可（该文件已有同类标注惯例）。

## Risks / Trade-offs

- [量化锚被模型机械执行，节奏本身变成新模板（章内电报体 / 跨章同参指纹）] → 三重防护：归宿沉底质感要求不进硬规则区（D2）；参数每章实例化、由情绪曲线派生并与上一章错开（D6），跨章不同参；writing-execution Step 5 与 anti-ai Gate D 清创兜底。残余风险：参数取值可按书校准。
- [每章提示词 token 增量] → 固定注入通道新增约 300 字（统计锚 4 条 + 正向三节 + 华美空洞简表行），约 400-600 tokens/章，低于场景方法论稀疏注入的单章波动量，可接受。
- [部署产物 `anti-ai.md` 体积上涨] → 约 4-6KB（<10%），单文件合并机制不变，换取消除「生成期节奏无量化锚」的缺口。
- [新数字触发 check-conflicts 冲突/越界] → 新对象（碎句/逗号/对白占比）与权威源既有阈值对象不重叠；CI 双闸即时暴露，实现时先红后绿验证。
- [test_platforms 断言不足导致合并遗漏未被发现] → 仿照既有「合并结构热源定律」断言，为统计锚增加合并产物内容断言（先红后绿）。

## Migration Plan

1. 知识层先行（statistical-anchor.md 新文件 + 三文件增补），跑 check-conflicts / check-agents。
2. init.py 合并清单更新，test_platforms.py 加断言（先红后绿）。
3. prompt-crafting.md 注入范围与自检表更新，跑 check-agents。
4. E2E：`test_platforms.py` 七平台全绿；老项目由 `sync-project.py` 拉取新产物。回滚即 revert 提交，无数据迁移。

## Open Questions

（无——口径裁决均已在 D5 落定，剩余数字校准属使用期按书调参，不影响本 change。）
