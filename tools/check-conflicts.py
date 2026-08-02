#!/usr/bin/env python3
"""反 AI 规则冲突静态检查

扫描 knowledge/ 与 skills/ 下的规则文件，检查两类问题：

A. 阈值冲突：同一对象在不同文件里定义了不同的数量阈值。
   权威源 = knowledge/anti-ai/common-rules.md。其他文件的阈值若与权威源
   同对象但数字不同 → 报冲突（职责声明要求其他文件只引用、不重复定义）。

B. 边界越界：方法论/豁免类文件（anti-ai-writing.md、boundary-cases.md）
   职责是解释"为什么"和"怎么做"，禁止出现数量线。检出即报越界。

用法: python tools/check-conflicts.py
返回码 0 = 通过，非 0 = 有问题（CI 用）。

阈值格式（兼容两种）：
  - 代码块: 单章阈值: 5 次 | 严重度: medium
  - 表格:   | 疲劳词 | 3 次 | 替代策略 |
"""

import sys
import re
from pathlib import Path

for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
SKILLS_DIR = ROOT / "skills"

# 唯一权威源——其他文件的阈值以它为准
AUTHORITY = KNOWLEDGE_DIR / "anti-ai" / "common-rules.md"

# 越界白名单：这些文件职责是方法论/豁免，禁止数量线
METHODOLOGY_FILES = [
    "knowledge/anti-ai/anti-ai-writing.md",
    "knowledge/anti-ai/boundary-cases.md",
]

# 扫描范围：knowledge/ + skills/ 下所有 .md
SCAN_GLOBS = [
    (KNOWLEDGE_DIR, "knowledge"),
    (SKILLS_DIR, "skills"),
]

# 匹配 "对象 | 数字 次" 表格行（纯数字：| 默默 | 3 次 |）
TBL_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d+)\s*次")
# 匹配 "对象 | ≤数字次/单位" 表格行（≤格式：| 突然/忽然 | ≤4次/章 |）
TBL_LE_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(?:≤|≤)?(\d+)\s*次/(?:章|500字|段|千字)")
# 匹配 "单章阈值: 数字 次[/单位]"
CODE_RE = re.compile(r"单章阈值[:：]\s*(\d+)\s*次(?:/(章|500字|段|千字))?")
# 通用数量线（越界检测用）
ANY_COUNT_RE = re.compile(r"(?:≤|≤)?\d+\s*次(?:/(章|500字|段|千字))?")
# 引用 common-rules 的行（豁免越界）
REFERENCE_RE = re.compile(r"common-rules\.md")

# 对象名规范化：取第一个关键词，去掉括号、斜杠组、顿号枚举
def norm_obj(raw: str) -> str:
    obj = raw.strip().replace("**", "")
    obj = re.sub(r"[（(].*?[)）]", "", obj)  # 去括号
    obj = obj.split("、")[0].split("/")[0].split(",")[0].strip()
    return obj


def extract_thresholds(text: str, path: Path) -> dict:
    """提取 {规范化对象: {数字, 行号, 原文}}。同文件同对象保留首个。"""
    found = {}
    lines = text.split("\n")
    for i, ln in enumerate(lines, 1):
        m = TBL_RE.match(ln)
        if m:
            obj = norm_obj(m.group(1))
            if not obj or obj in ("规则", "疲劳词", "检测项"):
                continue
            num = int(m.group(2))
            if obj not in found:
                found[obj] = {"num": num, "line": i, "raw": ln.strip()[:70]}
            continue
        m = TBL_LE_RE.match(ln)
        if m:
            obj = norm_obj(m.group(1))
            if not obj or obj in ("规则", "疲劳词", "检测项"):
                continue
            num = int(m.group(2))
            if obj not in found:
                found[obj] = {"num": num, "line": i, "raw": ln.strip()[:70]}
            continue
        m2 = CODE_RE.search(ln)
        if m2:
            # 代码块格式：对象来自前一行"命中模式"
            obj = None
            for j in range(i - 2, i):
                if j >= 1:
                    pm = re.search(r"命中模式[:：]\s*[\"“]?([^\"”|]+)", lines[j - 1])
                    if pm:
                        obj = norm_obj(pm.group(1))
                        break
            if not obj:
                obj = f"L{i}"
            num = int(m2.group(1))
            if obj not in found:
                found[obj] = {"num": num, "line": i, "raw": ln.strip()[:70]}
    return found


def check_conflicts() -> list:
    errors = []
    auth_text = AUTHORITY.read_text(encoding="utf-8")
    auth = extract_thresholds(auth_text, AUTHORITY)

    for base, label in SCAN_GLOBS:
        for f in sorted(base.rglob("*.md")):
            if f == AUTHORITY:
                continue
            rel = f.relative_to(ROOT).as_posix()
            text = f.read_text(encoding="utf-8")
            found = extract_thresholds(text, f)
            for obj, info in found.items():
                # 同文件内重复（速查表 + 正文）由保留首个策略天然豁免
                if obj in auth and auth[obj]["num"] != info["num"]:
                    errors.append(
                        f"{rel}:{info['line']} 「{obj}」阈值 {info['num']}次 与权威源 "
                        f"common-rules.md:{auth[obj]['line']} 的 {auth[obj]['num']}次 冲突"
                    )
    return errors


def check_boundary() -> list:
    errors = []
    for rel in METHODOLOGY_FILES:
        f = ROOT / rel
        if not f.exists():
            errors.append(f"{rel}: 文件不存在（越界检测跳过）")
            continue
        text = f.read_text(encoding="utf-8")
        lines = text.split("\n")
        for i, ln in enumerate(lines, 1):
            # 引用 common-rules 的行豁免
            if REFERENCE_RE.search(ln):
                continue
            if ANY_COUNT_RE.search(ln):
                errors.append(
                    f"{rel}:{i} 方法论/豁免文件出现数量线「{ln.strip()[:50]}」"
                    f"（阈值只能定义在 common-rules.md）"
                )
    return errors


def main() -> int:
    all_errors = []
    all_errors += check_conflicts()
    all_errors += check_boundary()

    for e in all_errors:
        print(f"  ❌ {e}")

    if all_errors:
        print(f"\n共 {len(all_errors)} 个问题")
        return 1
    print("✅ 规则冲突检查通过（无阈值冲突、无边界越界）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
