# detect-loop Specification

## Purpose
提供可选的外部检测校准闭环：作者自愿把自己的稿件送外部 AI 检测器核验时，agent 按最小干预原则定向修复（只动最高分片段、其余字符级不动），达标即锁版，并把经验沉淀为项目资产。

## Requirements

### Requirement: 仅作者触发且默认离线

detect-loop MUST 为可选 phase：仅当作者明确要求送检/核验时启动；默认管线（draft→anti-ai→review→archive）MUST NOT 自动进入该环节；本地无送检工具或作者未提供检测途径时 MUST 优雅终止并说明，不阻塞主流程。

#### Scenario: 未触发不启动
- **WHEN** 正常走完 anti-ai phase
- **THEN** 调度不产生 detect-loop order，直接进入 review

#### Scenario: 作者触发
- **WHEN** 作者说"送检/过一遍外部检测"
- **THEN** 调度产生 detect-loop order，流程按 SOP 执行

#### Scenario: 无工具降级
- **WHEN** 本地不存在可用送检工具
- **THEN** 环节终止并告知作者需自行准备检测途径，主流程可继续

### Requirement: 最小干预修复契约

修复 MUST 遵守：每轮只修一个最高分片段；其余片段字符级不动（以内容子串哈希验证）；片段首末句逐字保持；改幅等长优先；连续两轮改善不足 0.05 或反升时 MUST 停止同类改法（换内容类型或回滚上一版）；片段判定阈值（如 0.5）作为参数而非硬编码。检测反馈驱动的修改 MUST 遵守与写作侧相同的裁决顺序（作者设定与章纲 > 题材知识 > 结构默认值 > 检测优化）：MUST NOT 为降分改写锁定台词、章纲落点等作者侧核心表达，与文风冲突时以文风为准。

#### Scenario: 定向修复
- **WHEN** 检测返回多片段结果且仅一片超阈
- **THEN** 只修改该片段，其余片段修改前后哈希一致

#### Scenario: 检测优化不越权
- **WHEN** 降分修改与作者设定或章纲落点冲突
- **THEN** 保留作者侧表达，报告中标注该片段为"设定优先、接受残分"或提交作者裁决

#### Scenario: 止损
- **WHEN** 同一片段连续两轮改善不足 0.05 或分数反升
- **THEN** 停止同类改法，报告中给出换内容类型或回滚两个选项

### Requirement: 达标锁版与经验沉淀

全部片段低于阈值后 MUST 锁版：生成快照、记录内容哈希，锁版后不再改动；本轮的轮次、改动、逐片结果 MUST 追加进项目 `sandbox/detect-battles.md`；翻车原句 MUST 经作者确认后加入 `sandbox/prose-regressions.txt`；沉淀前 MUST 复跑 `check-chapter.py` 确认硬伤清零。

#### Scenario: 锁版
- **WHEN** 检测结果全部片段低于阈值
- **THEN** 生成锁版快照与哈希记录，后续修改被拒直到作者明确解版

#### Scenario: 经验入库
- **WHEN** 一轮战役结束
- **THEN** 战役记录追加完整轮次表，新增回归串有作者确认记录，`check-chapter.py` 复跑 exit 0

### Requirement: 合规边界与资产隔离

skill 文本 MUST 声明：本环节面向作者对自己稿件的自愿质量校准；仓库 MUST NOT 包含任何检测平台的自动化脚本、接口逆向文档、密钥与浏览器指纹方案；与本地工具的对接只以"输入稿件路径/输出逐片结果文件"的适配器接口描述。

#### Scenario: 仓库内容审查
- **WHEN** 检查本 change 产出与仓库内容
- **THEN** 无检测平台自动化脚本、无逆向协议文档、无密钥文件；适配器接口只描述输入/输出文件约定
