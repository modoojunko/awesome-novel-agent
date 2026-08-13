#!/usr/bin/env python3
"""style-distiller LLM 重构：验收聚合规则模块（案例2 验收报告 + 抽卡判定）。

纯数据 + 纯函数，无 LLM 调用：
- CHECK_CATEGORIES  验收检查项四类（spec 7.1）
- verdict           违反报告 PASS/FAIL 聚合（spec 7.1）
- should_reroll     抽卡判定：round<3 且本轮有违反 → 重写（spec 7.2）
- pick_best         超限取最优：违反最少一轮，同分取最新
- format_report     违反报告表格渲染（条号/原文要求/正文表现/违反与否/建议 + 结论行）

anti-ai 按此口径输出违反报告（格式见 verify-checklist.md）；本模块是确定性测试编码。

用法: python tools/style_verify.py < violations.json
返回码 0 = 成功（结论 PASS/FAIL 见报告末行）。
"""
from __future__ import annotations

import sys

from style_common import force_utf8

force_utf8()

# 1) 验收检查项四类（spec 7.1）
CHECK_CATEGORIES = ["数值/占比条", "硬性规则条", "建模规则条", "软引导条"]

# 违反判定收敛白名单（spec 7.1 / verify-checklist.md）：LLM 输出的字符串布尔一律按此收敛，
# 匹配前剥尾部标点与语气词（'是。'→'是'、'违反了'→'违反'、'是；'→'是'），白名单外一律不违反
# （'false'/'否'/空/'其余字符串'）。
VIOLATED_STRINGS = frozenset({"true", "是", "yes", "1", "违反", "违反了"})

def _is_violated(v) -> bool:
    """violated 判定：bool/字符串 布尔都收敛——LLM 可能输出 '是。'/'违反了'/'是；' 等字符串，误判会触发错误抽卡。
    字符串按 truthy 语义：'true'/'是'/'yes'/'1'/'违反'/'违反了'（含尾部标点/语气词）→ 违反；其余（'false'/'否'/空）→ 不违反。"""
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().strip("。？！…，,.!? ；; 　").strip("了")
        return s.lower() in VIOLATED_STRINGS
    return bool(v)

def verdict(items: list[dict]) -> str:
    """全违反否 → PASS；任一违反 → FAIL"""
    return "FAIL" if any(_is_violated(i.get("violated")) for i in items) else "PASS"

def should_reroll(round_no: int, violated: int) -> bool:
    """抽卡判定（spec 7.2）：round < 3 且本轮有违反 → 重写"""
    return round_no < 3 and violated > 0

def _violated_count(v) -> int:
    """violated 数值收敛：int/float 原样、数字字符串转 int（'3.0'→3、'10'→10）、bool/None/非法/非有限 → 0。
    LLM 可能输出字符串条数（"3"），原生比较会 TypeError 或按字典序选错（"10" < "3"）；True 是布尔不是条数。"""
    if v is None or isinstance(v, bool):
        return 0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0
    if f != f or f in (float("inf"), float("-inf")):   # nan/inf 过滤
        return 0
    return int(f)

def pick_best(rounds: list[dict]) -> dict:
    """超限取最优（spec 7.2）：违反条数最少的一轮，同分取最新。
    同分按列表位置（越靠后越新）取最新，避免依赖 dict ==（相同 dict 会退化成取最旧）。
    空轮次列表返回空 dict（调用方按无违反处理），避免 min() 抛 ValueError。"""
    if not rounds:
        return {}
    return min(enumerate(rounds), key=lambda ir: (_violated_count(ir[1].get("violated", 0)), -ir[0]))[1]

def format_report(items: list[dict]) -> str:
    """违反报告表格渲染（spec 7.1 输出格式）"""
    lines = ["| 条号 | 原文要求 | 正文表现 | 违反与否 | 建议 |", "|---|---|---|---|---|"]
    for i, it in enumerate(items, 1):
        lines.append(
            f"| {it.get('no', i)} | {it.get('require', '')} | {it.get('evidence', '')} | "
            f"{'是' if _is_violated(it.get('violated')) else '否'} | {it.get('advice', '')} |"
        )
    n_v = sum(1 for i in items if _is_violated(i.get("violated")))
    lines.append(f"\n结论：{verdict(items)}（{n_v}/{len(items)}）")   # 结论行复用 verdict()（review #42）
    return "\n".join(lines)

if __name__ == "__main__":
    import json, sys
    items = json.load(sys.stdin)          # 例: [{"no":1,"require":"禁'宛如'","evidence":"出现1次","violated":true,"advice":"替换"}]
    print(format_report(items))
