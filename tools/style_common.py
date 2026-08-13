#!/usr/bin/env python3
"""style-distill 共享工具（单源化，review #36/#38/#39/#40）。

style_render / style_verify / check-agents / platforms / 测试 共用，避免多副本漂移：
- force_utf8         stdout/stderr 强制 UTF-8（Windows GBK 防崩，替代各脚本复制的 reconfigure）
- frontmatter_text   frontmatter 原文提取（按行定位闭合，值内含 '---' 不错位、BOM 兼容）
- split_frontmatter  frontmatter → (dict, 正文)（缺闭行/解析失败/非 map → ({}, 原文)）
- SCENE_INJECTION    场景稀疏注入矩阵（唯一权威；check-agents 的场景/维度枚举派生自此）
- pct_ok             决策 A 单位校验：0-100 百分数合法值（type 排除 bool）
"""
from __future__ import annotations

import sys


def force_utf8() -> None:
    """stdout/stderr 强制 UTF-8，避免 Windows GBK 控制台报错（AGENTS.md:79）。"""
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except AttributeError:
            pass


def frontmatter_text(text: str) -> str | None:
    """frontmatter 原文（两行 --- 之间）。按行定位闭合行，正文含 '---'（markdown 分隔线）不错位；
    缺闭合返回 None。BOM 兼容（init 的 utf-8-sig 口径，review #23）。"""
    text = text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def split_frontmatter(text: str) -> tuple:
    """frontmatter → (dict, 正文)。缺闭行/解析失败/非 map → ({}, 原文)。"""
    import yaml
    text = text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[1:i])
            try:
                data = yaml.safe_load(fm)
            except Exception:
                data = None
            return (data if isinstance(data, dict) else {}), "\n".join(lines[i + 1:])
    return {}, text


# 场景稀疏注入矩阵（spec 6.3 / 旧 injection-template 表）——唯一权威，check-agents 枚举派生自此
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

STYLE_CARD_SCENE_TYPES = frozenset(SCENE_INJECTION)
STYLE_CARD_DIMS = list(SCENE_INJECTION["general"])


def pct_ok(v) -> bool:
    """决策 A 单位校验：0-100 百分数合法值（type 排除 bool——True/False 是 int 子类）。
    旧 jieba 引擎产出 0-100 一位小数百分数（13.4），0.3 是 0.3% 而非 30%。"""
    return type(v) in (int, float) and not isinstance(v, bool) and 0 <= v <= 100
