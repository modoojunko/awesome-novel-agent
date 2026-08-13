# style-distill skill — 三阶段 13 模板 LLM 蒸馏（style-distill-order）

## 一、主卡蒸馏
1. 收集样本：作者参考文本（.md/.txt）或已归档章节。**少于 6000 字（约 3 章的量）向 novel-agent 说明质量不足可挂起**——1500 字样本句长分布/五层占比统计噪声大、场景卡子样本不足（每类 ≥800 字会大量跳过）；6000-10000 字才能覆盖多场景类型并给出稳定统计。
2. 读 `.claude/knowledge/style-distill/prompt-templates/feature-extract.md`（方法论 = 13 模板定义）。
3. 阶段一 拆解（模板 1-4）：对样本逐段/逐句/逐情绪标注（LLM 内部推理，不写文件）。
4. 阶段二 量化（模板 5-8）：频次/五层占比/情绪通道/词汇 → 量化表。
5. 阶段三 建模（模板 9-13）：句式卡/行为树/对话模式/节奏模型/锚点 → 建模规则。
6. 收敛：
   - 量化表 → 卡量化维（案例 1 九维，schema 见 check-agents）
   - 建模规则 → 卡声音层（hard_constraints / soft_guidance / few_shot_examples）
7. 写 `settings/writing-style.md`（收敛卡）+ `settings/style-profiles/analysis/general.md`（量化表 + 建模规则全文）。
8. 备份旧卡到 `settings/.style-versions/v{N}_{YYYY-MM-DD}.md`（N=现有最大+1，卡与分析稿同版本）。
9. confidence：LLM 按样本质量/一致性给 **1-100（必须 >0）**——0 仅用于未蒸馏/手动卡（走定性注入分支，见 prompt-crafting Step 1.1）；蒸馏卡置 0 会静默退回定性注入、丢失量化渲染。`last_updated` 写当日。
10. **生成作者画像**（作者确认用，写入 `settings/style-profiles/analysis/general.md` 顶部「作者画像」节 + 交接报告）：
    - 开头说明定位：**「以下是你文风在 AI 眼里的数据化解读——不是文学评价，是 AI 提取出来供后续写作复用的特征。像不像你，你说了算。」**
    - 内容全部用作者语言，不出现字段名/confidence/维度名：
      - 叙事身份（卡正文原文）
      - 硬约束（卡正文原文，2-4 条）
      - 量化特征通俗翻译 3-5 条：「短句为主（大多 20 字内）」「对话占比约一半」「白描为主、修辞克制」「偏好词：……」
      - 风格例句 2-3 条（few_shot_examples 原文）
    - 结尾确认问句：「读起来像你的写法吗？不像 → 告诉 novel-agent『不像』，重新蒸馏。」

## 二、场景卡蒸馏（style-distill-order 内）
1. 对样本按段落分类场景（dialogue/fight/environment/inner-mono/transition/group-scene）。
2. 每类聚合子样本（≥800 字才蒸馏；不足跳过该场景卡）。
3. 同 5 一主卡三阶段跑该场景子样本；阶段三侧重场景差异规则。
4. 收敛为 override（只写与主卡的差异维度）+ 场景声音层。
5. 写 `settings/style-profiles/{scene_type}.md`（inherits: writing-style.md + override）
   + `settings/style-profiles/analysis/{scene_type}.md`（该场景量化表 + 建模规则）。

## 三、写白名单（唯一例外）
| 工具 | 允许写 | 禁止 |
|------|--------|------|
| Write/Edit | settings/writing-style.md、settings/style-profiles/*、settings/style-profiles/analysis/*、settings/.style-versions/*、.agent/task/*-order.md（仅改 status） | 不写其他 settings、chapters、archives |
| Read | archives/、chapters/、settings/、样本文件 | 绝不读项目之外 |
| Bash | 无脚本调用（纯 LLM 提取）；其他命令向 novel-agent 说明 | 不调已退役工具 |

## 四、防冲突 / 自检
- banned_words 与 anti-ai 禁用词合并去重。
- 场景卡 override 不与主卡同维度并列（override 即覆盖）。
- 自检：frontmatter 过 check-agents 校验（9 维键/枚举/分布和）；备份存在；幂等（重复跑同样本不产生多余备份）。
- 卡冻结：本技能不做任何更新——机器生成章永不回写卡；重蒸馏仅作者触发。
