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

# 0) 数值防御：LLM 或手改 YAML 可能把数值写成字符串，渲染端统一收敛（spec 卡值应为数值）
def _num(v, default: float = 0.0) -> float:
    """字符串/数值 → float；None/非法 → default。纯防御，不抛异常。"""
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            return default
    return default

# 1) 密度类区间：confidence → ±%（spec 6.1a）
RANGE_TIERS = [(70, 0.10), (50, 0.20), (0, 0.30)]

def range_for(value: float, confidence: int) -> str:
    """5.8 @ 75 → '5-6'（X×(1±tier)，round 取整）。value/confidence 字符串也收敛为数值。"""
    value = _num(value)
    confidence = int(_num(confidence))
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
    value = _num(value)
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
    conf = int(_num(card.get("confidence")))
    out: dict[str, list[str]] = {k: [] for k in
        ["词汇", "句式", "节奏", "修辞与感官", "情绪表达", "对话风格", "衔接", "视角",
         "硬性规则", "整体基调", "风格参考例句"]}
    if not conf:
        # 未蒸馏卡（confidence=0）：量化维全零，渲染 0-1 区间误导——按 spec 应走正文定性四字段注入，
        # 这里仅透传声音层并给出提示，不再产出虚假量化区间。
        _sound_layer(out, card)
        out["硬性规则"].insert(0, "（未蒸馏卡：量化维未填充，请按正文定性四字段注入，不走案例 2 渲染）")
        return out
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
    _sound_layer(out, card)
    return out

def _sound_layer(out: dict[str, list[str]], card: dict) -> None:
    """声音层透传：hard_constraints/soft_guidance/few_shot_examples 原样保留（spec 案例 2 声音层）。
    防御：字符串或非列表输入按单项包裹，避免 list('字符串') 拆成逐字。"""
    hc = card.get("hard_constraints")
    out["硬性规则"] = _as_list(hc)
    sg = card.get("soft_guidance")
    out["整体基调"] = _as_list(sg)
    fse = card.get("few_shot_examples")
    if not isinstance(fse, list):
        fse = [fse] if fse else []
    out["风格参考例句"] = [f"[{e.get('type')}] {e.get('text')} — {e.get('reason')}" if isinstance(e, dict)
                        else str(e) for e in fse]

def _as_list(v) -> list[str]:
    """字符串 → 单元素列表；已是列表 → 原样；None/空 → []。"""
    if v is None:
        return []
    if isinstance(v, list):
        return list(v)
    if isinstance(v, (str, int, float)):
        return [str(v)]
    return []

def _parse_frontmatter(text: str) -> dict:
    """frontmatter → dict。按行定位闭合 '---'（值内含 '---' 不错位），缺闭行返回 {}。"""
    import yaml
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[1:i])
            return yaml.safe_load(fm) or {}
    return {}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True)
    args = ap.parse_args()
    text = __import__("pathlib").Path(args.card).read_text(encoding="utf-8")
    card = _parse_frontmatter(text)
    if not card:
        print("卡缺 frontmatter", file=sys.stderr)
        return 2
    for sec, items in render_card(card, scene_type=card.get("scene_type") or "general").items():
        if items:
            print(f"【{sec}】")
            for it in items:
                print(f"  - {it}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
