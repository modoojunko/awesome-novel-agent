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
    if not text.lstrip().startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) != 3 or not yaml:
        return None, text
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        print(f"[warn] 风格卡 YAML 解析失败 {path}: {e}", file=sys.stderr)
        return None, text
    if not isinstance(fm, dict):
        return None, text
    return fm, parts[2]


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
    merged["source_sample_length"] = int(
        (fa.get("source_sample_length", 0) * wA + fb.get("source_sample_length", 0) * wB) / total
    )
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
