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

RE_STOP = set("的了一是在不和有这我他她它们就都也不为之与把被让要向从到说走看想给去又再很那这本个子等面着头口手眼里出来过去上下前后中还是而但所以然后因为因此如果同时另外例如比如通过作为关于对于根据依照随着由")

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
    # 无 jieba 时 POS 不可用，三个比例记 None（与 lexicon 的 adj/adv 一致，避免 0.0 假测量）
    if not HAS_JIEBA:
        return {"action_verb_ratio": None, "mental_verb_ratio": None, "state_verb_ratio": None}
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
