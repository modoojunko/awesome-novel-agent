#!/usr/bin/env python3
"""style-distiller LLM 重构：验收聚合规则模块（案例2 验收报告 + 抽卡判定）。

纯数据 + 纯函数，无 LLM 调用：
- CHECK_CATEGORIES  验收检查项四类（spec 7.1）
- verdict           违反报告 PASS/FAIL 聚合（spec 7.1）
- should_reroll     抽卡判定：round<3 且本轮有违反 → 重写（spec 7.2）
- pick_best         超限取最优：违反最少一轮，同分取最新
- format_report     违反报告表格渲染（条号/原文要求/正文表现/违反与否/建议 + 结论行）

anti-ai 按此口径输出违反报告（格式见 verify-checklist.md）；本模块是确定性测试编码。
"""
from __future__ import annotations

# 1) 验收检查项四类（spec 7.1）
CHECK_CATEGORIES = ["数值/占比条", "硬性规则条", "建模规则条", "软引导条"]

def verdict(items: list[dict]) -> str:
    """全违反否 → PASS；任一违反 → FAIL"""
    return "FAIL" if any(i.get("violated") for i in items) else "PASS"

def should_reroll(round_no: int, violated: int) -> bool:
    """抽卡判定（spec 7.2）：round < 3 且本轮有违反 → 重写"""
    return round_no < 3 and violated > 0

def pick_best(rounds: list[dict]) -> dict:
    """超限取最优（spec 7.2）：违反条数最少的一轮，同分取最新"""
    return min(rounds, key=lambda r: (r.get("violated", 0), -rounds.index(r)))

def format_report(items: list[dict]) -> str:
    """违反报告表格渲染（spec 7.1 输出格式）"""
    lines = ["| 条号 | 原文要求 | 正文表现 | 违反与否 | 建议 |", "|---|---|---|---|---|"]
    for i, it in enumerate(items, 1):
        lines.append(
            f"| {it.get('no', i)} | {it.get('require', '')} | {it.get('evidence', '')} | "
            f"{'是' if it.get('violated') else '否'} | {it.get('advice', '')} |"
        )
    n_v = sum(1 for i in items if i.get("violated"))
    lines.append(f"\n结论：{'FAIL' if n_v else 'PASS'}（{n_v}/{len(items)}）")
    return "\n".join(lines)

if __name__ == "__main__":
    import json, sys
    items = json.load(sys.stdin)          # 例: [{"no":1,"require":"禁'宛如'","evidence":"出现1次","violated":true,"advice":"替换"}]
    print(format_report(items))
