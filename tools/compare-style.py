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
