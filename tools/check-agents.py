#!/usr/bin/env python3
"""awesome-novel-skill agent 定义静态检查

校验 agents/*.md 的 frontmatter：
  1. YAML 合法
  2. frontmatter 里引用的 skills/knowledge 路径在仓库真实存在（或是有意的占位/部署后路径）
  3. tools 字段只含合法工具名（若存在）

用法: python tools/check-agents.py
返回码 0 = 通过，非 0 = 有问题（CI 用）。

规则说明：
- agents/ 下的 .md 是 Claude Code 语法的 agent 源定义
- skills: 引用 skills/*.md（必存在）
- knowledge: 引用两类——
    (a) 仓库内相对路径（settings/、.claude/ 等，按仓库根解析，需存在）
    (b) 部署后路径（.claude/knowledge/...，由 init.py 生成，仓库可能没有源文件）
  对 (b) 类做"路径模式"白名单校验，不要求文件存在。
"""

from __future__ import annotations  # str | None 等注解在 Python 3.9 下延迟求值，避免 import 即 TypeError

import sys
import re
import yaml
from pathlib import Path

# 强制 UTF-8 输出，避免 Windows GBK 控制台报错
for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
SKILLS_DIR = ROOT / "skills"

# 合法工具名（Claude Code tools 白名单）
VALID_TOOLS = {
    "Read", "Write", "Edit", "Glob", "Grep", "Bash", "PowerShell",
    "WebFetch", "WebSearch", "NotebookEdit", "TodoWrite", "AskUserQuestion",
    "Skill", "Agent", "Task",
}

# 部署后生成、仓库里不一定有源文件的路径模式（白名单，不要求文件存在）
# 这些由 init.py 按题材/合并生成，或由 updater 归档时创建
DEPLOYED_PATTERNS = [
    re.compile(r"^\.claude/knowledge/(anti-ai|writer-style|genre-example|permanent-memory)\.md$"),
    re.compile(r"^\.claude/knowledge/[a-z-]+\.md$"),          # format-specs 平铺产物
    re.compile(r"^\.claude/knowledge/(plot-craft|scene-craft|character-craft|title-craft|style-distill)/"),
    re.compile(r"^settings/character-setting/"),               # 每角色一个文件
    re.compile(r"^settings/(world-setting|genre-setting|writing-style|timeline|foreshadowing)\.md$"),
    re.compile(r"^settings/style-profiles/"),               # 分场景风格卡（每场景一个文件）
    re.compile(r"^settings/\.style-versions/"),             # 蒸馏版本快照目录（style-distiller 蒸馏备份时创建）
    re.compile(r"^\.agent/"),                                  # 运行时状态
    re.compile(r"^story\.md$"),
    re.compile(r"^volumes/"), re.compile(r"^chapters/"), re.compile(r"^prompts/"), re.compile(r"^archives/"),
]


def _split_frontmatter(text: str) -> str | None:
    """提取 frontmatter 正文（两行 --- 之间）。按行定位闭合行，正文含 '---'（如 markdown 分隔线）不错位；缺闭合返回 None。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def check_file(path: Path) -> list:
    errors = []
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return [f"{path.name}: 缺少 frontmatter (--- 开头)"]

    fm_text = _split_frontmatter(text)
    if fm_text is None:
        return [f"{path.name}: frontmatter 未正确闭合 (需两对 ---)"]

    try:
        fm = yaml.safe_load(fm_text)
    except Exception as e:
        return [f"{path.name}: frontmatter YAML 解析失败: {e}"]

    if not isinstance(fm, dict):
        return [f"{path.name}: frontmatter 不是 YAML map"]

    # name 必填
    if "name" not in fm:
        errors.append(f"{path.name}: 缺少 name 字段")

    # tools 字段合法性
    tools = fm.get("tools")
    if tools:
        names = [t.strip() for t in str(tools).split(",") if t.strip()]
        bad = [t for t in names if t not in VALID_TOOLS]
        if bad:
            errors.append(f"{path.name}: tools 含非法工具名 {bad}（合法: {sorted(VALID_TOOLS)}）")

    # skills / knowledge 路径存在性
    for key in ("skills", "knowledge"):
        entries = fm.get(key) or []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            p = entry.get("path")
            if not p:
                continue
            rel = str(p)
            # 占位符（如 {genre}）→ 跳过，init.py 会替换或属于合并产物
            if "{" in rel:
                continue
            # 部署后路径 → 白名单模式，不要求文件存在，但 settings/*.md 必须有对应模板
            if _is_deployed(rel):
                if rel.startswith("settings/") and rel.endswith(".md"):
                    # 每角色的动态文件（character-setting/）不校验模板
                    if not rel.startswith("settings/character-setting/"):
                        tpl = ROOT / "templates" / rel
                        if not tpl.exists():
                            errors.append(
                                f"{path.name}: 引用 settings/ 路径 {rel}，但 templates/settings/ 无对应模板"
                                f"（新项目 init.py 不会生成它 → 运行时必缺）"
                            )
                continue
            target = ROOT / rel
            if not target.exists():
                errors.append(f"{path.name}: 引用不存在的 {key} 路径: {rel}")

    return errors


def _is_deployed(rel: str) -> bool:
    """判断路径是否属于'部署后生成、仓库无源'的模式。"""
    rel = rel.replace("\\", "/")
    # 仓库内 skills/ 下的 .md 必须真实存在（skill 源就在仓库）
    if rel.startswith("skills/") or rel.startswith("knowledge/"):
        return False
    for pat in DEPLOYED_PATTERNS:
        if pat.match(rel):
            return True
    return False


STYLE_CARD_SCENE_TYPES = {"general", "dialogue", "fight", "environment",
                          "inner-mono", "transition", "group-scene"}
STYLE_CARD_DIMS = ["lexicon", "syntax", "rhythm", "rhetoric", "emotion_expression",
                   "narrative", "dialogue_style", "cohesion", "verb_style"]


def _pct_sum_errors(d: dict, label: str, expected: float = 100, max_sum: float | None = None) -> list:
    """占比/分布 dict 求和校验：值必须全为数值（type 排除 bool）；全零 = 占位跳过；非零须和≈expected（或≤max_sum）。

    字符串值（LLM 或手改）不再被 `if total and` 静默跳过——非数值直接报错。"""
    bad = [k for k, v in d.items() if type(v) not in (int, float)]
    if bad:
        return [f"{label} 值应为数值（非数值键: {sorted(bad)}）"]
    total = sum(d.values())
    if total == 0:
        return []                                  # 全零占位（未蒸馏/空 override）
    if max_sum is not None:
        if total > max_sum:
            return [f"{label} 总计应 ≤{max_sum}（当前 {round(total)}）"]
        return []
    if abs(total - expected) > 1:
        return [f"{label} 和应≈{expected}（当前 {round(total)}）"]
    return []


def check_style_card(path: Path) -> list:
    errors = []
    text = path.read_text(encoding="utf-8")
    fm_text = _split_frontmatter(text)
    if fm_text is None:
        return [f"{path.name}: 风格卡缺 frontmatter（需两对 ---）"]
    try:
        fm = yaml.safe_load(fm_text)
    except Exception as e:
        return [f"{path.name}: 卡片 frontmatter YAML 解析失败: {e}"]
    if not isinstance(fm, dict):
        return [f"{path.name}: 卡片 frontmatter 不是 map"]
    for k in ("profile_version", "scene_type", "confidence", "last_updated", "source_sample_length"):
        if k not in fm:
            errors.append(f"{path.name}: 卡片缺 {k}")
    st = fm.get("scene_type")
    if st not in STYLE_CARD_SCENE_TYPES:
        errors.append(f"{path.name}: scene_type={st!r} 不在枚举 {sorted(STYLE_CARD_SCENE_TYPES)}")
    conf = fm.get("confidence")
    # 用 type() 而非 isinstance() 以排除 bool（True/False 是 int 子类，会蒙混过关）
    if not type(conf) is int or not (0 <= conf <= 100):
        errors.append(f"{path.name}: confidence 需为 0-100 整数（当前 {conf!r}）")
    # schema 判别（不按文件名）：有 override → 场景卡（稀疏差异）；否则 → 全量 9 维
    #（主卡 + genre-baselines 的 base/benchmark/delta 卡都是全量 schema，后者数值为 0 占位）。
    if "override" in fm:
        ov = fm.get("override")
        if not isinstance(ov, dict):
            errors.append(f"{path.name}: 场景卡需 override 字段（dict，只写与主卡的差异维度）")
        else:
            for dim in ov:
                if dim not in STYLE_CARD_DIMS:
                    errors.append(f"{path.name}: override 出现未知维度 {dim!r}")
    else:
        for dim in STYLE_CARD_DIMS:
            if dim not in fm:
                errors.append(f"{path.name}: 卡片缺维度 {dim}")
    bf = fm.get("baseline_for")
    if bf is not None and (not isinstance(bf, str) or not bf):
        errors.append(f"{path.name}: baseline_for 需为非空字符串（当前 {bf!r}）")
    locked = fm.get("locked")
    if locked is not None and not isinstance(locked, list):
        errors.append(f"{path.name}: locked 需为列表")
    elif locked:
        for dim in locked:
            if dim not in STYLE_CARD_DIMS:
                errors.append(f"{path.name}: locked 含未知维度 {dim!r}（spec §13-5#3）")
    inh = fm.get("inherits")
    if inh:
        # 继承目标：场景卡继承主卡（style-profiles/../writing-style.md）或同级场景卡
        candidates = [path.parent / str(inh), path.parent.parent / str(inh)]
        if not any(c.exists() for c in candidates):
            try:
                rels = "、".join(str(c.relative_to(ROOT)) for c in candidates)
            except ValueError:
                rels = "、".join(str(c) for c in candidates)  # 路径不在 ROOT 下（测试/外部调用）
            errors.append(f"{path.name}: inherits 引用不存在: {inh}（期望 {rels}）")
    # --- 蒸馏卡可选增强字段（2026-08-12 双态：存在才校验，缺失兼容旧卡/未蒸馏卡） ---
    def _opt_pct(v):
        return isinstance(v, (int, float)) and 0 <= v <= 100

    lex = fm.get("lexicon") if isinstance(fm.get("lexicon"), dict) else {}
    npr = lex.get("name_pronoun_ratio")
    if isinstance(npr, dict):
        keys = set(npr)
        if keys != {"name", "he_she", "i_you"}:
            errors.append(f"{path.name}: name_pronoun_ratio 键应为 name/he_she/i_you（当前 {sorted(keys)}）")
        else:
            for e in _pct_sum_errors(npr, f"{path.name}: name_pronoun_ratio 三维和"):
                errors.append(e)

    em = fm.get("emotion_expression") if isinstance(fm.get("emotion_expression"), dict) else {}
    if "inner_monologue_pct" in em and not _opt_pct(em["inner_monologue_pct"]):
        errors.append(f"{path.name}: inner_monologue_pct 需为 0-100 数值（当前 {em['inner_monologue_pct']!r}）")

    vs = fm.get("verb_style") if isinstance(fm.get("verb_style"), dict) else {}
    if vs.get("strength") not in (None, "", "weak", "medium", "strong"):
        errors.append(f"{path.name}: verb_style.strength 应为 weak/medium/strong（当前 {vs.get('strength')!r}）")

    for key in ("hard_constraints", "soft_guidance"):
        v = fm.get(key)
        if v is not None and not isinstance(v, list):
            errors.append(f"{path.name}: {key} 需为列表")
    if fm.get("few_shot_examples") is not None and not isinstance(fm.get("few_shot_examples"), list):
        errors.append(f"{path.name}: few_shot_examples 需为列表")

    rhy = fm.get("rhythm") if isinstance(fm.get("rhythm"), dict) else {}
    _FIVE = ("dialogue_pct", "action_pct", "environment_pct", "inner_thought_pct", "narration_pct")
    if all(f in rhy for f in _FIVE):
        five = {f: rhy[f] for f in _FIVE}
        for e in _pct_sum_errors(five, f"{path.name}: 五层占比总计", max_sum=110):   # 五层可重叠，上限 110%（spec §5.1）
            errors.append(e)

    _DIST = {"syntax": ["sentence_length_dist"], "rhetoric": ["metaphor_preference", "sensory_dist"]}
    for dim, fields in _DIST.items():
        d = fm.get(dim) if isinstance(fm.get(dim), dict) else {}
        for f in fields:
            sub = d.get(f)
            if isinstance(sub, dict) and sub:
                for e in _pct_sum_errors(sub, f"{path.name}: {f} 分布和"):
                    errors.append(e)
    return errors


def check_style_cards() -> list:
    base = ROOT / "templates" / "settings"
    main = base / "writing-style.md"
    if not main.exists():
        return ["templates/settings/writing-style.md 不存在（旧布局仓库？）"]
    errors = []
    for p in [main] + sorted((base / "style-profiles").rglob("*.md")):   # 递归：含 genre-baselines/**/base|benchmark|delta
        errors.extend(check_style_card(p))
    return errors


def main() -> int:
    if not AGENTS_DIR.is_dir():
        print("⚠️  agents/ 目录不存在")
        return 1

    all_errors = []
    for f in sorted(AGENTS_DIR.glob("*.md")):
        errs = check_file(f)
        for e in errs:
            print(f"  ❌ {e}")
        all_errors.extend(errs)

    # 校验 agents/ 引用的 skills 文件是否真存在于 skills/ 目录
    refs = set()
    for f in AGENTS_DIR.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"skills/([a-z-]+\.md)", text):
            refs.add(m.group(1))
    missing_skills = [r for r in sorted(refs) if not (SKILLS_DIR / r).exists()]
    for s in missing_skills:
        print(f"  ❌ skills 引用缺失: skills/{s}")
        all_errors.append(f"skills/{s}")

    style_errs = check_style_cards()
    for e in style_errs:
        print(f"  ❌ {e}")
    all_errors.extend(style_errs)

    if all_errors:
        print(f"\n共 {len(all_errors)} 个问题")
        return 1
    print("✅ agent 定义全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
