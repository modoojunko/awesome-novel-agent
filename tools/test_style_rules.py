#!/usr/bin/env python3
"""style_render + style_verify 规则单测（TDD Task 4，长期保留）。

用法: python tools/test_style_rules.py
返回码 0 = 全部通过。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 强制 UTF-8 输出，避免 Windows GBK 控制台报错（AGENTS.md:79）
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
from style_render import range_for, enum_zh, pct_zh, _pct, _num, _flatten_dists, render_card, SCENE_INJECTION
from style_verify import verdict, should_reroll, pick_best, format_report, _is_violated, VIOLATED_STRINGS
from test_util import check, summary, exit_code

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
    "cohesion": {"conjunction_freq_per_100": 2.6, "transition_sentence_ratio": 4, "paragraph_bridge_style": "action"},
    "verb_style": {"action_verb_ratio": 35, "mental_verb_ratio": 40, "state_verb_ratio": 25, "strength": "medium"},
    "hard_constraints": ["内心独白必须用引号包裹"],
    "soft_guidance": ["整体基调：轻松吐槽向"],
    "few_shot_examples": [{"type": "inner_thought", "text": "好想死啊", "reason": "口头禅式吐槽"}],
}

def test_range_for():
    check("5.8@75 → '5-6'", range_for(5.8, 75) == "5-6", range_for(5.8, 75))
    check("16@75 → '14-18'", range_for(16, 75) == "14-18", range_for(16, 75))
    check("5.8@50 → 区间加宽 '5-7'(±20%)", range_for(5.8, 50) == "5-7", range_for(5.8, 50))
    check("5.8@90 → '5-6'(±10%)", range_for(5.8, 90) == "5-6", range_for(5.8, 90))
    check("零值 → '0'（不虚构 0-1）", range_for(0, 75) == "0", range_for(0, 75))
    check("极低值 0.2@75 → '0'（单值）", range_for(0.2, 75) == "0", range_for(0.2, 75))
    check("_num(True) → 0（bool 排除）", _num(True) == 0, _num(True))
    check("_num(nan) → 0（非有限过滤）", _num(float("nan")) == 0, _num(float("nan")))
    check("_num(inf) → 0", _num(float("inf")) == 0, _num(float("inf")))

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

def test_pct_normalize():
    # 决策 A 修正：0-100 百分数语义，无 0-1 分数 ×100 假设（旧引擎产出 0-100 一位小数百分数）
    check("13.4 → 13.4（旧引擎一位小数百分数）", _pct(13.4) == 13.4, _pct(13.4))
    check("0.30 → 0.3（低百分数，不做 ×100）", _pct(0.30) == 0.3, _pct(0.30))
    check("0.99 → 0.99", _pct(0.99) == 0.99, _pct(0.99))
    check("2.31 → 2.31（旧引擎人名/代词比值）", _pct(2.31) == 2.31, _pct(2.31))
    check("整数原样 23 → 23", _pct(23) == 23, _pct(23))
    check("23.0 → 23（整数值收敛为 int）", _pct(23.0) == 23, _pct(23.0))
    check("0 → 0", _pct(0) == 0, _pct(0))
    check("字符串 '13.4' → 13.4", _pct("13.4") == 13.4, _pct("13.4"))
    check("None → 0", _pct(None) == 0, _pct(None))
    check("非法串 → 0", _pct("abc") == 0, _pct("abc"))
    check("越界 150 → 0（防御收敛）", _pct(150) == 0, _pct(150))
    check("bool True → 0（bool 排除）", _pct(True) == 0, _pct(True))

def test_render_percent_normalize():
    # 决策 A 修正：旧引擎 0-100 一位小数百分数按原样渲染（13.4%），不做 ×100
    legacy = dict(CARD)
    legacy["syntax"] = dict(CARD["syntax"])
    legacy["syntax"]["question_ratio"] = 13.4
    legacy["syntax"]["exclamation_ratio"] = 7.2
    legacy["dialogue_style"] = dict(CARD["dialogue_style"])
    legacy["dialogue_style"]["subtext_ratio"] = 22.5
    lo = render_card(legacy)
    check("旧百分数 question_ratio 13.4 → 13.4%（少量）", any("疑问句占比：13.4%（少量）" in x for x in lo["句式"]), lo.get("句式"))
    check("旧百分数 exclamation_ratio 7.2 → 7.2%", any("感叹句占比：7.2%" in x for x in lo["句式"]), lo.get("句式"))
    check("旧百分数 subtext_ratio 22.5 → 22.5%", any("潜台词占比：22.5%" in x for x in lo["对话风格"]), lo.get("对话风格"))
    out = render_card(CARD)
    check("整数 question_ratio 13 → 渲染 13%（少量）", any("疑问句占比：13%（少量）" in x for x in out["句式"]), out.get("句式"))
    check("整数 subtext_ratio 22 → 渲染 22%", any("潜台词占比：22%" in x for x in out["对话风格"]), out.get("对话风格"))
    check("密度字段不受 _pct 归一（每百字 X）", any("每百字 5-6" in x for x in out["词汇"]), out.get("词汇"))

def test_render_percent_all_fields_consistent():
    # 全部标量百分比字段统一 0-100 展示（旧引擎一位小数百分数不乘 100、不原样吞掉）
    legacy = dict(CARD)
    legacy["lexicon"] = dict(CARD["lexicon"]); legacy["lexicon"]["name_pronoun_ratio"] = 2.31   # 旧引擎人名/代词比值
    legacy["syntax"] = dict(CARD["syntax"]); legacy["syntax"]["single_sentence_paragraph_pct"] = 46.1
    legacy["rhythm"] = dict(CARD["rhythm"]); legacy["rhythm"]["dialogue_pct"] = 48.2
    legacy["emotion_expression"] = dict(CARD["emotion_expression"])
    legacy["emotion_expression"]["direct_pct"] = 15.1; legacy["emotion_expression"]["inner_monologue_pct"] = 34.8
    legacy["verb_style"] = dict(CARD["verb_style"]); legacy["verb_style"]["action_verb_ratio"] = 35.4
    lo = render_card(legacy)
    check("单句段 46.1 → 46.1%", any("单句段占比 ≥ 46.1%" in x for x in lo["句式"]), lo.get("句式"))
    check("对话 48.2 → 48.2%（近一半）", any("对话约 48.2%（近一半）" in x for x in lo["节奏"]), lo.get("节奏"))
    check("直接陈述 15.1 → 15.1%", any("直接陈述 15.1%" in x for x in lo["情绪表达"]), lo.get("情绪表达"))
    check("内心独白 34.8 → 34.8%", any("内心独白 34.8%" in x for x in lo["情绪表达"]), lo.get("情绪表达"))
    check("动词动作 35.4 → 35.4%", any("动作 35.4%" in x for x in lo["句式"]), lo.get("句式"))
    check("过渡句 4 → 4%（cohesion 渲染补齐）", any("过渡句占比：4%" in x for x in lo["衔接"]), lo.get("衔接"))
    check("名称比值 2.31 → 2.31（不乘 100）", any("人名/代词使用比例 2.31" in x for x in lo["词汇"]), lo.get("词汇"))

def test_render_density_skip_unmeasured():
    # 缺密度键 = 未测 → 不注入（防 or 0 把未测当实测 0）
    sparse = dict(CARD)
    sparse["lexicon"] = dict(CARD["lexicon"])
    sparse["lexicon"].pop("adj_density_per_100")
    out = render_card(sparse)
    check("缺形容词密度键不注入", not any("形容词密度" in x for x in out["词汇"]), out.get("词汇"))
    check("副词密度仍在", any("副词密度：每百字 3-4" in x for x in out["词汇"]), out.get("词汇"))

def test_render_override_guard():
    # 未合并场景卡（override-only）→ 明确报错，防静默全零渲染（spec §6.3）
    scene = {"confidence": 75, "scene_type": "dialogue",
             "override": {"lexicon": {"adj_density_per_100": 5.8}, "dialogue_style": {"subtext_ratio": 22}},
             "inherits": "writing-style.md"}
    try:
        render_card(scene, "dialogue")
        check("未合并场景卡应 raise ValueError", False, "no raise")
    except ValueError:
        check("未合并场景卡 raise ValueError", True)

def test_flatten_dists_clean():
    check("负值桶丢弃", _flatten_dists({"short_le_8": -5}) == [], _flatten_dists({"short_le_8": -5}))
    check("非法字符串桶丢弃", _flatten_dists({"short_le_8": "abc"}) == [], _flatten_dists({"short_le_8": "abc"}))
    check("字符串数值收敛（'35' → 35%）", _flatten_dists({"short_le_8": "35"}) == ["短句（≤8字）占比 35%"], _flatten_dists({"short_le_8": "35"}))
    check("0.5 合法桶保留", _flatten_dists({"short_le_8": 0.5}) == ["短句（≤8字）占比 0.5%"], _flatten_dists({"short_le_8": 0.5}))
    check("nan 桶丢弃", _flatten_dists({"short_le_8": float("nan")}) == [], _flatten_dists({"short_le_8": float("nan")}))

def test_verify_string_bool():
    # #11 修复：字符串布尔收敛——剥尾部标点后按白名单匹配（是。→是），白名单外一律不违反
    check("'是。' → 违反", _is_violated("是。") is True, _is_violated("是。"))
    check("'违反。' → 违反", _is_violated("违反。") is True, _is_violated("违反。"))
    check("'true。' → 违反", _is_violated("true。") is True, _is_violated("true。"))
    check("'yes。' → 违反", _is_violated("yes。") is True, _is_violated("yes。"))
    check("'是！' → 违反", _is_violated("是！") is True, _is_violated("是！"))
    check("'YES' → 违反", _is_violated("YES") is True, _is_violated("YES"))
    check("'否。' → 不违反", _is_violated("否。") is False, _is_violated("否。"))
    check("'false' → 不违反", _is_violated("false") is False, _is_violated("false"))
    check("'其余字符串' → 不违反", _is_violated("其余字符串") is False, _is_violated("其余字符串"))
    check("None → 不违反", _is_violated(None) is False, _is_violated(None))
    check("bool True/False 原样", _is_violated(True) is True and _is_violated(False) is False)
    check("VIOLATED_STRINGS 为文档白名单 5 令牌", VIOLATED_STRINGS == frozenset({"true", "是", "yes", "1", "违反"}))

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

def test_verify_pick_best_coerce():
    # 字符串条数收敛（LLM 可能输出 "3"）：混合 int/str 不崩、全 str 按数值选（非字典序）
    check("混合 int/str 不崩且选对", pick_best([{"violated": 3}, {"violated": "1"}])["violated"] in (1, "1"))
    check("全字符串按数值取最少（10 vs 3 → 3）", pick_best([{"violated": "10"}, {"violated": "3"}])["violated"] == "3")
    check("None violated → 0", pick_best([{"violated": None}])["violated"] == 0 or pick_best([{"violated": None}])["violated"] is None)

def test_verify_report():
    r = format_report([{"no": 1, "require": "禁'宛如'", "evidence": "出现1次", "violated": True, "advice": "替换"}])
    check("含表头", "原文要求" in r, r)
    check("含结论 FAIL 与汇总", "FAIL" in r and "1/1" in r, r)

test_range_for(); test_enum_zh(); test_pct_zh(); test_scene_injection()
test_render_card(); test_render_card_verb(); test_render_card_sparse(); test_render_card_fallback()
test_pct_normalize(); test_render_percent_normalize(); test_render_percent_all_fields_consistent()
test_render_density_skip_unmeasured(); test_render_override_guard(); test_flatten_dists_clean()
test_verify_verdict(); test_verify_reroll(); test_verify_pick_best(); test_verify_pick_best_coerce()
test_verify_report(); test_verify_string_bool()
print(f"\n{summary()}")
sys.exit(exit_code())
