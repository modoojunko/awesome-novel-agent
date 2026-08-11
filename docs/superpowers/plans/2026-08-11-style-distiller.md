# style-distiller（文风蒸馏与风格化生成）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 awesome-novel 新增第 9 个子 agent `style-distiller`，实现 F1-F8：风格卡数据结构（数字化 9 大维度）、jieba 脚本统计 + LLM 语义两段式蒸馏、prompt-crafter 按场景稀疏注入、分场景风格卡、增量更新 + 备份 + locked、anti-ai Gate G 风格校验、compare/mix 风格工具。

**Architecture:** 风格卡（`settings/writing-style.md` 主卡 + `settings/style-profiles/*` 场景卡）承载「YAML frontmatter 量化层（9 大维度）+ Markdown 正文定性层（旧 4 字段迁移）」双结构。新增 `tools/distill-style.py` 做确定性统计（jieba POS，无 jieba 降级纯正则），style-distiller agent 先跑脚本拿 partial YAML 证据、再跑 LLM 语义标注补全、合并写卡。prompt-crafter 在 Step 1 读主卡 + 本章场景卡，按场景类型稀疏注入「写作风格约束」块（量化数值用「约 X（±Y%）」容差表述），与 scene-craft「场景写作指引」块分工去重。增量更新（F5）用滑动平均 + 版本备份 + locked 跳过；Gate G（F6）复用同一脚本按容差档校验。

**Tech Stack:** Python 3（标准库 + pyyaml + jieba 可选）、Claude Code agents/skills Markdown、YAML frontmatter、git。

**Spec:** `docs/superpowers/specs/2026-08-10-style-distiller-design.md`

---

## Global Constraints

- **场景类型枚举（唯一）**：`general | dialogue | fight | environment | inner-mono | transition | group-scene`（复用 prompt-crafter 现有 6 类，主卡用 `general`，不引入平行枚举）。
- **9 大维度键名（唯一 schema）**：`lexicon / syntax / rhythm / rhetoric / emotion_expression / narrative / dialogue_style / cohesion / verb_style`，各维度字段见 distilled-style-spec.md，前后任务必须一致。
- **置信度公式**：`confidence = min(100, 20 + min(40, sample_length/50) + min(40, chapter_count*5))`。
- **容差档**：0-20 手动不校验 / 21-50 ±30% / 51-70 ±20% / 71-90 ±15% / 91-100 ±10%。
- **滑动平均 α**：confidence<30→0.5 / 30-60→0.65 / >60→0.75。
- **注入优先级**：作者最新记忆偏好（writing-memory）> 风格卡数值 > genre-example 基线；风格卡内 `banned_words`/`hard_constraints` 为红线级（任何压缩不得删改），量化数值为写作规范级（与第 6 层同级）。
- **confidence=0 语义**：只注入定性层，量化层不注入，直到首次蒸馏。
- **格式**：卡片 frontmatter 用 YAML（`profile_version: "1.0"`）；正文定性层保留旧 4 字段内容（role/core_principles/possible_mistakes/depiction_techniques → 新节名），迁移零损失。
- **脚本约束**：`distill-style.py` 只做确定性计算，无网络无 LLM；jieba 缺失时降级纯正则（需 POS 的项记 None）。
- **写白名单**：style-distiller 只写 `settings/writing-style.md`、`settings/style-profiles/`、`settings/.style-versions/`，其余 settings 仍归 updater（ARCHITECTURE.md 标注此例外）。
- **幂等**：增量更新写 `.agent/style-update/{chapter}.done` checkpoint（与 `.agent/archiving/` 同款），防重放。
- **docs/ 在 .gitignore**：计划与 spec 相关提交需 `git add -f`。

---

## 验收标准（Spec §13 六项 → 可执行验收）

| # | 标准 | 验证方法 | 载体 | 通过条件 |
|---|------|---------|------|---------|
| **C1** | 1500 字样本蒸馏，核心参数（句长/形容词密度/对话占比/连接词密度）与人工统计偏差 ≤15% | 单元测试：构造可人工计数样本，脚本 vs 独立手工计数 | `test_style_distill.py::test_acceptance`（C1 段） | 四项参数各自 `\|script - manual\| / manual ≤ 0.15` |
| **C2** | 同一风格卡生成 3 段同场景正文，风格参数偏差 ≤20% | 验收运行：用蒸馏卡（confidence≥51）生成 3 段同场景正文，对每段跑 `distill-style.py check` | Task 18 验收运行（LLM 生成 + check） | 3 段客观维度全部 `\|dev\| ≤ 20%` |
| **C3** | 战斗卡 vs 对话卡生成正文显著差异 | 验收运行：同素材分别按两场景卡生成，compare 维度 | Task 18 验收运行 | 句长/对话占比/动词力度至少 2 项差异 ≥ 容差阈值 |
| **C4** | 连续归档 5 章后置信度 ≥70、参数波动 <10% | 单元测试：模拟 5 章归档跑 `update` | `test_acceptance`（C4 段） | 最终 confidence ≥70 且核心参数相对波动 <10% |
| **C5** | 现有项目升级不报错、旧 writing-style.md 自动迁移 | 单元测试：旧格式卡 → init + sync | `test_acceptance`（C5 段） | 两脚本 exit 0、产出新格式、内容零损失 |
| **C6** | 仙侠/都市/悬疑三套标杆卡，作者盲测正确率 ≥70% | 手动内容验收（作者）：三套基线卡填值后盲测 | 作者（不在代码内） | 正确率 ≥70%（代码不测，收尾前由作者补做） |

> C1/C4/C5 在 Task 18 固化为 `test_acceptance` 并纳入 CI；C2/C3 在 Task 18 给出可重复的验收运行步骤（任一实现变更后需重跑）；C6 是内容任务，作者完成标杆卡后按 spec 盲测。

---

## 文件结构

| 文件 | 责任 | 阶段 |
|------|------|------|
| `tools/test_style_distill.py` | **新建**：本计划的 TDD 载体（单元 + E2E），随阶段增长 | P0 |
| `templates/settings/writing-style.md` | **改**：旧 4 字段纯 Markdown → 新格式（YAML frontmatter 量化层 + 正文定性层） | P0 |
| `templates/settings/style-profiles/{6}.md` | **新建**：6 张场景卡模板（`inherits: "writing-style.md"` + 空 override） | P0 |
| `knowledge/format-specs/distilled-style-spec.md` | **新建**：新风格卡格式规范（frontmatter schema + 9 维度 + 迁移映射 + 验收） | P0 |
| `tools/init.py` | **改**：seed 写新格式；`migrate_writing_style()` 旧 4 字段卡自动迁移；`deploy_tools()` 部署脚本到项目 `tools/` | P0/P1 |
| `tools/distill-style.py` | **新建**：蒸馏引擎（distill 模式 P1；update 模式 P3；check 模式 P4） | P1 |
| `agents/style-distiller.md` | **新建**：第 9 个子 agent | P1 |
| `skills/style-distill.md` | **新建**：风格蒸馏 SOP（脚本统计 → LLM 语义 → 合并写卡 → 增量/场景卡） | P1 |
| `knowledge/style-distill/prompt-templates/distill-prompt.md` | **新建**：LLM 语义标注 prompt | P1 |
| `knowledge/style-distill/prompt-templates/injection-template.md` | **新建**：prompt-crafter 渲染「写作风格约束」块的模板 | P1 |
| `knowledge/style-distill/prompt-templates/gate-g-checklist.md` | **新建**：anti-ai Gate G 检查清单 | P4 |
| `skills/prompt-crafting.md` | **改**：Step 1 读卡 / Step 1.5 裁决表扩展 / Step 2「写作风格约束」块 / Step 4 +2 自检项 | P1 |
| `agents/prompt-crafter.md` | **改**：knowledge 加场景卡 + distilled-style-spec | P1 |
| `tools/requirements.txt` | **改**：+ jieba | P1 |
| `.github/workflows/static.yml` | **改**：CI 装 jieba | P1 |
| `tools/platforms.py` | **改**：reasonix exec_agents 加 style-distiller | P1 |
| `tools/test_platforms.py` | **改**：agent 计数 8→9 / reasonix skill 10→11 | P1 |
| `tools/sync-project.py` | **改**：同步模板/脚本到已有项目 + 迁移钩子 + 指纹含 templates | P1 |
| `agents/novel-agent.md` | **改**：3 个调度点（setup 蒸馏 / archive 增量 / 手动） | P1/P3 |
| `skills/novel-dispatch.md` | **改**：调度表 +3 行 | P1/P3 |
| `templates/settings/style-profiles/genre-baselines/{genre}/` | **新建**：题材基线三层结构（基础卡/delta/标杆卡）占位模板 | P2 |
| `tools/compare-style.py` | **新建**：F7 两卡 YAML diff → 维度变化表 | P5 |
| `tools/mix-style.py` | **新建**：F8 数值加权平均 + 定性节合并 | P5 |
| `skills/anti-ai.md` | **改**：Gate G 扫描 + Phase 2 第 7 指标 + 报告行 | P4 |
| `agents/anti-ai.md` | **改**：knowledge 加风格卡 + tools 加 Bash | P4 |
| `knowledge/anti-ai/boundary-cases.md` | **改**：Gate G 豁免组 | P4 |
| `tools/check-agents.py` | **改**：DEPLOYED_PATTERNS + 卡片 YAML/inherits 校验 | P5 |
| `ARCHITECTURE.md` / `AGENTS.md` / `SKILL.md` / `templates/CLAUDE.md` / `README.md` | **改**：9 agent + 风格写白名单例外 + reasonix 11 skill + 版本 | 收尾 |

---

# Phase 0：卡片格式定稿（F1）

## Task 1: 写验证脚本骨架（先红）

**Files:**
- Create: `tools/test_style_distill.py`

**Interfaces:**
- Consumes: 无（测试载体）
- Produces: `tools/test_style_distill.py` 的 `check(name, cond, detail)` / `run(cmd, cwd)` / `main()` 基础设施，后续 Task 全部往这里追加用例

- [ ] **Step 1: 写验证脚本骨架 + 卡片格式测试（红）**

```python
#!/usr/bin/env python3
"""style-distiller 模块验证脚本。

用法: python tools/test_style_distill.py
返回码 0 = 全部通过，非 0 = 有失败（CI 用）。

覆盖（随阶段增长）：
- P0 单元：卡片 frontmatter schema / 迁移
- P1 单元：distill 统计 / confidence / E2E init 部署
- P3 单元：增量滑动平均 / 备份 / checkpoint
- P4 单元：check 容差
- P5 单元：compare / mix
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


def run(cmd, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def init_project(tmp: Path, genre: str = "1"):
    return run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", genre])


SCENE_TYPES = ["general", "dialogue", "fight", "environment", "inner-mono", "transition", "group-scene"]
REQUIRED_FM_KEYS = ["profile_version", "scene_type", "confidence", "last_updated"]
DIM_KEYS = ["lexicon", "syntax", "rhythm", "rhetoric", "emotion_expression",
            "narrative", "dialogue_style", "cohesion", "verb_style"]
SCENE_CARDS = ["dialogue", "fight", "environment", "inner-mono", "transition", "group-scene"]


def parse_fm(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    import yaml
    parts = text.split("---", 2)
    return yaml.safe_load(parts[1]) if len(parts) == 3 else None


def test_card_schema():
    print("[unit] 卡片 frontmatter schema")
    main = REPO / "templates" / "settings" / "writing-style.md"
    check("主卡模板存在", main.exists())
    if not main.exists():
        return
    fm = parse_fm(main)
    check("主卡 frontmatter 可解析", fm is not None)
    for k in REQUIRED_FM_KEYS + DIM_KEYS:
        check(f"主卡含 {k}", bool(fm) and k in fm)
    check("主卡 scene_type=general", fm and fm.get("scene_type") == "general")
    check("主卡 confidence=0", fm and fm.get("confidence") == 0)
    for name in SCENE_CARDS:
        card = REPO / "templates" / "settings" / "style-profiles" / f"{name}.md"
        check(f"场景卡 {name} 存在", card.exists())
        cfm = parse_fm(card)
        check(f"{name} 可解析", cfm is not None)
        check(f"{name} scene_type={name}", cfm and cfm.get("scene_type") == name)
        check(f"{name} inherits 主卡", cfm and cfm.get("inherits") == "writing-style.md")
        check(f"{name} confidence=0", cfm and cfm.get("confidence") == 0)


def test_migration():
    print("[unit] 旧 4 字段卡迁移")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        wsf = tmp / "settings" / "writing-style.md"
        # init 后应为新格式（含 frontmatter）
        check("init 产新格式主卡", wsf.exists() and wsf.read_text(encoding="utf-8").startswith("---"))
        check("init 部署 style-profiles", (tmp / "settings" / "style-profiles").is_dir())
        n = len(list((tmp / "settings" / "style-profiles").glob("*.md")))
        check("6 张场景卡已部署", n == 6, f"实际 {n}")
        # 旧格式 → 迁移 → 新格式
        old = tmp / "settings" / "writing-style.md"
        old.write_text("# 写作风格\n\n## role（叙事身份）\n\n第一人称\n\n"
                       "## core_principles（不可违背的写作信条）\n\n- 不写废话\n\n"
                       "## possible_mistakes（AI 易犯错误）\n\n- 套路化\n\n"
                       "## depiction_techniques（描写层次和手法）\n\n感官描写\n",
                       encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        check("迁移后 init exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        fm = parse_fm(wsf)
        check("迁移后含 frontmatter", fm is not None)
        body = wsf.read_text(encoding="utf-8")
        check("迁移保留叙事身份内容", "第一人称" in body)
        check("迁移保留硬约束内容", "不写废话" in body)
        check("迁移保留易错内容", "套路化" in body)
        check("迁移保留描写手法内容", "感官描写" in body)
        check("迁移备份旧版", (tmp / "settings" / ".style-versions" / "v0_migrated.md").exists())


def main():
    test_card_schema()
    test_migration()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行，确认失败（红）**

Run: `python tools/test_style_distill.py`
Expected: 全红。`主卡模板存在`、`6 张场景卡`、`init 产新格式主卡` 等全部 FAIL（模板与迁移还没做）。

- [ ] **Step 3: Commit**

```bash
git add tools/test_style_distill.py
git commit -m "test: style-distiller 验证脚本骨架（先红）"
```

---

## Task 2: 新格式主卡 + 6 张场景卡模板

**Files:**
- Modify: `templates/settings/writing-style.md`
- Create: `templates/settings/style-profiles/{dialogue,fight,environment,inner-mono,transition,group-scene}.md`
- Test: `tools/test_style_distill.py`（`test_card_schema`）

**Interfaces:**
- Consumes: 9 大维度 schema（Global Constraints）
- Produces: 主卡 frontmatter 结构（`profile_version/scene_type/source_sample_length/confidence/last_updated/locked` + 9 维度键）与场景卡结构（+`inherits`/`override`），后续蒸馏/注入/校验全部依赖此 schema

- [ ] **Step 1: 重写主卡模板**

`templates/settings/writing-style.md` 整文件替换为：

```markdown
---
profile_version: "1.0"
scene_type: general
source_sample_length: 0
confidence: 0
last_updated: ""
locked: []

# 9 大维度（PRD 定义；0/空 = 未蒸馏，首次蒸馏后由 style-distiller 填充）
lexicon: { adj_density_per_100: 0, adv_density_per_100: 0, four_phrase_freq_per_100: 0, preferred_words: [], banned_words: [], name_pronoun_ratio: 0 }
syntax: { avg_sentence_length: 0, sentence_length_dist: {}, single_sentence_paragraph_pct: 0, avg_sentences_per_paragraph: 0, question_ratio: 0, exclamation_ratio: 0 }
rhythm: { dialogue_pct: 0, action_pct: 0, environment_pct: 0, inner_thought_pct: 0, narration_pct: 0 }
rhetoric: { metaphor_density_per_100: 0, metaphor_preference: "", sensory_dist: "" }
emotion_expression: { direct_pct: 0, action_physiology_pct: 0, environment_projection_pct: 0 }
narrative: { perspective: "", focal_character: "", inner_monologue_style: "" }
dialogue_style: { tag_style: "", avg_dialogue_length: 0, interrupt_freq_per_100: 0, subtext_ratio: 0, direct_address_freq_per_100: 0 }
cohesion: { conjunction_freq_per_100: 0, transition_sentence_ratio: 0, paragraph_bridge_style: "" }
verb_style: { action_verb_ratio: 0, mental_verb_ratio: 0, state_verb_ratio: 0, strength: "" }
---

# 写作风格

## 叙事身份（原 role）

{role}

## 硬约束（原 core_principles）

- {principle_1}

## AI 易犯错误（原 possible_mistakes）

- {mistake_1}

## 描写层次和手法（原 depiction_techniques）

{depiction_techniques}

## few-shot 例句

- （蒸馏后由 style-distiller 填入标志性例句）
```

> 正文定性层节名与旧 4 字段一一对应（注释保留原名），保证 prompt-crafter 既有定性注入与旧卡迁移都零改动成本。占位符守卫逻辑（prompt-crafting.md 已用 `{...}` 检测）天然兼容。

- [ ] **Step 2: 写 6 张场景卡模板**

以 `dialogue` 为例，其余 5 张同构（只改 `scene_type` 与标题/正文说明）：

`templates/settings/style-profiles/dialogue.md`：

```markdown
---
profile_version: "1.0"
scene_type: dialogue
source_sample_length: 0
confidence: 0
last_updated: ""
inherits: "writing-style.md"
override: {}
locked: []
---

# 对话场景风格卡

继承主卡 `writing-style.md`，本卡只覆盖对话场景差异维度（dialogue_style / lexicon / syntax）。
量化 override 由 style-distiller 按对话样本蒸馏后填充。

## 描写层次和手法（对话场景）

- （蒸馏后由 style-distiller 填充对话场景专属技法）

## few-shot 例句

- （对话场景标志性例句）
```

其余 5 张：`fight.md`（覆盖 verb_style / syntax / rhythm.action_pct）、`environment.md`（rhetoric.sensory_dist / rhythm.environment_pct）、`inner-mono.md`（emotion_expression / narrative.inner_monologue_style）、`transition.md`（cohesion / rhythm）、`group-scene.md`（rhythm / dialogue_style）。正文只改场景名与「覆盖维度」注释。

- [ ] **Step 3: 运行测试，确认卡 schema 绿**

Run: `python tools/test_style_distill.py`
Expected: `[unit] 卡片 frontmatter schema` 段全 ok；`[unit] 旧 4 字段卡迁移` 段仍 FAIL（init.py 还没改）。

- [ ] **Step 4: Commit**

```bash
git add templates/settings/writing-style.md templates/settings/style-profiles/
git commit -m "feat: 新格式风格卡模板（主卡 + 6 场景卡，F1 数据结构）"
```

---

## Task 3: 蒸馏风格卡格式规范

**Files:**
- Create: `knowledge/format-specs/distilled-style-spec.md`

**Interfaces:**
- Consumes: 9 大维度 schema、迁移映射
- Produces: 仓库内权威格式规范（部署后平铺到 `.claude/knowledge/distilled-style-spec.md`），prompt-crafter / style-distiller 的 knowledge 引用它

- [ ] **Step 1: 写格式规范**

```markdown
# 蒸馏风格卡格式规范（distilled-style-spec）

风格卡分两种：主卡 `settings/writing-style.md`（scene_type: general，全局默认）与
场景卡 `settings/style-profiles/{scene_type}.md`（分场景差异）。两者共用同一 frontmatter schema。

## 一、frontmatter 量化层

必需字段：`profile_version`（"1.0"）、`scene_type`、`source_sample_length`（蒸馏样本总字数）、
`confidence`（0-100，0=手动设定/未蒸馏）、`last_updated`（YYYY-MM-DD）。
场景卡另有：`inherits`（继承主卡路径）、`override`（只写差异维度）、`locked`（手动锁定维度，F5 增量跳过）。

9 大维度（PRD 定义，键名唯一，不可改名）：

| 维度 | 字段 | 说明 |
|------|------|------|
| lexicon | adj_density_per_100 / adv_density_per_100 / four_phrase_freq_per_100 / preferred_words[] / banned_words[] / name_pronoun_ratio | 词法：脚本统计 |
| syntax | avg_sentence_length / sentence_length_dist{} / single_sentence_paragraph_pct / avg_sentences_per_paragraph / question_ratio / exclamation_ratio | 句法：脚本统计 |
| rhythm | dialogue_pct / action_pct / environment_pct / inner_thought_pct / narration_pct | 节奏占比：dialogue_pct 脚本统计，其余 LLM 估算 |
| rhetoric | metaphor_density_per_100 / metaphor_preference / sensory_dist | 修辞：LLM |
| emotion_expression | direct_pct / action_physiology_pct / environment_projection_pct | 情绪表达：LLM |
| narrative | perspective / focal_character / inner_monologue_style | 叙事：LLM |
| dialogue_style | tag_style / avg_dialogue_length / interrupt_freq_per_100 / subtext_ratio / direct_address_freq_per_100 | 对话：LLM |
| cohesion | conjunction_freq_per_100 / transition_sentence_ratio / paragraph_bridge_style | 衔接：前两项脚本，bridge LLM |
| verb_style | action_verb_ratio / mental_verb_ratio / state_verb_ratio / strength | 动词：前三项脚本，strength LLM |

## 二、正文定性层

主卡正文保留旧 4 字段映射（迁移零损失）：

| 旧字段 | 新位置 |
|--------|--------|
| role | 正文「叙事身份」节 |
| core_principles | 正文「硬约束」节（注入时视为红线级） |
| possible_mistakes | 正文「AI 易犯错误」节（与 banned_words 互补） |
| depiction_techniques | 正文「描写层次和手法」节（原样保留） |

正文另含 `few-shot 例句`：蒸馏选出的标志性例句（按场景类型分组）。

## 三、继承与合成

- 场景卡 `inherits` 指向主卡，`override` 只覆盖差异维度；prompt-crafter 读卡时合并 override（继承链解析放 Step 1 内，不引入新解析器）。
- 主卡兜底：某场景无场景卡时只用主卡。

## 四、置信度与容差

`confidence = min(100, 20 + min(40, sample_length/50) + min(40, chapter_count*5))`
容差档：0-20 手动 / 21-50 ±30% / 51-70 ±20% / 71-90 ±15% / 91-100 ±10%。
confidence=0 时量化层不注入，提示词只走定性层，直到首次蒸馏。

## 五、验收自检

1. frontmatter 含全部 9 大维度键，字段类型与 schema 一致
2. scene_type 在 6 类枚举内（主卡 general）
3. confidence 0-100 整数；locked 只含已定义维度键
4. 场景卡 inherits 指向存在的卡（主卡或其他场景卡）
5. 量化值以「约 X（±Y%）」表述注入，不写死
```

- [ ] **Step 2: 静态检查（spec 文档不进 check-agents，人工 review 即可）**

Run: `python tools/check-agents.py`
Expected: 不变仍通过（本 Task 未改任何 agent）。

- [ ] **Step 3: Commit**

```bash
git add -f knowledge/format-specs/distilled-style-spec.md
git commit -m "docs: 蒸馏风格卡格式规范 distilled-style-spec.md"
```

---

## Task 4: init.py 迁移旧卡 + seed 新格式 + 部署脚本

**Files:**
- Modify: `tools/init.py`
- Test: `tools/test_style_distill.py`（`test_migration`）

**Interfaces:**
- Consumes: 新格式主卡结构（Task 2）
- Produces:
  - `init.migrate_writing_style(project_path)` — 旧 4 字段卡 → 新格式（confidence=0，备份旧版到 `settings/.style-versions/v0_migrated.md`）；**在 main() 最前（create_skeleton 之前）调用**
  - `init.deploy_tools(project_path)` — 拷贝仓库 `tools/distill-style.py`（及后续 compare/mix）到项目 `tools/`
  - `create_skeleton` 改为**跳过已存在文件**（只补缺失）；`seed_settings_from_genre` 对已填卡（无 `{...}` 占位符）**跳过覆盖** —— 保证 re-init/升级不破坏用户与迁移产物

- [ ] **Step 1: 加新格式主卡写入辅助函数**

在 `seed_settings_from_genre` 之前新增（复用已有 `_md_section` / `_md_bullets`）：

```python
def _write_new_style_card(path: Path, role: str, principles: list, mistakes: list,
                          depiction: str, seeded: bool = True) -> None:
    """写新格式写作风格卡（frontmatter 量化层 + 正文定性层）。
    confidence=0 → 提示词只走定性层，直到首次蒸馏。"""
    prefix = "> [auto-seeded] 由 init.py 按题材预填，量化层留空，首次蒸馏后由 style-distiller 填充。\n\n" if seeded else ""
    principles_txt = "\n".join(f"- {p}" for p in principles) if principles else "- {principle_1}"
    mistakes_txt = "\n".join(f"- {m}" for m in mistakes) if mistakes else "- {mistake_1}"
    content = f"""---
profile_version: "1.0"
scene_type: general
source_sample_length: 0
confidence: 0
last_updated: ""
locked: []

lexicon: {{ adj_density_per_100: 0, adv_density_per_100: 0, four_phrase_freq_per_100: 0, preferred_words: [], banned_words: [], name_pronoun_ratio: 0 }}
syntax: {{ avg_sentence_length: 0, sentence_length_dist: {{}}, single_sentence_paragraph_pct: 0, avg_sentences_per_paragraph: 0, question_ratio: 0, exclamation_ratio: 0 }}
rhythm: {{ dialogue_pct: 0, action_pct: 0, environment_pct: 0, inner_thought_pct: 0, narration_pct: 0 }}
rhetoric: {{ metaphor_density_per_100: 0, metaphor_preference: "", sensory_dist: "" }}
emotion_expression: {{ direct_pct: 0, action_physiology_pct: 0, environment_projection_pct: 0 }}
narrative: {{ perspective: "", focal_character: "", inner_monologue_style: "" }}
dialogue_style: {{ tag_style: "", avg_dialogue_length: 0, interrupt_freq_per_100: 0, subtext_ratio: 0, direct_address_freq_per_100: 0 }}
cohesion: {{ conjunction_freq_per_100: 0, transition_sentence_ratio: 0, paragraph_bridge_style: "" }}
verb_style: {{ action_verb_ratio: 0, mental_verb_ratio: 0, state_verb_ratio: 0, strength: "" }}
---

# 写作风格

{prefix}## 叙事身份（原 role）

{role}

## 硬约束（原 core_principles）

{principles_txt}

## AI 易犯错误（原 possible_mistakes）

{mistakes_txt}

## 描写层次和手法（原 depiction_techniques）

{depiction}

## few-shot 例句

- （蒸馏后由 style-distiller 填入标志性例句）
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
```

- [ ] **Step 2: 重写 seed_settings_from_genre 的 writing-style 部分（含「已填卡跳过」守卫）**

把该函数里写 `settings/writing-style.md` 的整段（现为 style_out 列表构造 + write_text，旧 4 字段 Markdown）替换为：先判「已填卡跳过」，再调用 `_write_new_style_card`。复用该函数内已算好的 `role` / `blueprint` / `taboo` 变量（`role = _md_section(text, "叙事者角色") or "（待设定）"`、`blueprint = _md_section(text, "文风蓝图") or "（待设定）"`、`taboo = _md_bullets(_md_section(text, "类型禁忌"))`，约 line 471-472 / 446）：

```python
    # writing-style.md → 新格式（frontmatter 量化层 + 正文定性层）
    # 守卫：卡已存在且无未填充 {...} 占位符 → 已有实质内容（迁移产物/作者编辑），不覆盖
    style_card = project_path / "settings" / "writing-style.md"
    if style_card.exists() and "{" not in style_card.read_text(encoding="utf-8"):
        print("  ✅ writing-style.md 已有实质内容，跳过题材预填（保留迁移/编辑结果）")
    else:
        _write_new_style_card(
            style_card,
            role=role or "{role}",
            principles=[blueprint] if blueprint else [],
            mistakes=taboo,
            depiction=blueprint or "{depiction_techniques}",
        )
```

> 注意：`_md_section` 对「文风蓝图」返回整段文本（既当 core_principles 又当 depiction_techniques，与现状一致）；`taboo` 已是 list。若现有变量名/签名不同，按 init.py 现状适配。

- [ ] **Step 3: create_skeleton 跳过已存在文件**

`create_skeleton` 现用 `shutil.copy2` 无条件把 `templates/` 拷到项目，re-init 会把用户/迁移后的 `writing-style.md` 覆盖掉（测试 `test_migration` 第二段必失败）。改为目标已存在时跳过——只补缺失文件，与函数注释「创建缺失的文件和目录」一致：

```python
    if SOURCE_TEMPLATES.exists():
        for item in SOURCE_TEMPLATES.rglob("*"):
            if item.is_file() and item.name != ".gitkeep":
                rel_path = item.relative_to(SOURCE_TEMPLATES)
                if rel_path.parts[0] == "migration":
                    continue
                target = project_path / rel_path
                if target.exists():
                    continue          # 已存在不覆盖（升级/迁移不破坏用户工作）
                target.parent.mkdir(parents=True, exist_ok=True)
                # …原有 codex/CLAUDE.md 特判分支保持不变…
```

> 影响面：新建项目（target 全不存在）行为不变；已有项目 re-init 改为只补缺失文件。`test_platforms` 用全新临时目录，不受影响。

- [ ] **Step 4: 新增 migrate_writing_style()（main() 最前、create_skeleton 之前调用）**

在 main() 调用区附近新增；调用点放在 main() **最前**（`create_skeleton` 之前）——必须赶在模板拷贝与题材预填之前迁移旧卡，否则旧卡内容先被覆盖、迁移无从谈起。提取旧卡用**带后缀的完整标题**（旧卡是 `## role（叙事身份）` 等，`_md_section`/`_md_bullets` 的标题正则需精确匹配）：

```python
def migrate_writing_style(project_path: Path) -> None:
    """旧 4 字段 writing-style.md → 新格式（仅当旧格式：无 frontmatter）。
    旧版备份到 settings/.style-versions/v0_migrated.md。"""
    card = project_path / "settings" / "writing-style.md"
    if not card.exists():
        return
    text = card.read_text(encoding="utf-8")
    if text.lstrip().startswith("---"):          # 已是新格式
        return
    # 旧标题带中文后缀（如 "## role（叙事身份）"），按完整标题提取
    role = _md_section(text, "role（叙事身份）") or "{role}"
    principles = _md_bullets(_md_section(text, "core_principles（不可违背的写作信条）"))
    mistakes = _md_bullets(_md_section(text, "possible_mistakes（AI 易犯错误）"))
    depiction = _md_section(text, "depiction_techniques（描写层次和手法）") or "{depiction_techniques}"
    vers = project_path / "settings" / ".style-versions"
    vers.mkdir(parents=True, exist_ok=True)
    (vers / "v0_migrated.md").write_text(text, encoding="utf-8")
    _write_new_style_card(card, role, principles, mistakes, depiction, seeded=False)
    print("  ✅ 旧 4 字段 writing-style.md 已迁移到新格式（confidence=0，旧版已备份）")
```

- [ ] **Step 5: 新增 deploy_tools() + 骨架目录加 tools**

在 `create_skeleton` 的 dirs 列表加 `"tools"`，并新增函数（main() 在 deploy_agents 之后调用）：

```python
_DEPLOY_TOOLS = ["distill-style.py", "compare-style.py", "mix-style.py"]  # 现有文件才拷，缺省跳过

def deploy_tools(project_path: Path) -> None:
    """拷贝风格工具脚本到项目 tools/（style-distiller / anti-ai 用 Bash 调）。"""
    src = SKILL_HOME / "tools"
    dst = project_path / "tools"
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for name in _DEPLOY_TOOLS:
        f = src / name
        if f.exists():
            (dst / name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
            n += 1
    if n:
        print(f"  ✅ 已部署风格工具脚本到 tools/（{n} 个）")
```

- [ ] **Step 6: 运行测试，确认迁移绿**

Run: `python tools/test_style_distill.py`
Expected: `[unit] 卡片 frontmatter schema` 与 `[unit] 旧 4 字段卡迁移` 两段全 ok（init 产新格式、6 卡部署、迁移保内容、备份 v0_migrated）。

- [ ] **Step 7: Commit**

```bash
git add tools/init.py
git commit -m "feat: init.py 新格式风格卡 seed + 旧 4 字段自动迁移 + tools 脚本部署"
```

---

# Phase 1：核心闭环（F2 + F3）

## Task 5: distill-style.py — distill 模式（统计引擎）

**Files:**
- Create: `tools/distill-style.py`
- Test: `tools/test_style_distill.py`（追加 `test_distill` 段）

**Interfaces:**
- Consumes: 9 大维度 schema、置信度/容差公式
- Produces:
  - CLI `distill-style.py distill -o <partial.yml> -e <evidence.md> <样本...>` → 退出 0
  - `build_partial(texts) -> dict`（含 `source_sample_length` / `confidence` / 客观维度子 dict）
  - `compute_confidence(sample_length, chapter_count) -> int`
  - `tolerance_for(confidence) -> float`
  - `load_card(path) -> dict` / `dump_card(dims, body) -> str`（供 update/check/compare/mix 复用）

- [ ] **Step 1: 写 distill 模式全量实现**

```python
#!/usr/bin/env python3
"""style-distiller 蒸馏引擎：jieba POS 统计 + 正则兜底（确定性，无网络无 LLM）。

style-distiller / anti-ai agent 用 Bash 调用。三种模式：
  distill  从样本统计客观维度 → 输出 partial YAML + 每维度证据（本 Task）
  update   增量：旧卡客观维度滑动平均 + 备份 + 置信度重算（Phase 3 补）
  check    Gate G：正文客观维度 vs 卡片容差 → 偏差表（Phase 4 补）

用法:
  python distill-style.py distill -o <partial.yml> -e <evidence.md> <样本文件...>

无 jieba 时降级纯正则统计（需 POS 的项记 None）。退出码 0 = 成功。
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import jieba.posseg as pseg          # type: ignore
    HAS_JIEBA = True
except Exception:
    HAS_JIEBA = False

try:
    import yaml
except Exception:
    yaml = None

RE_STOP = set("的了一是在不和有这我他她它们就都也不为之与把被让要向从到说走看想给去又再很那这本个子等面着头口手眼心里出来过去上下前后中还是而但所以然后因为因此如果同时另外例如比如通过作为关于对于根据依照随着由")

ADJ_TAGS = {"a", "ad", "an"}
ADV_TAGS = {"d"}
VERB_TAGS = {"v", "vd", "vn", "vi", "vl", "vg", "vq"}
MENTAL_VERBS = {"想", "觉得", "认为", "意识到", "明白", "感到", "发现", "知道", "怀疑", "相信", "记得", "决定", "以为"}
STATE_VERBS = {"是", "有", "像", "如", "仿佛", "似", "在", "属于", "成为", "变成", "保持"}
TRANSITION_WORDS = ("然而", "但是", "不过", "可是", "于是", "因此", "所以", "随后", "接着", "这时", "此刻", "另一边", "与此同时", "忽然", "突然", "但")
CONJUNCTIONS = {"而且", "并且", "但是", "不过", "可是", "然而", "所以", "因此", "因为", "由于", "于是",
                "虽然", "但", "却", "还", "又", "也", "就", "才", "或", "和", "跟", "与", "以及",
                "不只", "不仅", "不但", "何况", "况且", "此外", "另外"}

SENT_END = re.compile(r"[。！？…；!?;]")
WORD4 = re.compile(r"[一-鿿]{4}")
QUOTE_OPEN = set('“"「『')
QUOTE_CLOSE = set('”"」』')
PARA_SPLIT = re.compile(r"\n\s*\n")
WS = re.compile(r"\s")


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def char_len(text: str) -> int:
    return len(WS.sub("", text))


def split_sentences(text: str) -> list:
    return [p.strip() for p in SENT_END.split(text) if p.strip()]


def paragraphs(text: str) -> list:
    return [p.strip() for p in PARA_SPLIT.split(text) if p.strip()]


def pos_tokens(text: str):
    if HAS_JIEBA:
        return [(w, str(p)) for w, p in pseg.cut(text)]
    return [(w, None) for w in re.findall(r"[一-鿿]{2,}", text)]


# ------------------------------------------------------------ 各维度统计

def _name_pronoun_ratio(words):
    names = sum(1 for w in words if len(w) >= 2 and w not in RE_STOP)
    pro = sum(1 for w in words if w in "他她它你们我们它们")
    return names / max(pro, 1)


def lexicon_stats(text, tokens):
    n = max(char_len(text), 1)
    words = [w for w, _ in tokens]
    adj = [w for w, p in tokens if p in ADJ_TAGS]
    adv = [w for w, p in tokens if p in ADV_TAGS]
    four = list(WORD4.findall(text))
    freq = {}
    for w in words:
        if len(w) >= 2 and w not in RE_STOP:
            freq[w] = freq.get(w, 0) + 1
    preferred = [w for w, c in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:20] if c >= 2][:10]
    return {
        "adj_density_per_100": round(100 * len(adj) / n, 2) if HAS_JIEBA else None,
        "adv_density_per_100": round(100 * len(adv) / n, 2) if HAS_JIEBA else None,
        "four_phrase_freq_per_100": round(100 * len(four) / n, 2),
        "preferred_words": preferred,
        "banned_words": [],
        "name_pronoun_ratio": round(_name_pronoun_ratio(words), 2) if HAS_JIEBA else None,
    }


def syntax_stats(text):
    sents = split_sentences(text)
    paras = paragraphs(text)
    n = max(len(sents), 1)
    lengths = [char_len(s) for s in sents]
    buckets = {}
    for L in lengths:
        b = "<10" if L < 10 else "10-20" if L < 20 else "20-30" if L < 30 else "30-40" if L < 40 else ">40"
        buckets[b] = buckets.get(b, 0) + 1
    single = sum(1 for p in paras if len(split_sentences(p)) == 1)
    q = text.count("？") + text.count("?")
    ex = text.count("！") + text.count("!")
    spc = sum(len(split_sentences(p)) for p in paras) / max(len(paras), 1)
    return {
        "avg_sentence_length": round(sum(lengths) / n, 1),
        "sentence_length_dist": {k: round(100 * v / n, 1) for k, v in buckets.items()},
        "single_sentence_paragraph_pct": round(100 * single / max(len(paras), 1), 1),
        "avg_sentences_per_paragraph": round(spc, 1),
        "question_ratio": round(100 * q / n, 1),
        "exclamation_ratio": round(100 * ex / n, 1),
    }


def rhythm_stats(text):
    total = char_len(text)
    inside, in_quote = False, 0
    for ch in text:
        if ch in QUOTE_OPEN:
            inside = True
        elif ch in QUOTE_CLOSE:
            inside = False
        elif inside and ch.strip():
            in_quote += 1
    return {"dialogue_pct": round(100 * in_quote / max(total, 1), 1)}


def cohesion_stats(text, tokens):
    n = max(char_len(text), 1)
    words = [w for w, _ in tokens]
    con = sum(1 for w in words if w in CONJUNCTIONS)
    sents = split_sentences(text)
    trans = sum(1 for s in sents if s[:2] in TRANSITION_WORDS)
    return {
        "conjunction_freq_per_100": round(100 * con / n, 2),
        "transition_sentence_ratio": round(100 * trans / max(len(sents), 1), 1),
    }


def verb_style_stats(tokens):
    verbs = [w for w, p in tokens if p in VERB_TAGS]
    n = max(len(verbs), 1)
    action = [w for w in verbs if w not in MENTAL_VERBS and w not in STATE_VERBS]
    mental = [w for w in verbs if w in MENTAL_VERBS]
    state = [w for w in verbs if w in STATE_VERBS]
    return {
        "action_verb_ratio": round(100 * len(action) / n, 1),
        "mental_verb_ratio": round(100 * len(mental) / n, 1),
        "state_verb_ratio": round(100 * len(state) / n, 1),
    }


def select_few_shot(text, k=5):
    sents = [s for s in split_sentences(text) if 15 <= char_len(s) <= 80]
    sents.sort(key=lambda s: (-len(list(WORD4.finditer(s))), char_len(s)))
    return sents[:k]


# ------------------------------------------------------------ 置信度 / 输出

def compute_confidence(sample_length: int, chapter_count: int = 0) -> int:
    return min(100, 20 + min(40, int(sample_length / 50)) + min(40, chapter_count * 5))


def tolerance_for(confidence: int) -> float:
    if confidence <= 20:
        return 0.0
    if confidence <= 50:
        return 0.30
    if confidence <= 70:
        return 0.20
    if confidence <= 90:
        return 0.15
    return 0.10


def build_partial(texts) -> dict:
    full = "\n".join(read_text(t) for t in texts)
    tokens = pos_tokens(full)
    return {
        "source_sample_length": char_len(full),
        "confidence": compute_confidence(char_len(full)),
        "lexicon": lexicon_stats(full, tokens),
        "syntax": syntax_stats(full),
        "rhythm": rhythm_stats(full),
        "cohesion": cohesion_stats(full, tokens),
        "verb_style": verb_style_stats(tokens),
        "few_shot_candidates": select_few_shot(full),
    }


def dump_yaml(data) -> str:
    if yaml:
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    return str(data)  # 兜底：无 pyyaml 时降级为 repr（仅调试用）


def render_evidence(partial: dict, samples) -> str:
    lines = ["# 蒸馏证据", "", "样本文件："]
    lines += [f"- {s}" for s in samples]
    lines.append(f"\n样本总字数：{partial['source_sample_length']}")
    lines.append(f"置信度：{partial['confidence']}")
    lines.append("\n## 客观维度")
    for k in ("lexicon", "syntax", "rhythm", "cohesion", "verb_style"):
        lines.append(f"\n### {k}")
        for kk, vv in partial.get(k, {}).items():
            lines.append(f"- {kk}: {vv}")
    lines.append("\n## few-shot 候选句")
    for s in partial.get("few_shot_candidates", []):
        lines.append(f"- {s}")
    return "\n".join(lines)


def cmd_distill(args) -> int:
    partial = build_partial(args.samples)
    Path(args.out).write_text(dump_yaml({"distill": partial}), encoding="utf-8")
    if args.evidence:
        Path(args.evidence).write_text(render_evidence(partial, args.samples), encoding="utf-8")
    print(f"distill: {len(args.samples)} 个样本，总字数 {partial['source_sample_length']}，"
          f"confidence={partial['confidence']}，partial 写 {args.out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="distill-style.py", description="文风蒸馏统计引擎")
    sub = ap.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("distill", help="从样本统计客观维度")
    d.add_argument("-o", "--out", required=True, help="partial YAML 输出路径")
    d.add_argument("-e", "--evidence", help="证据 markdown 输出路径（可选）")
    d.add_argument("samples", nargs="+", help="样本文件（.md/.txt）")
    # update / check 子命令在 Phase 3 / Phase 4 追加
    args = ap.parse_args(argv)
    if args.mode == "distill":
        return cmd_distill(args)
    ap.error(f"未知模式: {args.mode}")


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 追加单元测试（test_style_distill.py 的 main() 里调 test_distill）**

```python
def test_distill():
    print("[unit] distill 统计引擎")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        sample = tmp / "sample.md"
        sample.write_text(
            "他缓缓推开门，寒风扑面而来，院子里一片死寂。"
            "他握紧拳头，指节发白，心里默默算着时间。"
            "“你终于来了。”她说，声音很轻。"
            "他点点头，没有回答，只是又看了一眼那条通往山下的路。",
            encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "distill-style.py"), "distill",
                 "-o", str(tmp / "p.yml"), "-e", str(tmp / "e.md"), str(sample)], cwd=str(TOOLS))
        check("distill exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        p = tmp / "p.yml"
        check("partial 已写", p.exists())
        import yaml as _y
        data = _y.safe_load(p.read_text(encoding="utf-8"))["distill"]
        check("含 sample_length", data["source_sample_length"] > 0)
        check("含 confidence", 0 < data["confidence"] <= 100)
        check("lexicon 含四个字段",
              all(k in data["lexicon"] for k in ("adj_density_per_100", "adv_density_per_100",
                                                 "four_phrase_freq_per_100", "preferred_words")))
        check("syntax 含 avg_sentence_length", data["syntax"]["avg_sentence_length"] > 0)
        check("rhythm 含 dialogue_pct", "dialogue_pct" in data["rhythm"])
        check("对话占比>0", data["rhythm"]["dialogue_pct"] > 0)
        # 确定性：跑两次结果一致
        r2 = run([sys.executable, str(TOOLS / "distill-style.py"), "distill",
                  "-o", str(tmp / "p2.yml"), str(sample)], cwd=str(TOOLS))
        d2 = _y.safe_load((tmp / "p2.yml").read_text(encoding="utf-8"))["distill"]
        check("确定性（两次一致）", data["syntax"] == d2["syntax"], f"{data['syntax']} vs {d2['syntax']}")
        # 置信度公式
        check("confidence 1500字≈20+30=50", compute_conf(1500) == 50)
        check("confidence 封顶 100", compute_conf(10 ** 6) == 100)


def compute_conf(length, chapters=0):
    return min(100, 20 + min(40, int(length / 50)) + min(40, chapters * 5))
```

（`test_distill` 加入 main() 调用序列。）

- [ ] **Step 3: 运行测试，确认绿**

Run: `python tools/test_style_distill.py`
Expected: schema / migration / distill 三段全 ok。无 jieba 环境同样通过（adj/adv 记 None，断言不要求其非 None）。

- [ ] **Step 4: Commit**

```bash
git add tools/distill-style.py tools/test_style_distill.py
git commit -m "feat: distill-style.py 统计引擎（distill 模式，jieba + 纯正则降级）"
```

---

## Task 6: style-distiller agent + style-distill.md SOP + 蒸馏 prompt

**Files:**
- Create: `agents/style-distiller.md`
- Create: `skills/style-distill.md`
- Create: `knowledge/style-distill/prompt-templates/distill-prompt.md`
- Test: `python tools/check-agents.py`

**Interfaces:**
- Consumes: distill-style.py CLI（Task 5）、卡片 schema（Task 2）、格式规范（Task 3）
- Produces: agent `style-distiller` 定义（写白名单：writing-style.md / style-profiles / .style-versions）；skill `style-distill.md` 三段式 SOP

- [ ] **Step 1: 写 agent 定义**

`agents/style-distiller.md`：

```markdown
---
name: style-distiller
description: 风格蒸馏——对样本文本/归档章节跑蒸馏脚本提取可量化风格数据，写风格主卡、场景卡与版本快照
role: 风格蒸馏师
react: true
tools: Read, Write, Edit, Glob, Grep, Bash
memory: []
skills:
  - path: skills/style-distill.md
    description: 风格蒸馏 SOP（脚本统计 → LLM 语义 → 合并写卡 → 增量/场景卡）
knowledge:
  - path: settings/writing-style.md
    description: 写作风格主卡（读旧写新，定性层 + 量化层）
  - path: settings/style-profiles/
    description: 分场景风格卡目录
  - path: settings/.style-versions/
    description: 蒸馏版本快照目录（备份与 locked 前置版本）
  - path: .claude/knowledge/writer-style.md
    description: 作家文风偏好（只读基线，不写入）
  - path: .claude/knowledge/distilled-style-spec.md
    description: 蒸馏风格卡格式规范（frontmatter schema + 9 维度）
  - path: knowledge/style-distill/prompt-templates/
    description: 蒸馏 prompt 模板目录
---

# style-distiller

你是风格蒸馏师。把作者认可的样本（或已归档定稿）转化为可量化的风格卡：脚本统计客观维度，LLM 补语义维度，合并写卡。

## 一、职责

- 主卡蒸馏：`settings/writing-style.md`（confidence 重算）
- 场景卡蒸馏：`settings/style-profiles/{scene_type}.md`（override 只写差异）
- 增量更新：对归档章节跑脚本档，语义档低频重估，备份 + locked 跳过
- 只读 `archives/`、`chapters/`、作者提供的样本；只写风格三件套，**不碰**其他 settings（归 updater）

## 二、写白名单（唯一例外）

| 工具 | 允许写 | 禁止 |
|------|--------|------|
| Write/Edit | `settings/writing-style.md`、`settings/style-profiles/*`、`settings/.style-versions/*`、`.agent/task/*-order.md`（仅改 status） | 不写其他 settings、chapters、archives |
| Read | `archives/`、`chapters/`、`settings/`、样本文件 | 绝不读项目之外 |
| Bash | `python tools/distill-style.py ...`（项目内 tools/） | 其他命令需向 novel-agent 说明 |

## 三、交接

完成 order 后：把 order 覆盖为 `status: DONE`；报告里给「更新了哪些维度 + confidence 变化 + 是否触发语义重估」摘要。发现样本质量不足（<1500 字、多题材混杂）时向作者/novel-agent 说明并挂起。
```

> 注意：agent 的 skills/knowledge 引用会进 check-agents 校验——`knowledge/style-distill/prompt-templates/` 是仓库真实路径（Task 本步创建），`.claude/knowledge/*` 命中现有 DEPLOYED_PATTERNS。`settings/style-profiles/` 与 `settings/.style-versions/` 需在 Task 15 给 check-agents 补白名单，否则此刻运行会报错——先运行确认，把报错留给 Task 15 处理。

- [ ] **Step 2: 写 style-distill.md SOP**

`skills/style-distill.md`：

```markdown
# style-distill skill

## 一、三段式蒸馏（主卡，style-distill-order）

### 段 1：脚本统计（确定性）
- 收集样本：作者提供的参考文本（.md/.txt）或已归档章节。少于 1500 字时向 novel-agent 说明质量不足，可挂起。
- Bash 调：`python tools/distill-style.py distill -o .agent/task/partial.yml -e .agent/task/evidence.md <样本...>`
- 读 partial.yml + evidence.md：拿到客观维度（lexicon/syntax/rhythm.dialogue_pct/cohesion/verb_style）与 few-shot 候选。

### 段 2：LLM 语义标注
- 读 `knowledge/style-distill/prompt-templates/distill-prompt.md`，按模板补：rhetoric / emotion_expression / narrative / dialogue_style / rhythm 非对话占比 / verb_style.strength / cohesion.paragraph_bridge_style，以及 banned_words 定稿、preferred_words 去噪、few-shot 精选。
- 语义维度参考：样本原文 + 客观维度 + 既有卡（保留 locked 项）。

### 段 3：合并写卡 + 备份
- 合并客观 + 语义 → 按 distilled-style-spec 写 `settings/writing-style.md`（新 frontmatter + 定性层）。
- 更新前把旧版备份到 `settings/.style-versions/v{N}_{YYYY-MM-DD}.md`（N 取现有最大 +1）。
- confidence 重算（脚本段已给）。覆盖 body 的 few-shot 例句。

## 二、场景卡蒸馏（style-distill-order 内，可选）
- 按样本的段落场景类型归属（对话/战斗/环境/心理/过渡/群像），对每类子样本跑 distill → 差异维度写 `settings/style-profiles/{scene_type}.md`（override 只写该场景与主卡显著不同的维度，confidence 与 source_sample_length 用该子样本的值）。

## 三、防重复 / 防冲突
- banned_words 与 `.claude/knowledge/anti-ai.md` 禁用词合并去重。
- 场景卡 override 不与主卡同维度并列（override 即覆盖）。
- locked 维度：任何蒸馏/增量都跳过。

## 四、验收自检
1. frontmatter 含 9 大维度键，类型符合 schema
2. confidence 0-100；容差档标注正确
3. banned_words 与 anti-ai 禁用词无重复
4. 备份文件存在；幂等：重复跑同一样本不产生多余备份（以当日版本为准）
```

- [ ] **Step 3: 写蒸馏 LLM 语义标注 prompt 模板**

`knowledge/style-distill/prompt-templates/distill-prompt.md`：

```markdown
# 蒸馏 LLM 语义标注 Prompt（style-distiller 段 2 用）

你是文风标注器。基于样本原文与脚本客观维度，补齐风格卡 9 大维度中脚本算不出的部分。

## 输入
- 样本原文（若干段）
- 客观维度 partial（脚本输出）
- 既有卡（如有，保留 locked 项）

## 只补下列维度（脚本已算的不要重写）
- **rhetoric**：metaphor_density_per_100（每百字比喻数）、metaphor_preference（常用喻体类型，1 句）、sensory_dist（主要感官通道，1 句）
- **emotion_expression**：direct_pct（直接情绪词比例，估算）、action_physiology_pct（动作/生理描写比例）、environment_projection_pct（移情环境比例），三者合计约 100
- **narrative**：perspective（视角，1 词）、focal_character（聚焦角色）、inner_monologue_style（内心独白风格，1 句）
- **dialogue_style**：tag_style（"说"字风格/动作代替，1 句）、avg_dialogue_length（估字数）、interrupt_freq_per_100、subtext_ratio（潜台词比例）、direct_address_freq_per_100（称呼频率）
- **rhythm**：action_pct / environment_pct / inner_thought_pct / narration_pct（估算，与 dialogue_pct 合计约 100）
- **verb_style.strength**：动词力度（1-5）
- **cohesion.paragraph_bridge_style**：段间衔接方式（1 句）
- **lexicon.banned_words**：从 preferred_words 高频词里筛出"显得廉价/滥用"的词；**lexicon.preferred_words**：去噪保留 5-10 个
- **few-shot**：从样本挑 3-5 句标志性句子（短、有辨识度）

## 输出
按 distilled-style-spec 的 9 大维度结构输出补全后的 frontmatter YAML 片段（只含你补的字段），以及正文 few-shot 例句列表。数值给整数/一位小数，文字描述≤1 句。
```

- [ ] **Step 4: 运行 check-agents，确认 agent/skill/knowledge 引用合法**

Run: `python tools/check-agents.py`
Expected: 除 `settings/style-profiles/`、`settings/.style-versions/` 两个 DEPLOYED_PATTERNS 缺失外全通过（这两条报错在 Task 15 修复；若无法容忍中间态报错，把 Task 15 的 check-agents 改动提前到本 Task）。

- [ ] **Step 5: Commit**

```bash
git add agents/style-distiller.md skills/style-distill.md knowledge/style-distill/
git commit -m "feat: style-distiller agent + style-distill SOP + 蒸馏 prompt 模板"
```

---

## Task 7: prompt-crafter 风格注入（F3）

**Files:**
- Modify: `skills/prompt-crafting.md`
- Modify: `agents/prompt-crafter.md`
- Create: `knowledge/style-distill/prompt-templates/injection-template.md`

**Interfaces:**
- Consumes: 卡片 schema（Task 2）、格式规范（Task 3）
- Produces: prompt-crafting.md 的 Step 1 读卡 / Step 1.5 裁决扩展 / Step 2「写作风格约束」块 / Step 4 +2 自检项

- [ ] **Step 1: 写注入渲染模板**

`knowledge/style-distill/prompt-templates/injection-template.md`：

```markdown
# 写作风格约束块渲染模板（prompt-crafter 用）

## 何时注入
- confidence=0 → 本块不注入（只走正文定性层注入）。
- 主卡兜底：本章每个场景类型查 `settings/style-profiles/{scene_type}.md`，有则合成（主卡数值被场景卡 override 覆盖），无则只用主卡。

## 渲染规则
1. 数值一律「约 X（±Y%）」——Y 按主卡 confidence 容差档：21-50→30 / 51-70→20 / 71-90→15 / 91-100→10。
2. 按场景类型稀疏注入（本章无该场景的维度不注入）：

| 场景类型 | 重点注入 | 不注入 |
|---------|---------|--------|
| dialogue | dialogue_style + dialogue_pct + lexicon | verb_style、environment_pct |
| fight | verb_style + syntax（短句）+ rhythm.action_pct | subtext_ratio、sensory_dist |
| environment | rhetoric.sensory_dist + rhythm.environment_pct | interrupt_freq |
| inner-mono | emotion_expression + narrative.inner_monologue_style | dialogue_style |
| transition | cohesion + rhythm | rhetoric |
| group-scene | rhythm + dialogue_style | verb_style |

3. 红线级（置于约束红线区，任何压缩不得删改）：卡内 banned_words、硬约束节。
4. few-shot：每场景类型 1-2 句标志性例句（无则省略）。

## 输出块示例
```
【写作风格约束】（本场景：dialogue）
- 对话占比约 40%（±20%）；对话多短句，平均约 12 字（±20%）
- 对话标签以动作代替为主，禁用"说"字赘述
- banned_words：{…}（红线，不得出现）
- few-shot：{例句 1}；{例句 2}
```
```

- [ ] **Step 2: 改 prompt-crafting.md Step 1（读卡 + confidence 分支）**

把「1. **writing-style.md** → 提取四字段（core_principles, possible_mistakes, depiction_techniques）+ genre + model」替换为：

```markdown
1. **writing-style.md（主卡）** → 提取正文定性层四字段（core_principles, possible_mistakes, depiction_techniques）+ 量化层 9 大维度 + confidence。confidence=0 → 只注入定性层；否则按容差档渲染「写作风格约束」块（见注入模板）
```

并在「8. **永久记忆** …」之后追加一条：

```markdown
9. **style-profiles/ 场景卡** → 本章每个场景类型查 `settings/style-profiles/{scene_type}.md`，有则把该卡 override 合并进主卡量化层（仅该场景注入用）；无则主卡兜底
```

- [ ] **Step 3: 改 prompt-crafting.md Step 1.5 裁决表**

在优先级 1「约束红线」行「执行要求」列追加：「风格卡 `banned_words` / `hard_constraints` 并入红线级，任何压缩不得删改」。
在优先级 6「写作规范」行「执行要求」列追加：「写作规范级内冲突优先级：作者最新记忆偏好（writing-memory）> 风格卡量化数值 > genre-example 题材基线」。

- [ ] **Step 4: 改 prompt-crafting.md Step 2 输出节——新增「写作风格约束」子节**

在「#### 场景写作指引」（L489）之后、「#### 质感要求」（L493）之前插入：

```markdown
#### 写作风格约束

（从主卡 + 本章场景卡按注入模板渲染）：本章涉及 {N} 种场景类型，按场景类型稀疏注入量化约束（「约 X（±Y%）」，Y 按主卡 confidence 容差档）与 1-2 条 few-shot。主卡兜底场景。confidence=0 时本子节不注入。banned_words / 硬约束归入「不可违反规则·红线约束」。

**分工：** 本子节只注入「多少」（量化数值 + few-shot），scene-craft 方法论只注入「怎么写」（场景写作指引子节），两者不并列重复。
```

- [ ] **Step 5: 改 prompt-crafting.md Step 4 自检表——新增 2 项**

在「writing-style 注入」行之后插入两行：

```markdown
| 风格块与指引无重复 | 「写作风格约束」块与「场景写作指引」块无语义重复（量化约束不与方法论技法并列注入） |
| banned_words 无重复 | 注入的 banned_words 与 anti-ai 禁用词合并去重后无重复出现 |
```

- [ ] **Step 6: 改 prompt-crafter.md knowledge**

在 knowledge 列表追加两条：

```yaml
  - path: settings/style-profiles/
    description: 分场景风格卡（场景类型识别后按需加载）
  - path: .claude/knowledge/distilled-style-spec.md
    description: 蒸馏风格卡格式规范
```

- [ ] **Step 7: 回归校验**

Run: `python tools/check-agents.py`
Expected: 通过（除 style-distiller 的 style-profiles/.style-versions 白名单报错——Task 15 修）。

- [ ] **Step 8: Commit**

```bash
git add skills/prompt-crafting.md agents/prompt-crafter.md knowledge/style-distill/prompt-templates/injection-template.md
git commit -m "feat: prompt-crafter 风格卡稀疏注入（写作风格约束块 + 裁决表扩展 + 自检 2 项）"
```

---

## Task 8: 部署链（platforms / sync-project / requirements / CI / 计数）

**Files:**
- Modify: `tools/platforms.py`
- Modify: `tools/sync-project.py`
- Modify: `tools/requirements.txt`
- Modify: `.github/workflows/static.yml`
- Modify: `tools/test_platforms.py`

**Interfaces:**
- Consumes: `init.deploy_tools` / `init.migrate_writing_style`（Task 4）、`agents/style-distiller.md`（Task 6）
- Produces: reasonix 生成 style-distiller SKILL.md；sync-project 同步新模板/脚本 + 迁移钩子 + 指纹含 templates；CI 装 jieba；test_platforms 计数更新

- [ ] **Step 1: platforms.py — exec_agents 加 style-distiller**

在 `deploy_reasonix_skills` 的 `exec_agents` 字典（当前 7 项）末尾加一行：

```python
    "style-distiller": ["style-distill"],
```

> style-distiller 只有 1 个 SOP，按现有规则不进 read_skill 白名单（writer 同构）。

- [ ] **Step 2: requirements.txt + jieba；static.yml + pip install**

`tools/requirements.txt` 追加一行：

```
jieba
```

`.github/workflows/static.yml` 的 lint job 里 `pip install pyyaml` 改为 `pip install pyyaml jieba`，并在 4 个检查脚本后加第 5 条：

```yaml
    - name: style-distiller 验证
      run: python tools/test_style_distill.py
```

- [ ] **Step 3: test_platforms.py 计数更新**

`test_init_layout` 中 claude agents 数量断言 `n == 8` → `n == 9`；reasonix skill 名列表追加 `"style-distiller"`（原 10 → 11）。

- [ ] **Step 4: sync-project.py — 同步模板/脚本 + 迁移 + 指纹**

- `compute_fingerprint()` 的 `files` 收集加一段（agents/skills/knowledge 之外补 templates/settings 与 distill 脚本）：

```python
    for base in [TEMPLATE_SETTINGS_DIR, TOOLS_SRC_DIR]:  # 见下两常量
        if base.exists():
            for f in sorted(base.rglob("*")):
                if f.is_file() and f.name != ".gitkeep":
                    files.append(f)
```

  模块顶部加常量：`TEMPLATE_SETTINGS_DIR = SKILL_HOME / "templates" / "settings"`，`TOOLS_SRC_DIR = SKILL_HOME / "tools"`（新增常量；TOOLS_SRC_DIR 仅指纹 distill/compare/mix 三个脚本，避免全 tools/ 哈希）。

- 新增 `sync_style_assets(project)` 并在 `do_sync` 中调用：把 `templates/settings/style-profiles/*.md` 拷进项目 `settings/style-profiles/`（只补缺失文件，不覆盖已有）；把 `tools/distill-style.py`（+compare/mix，若存在）拷进项目 `tools/`；然后调用迁移钩子（从 init 导入）：

```python
def sync_style_assets(project: Path) -> int:
    count = 0
    src_cards = TEMPLATE_SETTINGS_DIR / "style-profiles"
    if src_cards.exists():
        dst = project / "settings" / "style-profiles"
        dst.mkdir(parents=True, exist_ok=True)
        for f in src_cards.glob("*.md"):
            if not (dst / f.name).exists():
                (dst / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                count += 1
    dst_tools = project / "tools"
    dst_tools.mkdir(parents=True, exist_ok=True)
    for name in ("distill-style.py", "compare-style.py", "mix-style.py"):
        src = TOOLS_SRC_DIR / name
        if src.exists() and not (dst_tools / name).exists():
            (dst_tools / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            count += 1
    try:
        from init import migrate_writing_style   # init.py main 有 __main__ 守卫，导入安全
        migrate_writing_style(project)
    except ImportError:
        pass
    if count:
        print(f"  [OK] 风格资产同步: {count} 个新文件")
    return count
```

- [ ] **Step 5: 回归验证**

Run:
```bash
python tools/test_platforms.py
python tools/test_style_distill.py
```
Expected: test_platforms 全绿（含新计数）；test_style_distill 全绿。若 test_platforms 因 reasonix 新 SKILL.md 引用改写断言受影响，按实际输出修正。

- [ ] **Step 6: Commit**

```bash
git add tools/platforms.py tools/sync-project.py tools/requirements.txt .github/workflows/static.yml tools/test_platforms.py
git commit -m "feat: style-distiller 部署链（reasonix 生成 / sync 同步 / CI jieba / 计数 8→9）"
```

---

## Task 9: novel-agent setup 调度点 + order 协议

**Files:**
- Modify: `agents/novel-agent.md`
- Modify: `skills/novel-dispatch.md`
- Test: `tools/test_style_distill.py`（追加 E2E：init 项目 → style-distiller agent 已部署）

**Interfaces:**
- Consumes: `style-distill-order.md` 协议（现有 order 模板）
- Produces: setup 阶段调度分支；novel-dispatch 调度表 +2 行（setup 蒸馏 + 手动，archive 增量归 Phase 3）

- [ ] **Step 1: novel-agent.md THINK setup 分支加调度点 1**

在 setup 分支「调 updater（setting-update-order）DONE 后」、推进 outline 之前插入：

```markdown
   ├─ 若作者提供了风格参考文本（或说"按这个风格写"）→
   │    写 style-distill-order.md（inputs: 样本路径 + settings/writing-style.md；outputs: 主卡/场景卡/.style-versions）
   │    → 调 style-distiller → DONE 后再推进 outline
   └─ 无样本 → 跳过（templates 预置题材卡兜底，confidence=0）
```

- [ ] **Step 2: novel-dispatch.md 调度表加行**

在 setup 行附近追加两行：

```markdown
| setup | style-distiller | style-distill-order.md（作者提供风格样本时触发） |
| 手动 | style-distiller | style-distill-order.md / style-update-order.md（作者主动触发重蒸馏/调参数/混风格） |
```

（archive 增量行在 Phase 3 Task 12 追加。）

- [ ] **Step 3: 追加 E2E 用例**

```python
def test_e2e_init_deploy():
    print("[e2e] init 部署 style-distiller")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        check("agent style-distiller 已部署", (tmp / ".claude" / "agents" / "style-distiller.md").exists())
        check("skill style-distill 已部署", (tmp / ".claude" / "skills" / "style-distill.md").exists())
        check("脚本已部署到 tools/", (tmp / "tools" / "distill-style.py").exists())
        check("主卡为新格式", (tmp / "settings" / "writing-style.md").read_text(encoding="utf-8").startswith("---"))
        check("场景卡已部署", (tmp / "settings" / "style-profiles" / "dialogue.md").exists())
```

（加入 main() 调用序列。）

- [ ] **Step 4: 跑测试**

Run: `python tools/test_style_distill.py`
Expected: 全绿（含新 E2E 段）。

- [ ] **Step 5: Commit**

```bash
git add agents/novel-agent.md skills/novel-dispatch.md tools/test_style_distill.py
git commit -m "feat: novel-agent setup 蒸馏调度点 + style-distill-order 协议"
```

---

# Phase 2：场景卡 + 题材基线（F4）

## Task 10: 场景卡蒸馏 SOP + 题材基线模板

**Files:**
- Modify: `skills/style-distill.md`（场景卡蒸馏节补全 + 题材基线节）
- Create: `templates/settings/style-profiles/genre-baselines/{xianxia,urban,suspense}/base.md`（题材基线三层占位）
- Test: `tools/test_style_distill.py`（追加题材基线模板存在性）

**Interfaces:**
- Consumes: distill-style.py CLI（Task 5）
- Produces: 题材基线三层结构（基础卡 → 题材偏移 delta → 标杆卡），供 style-distiller 与 mix-style（Task 14）组合

- [ ] **Step 1: style-distill.md 补「场景卡蒸馏」细则**

把「二、场景卡蒸馏」从概要补全为可执行步骤：

```markdown
## 二、场景卡蒸馏（style-distill-order 内）
1. 对样本按段落判定场景类型（对话/战斗/环境/心理/过渡/群像）。
2. 每类聚合出子样本（≥800 字才蒸馏该卡；不足则跳过该场景卡）。
3. 对每类子样本跑 `distill-style.py distill` → 得该场景客观维度。
4. 与主卡对比：差异显著（相对差 > 容差）的维度写进 `style-profiles/{scene_type}.md` 的 override，其余留空。
5. 定性节（描写层次/技法）由 LLM 按该场景样本提炼；few-shot 取该场景标志句。
```

- [ ] **Step 2: 题材基线三层模板**

创建 `templates/settings/style-profiles/genre-baselines/` 下三个题材目录（xianxia/urban/suspense），每目录三个文件（`base.md` 基础卡、`delta.md` 题材偏移、`benchmark.md` 标杆卡占位）。以 `xianxia/base.md` 为例：

```markdown
---
profile_version: "1.0"
scene_type: general
source_sample_length: 0
confidence: 0
last_updated: ""
locked: []
# 题材基线·基础卡（xianxia）
lexicon: { adj_density_per_100: 0, adv_density_per_100: 0, four_phrase_freq_per_100: 0, preferred_words: [], banned_words: [], name_pronoun_ratio: 0 }
syntax: { avg_sentence_length: 0, sentence_length_dist: {}, single_sentence_paragraph_pct: 0, avg_sentences_per_paragraph: 0, question_ratio: 0, exclamation_ratio: 0 }
rhythm: { dialogue_pct: 0, action_pct: 0, environment_pct: 0, inner_thought_pct: 0, narration_pct: 0 }
rhetoric: { metaphor_density_per_100: 0, metaphor_preference: "", sensory_dist: "" }
emotion_expression: { direct_pct: 0, action_physiology_pct: 0, environment_projection_pct: 0 }
narrative: { perspective: "", focal_character: "", inner_monologue_style: "" }
dialogue_style: { tag_style: "", avg_dialogue_length: 0, interrupt_freq_per_100: 0, subtext_ratio: 0, direct_address_freq_per_100: 0 }
cohesion: { conjunction_freq_per_100: 0, transition_sentence_ratio: 0, paragraph_bridge_style: "" }
verb_style: { action_verb_ratio: 0, mental_verb_ratio: 0, state_verb_ratio: 0, strength: "" }
---

# 题材基线·基础卡（仙侠）

（P1：占位，数值由对标杆作品样本蒸馏填充；P2：作者盲测校准。）
```

`delta.md`：同 schema，frontmatter 加 `baseline_for: xianxia`，正文说明「本卡只写与基础卡的题材偏移 delta，mix-style 合成用」。`benchmark.md`：作者认可的标杆卡占位（正文注明盲测目标正确率 ≥70%，见 spec §13-6）。

- [ ] **Step 3: 追加存在性测试**

```python
def test_genre_baselines():
    print("[unit] 题材基线模板")
    for g in ("xianxia", "urban", "suspense"):
        for layer in ("base", "delta", "benchmark"):
            f = REPO / "templates" / "settings" / "style-profiles" / "genre-baselines" / g / f"{layer}.md"
            check(f"{g}/{layer} 存在", f.exists())
```

- [ ] **Step 4: 跑测试 + Commit**

Run: `python tools/test_style_distill.py`
Expected: 全绿。

```bash
git add skills/style-distill.md templates/settings/style-profiles/genre-baselines/ tools/test_style_distill.py
git commit -m "feat: 场景卡蒸馏细则 + 题材基线三层模板（F4）"
```

---

# Phase 3：增量更新 + 备份 + locked（F5）

## Task 11: distill-style.py update 模式

**Files:**
- Modify: `tools/distill-style.py`
- Test: `tools/test_style_distill.py`（追加 `test_update` 段）

**Interfaces:**
- Consumes: `compute_confidence` / `tolerance_for` / 卡片 schema（Task 5）
- Produces: CLI `distill-style.py update -c <card> -o <out> <归档章节...>`；`sliding_alpha(confidence) -> float`；`load_card(path) -> (dims, body)`；`dump_card(dims, body) -> str`

- [ ] **Step 1: 加卡片读写 + update 实现**

在 `main()` 之前插入（并在 CLI 加 `update` 子命令）：

```python
# ------------------------------------------------------------ 卡片读写 / 增量

def load_card(path):
    """解析风格卡 → (frontmatter dict, 正文)。非新格式返回 (None, 原文)。"""
    text = Path(path).read_text(encoding="utf-8")
    if not text.lstrip().startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) != 3 or not yaml:
        return None, text
    return yaml.safe_load(parts[1]), parts[2]


def dump_card(dims: dict, body: str) -> str:
    if not yaml:
        return body
    fm = yaml.safe_dump(dims, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return f"---\n{fm}---\n{body}"


def sliding_alpha(confidence: int) -> float:
    return 0.50 if confidence < 30 else 0.65 if confidence <= 60 else 0.75


def chapter_count_from_fs(project: Path) -> int:
    arch = project / "archives"
    return sum(1 for f in arch.glob("vol-*.md")) if arch.is_dir() else 0


def cmd_update(args) -> int:
    dims, body = load_card(args.card)
    if dims is None:
        print(f"error: {args.card} 不是新格式风格卡（缺 frontmatter）", file=sys.stderr)
        return 2
    for ch in args.chapters:
        partial = build_partial([ch])
        alpha = sliding_alpha(dims.get("confidence", 0))
        for dim, fields in (("lexicon", ("adj_density_per_100", "adv_density_per_100",
                                         "four_phrase_freq_per_100", "name_pronoun_ratio")),
                            ("syntax", ("avg_sentence_length", "single_sentence_paragraph_pct",
                                        "avg_sentences_per_paragraph", "question_ratio", "exclamation_ratio")),
                            ("rhythm", ("dialogue_pct",)),
                            ("cohesion", ("conjunction_freq_per_100", "transition_sentence_ratio")),
                            ("verb_style", ("action_verb_ratio", "mental_verb_ratio", "state_verb_ratio"))):
            locked = set(dims.get("locked") or [])
            for field in fields:
                key = f"{dim}.{field}"
                if key in locked:
                    continue
                old = (dims.get(dim) or {}).get(field)
                new = (partial.get(dim) or {}).get(field)
                if old is None or new is None:
                    continue
                dims[dim][field] = round(old * alpha + new * (1 - alpha), 2)
        # 幂等 checkpoint（同章不重放）
        ck = Path(args.project) / ".agent" / "style-update" / f"{Path(ch).stem}.done"
        if ck.exists():
            continue
        ck.parent.mkdir(parents=True, exist_ok=True)
        ck.write_text("done\n", encoding="utf-8")
    # 备份旧版
    vers = Path(args.card).parent / ".style-versions"
    vers.mkdir(parents=True, exist_ok=True)
    maxn = 0
    for f in vers.glob("v*_*.md"):
        m = re.match(r"v(\d+)_", f.name)
        if m:
            maxn = max(maxn, int(m.group(1)))
    import datetime
    stamp = datetime.date.today().isoformat()
    (vers / f"v{maxn + 1}_{stamp}.md").write_text(
        dump_card(*load_card(args.card)) if False else Path(args.card).read_text(encoding="utf-8"),
        encoding="utf-8")
    # 置信度重算 + 写卡
    dims["confidence"] = compute_confidence(dims.get("source_sample_length", 0),
                                            chapter_count_from_fs(Path(args.project)))
    dims["last_updated"] = datetime.date.today().isoformat()
    Path(args.out).write_text(dump_card(dims, body), encoding="utf-8")
    print(f"update: 客观维度滑动平均更新 {len(args.chapters)} 章，confidence={dims['confidence']}，备份 v{maxn + 1}")
    return 0
```

CLI 追加：

```python
    u = sub.add_parser("update", help="增量：客观维度滑动平均 + 备份 + 置信度重算")
    u.add_argument("-c", "--card", required=True, help="当前风格卡路径")
    u.add_argument("-o", "--out", required=True, help="新卡输出路径")
    u.add_argument("--project", required=True, help="项目根（.agent/style-update checkpoint 与 archives 计数用）")
    u.add_argument("chapters", nargs="+", help="已归档定稿章节")
```

`main()` 里加分支：`if args.mode == "update": return cmd_update(args)`。

> 注：`dims[dim]` 可能是 dict，直接改字段即可；`locked` 用 `dim.field` 扁平键（如 `syntax.avg_sentence_length`），模板卡 `locked: []`。

- [ ] **Step 2: 追加单元测试**

```python
def test_update():
    print("[unit] 增量滑动平均")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        card = tmp / "settings" / "writing-style.md"
        # 造一份带数值的旧卡
        text = card.read_text(encoding="utf-8")
        text = text.replace("avg_sentence_length: 0", "avg_sentence_length: 20")
        card.write_text(text, encoding="utf-8")
        ch = tmp / "archives" / "vol-1-ch-1.md"
        ch.parent.mkdir(parents=True, exist_ok=True)
        ch.write_text("他快速出拳，拳风猎猎。\n\n她退后半步，眼神冰冷。\n\n" * 8, encoding="utf-8")
        out = tmp / "settings" / "writing-style-new.md"
        r = run([sys.executable, str(TOOLS / "distill-style.py"), "update",
                 "-c", str(card), "-o", str(out), "--project", str(tmp), str(ch)], cwd=str(TOOLS))
        check("update exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        import yaml as _y
        fm = _y.safe_load(out.read_text(encoding="utf-8").split("---", 2)[1])
        check("新卡 avg_sentence_length 介于 0-40",
              0 < fm["syntax"]["avg_sentence_length"] < 40, str(fm["syntax"]))
        check("备份存在", list((tmp / "settings" / ".style-versions").glob("v1_*.md")))
        # 幂等：同章再跑，不新增备份
        run([sys.executable, str(TOOLS / "distill-style.py"), "update",
             "-c", str(card), "-o", str(out), "--project", str(tmp), str(ch)], cwd=str(TOOLS))
        check("checkpoint 幂等（备份数不变）",
              len(list((tmp / "settings" / ".style-versions").glob("v1_*.md"))) == 1)
```

- [ ] **Step 3: 跑测试绿**

Run: `python tools/test_style_distill.py`
Expected: 全绿。

- [ ] **Step 4: Commit**

```bash
git add tools/distill-style.py tools/test_style_distill.py
git commit -m "feat: distill-style.py update 模式（滑动平均 + 备份 + locked + checkpoint 幂等）"
```

---

## Task 12: novel-agent archive 增量调度点 + style-update-order

**Files:**
- Modify: `agents/novel-agent.md`
- Modify: `skills/novel-dispatch.md`
- Modify: `skills/style-distill.md`（增量节）

**Interfaces:**
- Consumes: `style-update-order.md` 协议、`distill-style.py update`（Task 11）
- Produces: archive 阶段调度分支

- [ ] **Step 1: novel-agent.md archive 分支加调度点 2**

在 archive 阶段「updater archive-order DONE 后」、卷完成判定之前插入：

```markdown
   ├─ 归档完成后 → 写 style-update-order.md（inputs: settings/writing-style.md + 本次归档章节；outputs: 主卡 + .style-versions）
   │   → 调 style-distiller（增量：脚本档每章跑客观维度滑动平均；语义档由 style-distiller 按置信度<60 / 累计5章 / 作者要求重估）
   │   → DONE 后再继续卷完成判定
```

- [ ] **Step 2: novel-dispatch.md 加 archive 行**

```markdown
| archive | style-distiller | style-update-order.md（每次归档后增量蒸馏） |
```

- [ ] **Step 3: style-distill.md 补「增量蒸馏」节**

```markdown
## 五、增量蒸馏（style-update-order）
1. 读 order inputs（当前主卡 + 最新归档章节列表）。
2. Bash 调：`python tools/distill-style.py update -c settings/writing-style.md -o settings/writing-style.md --project . <归档章节...>`
   （update 内部做：客观维度滑动平均、locked 跳过、备份到 .style-versions、置信度重算、.agent/style-update/{chapter}.done 幂等。）
3. 语义档重估条件（满足任一）：confidence < 60 / 距上次语义重估 ≥5 章 / order 标注语义重估。此时按蒸馏 prompt 段 2 跑语义维度并写卡。
4. 增量只动量化数值，不碰正文定性层（与 updater 的 [writer-preference] 学习分工：updater 继续写 .claude/knowledge/writer-style.md，style-distiller 不动它）。
5. 高频定性条目若作者确认升华，才写进卡片 banned_words / hard_constraints。
```

- [ ] **Step 4: Commit**

```bash
git add agents/novel-agent.md skills/novel-dispatch.md skills/style-distill.md
git commit -m "feat: archive 后增量蒸馏调度 + style-update-order（F5）"
```

---

# Phase 4：Gate G（F6）

## Task 13: distill-style.py check 模式

**Files:**
- Modify: `tools/distill-style.py`
- Test: `tools/test_style_distill.py`（追加 `test_check` 段）

**Interfaces:**
- Consumes: `tolerance_for`（Task 5）
- Produces: CLI `distill-style.py check -c <card> <正文...>` → 偏差表（dim | measured | expected | dev | verdict: pass/warn/fail）

- [ ] **Step 1: 加 check 实现 + CLI 子命令**

```python
# ------------------------------------------------------------ Gate G 校验

def cmd_check(args) -> int:
    dims, _ = load_card(args.card)
    if dims is None:
        print(f"error: {args.card} 不是新格式风格卡", file=sys.stderr)
        return 2
    tol = tolerance_for(dims.get("confidence", 0))
    if tol == 0:
        print(f"check: confidence={dims.get('confidence')}（手动档），跳过量化校验，仅报告。")
        return 0
    print(f"# 风格偏差表（容差 ±{int(tol * 100)}%）")
    total_fail = 0
    for text_file in args.texts:
        partial = build_partial([text_file])
        for dim, fields in (("lexicon", ("adj_density_per_100", "adv_density_per_100",
                                         "four_phrase_freq_per_100")),
                            ("syntax", ("avg_sentence_length", "single_sentence_paragraph_pct",
                                        "avg_sentences_per_paragraph", "question_ratio", "exclamation_ratio")),
                            ("rhythm", ("dialogue_pct",)),
                            ("cohesion", ("conjunction_freq_per_100", "transition_sentence_ratio")),
                            ("verb_style", ("action_verb_ratio", "mental_verb_ratio", "state_verb_ratio"))):
            for field in fields:
                exp = (dims.get(dim) or {}).get(field)
                got = (partial.get(dim) or {}).get(field)
                if exp is None or got is None or not exp:
                    continue
                dev = (got - exp) / exp
                verdict = "pass" if abs(dev) <= tol else ("warn" if abs(dev) <= 2 * tol else "FAIL")
                if verdict == "FAIL":
                    total_fail += 1
                print(f"- {dim}.{field}: measured={got} expected={exp} dev={dev:+.0%} -> {verdict}")
    print(f"\n不通过维度数：{total_fail}")
    return 1 if total_fail else 0
```

CLI 追加：

```python
    c = sub.add_parser("check", help="Gate G：正文客观维度 vs 卡片容差")
    c.add_argument("-c", "--card", required=True, help="风格卡路径（主卡）")
    c.add_argument("texts", nargs="+", help="待校验正文文件")
```

`main()` 加分支：`if args.mode == "check": return cmd_check(args)`。

- [ ] **Step 2: 追加单元测试**

```python
def test_check():
    print("[unit] check 容差校验")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        card = tmp / "settings" / "writing-style.md"
        text = card.read_text(encoding="utf-8").replace(
            "confidence: 0", "confidence: 80").replace(
            "avg_sentence_length: 0", "avg_sentence_length: 25")
        card.write_text(text, encoding="utf-8")
        body = tmp / "body.md"
        body.write_text("他缓缓推开门，寒风扑面而来，院子里一片死寂。\n\n" * 20, encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "distill-style.py"), "check",
                 "-c", str(card), str(body)], cwd=str(TOOLS))
        check("check exit 0/1 皆合法（有 FAIL 为 1）", r.returncode in (0, 1))
        check("check 输出偏差表", "风格偏差表" in r.stdout)
```

- [ ] **Step 3: 跑测试 + Commit**

Run: `python tools/test_style_distill.py`
Expected: 全绿。

```bash
git add tools/distill-style.py tools/test_style_distill.py
git commit -m "feat: distill-style.py check 模式（Gate G 容差校验）"
```

---

## Task 14: anti-ai Gate G 扩展

**Files:**
- Modify: `skills/anti-ai.md`
- Modify: `agents/anti-ai.md`
- Modify: `knowledge/anti-ai/boundary-cases.md`
- Create: `knowledge/style-distill/prompt-templates/gate-g-checklist.md`

**Interfaces:**
- Consumes: `distill-style.py check`（Task 13）、卡片 schema
- Produces: anti-ai Phase 1 Gate G 扫描、Phase 2 第 7 指标、报告行、boundary-cases 豁免组

- [ ] **Step 1: 写 Gate G 清单模板**

`knowledge/style-distill/prompt-templates/gate-g-checklist.md`：

```markdown
# Gate G 风格偏差检查清单（anti-ai 用）

## 触发
Phase 1 扫描阶段，对每章正文跑 `python tools/distill-style.py check -c settings/writing-style.md <正文>`
（客观维度）。语义维度（rhetoric/emotion/narrative/dialogue_style 等）由 anti-ai LLM 按风格卡估算对比。

## 分级
- **通过**：客观维度全在容差内，语义维度无明显偏离。
- **警告（作者确认）**：1-3 个客观维度 warn，或语义维度轻微偏离 → 列出，作者确认后放行。
- **不通过（局部重写建议）**：≥1 个客观维度 FAIL（偏差 > 2×容差）或语义维度显著偏离 → 建议对偏离段落局部重写（只改表达，不改剧情）。

## 报告行
风格偏差：X 处（维度：avg_sentence_length 偏差 +18% …；定级：警告/不通过）

## 豁免（读 boundary-cases Gate G 组）
- 特定场景类型刻意偏离（战斗场景短句、对话场景长对话）命中豁免列表 → SKIP
```

- [ ] **Step 2: 改 skills/anti-ai.md Phase 1**

在 Gate F 扫描产出（当前约 L92）之后追加 Gate G 段：

```markdown
**Gate G：风格偏差（可选，读 `settings/writing-style.md` 主卡 + 对应场景卡）**
- Bash 调 `python tools/distill-style.py check -c settings/writing-style.md <正文>` → 读偏差表
- LLM 按风格卡估算语义维度（rhetoric/emotion/narrative/dialogue_style）对比
- 按 gate-g-checklist 分级：通过 / 警告（作者确认）/ 不通过（局部重写建议）
- 命中 boundary-cases Gate G 豁免组 → SKIP 标注
```

- [ ] **Step 3: 改 skills/anti-ai.md Phase 2 诊断表 + 报告**

诊断表（6 项量化指标表）加第 7 行：

```markdown
| 风格偏差维度数 | <2 | 2-3 | ≥4 |
```

Phase 4 报告格式（约 L241-266）末尾加一行：

```markdown
风格偏差：X 处（按维度列）
```

- [ ] **Step 4: 改 agents/anti-ai.md**

- frontmatter `tools` 确认含 `Bash`（没有则加）。
- `knowledge` 追加：

```yaml
  - path: settings/writing-style.md
    description: 写作风格主卡（Gate G 校验基线）
  - path: settings/style-profiles/
    description: 分场景风格卡（Gate G 场景差异基线）
  - path: .claude/knowledge/gate-g-checklist.md
    description: Gate G 检查清单
```

（`gate-g-checklist.md` 由 deploy_knowledge 从 knowledge/style-distill/ 部署到 `.claude/knowledge/`——若现有 deploy_knowledge 不递归该目录，则把 checklist 放 `knowledge/anti-ai/` 或按实际部署逻辑放置，任选其一保证项目内可达。）

- [ ] **Step 5: 改 boundary-cases.md**

新增豁免组「Gate G·风格偏差」：

```markdown
### Gate G·风格偏差豁免
| 类别 | 说明 |
|------|------|
| 场景类型刻意偏离 | 战斗场景刻意用短句、对话场景刻意长对话/低对话占比——若与场景卡标注的该场景 override 一致，不算偏差 |
| 人物口癖 | 角色化重复用词/句式（已在前组豁免） |
| 不确定 | 偏差在 warn 与 FAIL 之间 → 标 `[疑: 疑似误杀]` 不改，报作者确认 |
```

- [ ] **Step 6: 跑 check-agents + test_style_distill**

Run:
```bash
python tools/check-agents.py
python tools/test_style_distill.py
```
Expected: 全绿（style-profiles/.style-versions 白名单若在 Task 15 前仍缺，本 Task 报错可接受，Task 15 修复）。

- [ ] **Step 7: Commit**

```bash
git add skills/anti-ai.md agents/anti-ai.md knowledge/anti-ai/boundary-cases.md knowledge/style-distill/prompt-templates/gate-g-checklist.md
git commit -m "feat: anti-ai Gate G 风格偏差校验（F6）"
```

---

# Phase 5：F7 / F8 工具

## Task 15: tools/compare-style.py

**Files:**
- Create: `tools/compare-style.py`
- Modify: `tools/test_style_distill.py`（追加 `test_compare` 段）

**Interfaces:**
- Consumes: 卡片 schema
- Produces: CLI `compare-style.py <cardA> <cardB>` → 维度变化表（exit 0）

- [ ] **Step 1: 写实现**

```python
#!/usr/bin/env python3
"""F7：对比两张风格卡 YAML diff → 维度变化表。
用法: python compare-style.py <cardA> <cardB>
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None


def load(path: str):
    text = Path(path).read_text(encoding="utf-8")
    if not text.lstrip().startswith("---"):
        return None, text
    parts = text.split("---", 2)
    return (yaml.safe_load(parts[1]), parts[2]) if yaml and len(parts) == 3 else (None, text)


NUMERIC = {"adj_density_per_100", "adv_density_per_100", "four_phrase_freq_per_100",
           "name_pronoun_ratio", "avg_sentence_length", "single_sentence_paragraph_pct",
           "avg_sentences_per_paragraph", "question_ratio", "exclamation_ratio",
           "dialogue_pct", "action_pct", "environment_pct", "inner_thought_pct", "narration_pct",
           "metaphor_density_per_100", "direct_pct", "action_physiology_pct", "environment_projection_pct",
           "avg_dialogue_length", "interrupt_freq_per_100", "subtext_ratio", "direct_address_freq_per_100",
           "conjunction_freq_per_100", "transition_sentence_ratio",
           "action_verb_ratio", "mental_verb_ratio", "state_verb_ratio"}


def main(argv=None) -> int:
    if len(argv or sys.argv[1:]) < 2:
        print(__doc__.strip())
        return 2
    a, b = load(argv[0])
    c, d = load(argv[1])
    if not (a and c):
        print("error: 两张卡都需为新格式（含 frontmatter）", file=sys.stderr)
        return 2
    print("# 风格卡维度变化表")
    print("| 维度 | 卡A | 卡B | 差值 |")
    print("|---|---|---|---|")
    for dim in ("lexicon", "syntax", "rhythm", "rhetoric", "emotion_expression",
                "narrative", "dialogue_style", "cohesion", "verb_style"):
        da, dc = a.get(dim, {}), c.get(dim, {})
        for k in sorted(set(da) | set(dc)):
            va, vc = da.get(k), dc.get(k)
            if isinstance(va, (dict, list)) or isinstance(vc, (dict, list)):
                if va != vc:
                    print(f"| {dim}.{k} | {va} | {vc} | (结构/列表变化) |")
                continue
            if k in NUMERIC and isinstance(va, (int, float)) and isinstance(vc, (int, float)):
                diff = vc - va
                pct = f"{diff / va:+.0%}" if va else "—"
                print(f"| {dim}.{k} | {va} | {vc} | {pct} |")
            elif va != vc:
                print(f"| {dim}.{k} | {va or '—'} | {vc or '—'} | (定性变化) |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: 追加测试 + 跑绿 + Commit**

```python
def test_compare():
    print("[unit] compare-style")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        card = tmp / "settings" / "writing-style.md"
        t = card.read_text(encoding="utf-8").replace("avg_sentence_length: 0", "avg_sentence_length: 15")
        (tmp / "b.md").write_text(t, encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "compare-style.py"), str(card), str(tmp / "b.md")], cwd=str(TOOLS))
        check("compare exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        check("输出维度变化表", "avg_sentence_length" in r.stdout and "差值" in r.stdout)
```

```bash
git add tools/compare-style.py tools/test_style_distill.py
git commit -m "feat: compare-style.py 两卡维度变化表（F7）"
```

---

## Task 16: tools/mix-style.py

**Files:**
- Create: `tools/mix-style.py`
- Modify: `tools/test_style_distill.py`（追加 `test_mix` 段）

**Interfaces:**
- Consumes: 卡片 schema
- Produces: CLI `mix-style.py <cardA> <cardB> <wA> <wB> -o <out>` → 数值加权平均 + 定性节合并

- [ ] **Step 1: 写实现**

```python
#!/usr/bin/env python3
"""F8：混两张风格卡——数值加权平均 + 定性节合并。
用法: python mix-style.py <cardA> <cardB> <wA> <wB> -o <out.md>
数值字段加权平均；字符串/列表定性字段两边都保留（带来源标注）；out 由 style-distiller 做 LLM 定性合并后定稿。
"""

import sys
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

NUMERIC = {"adj_density_per_100", "adv_density_per_100", "four_phrase_freq_per_100",
           "name_pronoun_ratio", "avg_sentence_length", "single_sentence_paragraph_pct",
           "avg_sentences_per_paragraph", "question_ratio", "exclamation_ratio",
           "dialogue_pct", "action_pct", "environment_pct", "inner_thought_pct", "narration_pct",
           "metaphor_density_per_100", "direct_pct", "action_physiology_pct", "environment_projection_pct",
           "avg_dialogue_length", "interrupt_freq_per_100", "subtext_ratio", "direct_address_freq_per_100",
           "conjunction_freq_per_100", "transition_sentence_ratio",
           "action_verb_ratio", "mental_verb_ratio", "state_verb_ratio"}


def load(path: str):
    text = Path(path).read_text(encoding="utf-8")
    parts = text.split("---", 2)
    return (yaml.safe_load(parts[1]), parts[2]) if yaml and len(parts) == 3 else (None, text)


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) < 5 or "-o" not in argv:
        print(__doc__.strip())
        return 2
    a_path, b_path, wA, wB = argv[0], argv[1], float(argv[2]), float(argv[3])
    out = argv[argv.index("-o") + 1]
    fa, _ = load(a_path)
    fb, _ = load(b_path)
    if not (fa and fb):
        print("error: 两张卡都需为新格式", file=sys.stderr)
        return 2
    total = wA + wB
    merged = {}
    for dim in ("lexicon", "syntax", "rhythm", "rhetoric", "emotion_expression",
                "narrative", "dialogue_style", "cohesion", "verb_style"):
        merged[dim] = {}
        for k in sorted(set(fa.get(dim, {})) | set(fb.get(dim, {}))):
            va, vb = fa.get(dim, {}).get(k), fb.get(dim, {}).get(k)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and k in NUMERIC:
                merged[dim][k] = round((va * wA + vb * wB) / total, 2)
            elif va is None and vb is not None:
                merged[dim][k] = vb
            elif vb is None and va is not None:
                merged[dim][k] = va
            else:
                merged[dim][k] = [va, vb]  # 定性：两边保留，待 LLM 合并
    merged["profile_version"] = "1.0"
    merged["scene_type"] = fa.get("scene_type", "general")
    merged["confidence"] = min(100, int((fa.get("confidence", 0) * wA + fb.get("confidence", 0) * wB) / total))
    merged["last_updated"] = fa.get("last_updated", "")
    merged["locked"] = sorted(set(fa.get("locked") or []) | set(fb.get("locked") or []))
    fm = yaml.safe_dump(merged, allow_unicode=True, sort_keys=False, default_flow_style=False)
    body = ("# 混成风格卡\n\n（数值已加权平均；定性条目保留双方来源，由 style-distiller LLM 合并定性节后定稿。）\n")
    Path(out).write_text(f"---\n{fm}---\n{body}", encoding="utf-8")
    print(f"mix: {a_path}×{wA} + {b_path}×{wB} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 追加测试 + 跑绿 + Commit**

```python
def test_mix():
    print("[unit] mix-style")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        a = tmp / "settings" / "writing-style.md"
        t = a.read_text(encoding="utf-8").replace("avg_sentence_length: 0", "avg_sentence_length: 10")
        b = tmp / "b.md"
        b.write_text(t.replace("avg_sentence_length: 10", "avg_sentence_length: 30"), encoding="utf-8")
        out = tmp / "mix.md"
        r = run([sys.executable, str(TOOLS / "mix-style.py"), str(a), str(b), "0.5", "0.5",
                 "-o", str(out)], cwd=str(TOOLS))
        check("mix exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        import yaml as _y
        fm = _y.safe_load(out.read_text(encoding="utf-8").split("---", 2)[1])
        check("加权平均 10/30 → 20", fm["syntax"]["avg_sentence_length"] == 20.0,
              str(fm["syntax"]["avg_sentence_length"]))
```

```bash
git add tools/mix-style.py tools/test_style_distill.py
git commit -m "feat: mix-style.py 混卡（数值加权平均 + 定性合并）（F8）"
```

---

## Task 17: check-agents.py 卡片校验 + 全量回归

**Files:**
- Modify: `tools/check-agents.py`
- Test: `tools/test_style_distill.py` 全量

**Interfaces:**
- Consumes: 卡片 schema、inherits 约定
- Produces: `check-agents.py` 校验 style-distiller frontmatter + 卡片 YAML 合法 + inherits 引用存在

- [ ] **Step 1: DEPLOYED_PATTERNS 补风格资产**

在 `DEPLOYED_PATTERNS`（L46-55）追加：

```python
    re.compile(r"^settings/style-profiles/"),          # 分场景风格卡（含 genre-baselines/）
    re.compile(r"^settings/\.style-versions/"),        # 蒸馏版本快照
```

- [ ] **Step 2: 加卡片 YAML / inherits 校验函数**

在 `check_file` 之后新增，并在 `main()` 里调用：

```python
STYLE_CARD_SCENE_TYPES = {"general", "dialogue", "fight", "environment",
                          "inner-mono", "transition", "group-scene"}
STYLE_CARD_DIMS = ["lexicon", "syntax", "rhythm", "rhetoric", "emotion_expression",
                   "narrative", "dialogue_style", "cohesion", "verb_style"]


def check_style_card(path: Path) -> list:
    errors = []
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        return [f"{path.name}: 风格卡缺 frontmatter（需两对 ---）"]
    try:
        fm = yaml.safe_load(parts[1])
    except Exception as e:
        return [f"{path.name}: 卡片 frontmatter YAML 解析失败: {e}"]
    if not isinstance(fm, dict):
        return [f"{path.name}: 卡片 frontmatter 不是 map"]
    for k in ("profile_version", "scene_type", "confidence", "last_updated"):
        if k not in fm:
            errors.append(f"{path.name}: 卡片缺 {k}")
    st = fm.get("scene_type")
    if st not in STYLE_CARD_SCENE_TYPES:
        errors.append(f"{path.name}: scene_type={st!r} 不在枚举 {sorted(STYLE_CARD_SCENE_TYPES)}")
    conf = fm.get("confidence")
    if not isinstance(conf, int) or not (0 <= conf <= 100):
        errors.append(f"{path.name}: confidence 需为 0-100 整数（当前 {conf!r}）")
    for dim in STYLE_CARD_DIMS:
        if dim not in fm:
            errors.append(f"{path.name}: 卡片缺维度 {dim}")
    locked = fm.get("locked")
    if locked is not None and not isinstance(locked, list):
        errors.append(f"{path.name}: locked 需为列表")
    inh = fm.get("inherits")
    if inh:
        target = ROOT / "templates" / str(inh)
        if not target.exists() and not (ROOT / str(inh)).exists():
            errors.append(f"{path.name}: inherits 引用不存在: {inh}")
    return errors


def check_style_cards() -> list:
    errors = []
    base = ROOT / "templates" / "settings"
    for p in [base / "writing-style.md"] + sorted((base / "style-profiles").glob("*.md")):
        errors.extend(check_style_card(p))
    return errors
```

`main()` 末尾（返回前）调用并合并错误：

```python
    all_errors.extend(check_style_cards())
```

- [ ] **Step 3: 全量回归**

Run:
```bash
python tools/check-agents.py
python tools/test_style_distill.py
python tools/test_platforms.py
python tools/check-conflicts.py
python -m py_compile tools/*.py
```
Expected: 全部通过。check-agents 现在把 style-distiller 的 style-profiles/.style-versions 引用按白名单放行，并把模板卡 schema 校验纳入。

- [ ] **Step 4: Commit**

```bash
git add tools/check-agents.py
git commit -m "feat: check-agents 校验风格卡 YAML + inherits + style-profiles 白名单"
```

---

# 验收（Spec §13 六项）

## Task 18: 验收执行（C1-C6）

**Files:**
- Modify: `tools/test_style_distill.py`（追加 `test_acceptance` 段：C1/C4/C5 代码验收）
- Test: 本任务自身（C2/C3 为验收运行步骤，C6 为作者盲测）

**Interfaces:**
- Consumes: distill / update / check 三模式（Task 5/11/13）、迁移与部署（Task 4/8）、卡片 schema
- Produces: 六项验收结果表（C1-C6，每项 pass/fail + 证据）

- [ ] **Step 1: 追加 C1/C4/C5 代码验收到 test_style_distill.py**

```python
def _count_sents(text):
    return len([s for s in re.split(r"[。！？…；!?;]", text) if s.strip()])


def _count_chars(text):
    """仅去空白、保留引号——与 distill-style.py char_len 口径一致。"""
    return len(re.sub(r"\s", "", text))


def _count_quoted(text):
    n = inside = 0
    for ch in text:
        if ch in '“"「『':
            inside = True
        elif ch in '”"」』':
            inside = False
        elif inside and ch.strip():
            n += 1
    return n


def test_acceptance():
    print("[acceptance] C1/C4/C5")
    import yaml as _y
    # ---- C1: 核心参数 vs 人工计数，偏差 ≤15%（需 jieba 环境）----
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # 构造可人工点计的样本：3 组 × 3 句（叙述/转折/对话），形容词与连接词已知
        lines = [
            "寒冷的夜晚一片死寂，空旷的街道异常安静。",
            "然而寒风刺骨，因此他加快脚步，却仍感到浑身冰冷。",
            "“你终于来了。”他低声说，声音却异常微弱。",
        ]
        txt = "\n\n".join(lines * 3)
        sample = tmp / "c1.md"
        sample.write_text(txt, encoding="utf-8")
        p = tmp / "c1.yml"
        run([sys.executable, str(TOOLS / "distill-style.py"), "distill",
             "-o", str(p), str(sample)], cwd=str(TOOLS))
        d = _y.safe_load(p.read_text(encoding="utf-8"))["distill"]
        total = _count_chars(txt)
        manual = {
            "avg_sentence_length": total / _count_sents(txt),
            "dialogue_pct": 100 * _count_quoted(txt) / total,
            "conjunction_freq_per_100": 100 * sum(txt.count(w) for w in ("然而", "因此", "却")) / total,
            "adj_density_per_100": 100 * sum(txt.count(w)
                                             for w in ("寒冷", "死寂", "空旷", "安静", "刺骨", "冰冷", "微弱")) / total,
        }
        for k, manual_v in manual.items():
            got = (d["syntax"].get("avg_sentence_length") if k == "avg_sentence_length"
                   else d["rhythm"].get("dialogue_pct") if k == "dialogue_pct"
                   else d["cohesion"].get("conjunction_freq_per_100")
                   if k == "conjunction_freq_per_100"
                   else d["lexicon"].get("adj_density_per_100"))
            ok = got is not None and manual_v > 0 and abs(got - manual_v) / manual_v <= 0.15
            check(f"C1 {k} 偏差≤15% (manual={manual_v:.2f} got={got})", ok)
    # ---- C4: 连续归档 5 章 → confidence≥70、参数波动<10% ----
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        card = tmp / "settings" / "writing-style.md"
        text = card.read_text(encoding="utf-8")
        # 造 1250 字样本蒸馏出的源卡（confidence 基线 20+25）
        sample = tmp / "s.md"
        # ≥1250 字：confidence 基线 = 20 + min(40, L/50=26) = 46；5 章后 +25 → 71
        sample.write_text(("他快步走过长廊，推开厚重的木门，寒气扑面而来。\n\n") * 60, encoding="utf-8")
        p = tmp / "s.yml"
        run([sys.executable, str(TOOLS / "distill-style.py"), "distill",
             "-o", str(p), str(sample)], cwd=str(TOOLS))
        src = _y.safe_load(p.read_text(encoding="utf-8"))["distill"]
        text = text.replace("source_sample_length: 0", f"source_sample_length: {src['source_sample_length']}")
        text = text.replace("confidence: 0", f"confidence: {src['confidence']}")
        text = text.replace("avg_sentence_length: 0",
                            f"avg_sentence_length: {src['syntax']['avg_sentence_length']}")
        card.write_text(text, encoding="utf-8")
        arch = tmp / "archives"
        arch.mkdir(parents=True, exist_ok=True)
        for i in range(1, 6):  # 5 章，句长一致（每句 18 字），验证滑动平均收敛
            (arch / f"vol-1-ch-{i}.md").write_text(
                "他走过长廊，推开木门，寒气扑面而来。\n\n" * 20, encoding="utf-8")
        out = tmp / "settings" / "writing-style-new.md"
        for i in range(1, 6):
            run([sys.executable, str(TOOLS / "distill-style.py"), "update",
                 "-c", str(card), "-o", str(out), "--project", str(tmp),
                 str(arch / f"vol-1-ch-{i}.md")], cwd=str(TOOLS))
            card.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
        fm = _y.safe_load(out.read_text(encoding="utf-8").split("---", 2)[1])
        check("C4 5 章后 confidence≥70", fm["confidence"] >= 70, f"got {fm['confidence']}")
        v = fm["syntax"]["avg_sentence_length"]
        check("C4 参数波动<10%（收敛到章稳态 18 的 10% 内）", abs(v - 18) / 18 <= 0.10, f"got {v}")
    # ---- C5: 现有项目升级不报错 + 旧卡自动迁移 ----
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        (tmp / "settings" / "writing-style.md").write_text(
            "# 写作风格\n\n## role（叙事身份）\n\n第三人称限知\n\n"
            "## core_principles（不可违背的写作信条）\n\n- 不写废话\n\n"
            "## possible_mistakes（AI 易犯错误）\n\n- 模板腔\n\n"
            "## depiction_techniques（描写层次和手法）\n\n动作推进\n", encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        check("C5 升级 init exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        rs = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp)], cwd=str(tmp))
        check("C5 升级 sync exit 0", rs.returncode == 0, (rs.stdout + rs.stderr)[-400:])
        card = tmp / "settings" / "writing-style.md"
        body = card.read_text(encoding="utf-8")
        check("C5 新格式", body.startswith("---"))
        check("C5 内容零损失", all(k in body for k in ("第三人称限知", "不写废话", "模板腔", "动作推进")))
```

- [ ] **Step 2: 跑 C1/C4/C5，确认绿**

Run: `python tools/test_style_distill.py`
Expected: `[acceptance] C1/C4/C5` 段全 ok（若无 jieba，adj_density 记 None，C1 形容词项按降级语义报告 FAIL 而非跳过——该环境需装 jieba 再验收）。

- [ ] **Step 3: C2 / C3 验收运行（LLM 生成 + check）**

按以下步骤人工/agent 执行并记录结果：

1. 准备一张 confidence≥51 的蒸馏主卡（用 C1 样本蒸馏即可，confidence≈45-50；若不足，把 sample_length 加厚到 ≥1600 字或直接手填 confidence=60）。
2. **C2**：基于主卡生成 3 段同场景正文（≥300 字/段），对每段跑 `python tools/distill-style.py check -c <卡> <段>`。通过条件：3 段客观维度 `|dev|` 全部 ≤ 20%。
3. **C3**：对同一素材分别用对话场景卡与战斗场景卡各生成 1 段，跑 `check`，再 `compare-style.py` 对比两段实测维度。通过条件：句长 / 对话占比 / 动词力度至少 2 项差异 ≥ 容差。
4. 把三张结果表记入本 Task 的验收报告（提交时附在 commit message 或独立 `docs/superpowers/acceptance-style-distiller.md`）。

- [ ] **Step 4: C6 作者盲测（内容任务，收尾前补）**

作者完成三套标杆卡数值后，按 spec §13-6 组织盲测（正确率 ≥70%）。代码不测，此步在收尾（Task 19）前确认状态。

- [ ] **Step 5: Commit**

```bash
git add tools/test_style_distill.py
git commit -m "test: 验收 C1/C4/C5 固化 + C2/C3 验收运行步骤"
```

---

# 收尾

## Task 19: 文档同步 + 版本 bump

**Files:**
- Modify: `ARCHITECTURE.md`、`AGENTS.md`、`SKILL.md`、`templates/CLAUDE.md`、`README.md`、`docs/superpowers/specs/2026-08-10-style-distiller-design.md`（状态补"已实施"）

- [ ] **Step 1: ARCHITECTURE.md — 9 agent + 风格写白名单例外**

- 1.3 主 Agent 与子 Agent：`子 Agent × 7` → `子 Agent × 8`（总量 8 → 9），清单加 `style-distiller`。
- 1.4 分工表加一行：`style-distiller → 风格蒸馏（脚本统计 + LLM 语义 → 写风格主卡/场景卡/版本快照）`。
- 1.5 调度架构表加行：`setup → style-distiller（style-distill-order.md，作者提供风格样本时）`、`archive → style-distiller（style-update-order.md，每次归档后增量）`。
- settings 写入规则处标注例外：`例外：style-distiller 拥有 settings/writing-style.md、settings/style-profiles/、settings/.style-versions/ 专属写白名单，其余 settings 仍归 updater`。

- [ ] **Step 2: AGENTS.md / SKILL.md / templates/CLAUDE.md / README.md**

- AGENTS.md：agents 清单加 style-distiller；reasonix 相关提及 10 → 11 个 SKILL.md（若有）。
- SKILL.md：reasonix `10 个 SKILL.md` 提及 → 11；agent 数量相关描述 8 → 9（按现有行定位，grep `10 个 SKILL.md`、`8 个`）。
- templates/CLAUDE.md：「8 个 agent」→「9 个 agent」。
- README.md：功能列表补 style-distiller；版本号区与 bump 一致。

- [ ] **Step 3: 版本 bump（代码层变更；不打 tag）**

更新涉及的硬编码版本位置（`init.py` status skill_version、`templates/story.md`、`templates/.agent/status.md`、`SKILL.md` 的 skill_version，grep `4.0` 定位），提交随 PR review：

```bash
git add -A
git commit -m "docs: 9 agent 架构 + 版本 bump"
```

> ⚠️ **不在实施/验收中自动打 tag**：`git tag v4.13.0` 不作为自动步骤执行。版本 tag 由 PR #91 review + 合并后由作者/发布流程创建（`gh release` 或手动 tag），确保任何版本变更都经过 PR 审阅。

- [ ] **Step 4: 全量回归 + spec 状态更新**

Run: `python tools/test_style_distill.py && python tools/test_platforms.py && python tools/check-agents.py && python tools/check-conflicts.py`
Expected: 全绿。把 spec 头部「状态：已确认」补一行「实施：已按 2026-08-11 计划落地」，提交（`git add -f docs/...`）。

```bash
git add -f docs/superpowers/plans/2026-08-11-style-distiller.md docs/superpowers/specs/2026-08-10-style-distiller-design.md
git commit -m "docs: style-distiller 实施计划 + spec 实施状态"
```

---

## 自检记录

- **验收覆盖：** Spec §13 六项 → 验收标准节逐项映射。C1/C4/C5 固化为 `test_style_distill.py::test_acceptance`（Task 18，纳入 CI）；C2/C3 为 Task 18 验收运行步骤（LLM 生成 + check）；C6 为作者盲测（内容任务，收尾前补）。C1 的形容词密度依赖 jieba POS 打标，属 spec §14 已知风险（偏差超阈值 → 置信度/容差/人工校准兜底）。
- **迁移机制修正（2026-08-11 实施前发现）**：原 Task 4 有 2 个缺陷——(1) `create_skeleton` 的 `copy2` 无条件覆盖 + `seed_settings_from_genre` 无条件重写，使 re-init 时旧卡在 migrate 运行前即被销毁；(2) `_md_section(text, "role")` 正则精确匹配不中带中文后缀的旧标题 `## role（叙事身份）`。已修正为：migrate 前置到 main() 最前 + create_skeleton 跳过已存在文件 + seed 跳过已填卡 + 按完整旧标题提取。此修正使 `test_migration` 全绿、C5 验收可达。
- **Spec 覆盖：** §4（卡片格式）→ Task 1-4；§5（蒸馏引擎）→ Task 5/6；§6（prompt-crafter 注入）→ Task 7；§7（F4 场景卡 + 题材基线）→ Task 10；§8（F5 增量）→ Task 11/12；§9（F6 Gate G）→ Task 13/14；§10（F7/F8）→ Task 15/16；§11（工程清单：init/sync/check-agents/test_platforms/requirements/CI/agents/novel-agent/skills/knowledge/templates/docs）→ Task 4/8/9/12/14/17/19；§13 验收标准 → Task 18 + 各 task 测试；§14 风险（jieba 降级、注入占空间、增量漂移、迁移零损失）→ Task 5 降级、Task 7 稀疏注入、Task 11 α+locked+备份、Task 4 迁移映射。
- **占位符扫描：** 无 TBD/TODO；所有代码步骤给了完整实现。唯一「待填充」是题材基线数值（P1 占位，内容由作者蒸馏/盲测填充，属内容任务非代码任务）。
- **类型一致性：** `build_partial(texts)->dict`、`compute_confidence(int,int)->int`、`tolerance_for(int)->float`、`load_card(path)->(dict|None,str)`、`dump_card(dict,str)->str`、`sliding_alpha(int)->float`、CLI `distill/update/check` 三个子命令，Task 5/11/13 签名一致；卡片 9 大维度键名在模板（Task 2）、spec（Task 3）、脚本（Task 5/11/13）、check-agents（Task 17）四处一致。
- **待定项（执行时确认）：** anti-ai.md 当前 tools 是否含 Bash（Task 14 Step 4 现场补）；deploy_knowledge 对 knowledge/style-distill/ 的递归部署路径（Task 14 Step 4 兜底）；test_platforms 中 reasonix 引用改写断言在新 agent 下是否需微调（Task 8 Step 5 现场修正）。
