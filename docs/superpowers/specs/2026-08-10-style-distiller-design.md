# 设计文档：文风特征蒸馏与风格化生成模块（style-distiller）

- **日期**：2026-08-10
- **状态**：已确认（作者审批）
- **实施**：已按 2026-08-11 计划落地
- **关联**：[PRD issue #84](https://github.com/modoojunko/awesome-novel-agent/issues/84)（v1.1）
- **范围**：F1-F8 全量设计，一个设计文档；实施按 Phase 分批（对应 PRD 八章实施计划）

---

## 1. 背景与目标

现有写作风格依赖 `settings/writing-style.md` 的文字描述 + 题材预置画像：

- 风格描述模糊（"偏描写""古风"），LLM 遵从度低（约 40-60%）
- 生成后无法量化校验风格是否达标
- 长篇写作存在风格漂移
- 作者修改 AI 原文的经验无法沉淀为可复用参数

本设计实现一套**数字化文风特征体系**：可蒸馏（从样本文本提取量化特征）、可注入（数值参数进生成 prompt）、可校验（Gate G 检测偏差）、可迭代（归档后增量更新）。

## 2. 核心决策（已与作者确认）

| 决策点 | 结论 |
|--------|------|
| 范围 | F1-F8 全量一个设计文档，实施分阶段 |
| 蒸馏实现 | **脚本统计（jieba POS）+ LLM 语义** 两段式 |
| 实现位置 | 新增第 9 个子 agent `style-distiller` |
| 场景类型 | **复用 prompt-crafter 现有 6 类**（dialogue/fight/environment/inner-mono/transition/group-scene），文风维度用 PRD 9 大维度，注入防重复/防冲突 |

## 3. 架构

### 3.1 Agent 体系 8 → 9

| Agent | 风格职责 | 读写 |
|-------|---------|------|
| **style-distiller**（新） | F1 卡片格式 · F2 蒸馏 · F4 场景卡 · F5 增量更新 · F8 插值混合 · F7 对比 | **写** `settings/writing-style.md`、`settings/style-profiles/*`、`settings/.style-versions/*`（专属写白名单）；**读** 样本/定稿正文 |
| **prompt-crafter** | F3 风格注入 | **读** 主卡 + 场景卡 |
| **anti-ai** | F6 Gate G | **读** 主卡 + 场景卡，**写** `archives/*.anti-ai.md` 报告 |
| **updater** | 归档后触发信号 + 既有定性 [writer-preference] 学习（保持不变） | 其余 settings 照旧 |

### 3.2 调度点（novel-agent 唯一调度，一次一个任务）

```
setup   作者导入参考文本 → dispatch style-distiller（style-distill-order.md）→ 写 writing-style.md
         无样本 → 用 templates 预置题材卡兜底（confidence=0，提示词只走定性字段）
draft   （无新增调度）prompt-crafter 自行读卡片注入
anti-ai （无新增调度）anti-ai 自行跑 Gate G
archive updater 归档完成 → 报告标记"建议风格增量" → novel-agent dispatch style-distiller
        （style-update-order.md）→ 滑动平均更新 + 备份 + 置信度重算
手动   作者说"重新蒸馏 / 调一下形容词密度 / 混两个风格" → novel-agent dispatch style-distiller
```

### 3.3 关键约束衔接

- **settings 写入规则最小化例外**：style-distiller 只获得风格三件套（writing-style.md / style-profiles / .style-versions）写白名单，其余 settings 仍归 updater。在 ARCHITECTURE.md 标注此例外。
- **幂等**：增量更新写 `.agent/archiving/{chapter}.done` 同款 checkpoint，防重放重复。
- **蒸馏脚本复用**：`tools/distill-style.py` 由 style-distiller 用 Bash 调；anti-ai 的 Gate G 复用同一脚本做客观维度校验。

## 4. F1：风格卡数据结构

### 4.1 存储与文件

```
settings/
├── writing-style.md              # 主卡（全局默认，必选）
└── style-profiles/               # 分场景卡（可选）
    ├── dialogue.md  fight.md  environment.md
    ├── inner-mono.md  transition.md  group-scene.md
```

场景卡 `scene_type` 复用 prompt-crafter 现有类型；PRD 的 scene_type 枚举不引入平行体系。

### 4.2 frontmatter 结构

```yaml
---
profile_version: "1.0"
scene_type: general | dialogue | fight | environment | inner-mono | transition | group-scene
source_sample_length: 3250        # 蒸馏样本总字数（可信度参考）
confidence: 72                    # 0-100；0 = 手动设定
last_updated: "2026-08-10"
inherits: "writing-style.md"      # 仅场景卡有：继承主卡
override: { … }                   # 仅场景卡有：只覆盖差异维度
locked: [adj_density_per_100]     # 手动锁定，F5 增量更新跳过

# ── 9 大维度（PRD 定义）──
lexicon: { adj_density_per_100, adv_density_per_100, four_phrase_freq_per_100,
           preferred_words, banned_words, name_pronoun_ratio }
syntax: { avg_sentence_length, sentence_length_dist, single_sentence_paragraph_pct,
          avg_sentences_per_paragraph, question_ratio, exclamation_ratio }
rhythm: { dialogue_pct, action_pct, environment_pct, inner_thought_pct, narration_pct }
rhetoric: { metaphor_density_per_100, metaphor_preference, sensory_dist }
emotion_expression: { direct_pct, action_physiology_pct, environment_projection_pct }
narrative: { perspective, focal_character, inner_monologue_style }
dialogue_style: { tag_style, avg_dialogue_length, interrupt_freq_per_100,
                  subtext_ratio, direct_address_freq_per_100 }
cohesion: { conjunction_freq_per_100, transition_sentence_ratio, paragraph_bridge_style }
verb_style: { action_verb_ratio, mental_verb_ratio, state_verb_ratio, strength }
---
```

### 4.3 正文定性层（旧 4 字段映射）

- `role` → `narrative.perspective` + 正文「叙事身份」节
- `core_principles` → `hard_constraints`（正文「硬约束」节）
- `possible_mistakes` → `banned_words` 互补 + 正文「AI 易犯错误」节
- `depiction_techniques` → 正文「描写层次和手法」节（原样保留）
- 正文另含 `few_shot_examples`（蒸馏选出的标志性例句）

定性层保证 prompt-crafter 的定性注入不丢失，迁移后旧卡内容零损失。

## 5. F2：蒸馏引擎（两段式）

```
样本文本(.md/.txt) ──┐
                    ├─→ tools/distill-style.py（Bash 调用，无 LLM）
                    │    jieba.posseg 分词
                    │    算：lexicon(adj/adv 密度, 四字格频率, 高频词, 人称指代)
                    │        syntax(句长/分布/单句段/每段句数/问感叹)
                    │        rhythm(对话占比), cohesion(连接词频率,词表)
                    │        verb_style(动作/心理/状态动词比例,词表)
                    │        banned_words 候选, few-shot 候选句
                    │    → 输出 partial YAML + 每维度证据句
                    │
                    ├─→ LLM 语义标注（style-distiller 主循环）
                    │    读 partial YAML + 样本
                    │    补：rhetoric(比喻/感官) emotion_expression narrative
                    │        dialogue_style(标签/潜台词/称呼) cohesion(衔接方式)
                    │        verb_style(力度) rhythm 脚本分不出的部分
                    │        定性层（角色/信条/易错/手法）+ few-shot 定稿
                    │    → 合并 → 写完整 YAML 卡
                    │
                    └─→ 置信度计算 + 备份旧版
```

### 5.1 置信度计算（PRD 3.1.3）

```
confidence = min(100, base_score + sample_bonus + stability_bonus)
base_score = 20
sample_bonus = min(40, sample_length / 50)
stability_bonus = min(40, chapter_count × 5)
```

容差档：0-20 手动 / 21-50 ±30% / 51-70 ±20% / 71-90 ±15% / 91-100 ±10%。

### 5.2 依赖与工程约束

- `tools/requirements.txt` 追加 `jieba`；`static.yml` CI 同步安装。
- `distill-style.py` 只做确定性计算，无网络无 LLM 依赖。
- 降级：无 jieba 时脚本降级为纯正则统计（缺 adj/adv 密度等需 POS 的项），语义仍由 LLM 填。

## 6. F3：prompt-crafter 风格注入

### 6.1 输入源扩展

Step 1 新增读主卡 + 本章各场景对应场景卡（场景类型识别已存在，直接映射 `style-profiles/{scene_type}.md`）。

### 6.2 按场景稀疏注入

| 场景类型 | 重点注入维度 | 不注入 |
|---|---|---|
| dialogue | dialogue_style + dialogue_pct | verb_style、environment_pct |
| fight | verb_style + syntax(短句) + rhythm.action_pct | subtext_ratio、sensory_dist |
| environment | rhetoric.sensory_dist + rhythm.environment_pct | interrupt_freq |
| … | 依此类推，主卡兜底 | — |

### 6.3 防重复 / 防冲突机制

1. **分工**：风格卡只注入"多少"（量化约束 + few-shot 例句），scene-craft 方法论只注入"怎么写"（四步转化定性技法）。分属「写作风格约束」块与「场景写作指引」块，不同子节。
2. **去重**：banned_words 与 anti-ai 规则禁用词合并去重；对话/节奏类量化约束与 scene-craft 同名技法不并列注入。
3. **冲突优先级（扩展 Step 1.5 裁决表）**：作者最新记忆偏好（writing-memory）> 风格卡数值 > genre-example 基线。风格卡不让步于题材基线但让位于作者明确记忆。风格卡内部分级：`banned_words` / `hard_constraints` 视为**红线级**（任何压缩不得删改），量化数值指引视为**写作规范级**（与第 6 层同级，可让步于第 1-5 层约束）。
4. **置信度→容差**：数值以"约 X（±Y%）"表述，不写死。
5. **Step 4 验收自检新增 2 项**：风格块与场景指引无语义重复；banned_words 无重复出现。

## 7. F4：分场景风格卡

- 6 张场景卡 `inherits: "writing-style.md"` + `override:` 只写差异项。
- 匹配：prompt-crafter 对每个场景 scene_type 查卡 → 有则该卡 + 主卡合成注入；无则主卡兜底。
- 继承链解析放 prompt-crafter Step 1 内（读卡时合并 override），不引入新解析器。
- 预置：`templates/settings/style-profiles/` 6 张场景卡模板 + 题材基线模板（PRD 6.1 三层结构：基础卡 → 题材偏移 delta → 标杆卡，P1/P2 分批）。

合成示例：fight 场景 → 主卡 + `style-profiles/fight.md` override 合并 → 注入该场景的只有 verb_style / syntax / rhythm.action_pct 三项 + 1-2 条 few-shot。

## 8. F5：增量风格更新

- **触发链**：updater 归档完成 → order DONE → novel-agent 读归档报告"建议风格增量" → dispatch style-distiller（`style-update-order.md`）。
- **两档开销**：
  - 脚本档（每章自动）：`distill-style.py` 跑定稿 → 客观维度滑动平均更新。`新 = 旧×α + 新×(1-α)`，α 按置信度（<30→0.5 / 30-60→0.65 / >60→0.75，PRD 3.5.2）。
  - LLM 档（低频）：语义维度在置信度 < 60、或累计 5 章、或作者要求时才重估（N 取 5，可在实现阶段调整）。
- `locked` 字段：手动锁定维度跳过滑动平均。
- 备份：更新前备份旧版到 `settings/.style-versions/v{N}_{date}.md`；`.done` checkpoint 幂等。
- **与既有 updater 定性学习的关系**：updater 的 diff→[writer-preference] 继续写 `.claude/knowledge/writer-style.md`；style-distiller 增量只动量化数值，不碰定性条目。作者确认后才把高频定性条目升华进卡片 banned_words/hard_constraints。

## 9. F6：Gate G（anti-ai 扩展）

- anti-ai Phase 1 扫描新增 Gate G：读主卡 → 对每章跑 `distill-style.py` 客观维度 + LLM 估算语义维度 → 按容差对比。
- 分级：通过 / 警告（作者确认）/ 不通过（局部重写建议）。输出 PRD 3.6.4 表格。
- 复用蒸馏脚本，不新写检测器；误杀防护沿用 boundary-cases 豁免逻辑。
- 不改剧情，只改表达（与 anti-ai 定位一致）。

## 10. F7 / F8（P2/P3 工具）

- `tools/compare-style.py`：两张卡 YAML diff → 维度变化表（数值差 + 定性摘要）。
- `tools/mix-style.py`：数值加权平均 + style-distiller LLM 合并定性节，输出混合卡。

## 11. 迁移与工程清单

| 改动 | 内容 |
|---|---|
| `tools/init.py` | 新项目部署新卡模板 + 可选蒸馏钩子；旧 4 字段卡自动迁移（→ 新结构定性层，量化维留空，confidence=0 → 提示词只走定性层，直到首次蒸馏） |
| `tools/sync-project.py` | 同步新模板/新 skill/新 agent 到已有项目 |
| `tools/check-agents.py` | 校验 style-distiller frontmatter + 卡片 YAML 合法 + `inherits` 引用存在 |
| `tools/test_platforms.py` | E2E 覆盖新 agent 部署 + 蒸馏流程（claude/opencode/reasonix/codex 四平台） |
| `tools/requirements.txt` | + jieba；`static.yml` CI 同步安装 |
| `agents/` | 新 `style-distiller.md`；`novel-agent.md` 加 3 个调度点 |
| `skills/` | 新 `style-distill.md`；`prompt-crafting.md` 扩展（Step1 读卡/注入/Step4 自检）；`anti-ai.md` 加 Gate G |
| `knowledge/` | 新 `style-distill/prompt-templates/`（蒸馏 prompt / 注入模板 / Gate G 清单） |
| `templates/settings/` | 新格式 writing-style.md + 6 张场景卡 + 题材基线模板 |
| `docs/` | ARCHITECTURE.md（9 agent + 风格写白名单例外）、AGENTS.md、README 同步；版本 bump |

## 12. 实施顺序（对齐 PRD Phase）

1. **Phase 0**：卡片格式定稿（F1 数据结构 + 模板）
2. **Phase 1**：`distill-style.py` + style-distiller agent + prompt-crafter 注入（核心闭环）
3. **Phase 2**：场景卡 + 题材基线（F4）
4. **Phase 3**：增量更新 + 备份 + 锁定（F5）
5. **Phase 4**：Gate G（F6）
6. **Phase 5**：F7 / F8 工具

## 13. 验收标准（PRD 十）

1. 1500 字样本蒸馏，核心参数（句长、形容词密度、对话占比、连接词密度）与人工统计偏差 ≤ 15%
2. 同一风格卡生成 3 段同场景正文，风格参数偏差 ≤ 20%
3. 战斗卡 vs 对话卡生成正文，在句长/对话占比/动词力度等维度显著差异
4. 连续归档 5 章后置信度 ≥ 70，参数波动 < 10%
5. 现有项目升级不报错，旧 writing-style.md 自动迁移
6. 仙侠/都市/悬疑三套标杆卡，作者盲测正确率 ≥ 70%

## 14. 风险与应对

| 风险 | 应对 |
|------|------|
| 脚本数值与人工统计偏差超阈值 | 置信度机制 + 容差档 + 人工校准 |
| LLM 估算语义维度不准 | 低频重估 + few-shot 例句佐证 + 作者确认升华 |
| 注入块挤占 prompt 空间 | 按场景稀疏注入，只取相关维度 |
| 增量漂移 | 滑动平均 α 分档 + 版本备份 + locked 锁定 |
| 旧卡迁移丢失定性信息 | 4 字段映射到新结构定性层，零损失 |
| 依赖 jieba 破坏"仅标准库" | 可选依赖 + 无 jieba 降级为纯正则 |
