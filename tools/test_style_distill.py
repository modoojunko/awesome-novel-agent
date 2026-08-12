#!/usr/bin/env python3
"""style-distiller LLM 重构验证脚本（模板/流程/schema 断言，不依赖 LLM 精确数值）。

用法: python tools/test_style_distill.py
返回码 0 = 全部通过（CI 用）。

覆盖（spec §10；渲染/验收/抽卡判定部分在 tools/test_style_rules.py，本文件不重复）：
- schema 合法性：check-agents 的卡校验对主卡/场景卡模板通过（含分布和=100、枚举）
- 13 模板方法论：feature-extract.md 十三节齐全 + verify-checklist/rendering-rules 存在、退役模板已删
- 退役清理：三工具已删、CI 无 jieba、init/sync 无风格工具部署
- 抽卡契约：rewrite_of/violations 字段 + 无 style-update-order 残留（novel-agent/writer/dispatch 文档）+ writer 不以卡正文四字段为风格源
- 双态：未蒸馏模板 / 蒸馏卡 / 遗留 jieba 卡三态过 check_style_card（增强字段可选、存在才校验）+ init 模板保留 locked（未蒸馏态零改动）
"""
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ok  {name}")
    else: FAIL += 1; print(f"  FAIL {name}  {detail}")

def test_feature_extract():
    t = (REPO / "knowledge/style-distill/prompt-templates/feature-extract.md").read_text(encoding="utf-8")
    for name in ["模板 1", "模板 2", "模板 3", "模板 4", "模板 5", "模板 6", "模板 7",
                 "模板 8", "模板 9", "模板 10", "模板 11", "模板 12", "模板 13", "阶段一", "阶段二", "阶段三"]:
        check(f"feature-extract 含 {name}", name in t)
    # 13 模板 schema token（spec §9：量化表键完整、建模规则格式正确——句式卡结构公式/对话模式轮次序列/节奏模型关键参数/锚点模型章首章尾）
    for token in ("量化表", "结构公式", "轮次序列", "关键参数", "章首锚点", "章尾锚点"):
        check(f"feature-extract 含 schema token「{token}」", token in t)
    for f in ("rendering-rules.md", "verify-checklist.md"):
        check(f"{f} 存在", (REPO / "knowledge/style-distill/prompt-templates" / f).exists())
    for gone in ("distill-prompt.md", "injection-template.md", "gate-g-checklist.md"):
        check(f"退役模板 {gone} 已删", not (REPO / "knowledge/style-distill/prompt-templates" / gone).exists())

def test_schema_templates():
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_agents", str(TOOLS / "check-agents.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    main_tpl = REPO / "templates/settings/writing-style.md"
    errs = mod.check_style_card(main_tpl)
    check("主卡模板过卡校验", not errs, "; ".join(errs))
    for scene in sorted((REPO / "templates/settings/style-profiles").glob("*.md")):
        errs = mod.check_style_card(scene)
        check(f"场景卡 {scene.name} 过卡校验", not errs, "; ".join(errs))

def test_retire_clean():
    for bad in ("tools/distill-style.py", "tools/compare-style.py", "tools/mix-style.py"):
        check(f"{bad} 已删", not (REPO / bad).exists())
    static = (REPO / ".github/workflows/static.yml").read_text(encoding="utf-8")
    check("CI 无 jieba", "jieba" not in static)
    check("CI 运行 test_style_rules", "test_style_rules.py" in static)
    req = (REPO / "tools/requirements.txt").read_text(encoding="utf-8")
    check("requirements 无 jieba", "jieba" not in req)
    init = (REPO / "tools/init.py").read_text(encoding="utf-8")
    check("init 无 distill-style 部署", "distill-style.py" not in init)
    sync = (REPO / "tools/sync-project.py").read_text(encoding="utf-8")
    check("sync 无 _STYLE_TOOL_NAMES", "_STYLE_TOOL_NAMES" not in sync)

def test_reroll_contract():
    for f in ("agents/novel-agent.md", "agents/writer.md", "skills/writing-execution.md", "skills/novel-dispatch.md"):
        t = (REPO / f).read_text(encoding="utf-8")
        check(f"{f} 含 rewrite_of", "rewrite_of" in t)
        check(f"{f} 含 violations", "violations" in t)
        check(f"{f} 无 style-update-order", "style-update-order" not in t)
    writer_t = (REPO / "agents/writer.md").read_text(encoding="utf-8")
    check("writer 不以卡正文为风格源",
          "写作风格方法论" not in writer_t and "depiction_techniques" not in writer_t
          and "possible_mistakes" not in writer_t)

def test_anti_ai_verify():
    skill = (REPO / "skills/anti-ai.md").read_text(encoding="utf-8")
    check("anti-ai 含指令遵循验收", "指令遵循" in skill or "案例 2" in skill or "verify-checklist" in skill)
    check("anti-ai 无 distill-style.py", "distill-style.py" not in skill)
    check("anti-ai 无 gate-g-checklist", "gate-g-checklist" not in skill)

def test_dual_mode():
    import importlib.util, tempfile, yaml
    spec = importlib.util.spec_from_file_location("check_agents", str(TOOLS / "check-agents.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    main_tpl = REPO / "templates/settings/writing-style.md"
    fm = yaml.safe_load(main_tpl.read_text(encoding="utf-8").split("---", 2)[1])
    # 未蒸馏态：模板零改动、confidence=0 过校验（spec §4）
    check("未蒸馏态（旧模板原样）过卡校验", not mod.check_style_card(main_tpl))
    check("未蒸馏态 confidence=0", fm.get("confidence") == 0, str(fm.get("confidence")))
    # 蒸馏卡：原卡结构叠加声音层 + 增强字段 + confidence>0 → 过校验
    fm["profile_name"] = "测试蒸馏卡"; fm["confidence"] = 75
    fm["lexicon"]["name_pronoun_ratio"] = {"name": 45, "he_she": 50, "i_you": 5}
    fm["rhetoric"]["metaphor_preference"] = {"weapon_metal": 5, "nature": 10, "body": 20, "abstract": 30, "other": 35}
    fm["rhetoric"]["sensory_dist"] = {"visual": 72, "auditory": 15, "tactile": 10, "olfactory": 2, "gustatory": 1}
    fm["emotion_expression"]["inner_monologue_pct"] = 35
    fm["verb_style"]["strength"] = "medium"
    fm["hard_constraints"] = ["内心独白必须用引号包裹"]
    fm["soft_guidance"] = ["整体基调：轻松吐槽向"]
    fm["few_shot_examples"] = [{"type": "inner_thought", "text": "好想死啊", "reason": "口头禅式吐槽"}]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "writing-style.md"
        p.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        errs = mod.check_style_card(p)
        check("蒸馏卡（声音层+增强字段+confidence>0）过卡校验", not errs, "; ".join(errs))
    # 遗留 jieba 蒸馏卡：confidence>0、无声音层/增强字段 → 过校验（spec §6.0b 回退兼容）
    fm2 = yaml.safe_load(main_tpl.read_text(encoding="utf-8").split("---", 2)[1])
    fm2["confidence"] = 70
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "writing-style.md"
        p.write_text("---\n" + yaml.safe_dump(fm2, allow_unicode=True, sort_keys=False) + "---", encoding="utf-8")
        errs = mod.check_style_card(p)
        check("遗留 jieba 卡（confidence>0 无声音层）过卡校验", not errs, "; ".join(errs))
    # init 模板保留 locked（未蒸馏态零改动，无迁移）
    init = (REPO / "tools/init.py").read_text(encoding="utf-8")
    check("init 模板保留 locked（未蒸馏态零改动）", "locked" in init)
    # prompt-crafting 双态分支（spec §6：未蒸馏=正文定性四字段注入现状不变 / 已蒸馏=案例 2 渲染）
    pc = (REPO / "skills/prompt-crafting.md").read_text(encoding="utf-8")
    check("prompt-crafting 含 confidence 分支", "confidence" in pc)
    check("prompt-crafting 保留未蒸馏定性注入节（写作风格约束）", "写作风格约束" in pc)
    check("prompt-crafting 引用 rendering-rules（已蒸馏渲染）", "rendering-rules" in pc)
    check("prompt-crafting 引用 案例 2 结构", "案例 2" in pc)

def run_all():
    test_feature_extract(); test_schema_templates(); test_retire_clean()
    test_reroll_contract(); test_anti_ai_verify(); test_dual_mode()
    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0

if __name__ == "__main__":
    sys.exit(run_all())
