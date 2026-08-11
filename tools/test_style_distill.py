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
        old = tmp / "settings" / "writing-style.md"
        old.write_text("# 写作风格\n\n## role（叙事身份）\n\n第一人称\n\n"
                       "## core_principles（不可违背的写作信条）\n\n- 不写废话\n\n"
                       "## possible_mistakes（AI 易犯错误）\n\n- 套路化\n\n"
                       "## depiction_techniques（描写层次和手法）\n\n感官描写\n",
                       encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        check("迁移后 init exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        fm = parse_fm(wsf)
        check("迁移后含 frontmatter", fm is not None)
        body = wsf.read_text(encoding="utf-8")
        check("迁移保留叙事身份内容", "第一人称" in body)
        check("迁移保留硬约束内容", "不写废话" in body)
        check("迁移保留易错内容", "套路化" in body)
        check("迁移保留描写手法内容", "感官描写" in body)
        check("迁移备份旧版", (tmp / "settings" / ".style-versions" / "v0_migrated.md").exists())


def main():
    test_card_schema()
    test_migration()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
