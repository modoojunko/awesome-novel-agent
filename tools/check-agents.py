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

from style_common import (frontmatter_text, force_utf8, pct_ok,
                          STYLE_CARD_DIMS, STYLE_CARD_SCENE_TYPES)

force_utf8()

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
# （review #47：首项被 `[a-z-]+\.md` 完全包含属冗余，已删）
DEPLOYED_PATTERNS = [
    re.compile(r"^\.claude/knowledge/[a-z-]+\.md$"),          # 平铺产物（format-specs/anti-ai/genre-example/permanent-memory）
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
    """提取 frontmatter 正文（两行 --- 之间，单源实现见 style_common.frontmatter_text，review #38）。"""
    return frontmatter_text(text)


def _dup_keys(fm_text: str) -> list[str]:
    """检测 frontmatter YAML 顶层重复键——yaml.safe_load 是 last-wins 静默覆盖
    （confidence 0→80 无声翻转），需先于解析独立检测（review #22）。"""
    try:
        node = yaml.compose(fm_text)
    except Exception:
        return []
    if not isinstance(node, yaml.MappingNode):
        return []
    seen: set[str] = set()
    dup: list[str] = []
    for k, _v in node.value:
        key = k.value if isinstance(k, yaml.ScalarNode) else ""
        if key in seen:
            dup.append(key)
        seen.add(key)
    return dup


def check_file(path: Path) -> list:
    errors = []
    text = path.read_text(encoding="utf-8-sig")   # utf-8-sig：剥 BOM（review #23，与 init 口径一致）
    if not text.startswith("---"):
        return [f"{path.name}: 缺少 frontmatter (--- 开头)"]

    fm_text = _split_frontmatter(text)
    if fm_text is None:
        return [f"{path.name}: frontmatter 未正确闭合 (需两对 ---)"]

    for k in _dup_keys(fm_text):
        errors.append(f"{path.name}: YAML 重复键 {k!r}（last-wins 静默覆盖）")

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


# 风格卡场景/维度枚举——单源见 style_common.SCENE_INJECTION（review #36）
STYLE_CARD_SCENE_TYPES = STYLE_CARD_SCENE_TYPES
STYLE_CARD_DIMS = STYLE_CARD_DIMS


def _pct_sum_errors(d: dict, label: str, expected: float = 100, max_sum: float | None = None) -> list:
    """占比/分布 dict 求和校验：值必须全为数值（type 排除 bool）、非负；全零 = 占位跳过；非零须和≈expected（或≤max_sum）。

    字符串值（LLM 或手改）不再被 `if total and` 静默跳过——非数值直接报错；
    负值（{120,-20} 蒙混和=100）同样报错（review #19）。"""
    bad = [k for k, v in d.items() if type(v) not in (int, float)]
    if bad:
        return [f"{label} 值应为数值（非数值键: {sorted(bad)}）"]
    neg = [k for k, v in d.items() if v < 0]
    if neg:
        return [f"{label} 含负值（键: {sorted(neg)}）"]
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


def check_style_card(path: Path, fm: dict | None = None) -> list:
    """校验一张风格卡。fm 可预解析传入（review #43：check_style_cards 批量调用只解析一次）。"""
    errors = []
    text = path.read_text(encoding="utf-8-sig")   # utf-8-sig：剥 BOM（review #23，与 init 口径一致）
    fm_text = _split_frontmatter(text)
    if fm_text is None:
        return [f"{path.name}: 风格卡缺 frontmatter（需两对 ---）"]
    for k in _dup_keys(fm_text):
        errors.append(f"{path.name}: YAML 重复键 {k!r}（last-wins 静默覆盖）")
    if fm is None:
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
            for dim, ovd in ov.items():
                if dim not in STYLE_CARD_DIMS:
                    errors.append(f"{path.name}: override 出现未知维度 {dim!r}")
                elif not isinstance(ovd, dict):
                    errors.append(f"{path.name}: override.{dim} 需为 dict（当前 {type(ovd).__name__}）")
                else:
                    for k, v in ovd.items():          # 值校验：负数 / 占比越界（review #21）
                        if type(v) in (int, float) and not isinstance(v, bool):
                            if v < 0:
                                errors.append(f"{path.name}: override.{dim}.{k} 为负值（{v!r}）")
                            elif k.endswith(("_pct", "_ratio")) and v > 100:
                                errors.append(f"{path.name}: override.{dim}.{k} 占比越界 0-100（{v!r}）")
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
        if path.resolve() in {c.resolve() for c in candidates}:
            errors.append(f"{path.name}: inherits 自引用（继承自身，会形成环）")
        if not any(c.exists() for c in candidates):
            try:
                rels = "、".join(str(c.relative_to(ROOT)) for c in candidates)
            except ValueError:
                rels = "、".join(str(c) for c in candidates)  # 路径不在 ROOT 下（测试/外部调用）
            errors.append(f"{path.name}: inherits 引用不存在: {inh}（期望 {rels}）")
    # --- 蒸馏卡可选增强字段（2026-08-12 双态：存在才校验，缺失兼容旧卡/未蒸馏卡） ---
    def _pct_ok(v):
        # 决策 A 单位校验单源（style_common.pct_ok，review #39）：0-100 百分数（type 排除 bool）。
        # 旧 jieba 引擎产出 0-100 一位小数百分数（13.4），无 0-1 分数假设——0.3 是 0.3% 而非 30%。
        return pct_ok(v)

    def _pct_field(dim, field, val):
        errors.append(f"{path.name}: {dim}.{field} 需为 0-100 数值（当前 {val!r}）")

    def _density_ok(v):
        """密度字段（每百字 X 个）：非负数值即可（review #18——密度字段此前全库无校验）。"""
        return type(v) in (int, float) and not isinstance(v, bool) and v >= 0

    def _density_field(dim, field, val):
        errors.append(f"{path.name}: {dim}.{field} 需为非负数值（当前 {val!r}）")

    lex = fm.get("lexicon") if isinstance(fm.get("lexicon"), dict) else {}
    for f in ("adj_density_per_100", "adv_density_per_100", "four_phrase_freq_per_100"):
        v = lex.get(f)
        if v is not None and not _density_ok(v):
            _density_field("lexicon", f, v)
    npr = lex.get("name_pronoun_ratio")
    if isinstance(npr, dict):
        keys = set(npr)
        if keys != {"name", "he_she", "i_you"}:
            errors.append(f"{path.name}: name_pronoun_ratio 键应为 name/he_she/i_you（当前 {sorted(keys)}）")
        else:
            for e in _pct_sum_errors(npr, f"{path.name}: name_pronoun_ratio 三维和"):
                errors.append(e)
    elif npr is not None and not _pct_ok(npr):
        errors.append(f"{path.name}: lexicon.name_pronoun_ratio 标量需为 0-100 数值（旧引擎存人名/代词比值；当前 {npr!r}）")
    for wf in ("preferred_words", "banned_words"):
        wv = lex.get(wf)
        if wv is not None and not isinstance(wv, list):
            errors.append(f"{path.name}: lexicon.{wf} 需为列表（当前 {type(wv).__name__}）")

    syn = fm.get("syntax") if isinstance(fm.get("syntax"), dict) else {}
    for f in ("single_sentence_paragraph_pct", "question_ratio", "exclamation_ratio"):
        v = syn.get(f)
        if v is not None and not _pct_ok(v):
            _pct_field("syntax", f, v)
    for f in ("avg_sentence_length", "avg_sentences_per_paragraph"):
        v = syn.get(f)
        if v is not None and not _density_ok(v):
            _density_field("syntax", f, v)
    dia = fm.get("dialogue_style") if isinstance(fm.get("dialogue_style"), dict) else {}
    if dia.get("subtext_ratio") is not None and not _pct_ok(dia["subtext_ratio"]):
        _pct_field("dialogue_style", "subtext_ratio", dia["subtext_ratio"])
    for f in ("avg_dialogue_length", "interrupt_freq_per_100"):
        v = dia.get(f)
        if v is not None and not _density_ok(v):
            _density_field("dialogue_style", f, v)

    em = fm.get("emotion_expression") if isinstance(fm.get("emotion_expression"), dict) else {}
    for f in ("direct_pct", "action_physiology_pct", "environment_projection_pct", "inner_monologue_pct"):
        v = em.get(f)
        if v is not None and not _pct_ok(v):
            _pct_field("emotion_expression", f, v)

    vs = fm.get("verb_style") if isinstance(fm.get("verb_style"), dict) else {}
    if vs.get("strength") not in (None, "", "weak", "medium", "strong"):
        errors.append(f"{path.name}: verb_style.strength 应为 weak/medium/strong（当前 {vs.get('strength')!r}）")
    for f in ("action_verb_ratio", "mental_verb_ratio", "state_verb_ratio"):
        v = vs.get(f)
        if v is not None and not _pct_ok(v):
            _pct_field("verb_style", f, v)

    coh = fm.get("cohesion") if isinstance(fm.get("cohesion"), dict) else {}
    if coh.get("transition_sentence_ratio") is not None and not _pct_ok(coh["transition_sentence_ratio"]):
        _pct_field("cohesion", "transition_sentence_ratio", coh["transition_sentence_ratio"])
    if coh.get("conjunction_freq_per_100") is not None \
            and not _density_ok(coh["conjunction_freq_per_100"]):
        _density_field("cohesion", "conjunction_freq_per_100", coh["conjunction_freq_per_100"])

    rhe = fm.get("rhetoric") if isinstance(fm.get("rhetoric"), dict) else {}
    if rhe.get("metaphor_density_per_100") is not None \
            and not _density_ok(rhe["metaphor_density_per_100"]):
        _density_field("rhetoric", "metaphor_density_per_100", rhe["metaphor_density_per_100"])

    for key in ("hard_constraints", "soft_guidance"):
        v = fm.get(key)
        if v is not None and not isinstance(v, list):
            errors.append(f"{path.name}: {key} 需为列表")
    if fm.get("few_shot_examples") is not None and not isinstance(fm.get("few_shot_examples"), list):
        errors.append(f"{path.name}: few_shot_examples 需为列表")

    rhy = fm.get("rhythm") if isinstance(fm.get("rhythm"), dict) else {}
    _FIVE = ("dialogue_pct", "action_pct", "environment_pct", "inner_thought_pct", "narration_pct")
    if "override" not in fm:
        missing = [f for f in _FIVE if f not in rhy]
        if missing:
            errors.append(f"{path.name}: rhythm 缺五层占比键 {missing}（缺任一键整节校验跳过，review #20）")
    if all(f in rhy for f in _FIVE):
        five = {f: rhy[f] for f in _FIVE}
        for e in _pct_sum_errors(five, f"{path.name}: 五层占比总计", max_sum=110):   # 五层可重叠，上限 110%（spec §5.1）
            errors.append(e)
        for f in _FIVE:                                                             # 单桶 0-100（防 dialogue_pct:110 蒙混）
            if not _pct_ok(five[f]):
                _pct_field("rhythm", f, five[f])

    _DIST = {"syntax": ["sentence_length_dist"], "rhetoric": ["metaphor_preference", "sensory_dist"]}
    for dim, fields in _DIST.items():
        d = fm.get(dim) if isinstance(fm.get(dim), dict) else {}
        for f in fields:
            sub = d.get(f)
            if isinstance(sub, dict) and sub:
                for e in _pct_sum_errors(sub, f"{path.name}: {f} 分布和"):
                    errors.append(e)
    return errors


def _resolve_inherits(p: Path, inh: str) -> Path | None:
    """inherits 目标解析（与 check_style_card 相同的双候选路径）→ 命中文件或 None。"""
    for c in (p.parent / inh, p.parent.parent / inh):
        if c.exists():
            return c.resolve()
    return None


def check_style_cards() -> list:
    base = ROOT / "templates" / "settings"
    main = base / "writing-style.md"
    if not main.exists():
        return ["templates/settings/writing-style.md 不存在（旧布局仓库？）"]
    cards = [main] + sorted((base / "style-profiles").rglob("*.md"))   # 递归：含 genre-baselines/**/base|benchmark|delta
    # 统一解析一次（review #43：此前每卡解析两遍——校验一遍、继承环检测一遍）
    parsed: dict[str, dict] = {}
    for p in cards:
        fm_text = _split_frontmatter(p.read_text(encoding="utf-8-sig"))
        if fm_text:
            try:
                fm = yaml.safe_load(fm_text)
            except Exception:
                fm = {}
            parsed[str(p.resolve())] = fm if isinstance(fm, dict) else {}
    errors = []
    for p in cards:
        errors.extend(check_style_card(p, parsed.get(str(p.resolve()))))
    # 继承环检测（跨文件 DFS）：A→B→A 循环在单卡存在性检查中不被发现
    graph = {}
    for key, fm in parsed.items():
        if fm.get("inherits"):
            tgt = _resolve_inherits(Path(key), fm["inherits"])
            graph[key] = str(tgt) if tgt else None
    _visited: set[str] = set()
    _cycles: set[str] = set()

    def _find_cycle(n: str, stack: list[str]) -> list[str] | None:
        if n in stack:
            return stack[stack.index(n):] + [n]
        if n in _visited or n not in graph:
            return None
        _visited.add(n)
        nxt = graph[n]
        if nxt:
            r = _find_cycle(nxt, stack + [n])
            if r:
                return r
        return None

    for start in list(graph):
        cyc = _find_cycle(start, [])
        if cyc:
            _cycles.add(" → ".join(cyc))
    for cyc in sorted(_cycles):
        errors.append(f"inherits 继承环：{cyc}")
    return errors


def check_project_cards(project: Path) -> list:
    """校验运行态项目卡（settings/writing-style.md + settings/style-profiles/**）。
    仓库模板卡由 check_style_cards 校验；项目卡是 style-distiller 蒸馏落盘产物（review #18）。"""
    base = project / "settings"
    if not base.exists():
        return []
    cards = []
    main = base / "writing-style.md"
    if main.exists():
        cards.append(main)
    profiles = base / "style-profiles"
    if profiles.exists():
        cards.extend(sorted(profiles.rglob("*.md")))
    errors = []
    for p in cards:
        errors.extend(check_style_card(p))
    return errors


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="agent 定义静态检查")
    ap.add_argument("--project", default=None,
                    help="额外校验运行态项目卡（settings/ 下写作风格卡，style-distiller 蒸馏产物）")
    args = ap.parse_args()

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
        text = f.read_text(encoding="utf-8-sig")
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

    if args.project:
        proj_errs = check_project_cards(Path(args.project))
        for e in proj_errs:
            print(f"  ❌ [项目] {e}")
        all_errors.extend(proj_errs)

    if all_errors:
        print(f"\n共 {len(all_errors)} 个问题")
        return 1
    print("✅ agent 定义全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
