#!/usr/bin/env python3
"""style-distiller LLM 重构：渲染规则模块（卡 → 案例 2 提示词）。

纯数据 + 纯函数，无 LLM 调用：
- RANGE_TIERS   confidence → 密度类数值区间公式（spec §6.1a）
- ENUM_ZH       类别枚举 → 中文渲染映射（spec §6.2）
- pct_zh        占比 → 中文定性（spec §6.1a 占比类）
- SCENE_INJECTION 场景稀疏注入矩阵（spec §6.3）
- render_card   卡 → 案例 2 各节渲染条目（prompt-crafter 只读引用；测试直接 import）

用法: python tools/style_render.py --card settings/writing-style.md
返回码 0 = 成功；2 = 卡缺 frontmatter。
"""
from __future__ import annotations

import argparse
import math
import sys

# 强制 UTF-8 输出，避免 Windows GBK 控制台报错（AGENTS.md:79）
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# 0) 数值防御：LLM 或手改 YAML 可能把数值写成字符串/bool/nan/inf，渲染端统一收敛（spec 卡值应为数值）
def _num(v, default: float = 0.0) -> float:
    """字符串/数值 → float；None/bool/nan/inf/非法 → default。纯防御，不抛异常。"""
    if v is None or isinstance(v, bool):
        return default
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else default
    if isinstance(v, str):
        try:
            f = float(v.strip())
        except ValueError:
            return default
        return f if math.isfinite(f) else default
    return default

# 1) 密度类区间：confidence → ±%（spec 6.1a）
RANGE_TIERS = [(70, 0.10), (50, 0.20), (0, 0.30)]

def range_for(value: float, confidence: int) -> str:
    """5.8 @ 75 → '5-6'（X×(1±tier)，四舍五入 half-up 取整）。value/confidence 字符串也收敛为数值。"""
    value = _num(value)
    confidence = int(_num(confidence))
    tier = 0.30
    for floor, t in RANGE_TIERS:
        if confidence >= floor:
            tier = t
            break
    # half-up：round() 是银行家舍入（round(4.5)=4），卡值 5/15/25 必错 1
    lo = max(0, math.floor(value * (1 - tier) + 0.5))
    hi = math.floor(value * (1 + tier) + 0.5)
    if hi <= lo:
        return str(lo)   # 零值/极低值：单值（0 个/0 字），不虚构非零区间（防「每百字 0-1 个」假实测）
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

def _pct(v, default=None):
    """占比/比例字段单位收敛（spec 决策 A 修正）：一律按 0-100 百分数展示，不做 ×100。

    旧 jieba 引擎（distill-style.py）产出 round(100*x/n,1) 的 0-100 一位小数百分数（如 13.4），
    从未产出 0-1 分数；因此 0<v<1 视为合法低百分数（0.3 = 0.3%），消除旧 ×100 把 0.3 误判成 30% 的错。

    缺键/None/非法/越界（<0 或 >100）→ default（None）：调用方跳过该行，不伪造「0%（少量）」。
    适用于全部标量百分比字段（question/exclamation/subtext/单句段/五层节奏/情绪 pct/动词比/过渡句/name_pronoun 单值）。
    分布桶（sentence_length_dist 等，0.5 作为 bucket 合法 = 0.5%）与密度字段（每百字 X 个）不得套用。"""
    v = _num(v, None)
    if v is None or v < 0 or v > 100:
        return default
    return int(v) if float(v).is_integer() else v

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
    """sentence_length_dist 等分布 → 阈值分条。数值收敛：字符串→数值、零/负/nan/inf 丢弃（0.5 合法桶保留）。"""
    zh = {"short_le_8": "短句（≤8字）", "medium_9_20": "中句（9-20字）",
          "long_21_35": "长句（21-35字）", "xlong_gt_35": "超长句（>35字）",
          "weapon_metal": "兵器金属", "nature": "自然", "body": "身体", "abstract": "抽象", "other": "其他",
          "visual": "视觉", "auditory": "听觉", "tactile": "触觉", "olfactory": "嗅觉", "gustatory": "味觉",
          "name": "人名", "he_she": "他/她", "i_you": "我/你"}
    out = []
    for k, v in d.items():
        v = _num(v)
        if v <= 0:
            continue
        out.append(f"{zh.get(k, k)}占比 {v:g}%")
    return out

def render_card(card: dict, scene_type: str = "general", body: str = "") -> dict[str, list[str]]:
    """卡 → 案例 2 各节渲染条目。body 为卡正文（§6.0b 声音层回退用），无则回退不生效。
    缺键/越界值 = 未测 → 不渲染该行（防「平均句长：0 字」类伪实测）。"""
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

    # 场景卡守卫（spec §6.3）：未合并 override 的卡（style-distill 落盘形状）→ 明确报错，防静默全零渲染
    if "override" in card and not any(d in card for d in SCENE_INJECTION["general"]):
        raise ValueError(
            "render_card 收到未合并的场景卡（含 override 但无顶层 9 维）——请先叠加主卡"
            "（inherits 解析 + override 深合并）再渲染")

    # 词汇
    if "lexicon" in dims:
        lex = card.get("lexicon") or {}
        for _k, _zh in (("adj_density_per_100", "形容词密度"), ("adv_density_per_100", "副词密度"),
                        ("four_phrase_freq_per_100", "四字短语频率")):
            _v = lex.get(_k)
            if _v is not None:                                    # 缺键/未测 → 不注入（旧引擎 None=未测 vs 0）
                out["词汇"].append(f"{_zh}：每百字 {range_for(_v, conf)} 个")
        pw = _as_list(lex.get("preferred_words"))                 # 字符串按单项包裹，防逐字拆分
        if pw:
            out["词汇"].append("偏好词：" + "、".join(pw))
        npr = lex.get("name_pronoun_ratio")
        if isinstance(npr, dict):
            out["词汇"].extend(_flatten_dists(npr))                       # 三维 → 逐桶
        elif isinstance(npr, (int, float)):
            _npr = _pct(npr)                                              # 单值 → 0-100 百分数；越界/非法跳过
            if _npr is not None:
                out["词汇"].append(f"人名/代词使用比例 {_npr}%")
    # 句式
    if "syntax" in dims:
        syn = card.get("syntax") or {}
        if syn.get("avg_sentence_length") is not None:
            out["句式"].append(f"平均句长：{range_for(syn['avg_sentence_length'], conf)} 字左右")
        sld = syn.get("sentence_length_dist")
        if isinstance(sld, dict):
            out["句式"].extend(_flatten_dists(sld))
        if (_ssp := _pct(syn.get('single_sentence_paragraph_pct'))) is not None:
            out["句式"].append(f"单句段占比 ≥ {_ssp}%")
        if syn.get('avg_sentences_per_paragraph') is not None:
            out["句式"].append(f"每段平均句数：{syn['avg_sentences_per_paragraph']} 句")
        if (_qr := _pct(syn.get('question_ratio'))) is not None:
            out["句式"].append(f"疑问句占比：{_qr}%（{pct_zh(_qr)}）")
        if (_er := _pct(syn.get('exclamation_ratio'))) is not None:
            out["句式"].append(f"感叹句占比：{_er}%")
        # verb_style 并入句式（fight 场景经 SCENE_INJECTION 注入；存在且合法才渲染）
        vs = card.get("verb_style") or {}
        if vs.get("strength"):
            out["句式"].append(enum_zh("strength", vs["strength"]))
        _vr = []
        for _k, _zh in (("action_verb_ratio", "动作"), ("mental_verb_ratio", "心理"), ("state_verb_ratio", "状态")):
            _v = _pct(vs.get(_k))
            if _v is not None:
                _vr.append(f"{_zh} {_v}%")
        if _vr:
            out["句式"].append("动词：" + " / ".join(_vr))
    # 节奏
    if "rhythm" in dims:
        rhy = card.get("rhythm") or {}
        if (_dp := _pct(rhy.get("dialogue_pct"))) is not None:
            out["节奏"].append(f"对话约 {_dp}%（{pct_zh(_dp)}）")
        _ac, _en = _pct(rhy.get('action_pct')), _pct(rhy.get('environment_pct'))
        if _ac is not None and _en is not None:
            out["节奏"].append(f"动作约 {_ac}%、环境约 {_en}%")
        _it, _na = _pct(rhy.get('inner_thought_pct')), _pct(rhy.get('narration_pct'))
        if _it is not None and _na is not None:
            out["节奏"].append(f"内心独白约 {_it}%、叙述约 {_na}%")
    # 修辞
    if "rhetoric" in dims:
        rhe = card.get("rhetoric") or {}
        _md = rhe.get("metaphor_density_per_100")
        if _md is not None:
            out["修辞与感官"].append(f"比喻密度：每百字 {range_for(_md, conf)} 个")
        mp = rhe.get("metaphor_preference")
        if isinstance(mp, dict):
            out["修辞与感官"].append("常用喻体：" + "、".join(_flatten_dists(mp)))
        sd = rhe.get("sensory_dist")
        if isinstance(sd, dict):
            out["修辞与感官"].append("感官通道：" + "、".join(_flatten_dists(sd)))
    # 情绪
    if "emotion_expression" in dims:
        emo = card.get("emotion_expression") or {}
        _dp2, _ap = _pct(emo.get('direct_pct')), _pct(emo.get('action_physiology_pct'))
        if _dp2 is not None and _ap is not None:
            out["情绪表达"].append(f"直接陈述 {_dp2}%、动作/生理 {_ap}%")
        if emo.get("inner_monologue_pct") is not None:                    # 缺省不注入该子项（spec 6.0b/4.1）
            _ep, _ip = _pct(emo.get('environment_projection_pct')), _pct(emo.get('inner_monologue_pct'))
            if _ep is not None and _ip is not None:
                out["情绪表达"].append(f"环境投射 {_ep}%、内心独白 {_ip}%")
        elif (_ep := _pct(emo.get('environment_projection_pct'))) is not None:
            out["情绪表达"].append(f"环境投射 {_ep}%")
    # 对话
    if "dialogue_style" in dims:
        dia = card.get("dialogue_style") or {}
        if dia.get("tag_style"):
            out["对话风格"].append(enum_zh("tag_style", dia["tag_style"]))
        if dia.get('avg_dialogue_length') is not None:
            out["对话风格"].append(f"平均对话长度：{range_for(dia['avg_dialogue_length'], conf)} 字")
        _if = dia.get('interrupt_freq_per_100')
        if _if is not None:
            out["对话风格"].append(f"打断频率：每百字 {range_for(_if, conf)} 次")
        if (_sr := _pct(dia.get('subtext_ratio'))) is not None:
            out["对话风格"].append(f"潜台词占比：{_sr}%")
    # 衔接
    if "cohesion" in dims:
        coh = card.get("cohesion") or {}
        _cf = coh.get('conjunction_freq_per_100')
        if _cf is not None:
            out["衔接"].append(f"连接词频率：每百字 {range_for(_cf, conf)} 次")
        if (_ts := _pct(coh.get('transition_sentence_ratio'))) is not None:   # spec 声明，渲染/校验端补齐（review #22）
            out["衔接"].append(f"过渡句占比：{_ts}%")
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
    _sound_layer(out, card, body)
    return out

def _sound_layer(out: dict[str, list[str]], card: dict, body: str = "") -> None:
    """声音层透传：hard_constraints/soft_guidance/few_shot_examples 原样保留（spec 案例 2 声音层）。
    已蒸馏卡缺声音层键 → §6.0b 回退读正文定性四字段（硬约束+AI易犯错误→硬性规则、叙事身份→整体基调、
    描写层次→风格参考例句）。防御：字符串或非列表输入按单项包裹，避免 list('字符串') 拆成逐字。"""
    hc = _as_list(card.get("hard_constraints"))
    sg = _as_list(card.get("soft_guidance"))
    fse = card.get("few_shot_examples")
    if not isinstance(fse, list):
        fse = [fse] if fse else []
    if body:
        sec = None
        if not hc:
            sec = _body_sections(body)
            hc = sec.get("硬约束", []) + sec.get("AI 易犯错误", [])
        if not sg:
            if sec is None:
                sec = _body_sections(body)
            sg = sec.get("叙事身份", [])
        if not fse:
            if sec is None:
                sec = _body_sections(body)
            fse = [{"type": "描写层次", "text": t} for t in sec.get("描写层次和手法", [])]
    out["硬性规则"] = hc
    out["整体基调"] = sg
    # 按 type 分组（spec 渲染步骤 6）：同 type 合并一行；缺 text/reason 标「（未填写）」而非字面 None
    groups: dict[str, list[str]] = {}
    for e in fse:
        if not isinstance(e, dict):
            e = {"type": "未标注", "text": str(e)}
        t = e.get("type") or "未标注"
        txt = e.get("text") or "（未填写）"
        reason = e.get("reason")
        item = f"{txt} — {reason}" if reason else txt
        groups.setdefault(t, []).append(item)
    out["风格参考例句"] = [f"[{t}] " + "；".join(items) for t, items in groups.items()]

def _body_sections(body: str) -> dict[str, list[str]]:
    """卡正文按 '## ' 小节切分（§6.0b 回退用）：节名（去「（原 X）」后缀）→ 非空内容行（去 '- ' 前缀）。"""
    sections: dict[str, list[str]] = {}
    cur = None
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("## "):
            cur = s[3:].split("（")[0].strip()
            sections.setdefault(cur, [])
        elif cur is not None and s:
            sections[cur].append(s[2:].strip() if s.startswith("- ") else s)
    return sections

def _as_list(v) -> list[str]:
    """字符串 → 单元素列表；已是列表 → 原样；None/空 → []。"""
    if v is None:
        return []
    if isinstance(v, list):
        return list(v)
    if isinstance(v, (str, int, float)):
        return [str(v)]
    return []

def _parse_frontmatter(text: str) -> tuple:
    """frontmatter → (dict, 正文)。按行定位闭合 '---'（值内含 '---' 不错位），缺闭行返回 ({}, 原文)。"""
    import yaml
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[1:i])
            return yaml.safe_load(fm) or {}, "\n".join(lines[i + 1:])
    return {}, text

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True)
    args = ap.parse_args()
    text = __import__("pathlib").Path(args.card).read_text(encoding="utf-8")
    card, body = _parse_frontmatter(text)
    if not card:
        print("卡缺 frontmatter", file=sys.stderr)
        return 2
    for sec, items in render_card(card, scene_type=card.get("scene_type") or "general", body=body).items():
        if items:
            print(f"【{sec}】")
            for it in items:
                print(f"  - {it}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
