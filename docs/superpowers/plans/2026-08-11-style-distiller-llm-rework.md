# style-distiller LLM 重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 style-distiller 从「jieba 统计 + LLM 语义」重构为「纯 LLM 三阶段 13 模板逆向工程」，产出蒸馏卡 + 分析稿；prompt-crafter 双态渲染（未蒸馏=定性注入现状不变 / 蒸馏后=案例 2 蒸馏输出）作为生成与验收的唯一操作规格；anti-ai 改为指令遵循验收，novel-agent 调度 ≤3 次抽卡。

**Architecture:** 产卡/注入/生成/验收四角色分离 + **双态向前兼容**。style-distiller（仅作者触发，有样本时）跑 13 模板（拆解 1-4 → 量化 5-8 → 建模 9-13）收敛出蒸馏卡（量化维 + 声音层）与分析稿；prompt-crafter 按卡内 `confidence` 分支渲染（0=未蒸馏 → 正文定性四字段注入，现状不动；>0=已蒸馏 → 案例 2 量化区间 + 声音层透传，写 `prompts/`）；writer 用该提示词生成、anti-ai 用同一份提示词验收（PASS/FAIL + 违反报告）；FAIL → novel-agent 派 writer 带报告重写（≤3）。卡冻结：归档后无增量更新。旧卡/未蒸馏项目零改动、零迁移。

**Tech Stack:** Python 3.9+（无新增依赖，jieba 移除）、YAML、Claude Code agents/skills、纯 LLM 提取（无统计引擎）。

## Global Constraints

- **双态卡 + 向前兼容（2026-08-12 作者确认）**：卡状态由 frontmatter `confidence` 判定（0=未蒸馏/手动；>0=已蒸馏），复用旧 prompt-crafting Step 1.1 既有判定，**无新标记字段**。未蒸馏卡 = 旧模板原样（9 维零值 + 正文定性四字段 + `locked`），prompt 注入走旧定性路径，**模板不改、init seed 不改、旧项目零改动、无批量迁移**。蒸馏卡 = 9 维填充 + 声音层（`hard_constraints`/`soft_guidance`/`few_shot_examples`）+ `profile_name` + `confidence>0`；增强字段（三维 name_pronoun / inner_monologue_pct / strength）**可选**——存在才校验、缺失不报错。
- **卡冻结**：蒸馏一次到位；机器生成章永不回写卡；归档后不触发任何风格增量更新；重蒸馏仅作者主动触发（`style-distill-order.md`）。
- **写白名单（style-distiller 唯一例外）**：`settings/writing-style.md`、`settings/style-profiles/*`、`settings/style-profiles/analysis/*`（新增）、`settings/.style-versions/*`。只写这四处，不碰其他 settings。
- **13 模板归属**：模板 1-4 拆解为 LLM 内部推理过程稿，**不落盘**；模板 5-8 量化表 + 模板 9-13 建模规则**持久化到分析稿**并收敛进卡（量化维 + 声音层）。
- **蒸馏卡 schema（案例 1 结构）**：`profile_version`、`profile_name`、`scene_type`、`source_sample_length`、`confidence`、`last_updated` + 9 大维度（结构同旧模板）+ 声音层。`locked` 保留可接受（新流程为 no-op，不要求删除、不要求保留）。
- **类型规则**：客观数值精确值；类别枚举封闭集合（tag_style/strength/paragraph_bridge_style/inner_monologue_style/perspective）；百分比分布和=100（±1），五层占比总计 ≤110%；**增强字段存在才校验**。
- **案例 2 = 唯一操作规格**：writer 生成与 anti-ai 验收读 `prompts/vol-{N}-ch-{M}-prompt.md` 同一份，天然同源；未蒸馏态 prompt 含定性四字段（现状不变）。分析稿不进任何 agent 加载清单。
- **抽卡**：FAIL → 违反报告喂 writer 重写，round ≤3；超限取违反最少稿，报告留作者人工裁决。
- **退役**：`tools/distill-style.py`、`tools/compare-style.py`、`tools/mix-style.py`、jieba 依赖、F5 增量（`style-update-order`）、题材基线运行时、check 退出码契约（0/1/2）、C1、`injection-template.md`（→ rendering-rules.md）、旧 test_style_distill 数字断言。**不退役**：旧定性注入路径（正文四字段 + confidence=0 分支）、旧卡模板、init 旧模板 seed。
- **保留**：`tools/init.py`、`tools/sync-project.py`、`tools/check-agents.py`、`tools/check-conflicts.py`、`tools/test_platforms.py`（双态卡校验更新；模板/seed 不动）。
- **测试**：模板/流程/schema 断言，不依赖 LLM 精确数值；`python tools/test_style_distill.py` 重写（保留文件名，CI 不变）。LLM 非确定性由 schema 校验 + 模板一致性兜底。
- **C6 主验收**：作者盲测 ≥70%（作者内容任务，代码路径就绪即可）。
- **docs/ 被 gitignore**：本计划文件提交需 `git add -f`；任务内代码提交正常。
- **No auto-tagging**：tag 由 PR review+merge 后作者/发布流程创建。

---

### Task 1: 方法论模板 feature-extract.md（13 模板定义）

**Files:**
- Create: `knowledge/style-distill/prompt-templates/feature-extract.md`
- Delete: `knowledge/style-distill/prompt-templates/distill-prompt.md`

**Interfaces:**
- Consumes: 无（作者提供的 13 模板方法论，见 spec §5.1）
- Produces: `knowledge/style-distill/prompt-templates/feature-extract.md` —— Task 3（style-distiller 技能）引用它的路径；内容定义 13 模板的标注口径/封闭取值/输出格式，Task 10 的测试按它的节标题做 schema 断言。

- [ ] **Step 1: 删除旧 distill-prompt.md**

```bash
git rm knowledge/style-distill/prompt-templates/distill-prompt.md
```

- [ ] **Step 2: 写 feature-extract.md**

创建 `knowledge/style-distill/prompt-templates/feature-extract.md`，含以下节（13 个模板逐一定义，作者方法论原样落盘）：

```markdown
# feature-extract：三阶段 13 模板蒸馏方法论

你是文风逆向工程器。对样章依次跑「拆解 → 量化 → 建模」三阶段 13 模板，
产出量化表 + 建模规则，收敛为案例 1 特征卡。模板 1-4 为内部推理过程稿，不输出到文件。

## 阶段一 拆解（模板 1-4，LLM 内部推理，不落盘）

### 模板 1：文本分层标注表
逐自然段标注：段落序号 | 原文 | 层级标注（叙述/对话/内心独白/动作/环境，可多选主导层）| 备注。
### 模板 2：段落节奏标注表
逐段扩展：段落类型（单句段/双句段/多句段）| 段落功能（推进/吐槽/对话/描写/收束）| 段落位置（章首/章尾/中间）。
### 模板 3：句子级结构标注表
逐句标注：句子序号 | 原文 | 句长 | 句型（陈述/疑问/感叹/祈使）| 主语类型（{角色名}/代词/我/无主语）| 动词类型（动作/心理/状态/生理）。
### 模板 4：情绪表达标注表
逐情绪片段：序号 | 原文 | 情绪类型（紧张焦虑/羞耻尴尬/惊喜喜悦/失落沮丧/抗拒抵触/自嘲消解）| 表达通道（A直接陈述/B生理/C动作/D内心独白/E环境映射）| 通道说明。

## 阶段二 量化（模板 5-8，输出量化表，持久化）

### 模板 5：频次统计表
指标（值/口径）：总字数（正文全字数）| 总句数（按。？！…断句）| 总段数（自然段）|
平均句长（总字数÷总句数，1 位小数）| 短句占比 ≤8 字 | 中句 9-20 | 长句 21-35 | 超长 >35 |
疑问句占比 | 感叹句占比 | 单句段占比 | 每段平均句数（1 位小数）。分布桶和 =100%（±1）。
### 模板 6：五层占比统计表
叙述/对话/内心独白/动作/环境各层字数 + 占比；主导层归类，总计 ≤110%。
### 模板 7：情绪通道分布统计表
A/B/C/D/E 各通道出现次数 + 占比（和 =100%）+ 典型示例。
### 模板 8：词汇统计表
高频词表（去虚词，≥3 次）：排名|词汇|次数|每千字频率|词性|用途判断；禁用词表（在样章搜索确认 0 次）；
口头禅表：口头禅|次数|使用场景。

## 阶段三 建模（模板 9-13，输出建模规则，持久化 + 收敛进卡声音层）

### 模板 9：句式模板卡（S-01~，通常 6-10 张）
每张：模板编号|名称|原文示例|结构公式|适用场景|句长特征|情感基调。
### 模板 10：人物行为决策树
每主要角色一张：外界刺激 → 内心警报 → 身体反应 → 内心定性 → 自我消解 → 最低限度行动 的行为链。
### 模板 11：对话模式库（D-01~）
每模式：模式编号|名称|结构（轮次序列）|原文示例|适用场景。
### 模板 12：段落节奏模型
循环单元图（章首收束 → 主体推进/吐槽交替 → 章尾收束）+ 关键参数（如推进:独白比例、纯叙述上限、对话密集区后缓冲）。
### 模板 13：结构锚点模型
章首锚点/章尾锚点/中段呼应的原文表现 + 功能 + 变化规则。

## 收敛为蒸馏卡（案例 1 结构，双态向前兼容）
- 模板 5-8 量化表 → 卡量化维（lexicon/syntax/rhythm/rhetoric/emotion_expression/narrative/dialogue_style/cohesion/verb_style，九维结构见 distilled-style-spec）
- 模板 9-13 建模规则 → 卡声音层（hard_constraints/soft_guidance/few_shot_examples）
- **蒸馏卡 schema（2026-08-12 修正）**：frontmatter = 旧模板 9 维**结构不变**（只填值）+ **新增** `profile_name`、`hard_constraints`/`soft_guidance`/`few_shot_examples` + `confidence` 置 **>0**；`locked` 保留（no-op）。可选增强字段：`name_pronoun_ratio` 可写三维 `{name, he_she, i_you}`（和=100）或保持单值；`emotion_expression` 可加 `inner_monologue_pct`（缺省按 100-其余三项推断）；`verb_style.strength` 枚举 weak/medium/strong。**未蒸馏项目（无样本）不触发蒸馏，卡保持旧模板原样**。
- 输出格式：量化表 + 建模规则 + 收敛卡（案例 1 格式 YAML）
```

- [ ] **Step 3: 验证结构**

Run:
```bash
python -c "
import pathlib
t = pathlib.Path('knowledge/style-distill/prompt-templates/feature-extract.md').read_text()
for i, name in [(1,'文本分层'),(2,'段落节奏'),(3,'句子级'),(4,'情绪表达'),(5,'频次'),(6,'五层占比'),(7,'情绪通道'),(8,'词汇统计'),(9,'句式模板卡'),(10,'行为决策树'),(11,'对话模式'),(12,'段落节奏模型'),(13,'结构锚点')]:
    assert name in t, name
print('13 模板节齐全')"
```
Expected: 打印 `13 模板节齐全`。

- [ ] **Step 4: Commit**

```bash
git add knowledge/style-distill/prompt-templates/
git commit -m "feat: feature-extract 方法论模板（三阶段 13 模板定义），退役 distill-prompt.md"
```

---

### Task 2: 双态卡 schema 校验（check-agents 放宽 + 蒸馏卡校验；模板不动）

**Files:**
- Modify: `tools/check-agents.py`
- （**不改**）`templates/settings/writing-style.md`、`templates/settings/style-profiles/*.md`——旧模板原样保留（未蒸馏态零改动，向前兼容）

**Interfaces:**
- Consumes: 无（spec §4 双态 schema）
- Produces: `check_style_card` 双态校验——旧卡（未蒸馏）过校验保持现状 + 蒸馏卡（可选增强字段**存在才校验、缺失不报错**）。Task 3（style-distiller 写蒸馏卡）、Task 10（双态测试）按此规则读写/断言。`check_style_card` 的校验规则是本仓库卡 schema 的唯一权威。

- [ ] **Step 1: 读现状模板，确认不动**

Read `templates/settings/writing-style.md` + `templates/settings/style-profiles/*.md`：9 维零值 + 正文定性四字段 + `locked: []` 原样（本任务不修改模板；spec §4 未蒸馏态 = 旧模板原样）。

- [ ] **Step 2: 扩展 check_style_card 为双态校验**

编辑 `tools/check-agents.py` 的 `check_style_card`，在现有校验（必填键 `profile_version/scene_type/confidence/last_updated/source_sample_length`、scene_type 枚举、confidence 0-100 整数、主卡 9 维齐全、场景卡 override、locked 可选列表、inherits 候选）基础上，**函数末尾追加**以下宽松校验（字段存在才校验、缺失不报错）：

```python
# --- 蒸馏卡可选增强字段（2026-08-12 双态：存在才校验，缺失兼容旧卡/未蒸馏卡） ---
def _opt_pct(v):
    return isinstance(v, (int, float)) and 0 <= v <= 100

lex = fm.get("lexicon") if isinstance(fm.get("lexicon"), dict) else {}
npr = lex.get("name_pronoun_ratio")
if isinstance(npr, dict):
    keys = set(npr)
    if keys != {"name", "he_she", "i_you"}:
        errors.append(f"{path.name}: name_pronoun_ratio 键应为 name/he_she/i_you（当前 {sorted(keys)}）")
    else:
        total = sum(v for v in npr.values() if isinstance(v, (int, float)))
        if total and abs(total - 100) > 1:     # 全零 = 未填占位（等价旧单值 0），跳过和校验
            errors.append(f"{path.name}: name_pronoun_ratio 三维和应≈100（当前 {npr}）")

em = fm.get("emotion_expression") if isinstance(fm.get("emotion_expression"), dict) else {}
if "inner_monologue_pct" in em and not _opt_pct(em["inner_monologue_pct"]):
    errors.append(f"{path.name}: inner_monologue_pct 需为 0-100 数值（当前 {em['inner_monologue_pct']!r}）")

vs = fm.get("verb_style") if isinstance(fm.get("verb_style"), dict) else {}
if vs.get("strength") not in (None, "", "weak", "medium", "strong"):
    errors.append(f"{path.name}: verb_style.strength 应为 weak/medium/strong（当前 {vs.get('strength')!r}）")

for key in ("hard_constraints", "soft_guidance"):
    v = fm.get(key)
    if v is not None and not isinstance(v, list):
        errors.append(f"{path.name}: {key} 需为列表")
if fm.get("few_shot_examples") is not None and not isinstance(fm.get("few_shot_examples"), list):
    errors.append(f"{path.name}: few_shot_examples 需为列表")

rhy = fm.get("rhythm") if isinstance(fm.get("rhythm"), dict) else {}
_FIVE = ("dialogue_pct", "action_pct", "environment_pct", "inner_thought_pct", "narration_pct")
if all(f in rhy for f in _FIVE):
    total5 = sum(rhy[f] for f in _FIVE if isinstance(rhy[f], (int, float)))
    if total5 and total5 > 110:                  # 五层可重叠，上限 110%（spec §5.1）
        errors.append(f"{path.name}: 五层占比总计应 ≤110%（当前 {round(total5)}）")

_DIST = {"syntax": ["sentence_length_dist"], "rhetoric": ["metaphor_preference", "sensory_dist"]}
for dim, fields in _DIST.items():
    d = fm.get(dim) if isinstance(fm.get(dim), dict) else {}
    for f in fields:
        sub = d.get(f)
        if isinstance(sub, dict) and sub:
            total = sum(v for v in sub.values() if isinstance(v, (int, float)))
            if total and abs(total - 100) > 1:
                errors.append(f"{path.name}: {f} 分布和应≈100（当前 {round(total)}）")
```

**注意（不改的现状）**：必填键**不加** `profile_name`（旧卡没有）；**不删** `locked` 校验（旧卡保留 locked，蒸馏卡空列表也过）；**不要求**声音层/增强字段（未蒸馏卡缺省）。

- [ ] **Step 3: 蒸馏卡样本过校验（临时验证）**

用临时脚本验证蒸馏卡（旧模板结构 + 声音层 + 增强字段）过新校验：

```bash
python - <<'PY'
import sys, tempfile, yaml
from pathlib import Path
sys.path.insert(0, "tools")
import importlib.util
spec = importlib.util.spec_from_file_location("ca", "tools/check-agents.py")
ca = importlib.util.module_from_spec(spec); spec.loader.exec_module(ca)
base = Path("templates/settings/writing-style.md").read_text(encoding="utf-8")
fm = yaml.safe_load(base.split("---", 2)[1])          # 旧模板原 frontmatter
# 蒸馏卡 = 原卡结构叠加声音层 + 增强字段 + confidence>0（style-distiller 收敛产物）
fm["profile_name"] = "测试蒸馏卡"; fm["confidence"] = 75
fm["lexicon"]["name_pronoun_ratio"] = {"name": 45, "he_she": 50, "i_you": 5}
fm["rhetoric"]["metaphor_preference"] = {"weapon_metal": 5, "nature": 10, "body": 20, "abstract": 30, "other": 35}
fm["rhetoric"]["sensory_dist"] = {"visual": 72, "auditory": 15, "tactile": 10, "olfactory": 2, "gustatory": 1}
fm["emotion_expression"]["inner_monologue_pct"] = 35
fm["verb_style"]["strength"] = "medium"
fm["hard_constraints"] = ["内心独白必须用引号包裹"]
fm["soft_guidance"] = ["整体基调：轻松吐槽向"]
fm["few_shot_examples"] = [{"type": "inner_thought", "text": "好想死啊", "reason": "口头禅式吐槽"}]
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "writing-style.md"
    p.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
    errs = ca.check_style_card(p)
    assert not errs, errs
    print("蒸馏卡过校验 OK")
PY
```

Expected: 打印 `蒸馏卡过校验 OK`。（说明：蒸馏卡 = 原模板 frontmatter 解析后叠加字段，结构不动只填值/加声音层。）

- [ ] **Step 4: 验证旧模板仍过校验**

Run:
```bash
python tools/check-agents.py
```
Expected: `✅ agent 定义全部通过`，exit 0（旧模板未改过校验；新增校验对未蒸馏卡宽松跳过）。

- [ ] **Step 5: Commit**

```bash
git add tools/check-agents.py
git commit -m "feat: check-agents 双态卡校验（旧卡兼容 + 蒸馏卡可选增强字段存在才校验）"
```

---

### Task 3: style-distiller 技能重写（13 模板产卡 + 分析稿）

**Files:**
- Rewrite: `skills/style-distill.md`
- Modify: `agents/style-distiller.md`

**Interfaces:**
- Consumes: Task 1 的 `feature-extract.md`；Task 2 的双态卡 schema
- Produces: `skills/style-distill.md` 的蒸馏 SOP（不再调 distill-style.py / style-update-order / genre-baselines）—— Task 9 退役清理的 grep 依据；`agents/style-distiller.md` 的写白名单（含 analysis/）

- [ ] **Step 1: 重写 skills/style-distill.md**

整体替换为以下内容（删除旧「一段脚本统计/三段式/题材基线/增量蒸馏」节）：

```markdown
# style-distill skill — 三阶段 13 模板 LLM 蒸馏（style-distill-order）

## 一、主卡蒸馏
1. 收集样本：作者参考文本（.md/.txt）或已归档章节。少于 1500 字向 novel-agent 说明质量不足可挂起。
2. 读 `knowledge/style-distill/prompt-templates/feature-extract.md`（方法论 = 13 模板定义）。
3. 阶段一 拆解（模板 1-4）：对样本逐段/逐句/逐情绪标注（LLM 内部推理，不写文件）。
4. 阶段二 量化（模板 5-8）：频次/五层占比/情绪通道/词汇 → 量化表。
5. 阶段三 建模（模板 9-13）：句式卡/行为树/对话模式/节奏模型/锚点 → 建模规则。
6. 收敛：
   - 量化表 → 卡量化维（案例 1 九维，schema 见 check-agents）
   - 建模规则 → 卡声音层（hard_constraints / soft_guidance / few_shot_examples）
7. 写 `settings/writing-style.md`（收敛卡）+ `settings/style-profiles/analysis/general.md`（量化表 + 建模规则全文）。
8. 备份旧卡到 `settings/.style-versions/v{N}_{YYYY-MM-DD}.md`（N=现有最大+1，卡与分析稿同版本）。
9. confidence：LLM 按样本质量/一致性给 **1-100（必须 >0）**——0 仅用于未蒸馏/手动卡（走定性注入分支，见 prompt-crafting Step 1.1）；蒸馏卡置 0 会静默退回定性注入、丢失量化渲染。`last_updated` 写当日。

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
```

- [ ] **Step 2: 更新 agents/style-distiller.md**

- `description` 改为「三阶段 13 模板 LLM 提取，写风格主卡、场景卡、分析稿与版本快照」。
- `skills` 描述改为「三阶段 13 模板蒸馏 SOP（拆解 → 量化 → 建模 → 收敛卡 + 分析稿）」。
- `knowledge` 不动——`settings/style-profiles/` 已覆盖 analysis/ 子目录（DEPLOYED_PATTERNS `^settings/style-profiles/` 命中）；spec §3.1 规定分析稿不进任何 agent 加载清单、仅留档，因此 style-distiller 的 knowledge 声明不加 analysis/ 专用条目（写后自检走 skills/style-distill.md 的自检节）。
- `knowledge/style-distill/` 描述改为「feature-extract 方法论模板目录」。
- 二、写白名单表格：允许写加 `settings/style-profiles/analysis/*`；Bash 行改为「无脚本调用（纯 LLM 提取）」。
- 三、交接：删除「是否触发语义重估」表述（增量退役）；报告给「更新了哪些维度 + confidence + 分析稿摘要」。

- [ ] **Step 3: 验证无退役引用**

Run:
```bash
grep -rn "distill-style.py\|style-update-order\|genre-baselines\|增量" skills/style-distill.md agents/style-distiller.md; echo "exit=$?"
```
Expected: 无输出，exit=1（grep 无命中）。再跑：
```bash
python tools/check-agents.py
```
Expected: `✅ agent 定义全部通过`。

- [ ] **Step 4: Commit**

```bash
git add skills/style-distill.md agents/style-distiller.md
git commit -m "feat: style-distiller 技能重写为三阶段 13 模板 LLM 蒸馏（产卡+分析稿，卡冻结）"
```

---

### Task 4: 规则模块（style_render 渲染 + style_verify 验收聚合）

**Files:**
- Create: `tools/style_render.py`（卡 → 案例 2 渲染规则）
- Create: `tools/style_verify.py`（验收报告聚合 + 抽卡判定）
- Create: `tools/test_style_rules.py`（两模块单测，长期保留，CI 运行）

**Interfaces:**
- Consumes: 无（spec §6 渲染规则 / §7 验收与抽卡）
- Produces:
  - `range_for(value: float, confidence: int) -> str` —— 密度类数值区间（5.8@75 → `"5-6"`）
  - `enum_zh(key: str, value: str) -> str` —— 类别枚举 → 中文（spec §6.2 逐字对齐；`enum_zh("tag_style","mixed")` → `"标签混合使用"`）
  - `pct_zh(value: float) -> str` —— 占比 → 中文定性（48 → `"近一半"`）
  - `SCENE_INJECTION: dict` —— 场景稀疏注入矩阵（场景类型 → 注入维度）
  - `render_card(card: dict, scene_type: str = "general") -> dict[str, list[str]]` —— 卡 → 案例 2 各节条目：按 `SCENE_INJECTION[scene_type]` 稀疏注入（§6.3），量化回退（单值 npr → 比例描述、缺 inner_monologue_pct → 不注入该子项，§6.0b/§4.1），verb_style 力度/比例渲染（存在才注入）。Task 5 引用；测试断言输出。
  - `RANGE_TIERS`、`ENUM_ZH` 常量 —— test_style_rules.py 直接 import
  - `CHECK_CATEGORIES: list[str]` —— 验收检查项四类（数值/占比、硬性规则、建模规则、软引导）
  - `verdict(items: list[dict]) -> str` —— PASS（无违反）/ FAIL（任一违反）
  - `should_reroll(round_no: int, violated: int) -> bool` —— round<3 且 violated>0
  - `pick_best(rounds: list[dict]) -> dict` —— 违反最少一轮，同分取最新
  - `format_report(items: list[dict]) -> str` —— 违反报告表格渲染（条号/要求/表现/违反/建议 + 结论行）
  - `verdict`/`should_reroll`/`pick_best`/`format_report` 为 Task 6（anti-ai 违反报告口径）的确定性参照

- [ ] **Step 1: 写失败测试 tools/test_style_rules.py**

```python
#!/usr/bin/env python3
"""style_render + style_verify 规则单测（TDD Task 4，长期保留）。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from style_render import range_for, enum_zh, pct_zh, render_card, SCENE_INJECTION
from style_verify import verdict, should_reroll, pick_best, format_report

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ok  {name}")
    else: FAIL += 1; print(f"  FAIL {name}  {detail}")

CARD = {
    "profile_version": "1.0", "profile_name": "测试卡", "scene_type": "general",
    "source_sample_length": 5000, "confidence": 75, "last_updated": "2026-08-11",
    "lexicon": {"adj_density_per_100": 5.8, "adv_density_per_100": 3.5,
                "four_phrase_freq_per_100": 1.8, "preferred_words": ["好想死"], "banned_words": ["宛如"],
                "name_pronoun_ratio": {"name": 45, "he_she": 50, "i_you": 5}},
    "syntax": {"avg_sentence_length": 16, "sentence_length_dist": {"short_le_8": 38, "medium_9_20": 45, "long_21_35": 14, "xlong_gt_35": 3},
               "single_sentence_paragraph_pct": 38, "avg_sentences_per_paragraph": 2.2, "question_ratio": 13, "exclamation_ratio": 7},
    "rhythm": {"dialogue_pct": 48, "action_pct": 16, "environment_pct": 6, "inner_thought_pct": 25, "narration_pct": 5},
    "rhetoric": {"metaphor_density_per_100": 1.2, "metaphor_preference": {"weapon_metal": 5, "nature": 10, "body": 20, "abstract": 30, "other": 35},
                 "sensory_dist": {"visual": 72, "auditory": 15, "tactile": 10, "olfactory": 2, "gustatory": 1}},
    "emotion_expression": {"direct_pct": 15, "action_physiology_pct": 45, "environment_projection_pct": 5, "inner_monologue_pct": 35},
    "narrative": {"perspective": "third_limited", "focal_character": "贺天然", "inner_monologue_style": "direct"},
    "dialogue_style": {"tag_style": "mixed", "avg_dialogue_length": 12, "interrupt_freq_per_100": 6, "subtext_ratio": 22, "direct_address_freq_per_100": 8},
    "cohesion": {"conjunction_freq_per_100": 2.6, "transition_sentence_ratio": 0.04, "paragraph_bridge_style": "action"},
    "verb_style": {"action_verb_ratio": 35, "mental_verb_ratio": 40, "state_verb_ratio": 25, "strength": "medium"},
    "hard_constraints": ["内心独白必须用引号包裹"],
    "soft_guidance": ["整体基调：轻松吐槽向"],
    "few_shot_examples": [{"type": "inner_thought", "text": "好想死啊", "reason": "口头禅式吐槽"}],
}

def test_range_for():
    check("5.8@75 → '5-6'", range_for(5.8, 75) == "5-6", range_for(5.8, 75))
    check("16@75 → '14-18'", range_for(16, 75) == "14-18", range_for(16, 75))
    check("5.8@50 → 区间加宽(±20%)", range_for(5.8, 50) != range_for(5.8, 90), f"{range_for(5.8,50)} vs {range_for(5.8,90)}")

def test_enum_zh():
    check("mixed → 标签混合使用", enum_zh("tag_style", "mixed") == "标签混合使用", enum_zh("tag_style", "mixed"))
    check("pure_tags → 标签用'XX说'为主", enum_zh("tag_style", "pure_tags") == "标签用'XX说'为主", enum_zh("tag_style", "pure_tags"))
    check("medium → 动词力度中等", enum_zh("strength", "medium") == "动词力度中等", enum_zh("strength", "medium"))
    check("action → 段落靠动作衔接", enum_zh("paragraph_bridge_style", "action") == "段落靠动作衔接", enum_zh("paragraph_bridge_style", "action"))
    check("direct → 内心独白用引号直接呈现", enum_zh("inner_monologue_style", "direct") == "内心独白用引号直接呈现", enum_zh("inner_monologue_style", "direct"))
    check("未知值回退原值", enum_zh("strength", "???") == "???", enum_zh("strength", "???"))

def test_pct_zh():
    check("48 → 近一半", pct_zh(48) == "近一半", pct_zh(48))
    check("88 → 绝大多数", pct_zh(88) == "绝大多数", pct_zh(88))

def test_scene_injection():
    check("dialogue 场景含 dialogue_style", "dialogue_style" in SCENE_INJECTION["dialogue"], SCENE_INJECTION.get("dialogue"))
    check("fight 场景含 verb_style", "verb_style" in SCENE_INJECTION["fight"], SCENE_INJECTION.get("fight"))

def test_render_card():
    out = render_card(CARD)
    check("产出【句式】节", "句式" in out and any("平均句长" in x for x in out["句式"]), out.get("句式"))
    check("产出【词汇】节含密度区间", any("每百字 5-6" in x for x in out["词汇"]), out.get("词汇"))
    check("产出【对话风格】节", "对话风格" in out, list(out))
    check("硬性规则逐条透传", any("引号包裹" in x for x in out["硬性规则"]), out.get("硬性规则"))
    check("风格参考例句分组透传", any("inner_thought" in x for x in out["风格参考例句"]), out.get("风格参考例句"))

def test_render_card_verb():
    out = render_card(CARD)
    check("general 渲染动词力度", any("力度中等" in x for x in out["句式"]), out.get("句式"))
    check("general 渲染动词比例", any("动作 35%" in x for x in out["句式"]), out.get("句式"))

def test_render_card_sparse():
    out = render_card(CARD, "dialogue")
    check("dialogue 场景注入词汇", bool(out.get("词汇")), out.get("词汇"))
    check("dialogue 场景注入对话风格", bool(out.get("对话风格")), out.get("对话风格"))
    check("dialogue 场景不含句式", not out.get("句式"), out.get("句式"))
    check("dialogue 场景不含节奏", not out.get("节奏"), out.get("节奏"))

def test_render_card_fallback():
    legacy = dict(CARD)
    legacy["lexicon"] = dict(CARD["lexicon"])
    legacy["lexicon"]["name_pronoun_ratio"] = 55                      # 旧 jieba 卡单值
    legacy["emotion_expression"] = {k: v for k, v in CARD["emotion_expression"].items() if k != "inner_monologue_pct"}
    lo = render_card(legacy)
    check("单值 npr 渲染为比例", any("人名/代词使用比例 55%" in x for x in lo["词汇"]), lo.get("词汇"))
    check("缺 inner_monologue_pct 不注入该子项", not any("内心独白" in x for x in lo["情绪表达"]), lo.get("情绪表达"))

def test_verify_verdict():
    ok = [{"no": 1, "require": "禁'宛如'", "evidence": "无", "violated": False}]
    bad = [{"no": 1, "require": "禁'宛如'", "evidence": "出现1次", "violated": True}]
    check("无违反 → PASS", verdict(ok) == "PASS", verdict(ok))
    check("有违反 → FAIL", verdict(bad) == "FAIL", verdict(bad))

def test_verify_reroll():
    check("round1 有违反 → 重写", should_reroll(1, 2) is True)
    check("round3 有违反 → 不重写", should_reroll(3, 2) is False)
    check("无违反 → 不重写", should_reroll(1, 0) is False)

def test_verify_pick_best():
    rounds = [{"round": 1, "violated": 3}, {"round": 2, "violated": 1}, {"round": 3, "violated": 1}]
    check("取违反最少", pick_best(rounds)["violated"] == 1, pick_best(rounds))
    check("同分取最新", pick_best(rounds)["round"] == 3, pick_best(rounds))

def test_verify_report():
    r = format_report([{"no": 1, "require": "禁'宛如'", "evidence": "出现1次", "violated": True, "advice": "替换"}])
    check("含表头", "原文要求" in r, r)
    check("含结论 FAIL 与汇总", "FAIL" in r and "1/1" in r, r)

test_range_for(); test_enum_zh(); test_pct_zh(); test_scene_injection()
test_render_card(); test_render_card_verb(); test_render_card_sparse(); test_render_card_fallback()
test_verify_verdict(); test_verify_reroll(); test_verify_pick_best(); test_verify_report()
print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python tools/test_style_rules.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'style_render'`。

- [ ] **Step 3: 写 tools/style_render.py**

```python
#!/usr/bin/env python3
"""style-distiller LLM 重构：渲染规则模块（卡 → 案例 2 提示词）。

纯数据 + 纯函数，无 LLM 调用：
- RANGE_TIERS   confidence → 密度类数值区间公式（spec §6.1a）
- ENUM_ZH       类别枚举 → 中文渲染映射（spec §6.2）
- pct_zh        占比 → 中文定性（spec §6.1a 占比类）
- SCENE_INJECTION 场景稀疏注入矩阵（spec §6.3）
- render_card   卡 → 案例 2 各节渲染条目（prompt-crafter 只读引用；测试直接 import）

用法: python tools/style_render.py --card settings/writing-style.md
"""
from __future__ import annotations

import argparse
import sys

# 1) 密度类区间：confidence → ±%（spec 6.1a）
RANGE_TIERS = [(70, 0.10), (50, 0.20), (0, 0.30)]

def range_for(value: float, confidence: int) -> str:
    """5.8 @ 75 → '5-6'（X×(1±tier)，round 取整）"""
    tier = 0.30
    for floor, t in RANGE_TIERS:
        if confidence >= floor:
            tier = t
            break
    lo = max(0, round(value * (1 - tier)))
    hi = round(value * (1 + tier))
    if hi <= lo:
        hi = lo + 1
    return f"{lo}-{hi}"

# 2) 类别枚举 → 中文（spec 6.2，逐字对齐）
ENUM_ZH = {
    "tag_style": {
        "pure_tags": "标签用'XX说'为主", "mixed": "标签混合使用", "no_tags": "不用标签，动作替代"},
    "strength": {"weak": "动词力度轻", "medium": "动词力度中等", "strong": "动词力度烈"},
    "paragraph_bridge_style": {"action": "段落靠动作衔接", "dialogue": "靠对话衔接", "transition": "少用过渡句"},
    "inner_monologue_style": {"direct": "内心独白用引号直接呈现", "indirect": "间接转述"},
    "perspective": {"first_person": "第一人称", "second_person": "第二人称",
                    "third_limited": "第三人称有限视角", "third_omniscient": "第三人称全知视角"},
}

def enum_zh(key: str, value: str) -> str:
    return ENUM_ZH.get(key, {}).get(value, str(value))

# 3) 占比 → 中文定性（spec 6.1a）
def pct_zh(value: float) -> str:
    if value >= 80: return "绝大多数"
    if value >= 60: return "大部分"
    if value >= 40: return "近一半"
    if value >= 20: return "一部分"
    return "少量"

# 4) 场景稀疏注入矩阵（spec 6.3 / 旧 injection-template 表）
SCENE_INJECTION = {
    "general": ["lexicon", "syntax", "rhythm", "rhetoric", "emotion_expression",
                "narrative", "dialogue_style", "cohesion", "verb_style"],
    "dialogue": ["lexicon", "dialogue_style"],
    "fight": ["verb_style", "syntax"],
    "environment": ["rhetoric", "rhythm"],
    "inner-mono": ["emotion_expression", "narrative"],
    "transition": ["cohesion", "rhythm"],
    "group-scene": ["rhythm", "dialogue_style"],
}

# 5) 卡 → 案例 2 各节渲染
def _flatten_dists(d: dict) -> list[str]:
    """sentence_length_dist 等分布 → 阈值分条"""
    zh = {"short_le_8": "短句（≤8字）", "medium_9_20": "中句（9-20字）",
          "long_21_35": "长句（21-35字）", "xlong_gt_35": "超长句（>35字）",
          "weapon_metal": "兵器金属", "nature": "自然", "body": "身体", "abstract": "抽象", "other": "其他",
          "visual": "视觉", "auditory": "听觉", "tactile": "触觉", "olfactory": "嗅觉", "gustatory": "味觉",
          "name": "人名", "he_she": "他/她", "i_you": "我/你"}
    return [f"{zh.get(k, k)}占比 {v}%" for k, v in d.items() if v]

def render_card(card: dict, scene_type: str = "general") -> dict[str, list[str]]:
    conf = card.get("confidence") or 0
    out: dict[str, list[str]] = {k: [] for k in
        ["词汇", "句式", "节奏", "修辞与感官", "情绪表达", "对话风格", "衔接", "视角",
         "硬性规则", "整体基调", "风格参考例句"]}
    dims = SCENE_INJECTION.get(scene_type, SCENE_INJECTION["general"])   # 稀疏注入（spec 6.3）

    # 词汇
    if "lexicon" in dims:
        lex = card.get("lexicon") or {}
        out["词汇"].append(f"形容词密度：每百字 {range_for(lex.get('adj_density_per_100') or 0, conf)} 个")
        out["词汇"].append(f"副词密度：每百字 {range_for(lex.get('adv_density_per_100') or 0, conf)} 个")
        out["词汇"].append(f"四字短语频率：每百字 {range_for(lex.get('four_phrase_freq_per_100') or 0, conf)} 个")
        if lex.get("preferred_words"):
            out["词汇"].append("偏好词：" + "、".join(lex["preferred_words"]))
        npr = lex.get("name_pronoun_ratio")
        if isinstance(npr, dict):
            out["词汇"].extend(_flatten_dists(npr))                       # 三维 → 逐桶
        elif isinstance(npr, (int, float)):                               # 单值（旧 jieba 卡）→ 比例（spec 6.0b）
            out["词汇"].append(f"人名/代词使用比例 {npr}%")
    # 句式
    if "syntax" in dims:
        syn = card.get("syntax") or {}
        out["句式"].append(f"平均句长：{range_for(syn.get('avg_sentence_length') or 0, conf)} 字左右")
        sld = syn.get("sentence_length_dist")
        if isinstance(sld, dict):
            out["句式"].extend(_flatten_dists(sld))
        out["句式"].append(f"单句段占比 ≥ {syn.get('single_sentence_paragraph_pct') or 0}%")
        out["句式"].append(f"每段平均句数：{syn.get('avg_sentences_per_paragraph') or 0} 句")
        out["句式"].append(f"疑问句占比：{syn.get('question_ratio') or 0}%（{pct_zh(syn.get('question_ratio') or 0)}）")
        out["句式"].append(f"感叹句占比：{syn.get('exclamation_ratio') or 0}%")
        # verb_style 并入句式（fight 场景经 SCENE_INJECTION 注入；存在才渲染）
        vs = card.get("verb_style") or {}
        if vs.get("strength"):
            out["句式"].append(enum_zh("strength", vs["strength"]))
        if any(k in vs for k in ("action_verb_ratio", "mental_verb_ratio", "state_verb_ratio")):
            out["句式"].append(f"动词：动作 {vs.get('action_verb_ratio') or 0}% / 心理 {vs.get('mental_verb_ratio') or 0}% / 状态 {vs.get('state_verb_ratio') or 0}%")
    # 节奏
    if "rhythm" in dims:
        rhy = card.get("rhythm") or {}
        out["节奏"].append(f"对话约 {rhy.get('dialogue_pct') or 0}%（{pct_zh(rhy.get('dialogue_pct') or 0)}）")
        out["节奏"].append(f"动作约 {rhy.get('action_pct') or 0}%、环境约 {rhy.get('environment_pct') or 0}%")
        out["节奏"].append(f"内心独白约 {rhy.get('inner_thought_pct') or 0}%、叙述约 {rhy.get('narration_pct') or 0}%")
    # 修辞
    if "rhetoric" in dims:
        rhe = card.get("rhetoric") or {}
        out["修辞与感官"].append(f"比喻密度：每百字 {range_for(rhe.get('metaphor_density_per_100') or 0, conf)} 个")
        mp = rhe.get("metaphor_preference")
        if isinstance(mp, dict):
            out["修辞与感官"].append("常用喻体：" + "、".join(_flatten_dists(mp)))
        sd = rhe.get("sensory_dist")
        if isinstance(sd, dict):
            out["修辞与感官"].append("感官通道：" + "、".join(_flatten_dists(sd)))
    # 情绪
    if "emotion_expression" in dims:
        emo = card.get("emotion_expression") or {}
        out["情绪表达"].append(f"直接陈述 {emo.get('direct_pct') or 0}%、动作/生理 {emo.get('action_physiology_pct') or 0}%")
        if emo.get("inner_monologue_pct") is not None:                    # 缺省不注入该子项（spec 6.0b/4.1）
            out["情绪表达"].append(f"环境投射 {emo.get('environment_projection_pct') or 0}%、内心独白 {emo.get('inner_monologue_pct') or 0}%")
        else:
            out["情绪表达"].append(f"环境投射 {emo.get('environment_projection_pct') or 0}%")
    # 对话
    if "dialogue_style" in dims:
        dia = card.get("dialogue_style") or {}
        if dia.get("tag_style"):
            out["对话风格"].append(enum_zh("tag_style", dia["tag_style"]))
        out["对话风格"].append(f"平均对话长度：{range_for(dia.get('avg_dialogue_length') or 0, conf)} 字")
        out["对话风格"].append(f"打断频率：每百字 {range_for(dia.get('interrupt_freq_per_100') or 0, conf)} 次")
        out["对话风格"].append(f"潜台词占比：{dia.get('subtext_ratio') or 0}%")
    # 衔接
    if "cohesion" in dims:
        coh = card.get("cohesion") or {}
        out["衔接"].append(f"连接词频率：每百字 {range_for(coh.get('conjunction_freq_per_100') or 0, conf)} 次")
        if coh.get("paragraph_bridge_style"):
            out["衔接"].append(enum_zh("paragraph_bridge_style", coh["paragraph_bridge_style"]))
    # 视角
    if "narrative" in dims:
        nar = card.get("narrative") or {}
        if nar.get("perspective"):
            out["视角"].append(enum_zh("perspective", nar["perspective"]))
        if nar.get("focal_character"):
            out["视角"].append(f"聚焦角色：{nar['focal_character']}")
        if nar.get("inner_monologue_style"):
            out["视角"].append(enum_zh("inner_monologue_style", nar["inner_monologue_style"]))
    # 声音层透传
    out["硬性规则"] = list(card.get("hard_constraints") or [])
    out["整体基调"] = list(card.get("soft_guidance") or [])
    fse = card.get("few_shot_examples") or []
    out["风格参考例句"] = [f"[{e.get('type')}] {e.get('text')} — {e.get('reason')}" if isinstance(e, dict)
                        else str(e) for e in fse]
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True)
    args = ap.parse_args()
    import yaml
    text = __import__("pathlib").Path(args.card).read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        print("卡缺 frontmatter", file=sys.stderr)
        return 2
    card = yaml.safe_load(parts[1]) or {}
    for sec, items in render_card(card).items():
        if items:
            print(f"【{sec}】")
            for it in items:
                print(f"  - {it}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

创建 `tools/style_verify.py`：

```python
#!/usr/bin/env python3
"""style-distiller LLM 重构：验收聚合规则模块（案例2 验收报告 + 抽卡判定）。

纯数据 + 纯函数，无 LLM 调用：
- CHECK_CATEGORIES  验收检查项四类（spec 7.1）
- verdict           违反报告 PASS/FAIL 聚合（spec 7.1）
- should_reroll     抽卡判定：round<3 且本轮有违反 → 重写（spec 7.2）
- pick_best         超限取最优：违反最少一轮，同分取最新
- format_report     违反报告表格渲染（条号/原文要求/正文表现/违反与否/建议 + 结论行）

anti-ai 按此口径输出违反报告（格式见 verify-checklist.md）；本模块是确定性测试编码。
"""
from __future__ import annotations

# 1) 验收检查项四类（spec 7.1）
CHECK_CATEGORIES = ["数值/占比条", "硬性规则条", "建模规则条", "软引导条"]

def verdict(items: list[dict]) -> str:
    """全违反否 → PASS；任一违反 → FAIL"""
    return "FAIL" if any(i.get("violated") for i in items) else "PASS"

def should_reroll(round_no: int, violated: int) -> bool:
    """抽卡判定（spec 7.2）：round < 3 且本轮有违反 → 重写"""
    return round_no < 3 and violated > 0

def pick_best(rounds: list[dict]) -> dict:
    """超限取最优（spec 7.2）：违反条数最少的一轮，同分取最新"""
    return min(rounds, key=lambda r: (r.get("violated", 0), -rounds.index(r)))

def format_report(items: list[dict]) -> str:
    """违反报告表格渲染（spec 7.1 输出格式）"""
    lines = ["| 条号 | 原文要求 | 正文表现 | 违反与否 | 建议 |", "|---|---|---|---|---|"]
    for i, it in enumerate(items, 1):
        lines.append(
            f"| {it.get('no', i)} | {it.get('require', '')} | {it.get('evidence', '')} | "
            f"{'是' if it.get('violated') else '否'} | {it.get('advice', '')} |"
        )
    n_v = sum(1 for i in items if i.get("violated"))
    lines.append(f"\n结论：{'FAIL' if n_v else 'PASS'}（{n_v}/{len(items)}）")
    return "\n".join(lines)

if __name__ == "__main__":
    import json, sys
    items = json.load(sys.stdin)          # 例: [{"no":1,"require":"禁'宛如'","evidence":"出现1次","violated":true,"advice":"替换"}]
    print(format_report(items))
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python tools/test_style_rules.py`
Expected: 全部 ok，`35 passed, 0 failed`，exit 0。

- [ ] **Step 5: Commit**

```bash
git add tools/style_render.py tools/style_verify.py tools/test_style_rules.py
git commit -m "feat: 规则模块（style_render 渲染 + style_verify 验收聚合，区间/枚举/稀疏注入/报告/抽卡）"
```

---

### Task 5: prompt-crafter 渲染案例 2（技能 + 模板 + agent）

**Files:**
- Modify: `skills/prompt-crafting.md`
- Create: `knowledge/style-distill/prompt-templates/rendering-rules.md`
- Delete: `knowledge/style-distill/prompt-templates/injection-template.md`
- Modify: `agents/prompt-crafter.md`

**Interfaces:**
- Consumes: Task 4 的 `style_render.py` 规则（区间/枚举/注入矩阵）；spec §6 案例 2
- Produces: 渲染后的 `prompts/vol-{N}-ch-{M}-prompt.md` 含【词汇】【句式】【节奏】【修辞与感官】【情绪表达】【对话风格】【衔接】【视角】【硬性规则】【整体基调】【风格参考例句】【剧情上下文】【写作要求】—— Task 6（anti-ai 验收）与 Task 8（writer 重写）按此结构读取。

- [ ] **Step 1: 写 rendering-rules.md（案例 2 渲染规格）**

创建 `knowledge/style-distill/prompt-templates/rendering-rules.md`：

```markdown
# 案例 2 风格提示词渲染规格（prompt-crafter 已蒸馏态用）

## 适用范围（双态）
- 本规格仅用于**已蒸馏卡**（confidence>0）。未蒸馏态（confidence=0）由 prompt-crafting Step 1.1
  既有分支走正文定性四字段注入（现状不变，不读本文件）。

## 数据源
- 只读卡（settings/writing-style.md 主卡 + 按 scene_type 叠加 settings/style-profiles/{scene}.md override），
  **不读分析稿**（settings/style-profiles/analysis/）。
- 区间/枚举/注入矩阵规则：`tools/style_render.py`（读其 RANGE_TIERS / ENUM_ZH / SCENE_INJECTION 常量）。

## 渲染步骤
0. 回退守卫（§6.0b）：已蒸馏卡缺声音层（遗留 jieba 蒸馏卡，confidence>0 无 hard_constraints 等）→
   量化节照常渲染；声音层节【硬性规则】/【整体基调】/【风格参考例句】回退读卡正文定性四字段
   （叙事身份/硬约束/AI易犯错误/描写层次）注入，其中【风格参考例句】以正文的描写层次示例充当。
1. 数值密度类（adj_density_per_100 等）：按 confidence 用 RANGE_TIERS 定区间 →「每百字 L-U 个」。
2. 占比类（dialogue_pct 等）：「约 X%（中文定性：近一半/大部分/…）」。
3. 分布类（sentence_length_dist / metaphor_preference / sensory_dist / name_pronoun_ratio）：
   逐桶「{中文桶名}占比 X%」。
4. 类别枚举：按 ENUM_ZH 映射为中文短语（如 mixed → 「对话标签混合使用」）。
5. 稀疏注入：按本章 scene_type 用 SCENE_INJECTION 只注入相关维度；主卡兜底 general。
6. 声音层透传：hard_constraints →「硬性规则」逐条不删改；soft_guidance →「整体基调」；
   few_shot_examples →「风格参考例句」按 type 分组。
7. 固定注入：生成目标「严格匹配上述风格参数，偏差不超过 20%」+ 占位「剧情上下文」+「写作要求（直接写正文/字数）」。

## 输出结构
【词汇】【句式】【节奏】【修辞与感官】【情绪表达】【对话风格】【衔接】【视角】
【硬性规则】【整体基调】【风格参考例句】【剧情上下文】【写作要求】
```

- [ ] **Step 2: 更新 skills/prompt-crafting.md**

1. Step 1 第 1 条改为：**保留 confidence=0 分支不动**（读主卡正文 → 定性四字段注入，现状不变）；**confidence>0 分支替换为**按 rendering-rules.md 渲染案例 2（读主卡 + 场景卡 frontmatter → 量化节 + 声音层透传）。
2. Step 1 第 9 条（场景卡）保留，注明 override 叠加。
3. Step 2「输出·写作风格约束」子节改为**双态分支**：confidence=0 → 正文定性四字段注入（现状原样保留，节标题沿用）；confidence>0 → 该节输出 `【词汇】…【写作要求】`（案例 2 结构），引用 rendering-rules.md 的渲染步骤；「分工」注明量化节来自渲染规则、声音层原样透传。
4. Step 4 验收自检表：`writing-style 注入` 行改为「双态：confidence=0 → 定性四字段注入（现状不变）；confidence>0 → 案例 2 十一节齐全（量化节按 rendering-rules 渲染；硬性规则/基调/例句透传；无声音层走 §6.0b 回退）；banned_words 与 anti-ai 禁用词去重后无重复；无占位符泄漏」。

- [ ] **Step 3: 删除 injection-template.md、更新 agents/prompt-crafter.md**

```bash
git rm knowledge/style-distill/prompt-templates/injection-template.md
```

`agents/prompt-crafter.md`：`skills.prompt-crafting` 的 frontmatter 描述改为「4 层提示词组装 + 案例 2 风格参数渲染（rendering-rules）」；`knowledge` 不动——渲染规则由 `skills/prompt-crafting.md` 按仓库路径引用 `knowledge/style-distill/prompt-templates/rendering-rules.md`（该 skill 的 Step 2 已能读该目录模板，与旧 injection-template 同路径模式）。

- [ ] **Step 4: 验证**

Run:
```bash
grep -n "写作风格约束\|injection-template\|案例 2\|rendering-rules\|confidence" skills/prompt-crafting.md agents/prompt-crafter.md | head
python tools/check-agents.py
```
Expected: prompt-crafting.md **保留** `写作风格约束`（未蒸馏态定性注入节，现状不动）、无 `injection-template` 残留、出现 `案例 2`/`rendering-rules`/`confidence` 分支（已蒸馏态渲染）；check-agents `✅`。

- [ ] **Step 5: Commit**

```bash
git add skills/prompt-crafting.md agents/prompt-crafter.md knowledge/style-distill/prompt-templates/
git commit -m "feat: prompt-crafter 渲染案例2 提示词（rendering-rules 规格，风格约束块替换）"
```

---

### Task 6: anti-ai 案例 2 验收（指令遵循 + 违反报告）

**Files:**
- Modify: `skills/anti-ai.md`
- Create: `knowledge/style-distill/prompt-templates/verify-checklist.md`
- Delete: `knowledge/style-distill/prompt-templates/gate-g-checklist.md`
- Modify: `agents/anti-ai.md`

**Interfaces:**
- Consumes: Task 5 产出的案例 2 提示词（`prompts/vol-{N}-ch-{M}-prompt.md`）；spec §7
- Produces: `archives/*.anti-ai.md` 内嵌/相邻的**验收违反报告**（结论 PASS/FAIL + 逐条 条号/原文要求/正文表现/违反与否/建议）—— Task 7（novel-agent 抽卡）按此读取 verdict；Task 8（writer 重写）按违反报告条目反馈。

- [ ] **Step 1: 写 verify-checklist.md**

创建 `knowledge/style-distill/prompt-templates/verify-checklist.md`：

```markdown
# 案例 2 验收检查清单（anti-ai 用，替代旧 Gate G / distill-style.py check）

## 触发
对每章正文跑指令遵循验收：读同章 `prompts/vol-{N}-ch-{M}-prompt.md` 的
【词汇】【句式】【节奏】【修辞与感官】【情绪表达】【对话风格】【衔接】【视角】
【硬性规则】【整体基调】【风格参考例句】逐条对照正文判定。用与生成同一份提示词（同源）。
（双态：未蒸馏态提示词无量化节、含正文定性四字段 → 按定性条验收「叙事身份/硬约束/AI易犯错误/描写层次」；已蒸馏态 → 下方四类条 + 【风格参考例句】作风格锚点逐句对照正文。遗留 jieba 卡（confidence>0 无声音层）的硬性规则/基调/例句按 §6.0b 回退读正文定性四字段，例句以描写层次示例充当。）

## 检查项（四类）
1. 数值/占比条：「对话约 48%」→ 本章对话是否明显偏离（偏离即违反，不要求数值精确）。
2. 硬性规则条：逐条判定（如「禁止'宛如'」→ 查是否出现；出现即违反）。
3. 建模规则条：节奏参数（对话密集区≥4轮后必须独白缓冲、纯叙述≤3句）、对话模式（D-01~）、
   锚点（章首/章尾语义闭环）逐条判定。
4. 软引导条：整体基调是否吻合。

## 违反报告格式（写入 archives/*.anti-ai.md 验收节）
| 条号 | 原文要求 | 正文表现 | 违反与否 | 建议 |
结论：PASS / FAIL（违反条数 / 总条数）
汇总/判定/报告的确定性编码见 tools/style_verify.py（verdict / pick_best / format_report），anti-ai 按此口径输出。
```

- [ ] **Step 2: 更新 skills/anti-ai.md 的 Gate G 段**

把「Gate G：风格偏差」整段（含 `python tools/distill-style.py check`、退出码 0/1/2、按 gate-g-checklist 分级）替换为：

```markdown
### Gate G：风格验收（指令遵循，读同章提示词）
- 读 `prompts/vol-{N}-ch-{M}-prompt.md`（与 writer 生成同源），按 `knowledge/style-distill/prompt-templates/verify-checklist.md`
  逐条对照正文判定（数值/占比、硬性规则、建模规则、软引导四类）。
- 双态通用：提示词恒带风格（未蒸馏=正文定性四字段；已蒸馏=案例 2 量化+声音层），两种状态都用本流程、只按提示词内容验收。
- 输出违反报告（.anti-ai.md 验收节）：逐条「条号 + 原文要求 + 正文表现 + 违反与否 + 建议」，汇总违反条数/总条数，结论 PASS/FAIL。
- 汇总/判定/报告格式对齐 `tools/style_verify.py`（verdict/should_reroll/pick_best/format_report）；违反条目即抽卡反馈源。
- Gate A-F（去 AI 味）保持不变；Gate G 只出 verdict，不改正文。
```

Phase 2 表**删除**「风格偏差维度数」行（Gate G 已改为独立 PASS/FAIL，违反条数只在验收节汇总，不参与去 AI 味 severity 分级）。

- [ ] **Step 3: 删除 gate-g-checklist.md、更新 agents/anti-ai.md**

```bash
git rm knowledge/style-distill/prompt-templates/gate-g-checklist.md
```

`agents/anti-ai.md`：
- `knowledge`：删除 `settings/writing-style.md` + `settings/style-profiles/`（Gate G 基线不再直读卡——spec §3.1 同源验收，只读渲染后提示词）；`.claude/knowledge/style-distill/prompt-templates/gate-g-checklist.md` 路径改为 `verify-checklist.md`；新增 `prompts/`（`^prompts/` 已在 DEPLOYED_PATTERNS，无需模板）。
- Input Sources 增加 `prompts/vol-{N}-ch-{M}-prompt.md`（同源验收）；Output Artifacts 注明 `.anti-ai.md` 含验收违反报告节。
- 二、职责中「Gate G 独立判定」表述改为「案例 2 指令遵循验收」。

- [ ] **Step 4: 验证**

Run:
```bash
grep -rn "distill-style.py\|gate-g-checklist\|退出码\|exit code\|jieba" skills/anti-ai.md agents/anti-ai.md knowledge/style-distill/prompt-templates/ ; echo "grep_exit=$?"
python tools/check-agents.py
```
Expected: grep 无命中（exit=1），check-agents `✅`。

- [ ] **Step 5: Commit**

```bash
git add skills/anti-ai.md agents/anti-ai.md knowledge/style-distill/prompt-templates/
git commit -m "feat: anti-ai 案例2 指令遵循验收（verify-checklist，替代 Gate G 退出码契约）"
```

---

### Task 7: novel-agent 抽卡调度 + 卡冻结

**Files:**
- Modify: `agents/novel-agent.md`
- Modify: `skills/novel-dispatch.md`
- Modify: `ARCHITECTURE.md`（调度树注释：archive → style-distiller 增量行删除）

**Interfaces:**
- Consumes: Task 6 的违反报告 verdict（FAIL → 抽卡）；spec §7.2/§7.3
- Produces:
  - `writing-order.md` 新增字段契约（本任务定义，Task 8 消费）：
    `rewrite_of: archives/vol-{N}-ch-{M}-{slug}.draft.md`、`round: 1..3`、
    `violations: .agent/task/vol-{N}-ch-{M}-violations.md`（违反报告全文）
  - 删除归档后 `style-update-order` 调度（卡冻结）

- [ ] **Step 1: 更新 agents/novel-agent.md 的 anti-ai 分支**

在 `├── anti-ai → step=anti-ai` 分支（原「→ anti-ai 去 AI 味 → order DONE 后推进章节状态=anti-ai」）替换为抽卡逻辑：

```text
├── anti-ai → step=anti-ai → 读状态：章节状态 > anti-ai？→ 已跳过；
│     否则 → 派 anti-ai 验收（读 prompts 同源提示词 → 违反报告 PASS/FAIL）
│           order DONE 后读 .anti-ai.md 的验收节 verdict：
│           ├── FAIL 且 round < 3 → 写 rewrite-order（writing-order.md 带
│           │     rewrite_of + round + violations 字段，violations = 违反报告全文落 .agent/task/{chapter}-violations.md）
│           │     → 派 writer 重写 → writer DONE 后重派 anti-ai 再验收（round+1）
│           ├── FAIL 且 round == 3 → 取违反最少稿（比较各轮违反条数），报告留作者人工裁决，推进章节状态=anti-ai
│           └── PASS → 推进章节状态=anti-ai
```

删除归档分支中的 `style-update-order` 段（原「归档完成后 → 写 style-update-order.md → 调 style-distiller（增量）→ DONE 后再继续卷完成判定」），替换为注释：`卡冻结——归档后无风格增量；重蒸馏仅作者主动触发 style-distill-order`。

同步改 `ARCHITECTURE.md` 调度树：删除 `archive → style-distiller（style-update-order.md，每次归档后增量）` 行，替换为注释 `卡冻结：归档后无风格增量更新`（ARCHITECTURE.md:79）。

- [ ] **Step 2: 更新 skills/novel-dispatch.md**

1. 调度表删除行：`archive | style-distiller | style-update-order.md（每次归档后增量蒸馏）`；`手动 | style-distiller | style-distill-order.md / style-update-order.md` 改为只留 `style-distill-order.md`。
2. 新增「抽卡重写」行：`anti-ai FAIL | writer | writing-order.md（rewrite_of + round + violations）`。
3. 写 order 文件规则第 2 条补充：rewrite-order 只含 rewrite_of/round/violations 路径 + 原始风格提示词路径，不含执行步骤。

- [ ] **Step 3: 验证无 style-update-order 残留**

Run:
```bash
grep -rn "style-update-order" agents/ skills/ ARCHITECTURE.md ; echo "grep_exit=$?"
python tools/check-agents.py
```
Expected: grep 无命中（exit=1）；check-agents `✅`。

- [ ] **Step 4: Commit**

```bash
git add agents/novel-agent.md skills/novel-dispatch.md ARCHITECTURE.md
git commit -m "feat: novel-agent 抽卡调度（FAIL→writer 重写≤3）+ 卡冻结（去 style-update-order）"
```

---

### Task 8: writer 带反馈重写

**Files:**
- Modify: `agents/writer.md`
- Modify: `skills/writing-execution.md`

**Interfaces:**
- Consumes: Task 7 的 `writing-order.md` rewrite 字段契约；Task 5 的案例 2 提示词
- Produces: 重写后的 `archives/vol-{N}-ch-{M}-{slug}.draft.md`（只重写违反项，其余保持）—— Task 7 再派 anti-ai 复验。

- [ ] **Step 1: 更新 skills/writing-execution.md**

在流程头部（Step 1 准备 前）增加重写分支：

```markdown
## 重写分支（writing-order.md 含 rewrite_of 时）
1. 读 writing-order.md 的 rewrite_of / round / violations 字段。
2. 读原始案例 2 提示词 prompts/vol-{N}-ch-{M}-prompt.md + 违反报告 violations 文件。
3. 只重写违反报告中标记「违反」的条目对应段落，向「建议」靠拢；其余段落保持原文。
4. 完成后照常写 archives/*.draft.md，order 标 DONE（保留 round 原值，由 novel-agent 递增）。
```

- [ ] **Step 2: 更新 agents/writer.md**

- 三、Input Sources 增加：`.agent/task/writing-order.md` 的 rewrite 字段（rewrite_of/round/violations）、`.agent/task/*-violations.md`（重写时）。
- 七、Retry Policy 改为「抽卡重写由 novel-agent 调度，round ≤3；单次生成内部自检仍最多 2 次补充」。
- 四、Loop Integration 的 OBSERVE 增加「读 writing-order.md，若含 rewrite_of → 走重写分支」。
- **风格源切换（渲染后提示词 = 唯一写作风格源，双态通用；writer 不再直读卡正文四字段）：**
  - 三、Input Sources：删除 `settings/writing-style.md`（写作风格方法论）一行；`settings/genre-setting.md`（题材设定）保留。
  - 一、Dependencies：把「写前加载 writing-style.md 和 genre-setting.md 获取写作风格与题材设定」改为「写前加载案例 2 提示词（风格已渲染在内）和 genre-setting.md 获取题材设定」。
  - 四、Loop：OBSERVE 的「读 settings/」与 ACT 的「写前加载：writing-style.md 写作风格方法论」→ 均改为「写前加载：案例 2 提示词（风格节已在其中）」。
  - 五、Read 权限：`settings/` 从「仅 writing-style.md 和 genre-setting.md」改为「仅 genre-setting.md」；Permission Level 行同步。
  - 六、Style Rules：删除 role/core_principles/possible_mistakes/depiction_techniques 四项映射，改为「**Style Rules（渲染后提示词 = 唯一写作风格源，双态通用）**：未蒸馏态 = 正文定性四字段（叙事身份/硬约束/AI易犯错误/描写层次，prompt-crafter 注入现状不变）；已蒸馏态 = 硬性规则（不可违背）+ 整体基调（soft_guidance）+ 风格参考例句（few_shot）——prompt-crafter 已从卡渲染进提示词，writer 不直读卡正文」。
  - 九、Context Isolation：`settings/ 设定文件` → `settings/ 的 genre-setting.md`。

- [ ] **Step 3: 验证**

Run: `python tools/check-agents.py`
Expected: `✅ agent 定义全部通过`（无 skill 路径缺失）。

- [ ] **Step 4: Commit**

```bash
git add agents/writer.md skills/writing-execution.md
git commit -m "feat: writer 带违反报告重写（rewrite_of/round/violations 分支）"
```

---

### Task 9: 退役清理（删 3 工具 + jieba + init/sync 更新）

**Files:**
- Delete: `tools/distill-style.py`、`tools/compare-style.py`、`tools/mix-style.py`
- Modify: `tools/init.py`、`tools/sync-project.py`
- Modify: `.github/workflows/static.yml`

**Interfaces:**
- Consumes: Task 3/6 已消除对退役工具的引用
- Produces: 仓库无 distill/compare/mix/jieba/style-update-order 引用；init/sync 不再部署风格工具脚本；`_write_new_style_card`/`migrate_writing_style` **保持旧 schema 原样**（双态向前兼容：无迁移钩子，未蒸馏态零改动）

- [ ] **Step 1: 删除退役工具**

```bash
git rm tools/distill-style.py tools/compare-style.py tools/mix-style.py
```

- [ ] **Step 2: 更新 tools/init.py**

1. 删除 `_DEPLOY_TOOLS = ["distill-style.py", "compare-style.py", "mix-style.py"]`（init.py:318）及 `deploy_tools` 函数（init.py:321-330，仅服务这三脚本）——`deploy_tools` 调用一并移除，不再向新项目拷贝风格工具脚本。
2. `_write_new_style_card`（init.py:454）与 `migrate_writing_style`（init.py:585-608）**保持旧模板原样**——双态向前兼容要求未蒸馏态零改动、**无 schema 迁移**（spec §8 不迁移；蒸馏卡由 style-distiller 收敛时在原卡结构上叠加填值，见 Task 3）。

- [ ] **Step 3: 更新 tools/sync-project.py**

1. 删除 `_STYLE_TOOL_NAMES = ("distill-style.py", "compare-style.py", "mix-style.py")` 及 `sync_style_assets` 中的脚本同步逻辑（保留 templates/settings 树部署 + 迁移钩子——部署补缺语义，与卡 schema 迁移无关，见 Task 9 Step 2）。
2. `sync_style_assets`（sync-project.py:411+）递归部署 `templates/settings/` 树——`genre-baselines/` 模板随树保留作纯参照（spec §8「模板可留作纯参照」）；更新该处注释为「主卡 + 场景卡 + genre-baselines（纯参照，无运行时引用）」。
3. 运行时 `settings/style-profiles/analysis/` 是蒸馏产物，无需模板——确认不部署。

- [ ] **Step 4: 更新 static.yml + tools/requirements.txt**

`static.yml`：
1. `run: pip install pyyaml jieba`（line 28）→ `run: pip install pyyaml`。
2. `style-distiller 验证` 步骤（line 37-38）改为两行：
```yaml
      - name: style-distiller 验证
        run: |
          python tools/test_style_distill.py
          python tools/test_style_rules.py
```

`tools/requirements.txt`：删除 `jieba` 行及注释里对 distill-style.py/jieba 的说明（保留 pyyaml）。

- [ ] **Step 5: 验证无残留 + 回归**

Run:
```bash
grep -rn "distill-style\|compare-style\|mix-style\|jieba" tools/init.py tools/sync-project.py tools/requirements.txt .github/workflows/static.yml skills/ agents/ knowledge/ templates/ ARCHITECTURE.md | grep -v "style-distill-order\|style_distill\|style-distill/\|test_style\|feature-extract\|genre-baselines"; echo "grep_exit=$?"
python -m py_compile tools/*.py
python tools/check-agents.py
python tools/test_platforms.py
```
Expected: grep 只余允许的白名单命中或为空；py_compile 0；check-agents `✅`；test_platforms 全绿。

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: 退役统计引擎（distill/compare/mix 删 + jieba 去依赖）+ init/sync/CI 更新"
```

---

### Task 10: 测试重写 + CI + 双态 + 全量回归

**Files:**
- Rewrite: `tools/test_style_distill.py`（保留文件名，删旧数字断言；渲染/验收单测已在 Task 4 的 `tools/test_style_rules.py`，此处不重复）

**Interfaces:**
- Consumes: Task 1-9 全部产物；Task 4 的 `test_style_rules.py`（已绿，CI 与本节同时运行）；spec §10 测试矩阵
- Produces: `tools/test_style_distill.py` 全绿（schema/方法论/退役/抽卡契约/双态断言）

- [ ] **Step 1: 重写 tools/test_style_distill.py**

整体替换为以下测试组（风格沿用仓库 `check()` 断言模式）：

```python
#!/usr/bin/env python3
"""style-distiller LLM 重构验证脚本（模板/流程/schema 断言，不依赖 LLM 精确数值）。

用法: python tools/test_style_distill.py
返回码 0 = 全部通过（CI 用）。

覆盖（spec §10；渲染/验收/抽卡判定部分在 tools/test_style_rules.py，本文件不重复）：
- schema 合法性：check-agents 的卡校验对主卡/场景卡模板通过（含分布和=100、枚举）
- 13 模板方法论：feature-extract.md 十三节齐全 + verify-checklist/rendering-rules 存在、退役模板已删
- 退役清理：三工具已删、CI 无 jieba、init/sync 无风格工具部署
- 抽卡契约：rewrite_of/violations 字段 + 无 style-update-order 残留（novel-agent/writer/dispatch 文档）+ writer 不以卡正文四字段为风格源
- 双态：未蒸馏模板 / 蒸馏卡 / 遗留 jieba 卡三态过 check_style_card（增强字段可选、存在才校验）+ init 模板保留 locked（未蒸馏态零改动）
"""
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ok  {name}")
    else: FAIL += 1; print(f"  FAIL {name}  {detail}")

def test_feature_extract():
    t = (REPO / "knowledge/style-distill/prompt-templates/feature-extract.md").read_text(encoding="utf-8")
    for name in ["模板 1", "模板 2", "模板 3", "模板 4", "模板 5", "模板 6", "模板 7",
                 "模板 8", "模板 9", "模板 10", "模板 11", "模板 12", "模板 13", "阶段一", "阶段二", "阶段三"]:
        check(f"feature-extract 含 {name}", name in t)
    # 13 模板 schema token（spec §9：量化表键完整、建模规则格式正确——句式卡结构公式/对话模式轮次序列/节奏模型关键参数/锚点模型章首章尾）
    for token in ("量化表", "结构公式", "轮次序列", "关键参数", "章首锚点", "章尾锚点"):
        check(f"feature-extract 含 schema token「{token}」", token in t)
    for f in ("rendering-rules.md", "verify-checklist.md"):
        check(f"{f} 存在", (REPO / "knowledge/style-distill/prompt-templates" / f).exists())
    for gone in ("distill-prompt.md", "injection-template.md", "gate-g-checklist.md"):
        check(f"退役模板 {gone} 已删", not (REPO / "knowledge/style-distill/prompt-templates" / gone).exists())

def test_schema_templates():
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_agents", str(TOOLS / "check-agents.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    main_tpl = REPO / "templates/settings/writing-style.md"
    errs = mod.check_style_card(main_tpl)
    check("主卡模板过卡校验", not errs, "; ".join(errs))
    for scene in sorted((REPO / "templates/settings/style-profiles").glob("*.md")):
        errs = mod.check_style_card(scene)
        check(f"场景卡 {scene.name} 过卡校验", not errs, "; ".join(errs))

def test_retire_clean():
    for bad in ("tools/distill-style.py", "tools/compare-style.py", "tools/mix-style.py"):
        check(f"{bad} 已删", not (REPO / bad).exists())
    static = (REPO / ".github/workflows/static.yml").read_text(encoding="utf-8")
    check("CI 无 jieba", "jieba" not in static)
    check("CI 运行 test_style_rules", "test_style_rules.py" in static)
    req = (REPO / "tools/requirements.txt").read_text(encoding="utf-8")
    check("requirements 无 jieba", "jieba" not in req)
    init = (REPO / "tools/init.py").read_text(encoding="utf-8")
    check("init 无 distill-style 部署", "distill-style.py" not in init)
    sync = (REPO / "tools/sync-project.py").read_text(encoding="utf-8")
    check("sync 无 _STYLE_TOOL_NAMES", "_STYLE_TOOL_NAMES" not in sync)

def test_reroll_contract():
    for f in ("agents/novel-agent.md", "agents/writer.md", "skills/writing-execution.md", "skills/novel-dispatch.md"):
        t = (REPO / f).read_text(encoding="utf-8")
        check(f"{f} 含 rewrite_of", "rewrite_of" in t)
        check(f"{f} 含 violations", "violations" in t)
        check(f"{f} 无 style-update-order", "style-update-order" not in t)
    writer_t = (REPO / "agents/writer.md").read_text(encoding="utf-8")
    check("writer 不以卡正文为风格源",
          "写作风格方法论" not in writer_t and "depiction_techniques" not in writer_t
          and "possible_mistakes" not in writer_t)

def test_anti_ai_verify():
    skill = (REPO / "skills/anti-ai.md").read_text(encoding="utf-8")
    check("anti-ai 含指令遵循验收", "指令遵循" in skill or "案例 2" in skill or "verify-checklist" in skill)
    check("anti-ai 无 distill-style.py", "distill-style.py" not in skill)
    check("anti-ai 无 gate-g-checklist", "gate-g-checklist" not in skill)

def test_dual_mode():
    import importlib.util, tempfile, yaml
    spec = importlib.util.spec_from_file_location("check_agents", str(TOOLS / "check-agents.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    main_tpl = REPO / "templates/settings/writing-style.md"
    fm = yaml.safe_load(main_tpl.read_text(encoding="utf-8").split("---", 2)[1])
    # 未蒸馏态：模板零改动、confidence=0 过校验（spec §4）
    check("未蒸馏态（旧模板原样）过卡校验", not mod.check_style_card(main_tpl))
    check("未蒸馏态 confidence=0", fm.get("confidence") == 0, str(fm.get("confidence")))
    # 蒸馏卡：原卡结构叠加声音层 + 增强字段 + confidence>0 → 过校验
    fm["profile_name"] = "测试蒸馏卡"; fm["confidence"] = 75
    fm["lexicon"]["name_pronoun_ratio"] = {"name": 45, "he_she": 50, "i_you": 5}
    fm["rhetoric"]["metaphor_preference"] = {"weapon_metal": 5, "nature": 10, "body": 20, "abstract": 30, "other": 35}
    fm["rhetoric"]["sensory_dist"] = {"visual": 72, "auditory": 15, "tactile": 10, "olfactory": 2, "gustatory": 1}
    fm["emotion_expression"]["inner_monologue_pct"] = 35
    fm["verb_style"]["strength"] = "medium"
    fm["hard_constraints"] = ["内心独白必须用引号包裹"]
    fm["soft_guidance"] = ["整体基调：轻松吐槽向"]
    fm["few_shot_examples"] = [{"type": "inner_thought", "text": "好想死啊", "reason": "口头禅式吐槽"}]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "writing-style.md"
        p.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        errs = mod.check_style_card(p)
        check("蒸馏卡（声音层+增强字段+confidence>0）过卡校验", not errs, "; ".join(errs))
    # 遗留 jieba 蒸馏卡：confidence>0、无声音层/增强字段 → 过校验（spec §6.0b 回退兼容）
    fm2 = yaml.safe_load(main_tpl.read_text(encoding="utf-8").split("---", 2)[1])
    fm2["confidence"] = 70
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "writing-style.md"
        p.write_text("---\n" + yaml.safe_dump(fm2, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        errs = mod.check_style_card(p)
        check("遗留 jieba 卡（confidence>0 无声音层）过卡校验", not errs, "; ".join(errs))
    # init 模板保留 locked（未蒸馏态零改动，无迁移）
    init = (REPO / "tools/init.py").read_text(encoding="utf-8")
    check("init 模板保留 locked（未蒸馏态零改动）", "locked" in init)
    # prompt-crafting 双态分支（spec §6：未蒸馏=正文定性四字段注入现状不变 / 已蒸馏=案例 2 渲染）
    pc = (REPO / "skills/prompt-crafting.md").read_text(encoding="utf-8")
    check("prompt-crafting 含 confidence 分支", "confidence" in pc)
    check("prompt-crafting 保留未蒸馏定性注入节（写作风格约束）", "写作风格约束" in pc)
    check("prompt-crafting 引用 rendering-rules（已蒸馏渲染）", "rendering-rules" in pc)
    check("prompt-crafting 引用 案例 2 结构", "案例 2" in pc)

def run_all():
    test_feature_extract(); test_schema_templates(); test_retire_clean()
    test_reroll_contract(); test_anti_ai_verify(); test_dual_mode()
    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0

if __name__ == "__main__":
    sys.exit(run_all())
```

- [ ] **Step 2: 跑测试**

```bash
python tools/test_style_distill.py
python tools/test_style_rules.py
```
Expected: 两个文件全部 ok，`0 failed`，exit 0。

- [ ] **Step 3: 全量回归**

Run（顺序执行，全部须绿）：
```bash
python tools/test_style_distill.py
python tools/test_style_rules.py
python tools/test_platforms.py
python tools/check-agents.py
python tools/check-conflicts.py
python -m py_compile tools/*.py
```
Expected: test_style_distill + test_style_rules 全绿；test_platforms 全绿（107-108，随 Python 版本 tomllib 分支：CI 3.11 → 108）；check-agents exit 0；check-conflicts exit 0；py_compile 0。

- [ ] **Step 4: Commit**

```bash
git add tools/test_style_distill.py tools/
git commit -m "feat: 测试重写为模板/流程/schema 断言（渲染/验收单测在 test_style_rules.py）+ 全量回归"
```

- [ ] **Step 5: 提交本计划文件（docs 被 gitignore）**

```bash
git add -f docs/superpowers/plans/2026-08-11-style-distiller-llm-rework.md
git commit -m "docs: style-distiller LLM 重构实施计划（10 任务）"
```

---

## 验收对照（spec §11 → 任务）

| spec 验收 | 覆盖任务 |
|-----------|---------|
| C2' 生成验收 PASS 率 ≥90%（流程级） | Task 6/7/8（验收 + 抽卡，人工/作者跑） |
| C3' 场景区分 | Task 3（场景卡三阶段）、Task 5（稀疏注入） |
| C5 双态向前兼容（零迁移、旧项目零改动） | Task 2/9/10（check-agents 双态校验 + init 模板不动 + test_dual_mode 三态断言） |
| C6 作者盲测 ≥70%（主验收） | 代码路径就绪（Task 1-10）；填标杆卡 + 盲测为作者内容任务 |
