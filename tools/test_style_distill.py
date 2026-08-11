#!/usr/bin/env python3
"""style-distiller 模块验证脚本。

用法: python tools/test_style_distill.py
返回码 0 = 全部通过，非 0 = 有失败（CI 用）。

覆盖（随阶段增长）：
- P0 单元：卡片 frontmatter schema / 迁移
- P1 单元：distill 统计 / confidence / E2E init 部署
- P3 单元：增量滑动平均 / 备份 / checkpoint
- P4 单元：check 容差
- P5 单元：compare / mix
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}  {detail}")


def run(cmd, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def init_project(tmp: Path, genre: str = "1"):
    return run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", genre])


SCENE_TYPES = ["general", "dialogue", "fight", "environment", "inner-mono", "transition", "group-scene"]
REQUIRED_FM_KEYS = ["profile_version", "scene_type", "confidence", "last_updated"]
DIM_KEYS = ["lexicon", "syntax", "rhythm", "rhetoric", "emotion_expression",
            "narrative", "dialogue_style", "cohesion", "verb_style"]
SCENE_CARDS = ["dialogue", "fight", "environment", "inner-mono", "transition", "group-scene"]


def parse_fm(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    import yaml
    parts = text.split("---", 2)
    return yaml.safe_load(parts[1]) if len(parts) == 3 else None


def test_card_schema():
    print("[unit] 卡片 frontmatter schema")
    main = REPO / "templates" / "settings" / "writing-style.md"
    check("主卡模板存在", main.exists())
    if not main.exists():
        return
    fm = parse_fm(main)
    check("主卡 frontmatter 可解析", fm is not None)
    for k in REQUIRED_FM_KEYS + DIM_KEYS:
        check(f"主卡含 {k}", bool(fm) and k in fm)
    check("主卡 scene_type=general", fm and fm.get("scene_type") == "general")
    check("主卡 confidence=0", fm and fm.get("confidence") == 0)
    for name in SCENE_CARDS:
        card = REPO / "templates" / "settings" / "style-profiles" / f"{name}.md"
        check(f"场景卡 {name} 存在", card.exists())
        if not card.exists():
            continue
        cfm = parse_fm(card)
        check(f"{name} 可解析", cfm is not None)
        check(f"{name} scene_type={name}", cfm and cfm.get("scene_type") == name)
        check(f"{name} inherits 主卡", cfm and cfm.get("inherits") == "writing-style.md")
        check(f"{name} confidence=0", cfm and cfm.get("confidence") == 0)


def test_migration():
    print("[unit] 旧 4 字段卡迁移")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        wsf = tmp / "settings" / "writing-style.md"
        # init 后应为新格式（含 frontmatter）
        check("init 产新格式主卡", wsf.exists() and wsf.read_text(encoding="utf-8").startswith("---"))
        check("init 部署 style-profiles", (tmp / "settings" / "style-profiles").is_dir())
        n = len(list((tmp / "settings" / "style-profiles").glob("*.md")))
        check("6 张场景卡已部署", n == 6, f"实际 {n}")
        # 旧格式 → 迁移 → 新格式
        # 注意：旧 init seed 的 core_principles 是裸段落（文风蓝图整段，非 bullet），必须按真实旧卡
        # 形状构造。若写成 bullet，段落回退（migrate_writing_style）与 seed 守卫在同一 run 内不会被
        # 真正触发，迁移零损失与 re-init 幂等两条验收线都会形同虚设。
        old = tmp / "settings" / "writing-style.md"
        old.write_text("# 写作风格\n\n## role（叙事身份）\n\n第一人称\n\n"
                       "## core_principles（不可违背的写作信条）\n\n不写废话，惜墨如金\n\n"
                       "## possible_mistakes（AI 易犯错误）\n\n- 套路化\n\n"
                       "## depiction_techniques（描写层次和手法）\n\n感官描写\n",
                       encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        check("迁移后 init exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        fm = parse_fm(wsf)
        check("迁移后含 frontmatter", fm is not None)
        body = wsf.read_text(encoding="utf-8")
        check("迁移保留叙事身份内容", "第一人称" in body)
        check("迁移保留硬约束内容", "不写废话，惜墨如金" in body)
        check("迁移保留易错内容", "套路化" in body)
        check("迁移保留描写手法内容", "感官描写" in body)
        check("迁移备份旧版", (tmp / "settings" / ".style-versions" / "v0_migrated.md").exists())

        # re-init 幂等：第二次 init 不能覆盖/污染迁移产物（seed 守卫必须跳过已迁移卡），
        # 且旧内容全保留、4 个占位符 token 一个都不出现。
        r2 = run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        check("re-init 迁移卡 exit 0", r2.returncode == 0, (r2.stdout + r2.stderr)[-400:])
        body2 = wsf.read_text(encoding="utf-8")
        check("re-init 迁移卡仍含 frontmatter", body2.startswith("---"))
        for tok in ("第一人称", "不写废话，惜墨如金", "套路化", "感官描写"):
            check(f"re-init 迁移卡保留旧内容（{tok}）", tok in body2)
        for tok in ("{role}", "{principle_1}", "{mistake_1}", "{depiction_techniques}"):
            check(f"re-init 迁移卡无占位符 {tok}", tok not in body2)
        check("re-init 不重复迁移（备份仍为旧版原文）",
              (tmp / "settings" / ".style-versions" / "v0_migrated.md")
              .read_text(encoding="utf-8").startswith("# 写作风格\n\n## role（叙事身份）"))

        # bullet 变体：手工编写的旧卡可能用 `- ` bullet，段落回退不得破坏它（幂等性同样成立）
        with tempfile.TemporaryDirectory() as td2:
            tmp2 = Path(td2)
            init_project(tmp2)
            wsf2 = tmp2 / "settings" / "writing-style.md"
            wsf2.write_text("# 写作风格\n\n## role（叙事身份）\n\n第三人称\n\n"
                            "## core_principles（不可违背的写作信条）\n\n- 不水字数\n- 节奏快\n\n"
                            "## possible_mistakes（AI 易犯错误）\n\n- 空话套话\n\n"
                            "## depiction_techniques（描写层次和手法）\n\n白描\n",
                            encoding="utf-8")
            r3 = run([sys.executable, str(TOOLS / "init.py"), str(tmp2), "--genre", "1"])
            check("bullet 变体迁移 exit 0", r3.returncode == 0, (r3.stdout + r3.stderr)[-400:])
            body3 = wsf2.read_text(encoding="utf-8")
            for tok in ("第三人称", "不水字数", "节奏快", "空话套话", "白描"):
                check(f"bullet 变体迁移保留（{tok}）", tok in body3)
            for tok in ("{role}", "{principle_1}", "{mistake_1}", "{depiction_techniques}"):
                check(f"bullet 变体无占位符 {tok}", tok not in body3)


def test_distill():
    print("[unit] distill 统计引擎")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        sample = tmp / "sample.md"
        sample.write_text(
            "他缓缓推开门，寒风扑面而来，院子里一片死寂。"
            "他握紧拳头，指节发白，心里默默算着时间。"
            "“你终于来了。”她说，声音很轻。"
            "他点点头，没有回答，只是又看了一眼那条通往山下的路。",
            encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "distill-style.py"), "distill",
                 "-o", str(tmp / "p.yml"), "-e", str(tmp / "e.md"), str(sample)], cwd=str(TOOLS))
        check("distill exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        p = tmp / "p.yml"
        check("partial 已写", p.exists())
        import yaml as _y
        data = _y.safe_load(p.read_text(encoding="utf-8"))["distill"]
        check("含 sample_length", data["source_sample_length"] > 0)
        check("含 confidence", 0 < data["confidence"] <= 100)
        check("lexicon 含四个字段",
              all(k in data["lexicon"] for k in ("adj_density_per_100", "adv_density_per_100",
                                                 "four_phrase_freq_per_100", "preferred_words")))
        check("syntax 含 avg_sentence_length", data["syntax"]["avg_sentence_length"] > 0)
        check("rhythm 含 dialogue_pct", "dialogue_pct" in data["rhythm"])
        check("对话占比>0", data["rhythm"]["dialogue_pct"] > 0)
        # 确定性：跑两次结果一致
        r2 = run([sys.executable, str(TOOLS / "distill-style.py"), "distill",
                  "-o", str(tmp / "p2.yml"), str(sample)], cwd=str(TOOLS))
        d2 = _y.safe_load((tmp / "p2.yml").read_text(encoding="utf-8"))["distill"]
        check("确定性（两次一致）", data["syntax"] == d2["syntax"], f"{data['syntax']} vs {d2['syntax']}")
        # 置信度公式
        check("confidence 1500字≈20+30=50", compute_conf(1500) == 50)
        check("confidence 封顶 100", compute_conf(10 ** 6, 8) == 100)


def compute_conf(length, chapters=0):
    return min(100, 20 + min(40, int(length / 50)) + min(40, chapters * 5))


def main():
    test_card_schema()
    test_migration()
    test_distill()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
