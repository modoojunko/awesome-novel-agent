#!/usr/bin/env python3
"""style_render + style_verify 规则单测（TDD Task 4，长期保留）。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from style_render import range_for, enum_zh, pct_zh, _pct, render_card, SCENE_INJECTION
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
    "cohesion": {"conjunction_freq_per_100": 2.6, "transition_sentence_ratio": 0.04, "paragraph_bridge_style": "action"},
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
    check("0.30 → 30", _pct(0.30) == 30, _pct(0.30))
    check("0.28 → 28", _pct(0.28) == 28, _pct(0.28))
    check("0.99 → 99", _pct(0.99) == 99, _pct(0.99))
    check("0.25 → 25", _pct(0.25) == 25, _pct(0.25))
    check("整数原样 23 → 23", _pct(23) == 23, _pct(23))
    check("0 → 0", _pct(0) == 0, _pct(0))
    check("字符串分数 '0.30' → 30", _pct("0.30") == 30, _pct("0.30"))
    check("None → 0", _pct(None) == 0, _pct(None))
    check("非法串 → 0", _pct("abc") == 0, _pct("abc"))

def test_render_percent_normalize():
    legacy = dict(CARD)
    legacy["lexicon"] = dict(CARD["lexicon"])
    legacy["lexicon"]["name_pronoun_ratio"] = 0.99                    # 旧 jieba 单值分数
    legacy["syntax"] = dict(CARD["syntax"])
    legacy["syntax"]["question_ratio"] = 0.30
    legacy["syntax"]["exclamation_ratio"] = 0.28
    legacy["dialogue_style"] = dict(CARD["dialogue_style"])
    legacy["dialogue_style"]["subtext_ratio"] = 0.25
    lo = render_card(legacy)
    check("分数 question_ratio 0.30 → 渲染 30%（一部分）", any("疑问句占比：30%（一部分）" in x for x in lo["句式"]), lo.get("句式"))
    check("分数 exclamation_ratio 0.28 → 渲染 28%", any("感叹句占比：28%" in x for x in lo["句式"]), lo.get("句式"))
    check("分数 name_pronoun_ratio 0.99 → 渲染 99%", any("人名/代词使用比例 99%" in x for x in lo["词汇"]), lo.get("词汇"))
    check("分数 subtext_ratio 0.25 → 渲染 25%", any("潜台词占比：25%" in x for x in lo["对话风格"]), lo.get("对话风格"))
    out = render_card(CARD)
    check("整数 question_ratio 13 → 渲染 13%（少量）", any("疑问句占比：13%（少量）" in x for x in out["句式"]), out.get("句式"))
    check("整数 subtext_ratio 22 → 渲染 22%", any("潜台词占比：22%" in x for x in out["对话风格"]), out.get("对话风格"))
    check("密度字段不受 _pct 归一（每百字 X）", any("每百字 5-6" in x for x in out["词汇"]), out.get("词汇"))

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

def test_verify_report():
    r = format_report([{"no": 1, "require": "禁'宛如'", "evidence": "出现1次", "violated": True, "advice": "替换"}])
    check("含表头", "原文要求" in r, r)
    check("含结论 FAIL 与汇总", "FAIL" in r and "1/1" in r, r)

test_range_for(); test_enum_zh(); test_pct_zh(); test_scene_injection()
test_render_card(); test_render_card_verb(); test_render_card_sparse(); test_render_card_fallback()
test_pct_normalize(); test_render_percent_normalize()
test_verify_verdict(); test_verify_reroll(); test_verify_pick_best(); test_verify_report(); test_verify_string_bool()
print(f"\n{summary()}")
sys.exit(exit_code())
