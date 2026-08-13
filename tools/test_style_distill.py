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

from style_common import force_utf8
force_utf8()

from test_util import check, load_module, summary, exit_code

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
    mod = load_module("check_agents", TOOLS / "check-agents.py")
    main_tpl = REPO / "templates/settings/writing-style.md"
    errs = mod.check_style_card(main_tpl)
    check("主卡模板过卡校验", not errs, "; ".join(errs))
    scenes = sorted((REPO / "templates/settings/style-profiles").glob("*.md"))
    check("场景卡目录非空", len(scenes) > 0, "style-profiles/ 为空——校验静默通过")   # review #49
    for scene in scenes:
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
    check("anti-ai 含指令遵循验收", "指令遵循" in skill, "缺指令遵循字样")
    check("anti-ai 含案例 2 验收", "案例 2" in skill, "缺案例 2 字样")
    check("anti-ai 引用 verify-checklist", "verify-checklist" in skill, "缺 verify-checklist 引用")   # review #49 拆弱断言
    check("anti-ai 无 distill-style.py", "distill-style.py" not in skill)
    check("anti-ai 无 gate-g-checklist", "gate-g-checklist" not in skill)

def test_dual_mode():
    import tempfile, yaml
    mod = load_module("check_agents", TOOLS / "check-agents.py")
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

def test_unit_convergence():
    """决策 A 修正：占比字段一律 0-100 百分数（旧引擎一位小数百分数 13.4/2.31 通过；
    0.3=0.3% 不乘 100；1.5 是合法百分数）。越界值（>100）拒绝。"""
    import tempfile, yaml
    mod = load_module("check_agents", TOOLS / "check-agents.py")
    base = REPO / "templates/settings/writing-style.md"

    fm = yaml.safe_load(base.read_text(encoding="utf-8").split("---", 2)[1])
    fm["confidence"] = 75
    fm["syntax"]["question_ratio"] = 13.4          # 旧引擎一位小数百分数
    fm["syntax"]["exclamation_ratio"] = 7.2
    fm["syntax"]["single_sentence_paragraph_pct"] = 46.1
    fm["dialogue_style"]["subtext_ratio"] = 22.5
    fm["lexicon"]["name_pronoun_ratio"] = 2.31     # 旧引擎人名/代词比值
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "writing-style.md"
        p.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        errs = mod.check_style_card(p)
        check("决策A：旧引擎 0-100 一位小数百分数卡通过校验", not errs, "; ".join(errs))

    fm2 = yaml.safe_load(base.read_text(encoding="utf-8").split("---", 2)[1])
    fm2["confidence"] = 75
    fm2["syntax"]["question_ratio"] = 150
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "writing-style.md"
        p.write_text("---\n" + yaml.safe_dump(fm2, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        errs = mod.check_style_card(p)
        check("决策A：question_ratio=150 拒绝（超 0-100）", any("question_ratio" in e for e in errs), errs)

    fm3 = yaml.safe_load(base.read_text(encoding="utf-8").split("---", 2)[1])
    fm3["confidence"] = 75
    fm3["dialogue_style"]["subtext_ratio"] = 1.5
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "writing-style.md"
        p.write_text("---\n" + yaml.safe_dump(fm3, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        errs = mod.check_style_card(p)
        check("决策A：subtext_ratio=1.5 通过（1.5% 合法，旧引擎可产出）", not errs, "; ".join(errs))

def test_scalar_percent_validation():
    """校验端补齐：节奏单桶 >100、transition_sentence_ratio 越界、preferred_words 类型、self-inherits。"""
    import tempfile, yaml
    mod = load_module("check_agents", TOOLS / "check-agents.py")
    base = REPO / "templates/settings/writing-style.md"

    def _check(card_mut, contains):
        fm = yaml.safe_load(base.read_text(encoding="utf-8").split("---", 2)[1])
        fm["confidence"] = 75
        card_mut(fm)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "writing-style.md"
            p.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
            return mod.check_style_card(p)

    errs = _check(lambda fm: fm["rhythm"].update({"dialogue_pct": 110, "action_pct": 0, "environment_pct": 0, "inner_thought_pct": 0, "narration_pct": 0}), "rhythm")
    check("节奏单桶 >100 拒绝（dialogue_pct:110）", any("rhythm.dialogue_pct" in e for e in errs), errs)
    errs = _check(lambda fm: fm["cohesion"].update({"transition_sentence_ratio": 120}), "transition")
    check("transition_sentence_ratio>100 拒绝", any("transition_sentence_ratio" in e for e in errs), errs)
    errs = _check(lambda fm: fm["lexicon"].update({"preferred_words": "好想死"}), "preferred")
    check("preferred_words 非列表拒绝", any("preferred_words" in e for e in errs), errs)
    errs = _check(lambda fm: fm["lexicon"].update({"banned_words": "宛如"}), "banned")
    check("banned_words 非列表拒绝", any("banned_words" in e for e in errs), errs)

    # 自引用 inherits 被单卡校验检出
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "writing-style.md"
        fm = yaml.safe_load(base.read_text(encoding="utf-8").split("---", 2)[1])
        fm["confidence"] = 75
        fm["scene_type"] = "dialogue"
        fm["override"] = {"syntax": {"avg_sentence_length": 12}}
        fm["inherits"] = "writing-style.md"
        p.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        errs = mod.check_style_card(p)
        check("自引用 inherits 拒绝", any("自引用" in e for e in errs), errs)

def test_inherits_cycle_detected():
    """继承环（A→B→A）被 check_style_cards 跨文件检出。"""
    import tempfile, yaml
    mod = load_module("check_agents", TOOLS / "check-agents.py")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        tpl = root / "templates" / "settings"
        tpl.mkdir(parents=True)
        (tpl / "writing-style.md").write_text("---\nprofile_version: '1.0'\nscene_type: general\nconfidence: 70\nlast_updated: ''\nsource_sample_length: 100\n---\n", encoding="utf-8")
        sp = tpl / "style-profiles"; sp.mkdir()
        fm_a = {"profile_version": "1.0", "scene_type": "dialogue", "confidence": 70, "last_updated": "", "source_sample_length": 100, "override": {}, "inherits": "b.md"}
        fm_b = {"profile_version": "1.0", "scene_type": "dialogue", "confidence": 70, "last_updated": "", "source_sample_length": 100, "override": {}, "inherits": "a.md"}
        (sp / "a.md").write_text("---\n" + yaml.safe_dump(fm_a, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        (sp / "b.md").write_text("---\n" + yaml.safe_dump(fm_b, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        old_root = mod.ROOT
        mod.ROOT = root
        try:
            errs = mod.check_style_cards()
        finally:
            mod.ROOT = old_root
        check("A→B→A 继承环被检出", any("继承环" in e for e in errs), errs)

def test_project_cards_skips_analysis():
    """check_project_cards 排除 analysis/（量化表+建模规则+作者画像，无 frontmatter），
    防误报「风格卡缺 frontmatter」。"""
    import tempfile
    mod = load_module("check_agents", TOOLS / "check-agents.py")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "settings" / "style-profiles" / "analysis").mkdir(parents=True)
        (root / "settings" / "style-profiles" / "analysis" / "general.md").write_text(
            "# 分析稿\n\n量化表全文……\n\n## 作者画像\n\n这是你的文风……\n", encoding="utf-8")
        (root / "settings" / "writing-style.md").write_text(
            "---\nprofile_version: '1.0'\nscene_type: general\nconfidence: 70\nlast_updated: ''\nsource_sample_length: 100\n---\n",
            encoding="utf-8")
        (root / "settings" / "style-profiles" / "dialogue.md").write_text(
            "---\nprofile_version: '1.0'\nscene_type: dialogue\nconfidence: 70\nlast_updated: ''\nsource_sample_length: 100\noverride: {}\n---\n",
            encoding="utf-8")
        errs = mod.check_project_cards(root)
        check("check_project_cards 不扫 analysis/（无误报）",
              not any("general.md" in e for e in errs), errs)
        check("check_project_cards 仍校验真实场景卡（dialogue）",
              not any("dialogue.md" in e for e in errs), errs)

def test_verify_doc_code_alignment():
    """#11 修复交叉断言：verify-checklist.md 文档措辞与 style_verify.py 代码行为一致。
    文档违反白名单令牌（`` `true/是/yes/1/违反` ``）= 代码 VIOLATED_STRINGS；
    文档「其余字符串→不违反」= 代码对白名单外字符串返回 False，且尾部标点被剥（是。→是）。"""
    import re
    import style_verify
    doc = (REPO / "knowledge/style-distill/prompt-templates/verify-checklist.md").read_text(encoding="utf-8")
    m = re.search(r"`([^`]+)` → 违反", doc)
    check("verify-checklist 含违反白名单行", m is not None, "未找到 `...` → 违反 措辞")
    if m:
        doc_tokens = set(m.group(1).split("/"))
        check("文档白名单 = 代码 VIOLATED_STRINGS",
              doc_tokens == set(style_verify.VIOLATED_STRINGS),
              f"doc={sorted(doc_tokens)} vs code={sorted(style_verify.VIOLATED_STRINGS)}")
    check("文档「其余字符串→不违反」= 代码行为",
          style_verify._is_violated("其余字符串") is False and style_verify._is_violated("是。") is True,
          style_verify._is_violated("是。"))

def run_all():
    test_feature_extract(); test_schema_templates(); test_retire_clean()
    test_reroll_contract(); test_anti_ai_verify(); test_dual_mode(); test_unit_convergence()
    test_scalar_percent_validation(); test_inherits_cycle_detected()
    test_project_cards_skips_analysis()
    test_verify_doc_code_alignment()
    print(f"\n{summary()}")
    return exit_code()

if __name__ == "__main__":
    sys.exit(run_all())
