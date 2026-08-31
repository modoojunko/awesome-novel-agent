# v4.22.0 版本说明

> **关键词：** 结构热源定律 + 章节确定性检查 —— 从源头规避 AI 检测的知识与工具（朱雀实测经验通用化）

---

## 一句话

把一套经外部 AI 检测器实测验证（连续多章全部片段"人工特征"判定）的结构级写作定律通用化入库：新增结构热源知识（并入部署的 anti-ai.md）与章节交付确定性检查工具（check-chapter.py，与 check-prose.py 同机制部署到各平台），让 AI 热源在写前被规避、在交付前被机器拦住。

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **结构热源知识** | `knowledge/anti-ai/structural-heat.md`：七条实测定律（问答链密度、对话密度正向信号、位置热值、切片边界稳定、补字铁律、内容类型切换、整章重写边界）+ 13 种高风险结构（工作汇报体、微闭环递归体、过桥链前缀体、私人回忆证明链等）+ 写前自查卡与修复纪律。全部去书名化通用改写，数值标注为默认值，附裁决顺序：作者设定与章纲 > 题材知识 > 结构默认值 > 检测优化 |
| **知识合并部署** | `init.py` 将 structural-heat.md 并入 anti-ai 知识合并清单，随 `.claude/knowledge/anti-ai.md`（各平台对应知识目录）一起部署 |
| **章节确定性检查** | 新增 `tools/check-chapter.py`：硬性项（引语夹层-标签式、嵌套双引号、半角引号、"X个字"逐字对账不符、回归串命中）+ 警告项（破折/省略段内密集、广义夹层、多轮问答并段、弱化副词密度、尾随标签窄集等，需人工裁定）+ 平台口径字数统计（只报告不设阈值）。标点口径对齐 common-rules.md，不引入书级硬禁 |
| **项目级进化资产外置** | 回归模式库（`sandbox/prose-regressions.txt`）与锁定台词白名单（`sandbox/locked-lines.txt`）从项目文件读取，缺失即跳过——每本书攒自己的翻车串库与豁免清单 |
| **部署与同步** | init 部署、sync 指纹与恢复均覆盖 check-chapter.py（与 check-prose.py 同机制）；E2E 新增七平台断言 |
| **知识增量合并** | 从 human-writing 系规则包增量合入 anti-ai-writing.md（同义词循环、主语补全均匀、书面填充、系动词回避、过度限定堆叠、场景分级改写力度表）与 common-rules.md（判断类补"或许"），只增不删 |

## 兼容性

- 纯增量：既有工具（check-prose.py）阈值与行为不变；anti-ai 各 Phase 流程不变（结构扫描与双脚本初筛的管线挂接在后续版本）。
- 存量项目跑 `sync-project` 后获得新检查脚本与更新后的合并知识，无需任何手动操作。
- `check-chapter.py` 本版已部署但管线尚未调用（下一版本挂进 writing/anti-ai 流程），可直接手动使用：`python3 tools/check-chapter.py <章节文件>`。

## 测试

- `tools/test_check_chapter.py` 新增 19 项断言（各检查项正反例、退出码契约、回归库/白名单、CRLF、目录输入）。
- `tools/test_platforms.py` 272 项断言全绿（含新工具部署与知识合并断言）。
- check-agents / check-conflicts / py_compile 全绿。
