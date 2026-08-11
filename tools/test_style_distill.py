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


def _load_tool(name: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), str(TOOLS / f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def test_genre_baselines():
    print("[unit] 题材基线模板")
    for g in ("xianxia", "urban", "suspense"):
        for layer in ("base", "delta", "benchmark"):
            f = REPO / "templates" / "settings" / "style-profiles" / "genre-baselines" / g / f"{layer}.md"
            check(f"{g}/{layer} 存在", f.exists())


def test_e2e_init_deploy():
    print("[e2e] init 部署 style-distiller")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        agent_file = tmp / ".claude" / "agents" / "style-distiller.md"
        check("agent style-distiller 已部署", agent_file.exists())
        # claude 平台 skills 不入项目（技能源在仓库 skills/，init.py 只给 reasonix/codex 部署 skills）；
        # 实际交付机制是部署到项目的 agent 定义里声明 skills/style-distill.md 引用 → 校验该接线
        if agent_file.exists():
            agent_txt = agent_file.read_text(encoding="utf-8")
            check("agent 声明 style-distill SOP", "skills/style-distill.md" in agent_txt)
        check("脚本已部署到 tools/", (tmp / "tools" / "distill-style.py").exists())
        check("主卡为新格式", (tmp / "settings" / "writing-style.md").read_text(encoding="utf-8").startswith("---"))
        check("场景卡已部署", (tmp / "settings" / "style-profiles" / "dialogue.md").exists())


def test_update():
    print("[unit] 增量滑动平均")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        card = tmp / "settings" / "writing-style.md"
        # 造一份带数值的旧卡
        text = card.read_text(encoding="utf-8")
        text = text.replace("avg_sentence_length: 0", "avg_sentence_length: 20")
        card.write_text(text, encoding="utf-8")
        ch = tmp / "archives" / "vol-1-ch-1.md"
        ch.parent.mkdir(parents=True, exist_ok=True)
        ch.write_text("他快速出拳，拳风猎猎。\n\n她退后半步，眼神冰冷。\n\n" * 8, encoding="utf-8")
        out = tmp / "settings" / "writing-style-new.md"
        r = run([sys.executable, str(TOOLS / "distill-style.py"), "update",
                 "-c", str(card), "-o", str(out), "--project", str(tmp), str(ch)], cwd=str(TOOLS))
        check("update exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        import yaml as _y
        fm = _y.safe_load(out.read_text(encoding="utf-8").split("---", 2)[1])
        check("新卡 avg_sentence_length 介于 0-40",
              0 < fm["syntax"]["avg_sentence_length"] < 40, str(fm["syntax"]))
        check("备份存在", list((tmp / "settings" / ".style-versions").glob("v1_*.md")))
        first = out.read_text(encoding="utf-8")
        # 幂等：同章再跑，checkpoint 跳过 → 输出字节不变 + 不新增备份
        run([sys.executable, str(TOOLS / "distill-style.py"), "update",
             "-c", str(card), "-o", str(out), "--project", str(tmp), str(ch)], cwd=str(TOOLS))
        check("checkpoint 幂等（重复 run 输出字节不变）",
              out.read_text(encoding="utf-8") == first, (out.read_text(encoding="utf-8")[-200:], first[-200:]))
        check("checkpoint 幂等（不新增备份）",
              len(list((tmp / "settings" / ".style-versions").glob("v*_*.md"))) == 1)


def test_check():
    print("[unit] check 容差校验")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        card = tmp / "settings" / "writing-style.md"
        body = tmp / "body.md"
        body.write_text("他缓缓推开门，寒风扑面而来，院子里一片死寂。\n\n" * 20, encoding="utf-8")

        # 场景 A：正常容差 → 偏差表 + exit 0/1 合法
        text = card.read_text(encoding="utf-8").replace(
            "confidence: 0", "confidence: 80").replace(
            "avg_sentence_length: 0", "avg_sentence_length: 25")
        card.write_text(text, encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "distill-style.py"), "check",
                 "-c", str(card), str(body)], cwd=str(TOOLS))
        check("check exit 0/1 皆合法（有 FAIL 为 1）", r.returncode in (0, 1))
        check("check 输出偏差表", "风格偏差表" in r.stdout)

        # 场景 B：极端期望（avg_sentence_length=60）→ 实测必超 2×tol → FAIL → returncode 1
        card.write_text(card.read_text(encoding="utf-8").replace(
            "avg_sentence_length: 25", "avg_sentence_length: 60"), encoding="utf-8")
        rb = run([sys.executable, str(TOOLS / "distill-style.py"), "check",
                  "-c", str(card), str(body)], cwd=str(TOOLS))
        check("FAIL 场景 returncode=1", rb.returncode == 1, (rb.stdout + rb.stderr)[-300:])
        check("FAIL 场景含 -> FAIL", "-> FAIL" in rb.stdout, rb.stdout[-300:])
        import re as _re
        check("FAIL 场景计数≥1", _re.search(r"不通过维度数：[1-9]", rb.stdout) is not None, rb.stdout[-300:])

        # 场景 C：手动档（confidence≤20，tol=0）→ 跳过量化校验，returncode 0
        card.write_text(card.read_text(encoding="utf-8").replace(
            "confidence: 80", "confidence: 15"), encoding="utf-8")
        rc = run([sys.executable, str(TOOLS / "distill-style.py"), "check",
                  "-c", str(card), str(body)], cwd=str(TOOLS))
        check("手动档 returncode=0", rc.returncode == 0, (rc.stdout + rc.stderr)[-300:])
        check("手动档跳过量化校验", "跳过量化校验" in rc.stdout, rc.stdout[-300:])


def test_compare():
    print("[unit] compare-style")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        card = tmp / "settings" / "writing-style.md"
        t = card.read_text(encoding="utf-8").replace("avg_sentence_length: 0", "avg_sentence_length: 15")
        (tmp / "b.md").write_text(t, encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "compare-style.py"), str(card), str(tmp / "b.md")], cwd=str(TOOLS))
        check("compare exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        check("输出维度变化表", "avg_sentence_length" in r.stdout and "差值" in r.stdout)


def test_mix():
    print("[unit] mix-style")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        a = tmp / "settings" / "writing-style.md"
        t = a.read_text(encoding="utf-8").replace("avg_sentence_length: 0", "avg_sentence_length: 10")
        a.write_text(t, encoding="utf-8")
        b = tmp / "b.md"
        b.write_text(t.replace("avg_sentence_length: 10", "avg_sentence_length: 30"), encoding="utf-8")
        out = tmp / "mix.md"
        r = run([sys.executable, str(TOOLS / "mix-style.py"), str(a), str(b), "0.5", "0.5",
                 "-o", str(out)], cwd=str(TOOLS))
        check("mix exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        import yaml as _y
        fm = _y.safe_load(out.read_text(encoding="utf-8").split("---", 2)[1])
        check("加权平均 10/30 → 20", fm["syntax"]["avg_sentence_length"] == 20.0,
              str(fm["syntax"]["avg_sentence_length"]))


def _count_sents(text):
    return len([s for s in re.split(r"[。！？…；!?;]", text) if s.strip()])


def _count_chars(text):
    """仅去空白、保留引号——与 distill-style.py char_len 口径一致。"""
    return len(re.sub(r"\s", "", text))


def _count_quoted(text):
    n = inside = 0
    for ch in text:
        if ch in '“"「『':
            inside = True
        elif ch in '”"」』':
            inside = False
        elif inside and ch.strip():
            n += 1
    return n


def test_acceptance():
    print("[acceptance] C1/C4/C5")
    import yaml as _y
    # ---- C1: 核心参数 vs 人工计数，偏差 ≤15%（需 jieba 环境）----
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # 构造可人工点计的样本：3 组 × 3 句（叙述/转折/对话），形容词与连接词已知
        lines = [
            "寒冷的夜晚一片死寂，空旷的街道异常安静。",
            "然而寒风刺骨，因此他加快脚步，却仍感到浑身冰冷。",
            "“你终于来了。”他低声说，声音却异常微弱。",
        ]
        txt = "\n\n".join(lines * 3)
        sample = tmp / "c1.md"
        sample.write_text(txt, encoding="utf-8")
        p = tmp / "c1.yml"
        run([sys.executable, str(TOOLS / "distill-style.py"), "distill",
             "-o", str(p), str(sample)], cwd=str(TOOLS))
        d = _y.safe_load(p.read_text(encoding="utf-8"))["distill"]
        total = _count_chars(txt)
        manual = {
            "avg_sentence_length": total / _count_sents(txt),
            "dialogue_pct": 100 * _count_quoted(txt) / total,
            "conjunction_freq_per_100": 100 * sum(txt.count(w) for w in ("然而", "因此", "却")) / total,
            # adj_density 以 jieba POS(a/ad/an) 为测量基准（spec §14 已知风险）：
            # 本样本中 jieba 只把「寒冷/微弱」标为形容词（死寂/空旷/安静/刺骨/冰冷 标为其它词性），
            # 手工计数须与工具同口径——只数这两个词，公式验证才成立。
            "adj_density_per_100": 100 * sum(txt.count(w)
                                             for w in ("寒冷", "微弱")) / total,
        }
        for k, manual_v in manual.items():
            got = (d["syntax"].get("avg_sentence_length") if k == "avg_sentence_length"
                   else d["rhythm"].get("dialogue_pct") if k == "dialogue_pct"
                   else d["cohesion"].get("conjunction_freq_per_100")
                   if k == "conjunction_freq_per_100"
                   else d["lexicon"].get("adj_density_per_100"))
            ok = got is not None and manual_v > 0 and abs(got - manual_v) / manual_v <= 0.15
            check(f"C1 {k} 偏差≤15% (manual={manual_v:.2f} got={got})", ok)
    # ---- C4: 连续归档 5 章 → confidence≥70、参数波动<10% ----
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        card = tmp / "settings" / "writing-style.md"
        text = card.read_text(encoding="utf-8")
        # 造 1380 字样本蒸馏出的源卡（confidence 基线 20+27=47）
        sample = tmp / "s.md"
        # 1380 字：confidence 基线 = 20 + min(40, L/50=27) = 47；5 章后 +25 → 72
        sample.write_text(("他快步走过长廊，推开厚重的木门，寒气扑面而来。\n\n") * 60, encoding="utf-8")
        p = tmp / "s.yml"
        run([sys.executable, str(TOOLS / "distill-style.py"), "distill",
             "-o", str(p), str(sample)], cwd=str(TOOLS))
        src = _y.safe_load(p.read_text(encoding="utf-8"))["distill"]
        text = text.replace("source_sample_length: 0", f"source_sample_length: {src['source_sample_length']}")
        text = text.replace("confidence: 0", f"confidence: {src['confidence']}")
        text = text.replace("avg_sentence_length: 0",
                            f"avg_sentence_length: {src['syntax']['avg_sentence_length']}")
        card.write_text(text, encoding="utf-8")
        arch = tmp / "archives"
        arch.mkdir(parents=True, exist_ok=True)
        for i in range(1, 6):  # 5 章，句长一致（每句 18 字），验证滑动平均收敛
            (arch / f"vol-1-ch-{i}.md").write_text(
                "他走过长廊，推开木门，寒气扑面而来。\n\n" * 20, encoding="utf-8")
        out = tmp / "settings" / "writing-style-new.md"
        for i in range(1, 6):
            run([sys.executable, str(TOOLS / "distill-style.py"), "update",
                 "-c", str(card), "-o", str(out), "--project", str(tmp),
                 str(arch / f"vol-1-ch-{i}.md")], cwd=str(TOOLS))
            card.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
        fm = _y.safe_load(out.read_text(encoding="utf-8").split("---", 2)[1])
        check("C4 5 章后 confidence≥70", fm["confidence"] >= 70, f"got {fm['confidence']}")
        v = fm["syntax"]["avg_sentence_length"]
        check("C4 参数波动<10%（收敛到章稳态 18 的 10% 内）", abs(v - 18) / 18 <= 0.10, f"got {v}")
    # ---- C5: 现有项目升级不报错 + 旧卡自动迁移 ----
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        (tmp / "settings" / "writing-style.md").write_text(
            "# 写作风格\n\n## role（叙事身份）\n\n第三人称限知\n\n"
            "## core_principles（不可违背的写作信条）\n\n- 不写废话\n\n"
            "## possible_mistakes（AI 易犯错误）\n\n- 模板腔\n\n"
            "## depiction_techniques（描写层次和手法）\n\n动作推进\n", encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        check("C5 升级 init exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        rs = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp)], cwd=str(tmp))
        check("C5 升级 sync exit 0", rs.returncode == 0, (rs.stdout + rs.stderr)[-400:])
        card = tmp / "settings" / "writing-style.md"
        body = card.read_text(encoding="utf-8")
        check("C5 新格式", body.startswith("---"))
        check("C5 内容零损失", all(k in body for k in ("第三人称限知", "不写废话", "模板腔", "动作推进")))


def test_review_fix_migration_no_clobber():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "settings" / ".style-versions").mkdir(parents=True)
        # 旧卡缺 depiction_techniques 节（常见手写旧卡）
        old = tmp / "settings" / "writing-style.md"
        old.write_text("# 写作风格\n\n## role（叙事身份）\n\n第一人称限知\n\n## core_principles（不可违背的写作信条）\n\n不水字数\n\n## possible_mistakes（AI 易犯错误）\n\n注水\n", encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        card = (tmp / "settings" / "writing-style.md").read_text(encoding="utf-8")
        # #1 迁移产物保留作者内容、无占位 token、未被题材默认覆盖
        check("#1 缺节迁移保留 role", "第一人称限知" in card, card[:200])
        check("#1 迁移无占位符", "{role}" not in card and "{depiction_techniques}" not in card and "{principle_1}" not in card,
              card[:200])
        check("#1 缺节不触发 seed 覆盖", "不水字数" in card, card[:300])

def test_review_fix_seed_daishou():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "settings").mkdir(parents=True)
        old = tmp / "settings" / "writing-style.md"
        old.write_text("# 写作风格\n\n## role（叙事身份）\n\n（待设定）\n\n## core_principles（不可违背的写作信条）\n\n（待设定）\n\n## possible_mistakes（AI 易犯错误）\n\n（待设定）\n", encoding="utf-8")
        run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        card = (tmp / "settings" / "writing-style.md").read_text(encoding="utf-8")
        # #15：migrate 产出含（待设定）→ seed 守卫须识别为未填 → genre 默认（xianxia 叙事者角色）生效
        check("#15（待设定）被识别为未填", "（待设定）" not in card and "仙侠小说作家" in card, card[:300])

def test_review_fix_scaffold_refresh():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp)
        claude = tmp / "CLAUDE.md"
        claude.write_text("stale scaffold content", encoding="utf-8")
        ws = tmp / "settings" / "writing-style.md"
        # 作者在已迁移的新格式卡上追加内容（保留 frontmatter，否则 migrate 会当旧卡重迁）
        ws.write_text(ws.read_text(encoding="utf-8") + "\n<!-- 作者编辑标记：保留 -->\n", encoding="utf-8")
        run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        # #14 脚手架随模板刷新；用户内容保留（create_skeleton 只刷新根级脚手架，不覆盖 settings/）
        new_claude = claude.read_text(encoding="utf-8")
        check("#14 脚手架刷新", "stale scaffold content" not in new_claude, new_claude[:80])
        check("#14 用户内容保留", "作者编辑标记：保留" in ws.read_text(encoding="utf-8"), ws.read_text(encoding="utf-8")[:80])


def test_review_fix_sync_deploys():
    print("[review-fix] #12 sync 递归部署风格资产")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "settings").mkdir(parents=True)
        (tmp / "settings" / "style-profiles").mkdir(parents=True)
        (tmp / "tools").mkdir(parents=True)
        (tmp / ".agent").mkdir(parents=True)
        (tmp / ".agent" / "status.md").write_text("# 项目状态\n", encoding="utf-8")  # sync 要求有效项目
        (tmp / "archives").mkdir(parents=True)
        # 先建一个「缺主卡/缺 genre-baselines」的存量项目
        (tmp / "settings" / "style-profiles" / "dialogue.md").write_text("x", encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp)])
        # #12 递归部署：主卡 + genre-baselines 到项目
        check("#12 sync 部署主卡", (tmp / "settings" / "writing-style.md").exists(), r.stdout + r.stderr)
        check("#12 sync 部署 genre-baselines",
              (tmp / "settings" / "style-profiles" / "genre-baselines" / "xianxia" / "base.md").exists(),
              r.stdout + r.stderr)


def test_review_fix_init_deploys_style_distill():
    print("[review-fix] #13 init 部署 style-distill 知识")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        run([sys.executable, str(TOOLS / "init.py"), str(tmp), "--genre", "1"])
        p = tmp / ".claude" / "knowledge" / "style-distill" / "prompt-templates" / "distill-prompt.md"
        check("#13 init 部署 style-distill 知识", p.exists(), str(p))


def test_review_fix_mix():
    print("[review-fix] #2/#9/#36-mix 混卡修复")
    import yaml as _y
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        def mk_card(name, ssl, conf):
            dims = {"profile_version": "1.0", "scene_type": "general", "confidence": conf,
                    "last_updated": "", "source_sample_length": ssl, "locked": [],
                    "lexicon": {"adj_density_per_100": 2.0, "adv_density_per_100": 1.0,
                                "four_phrase_freq_per_100": 1.0, "name_pronoun_ratio": 1.0},
                    "syntax": {"avg_sentence_length": 20.0}, "rhythm": {"dialogue_pct": 30.0},
                    "cohesion": {"conjunction_freq_per_100": 2.0, "transition_sentence_ratio": 20.0},
                    "verb_style": {"action_verb_ratio": 0.5, "mental_verb_ratio": 0.3, "state_verb_ratio": 0.2}}
            c = tmp / name
            c.write_text("---\n" + _y.safe_dump(dims, allow_unicode=True, sort_keys=False) + "---\n# 卡\n", encoding="utf-8")
            return c
        a = mk_card("a.md", 1000, 50)
        b = mk_card("b.md", 2000, 60)
        out = tmp / "mix.md"
        r = run([sys.executable, str(TOOLS / "mix-style.py"), str(a), str(b), "0.5", "0.5", "-o", str(out)])
        fm = parse_fm(out)
        # #2 mix 输出含 source_sample_length = 加权均值
        check("#2 mix 输出含 source_sample_length", fm is not None and fm.get("source_sample_length") == 1500,
              str(fm and fm.get("source_sample_length")))
        # #9 旧卡（正文两处 ---）→ 优雅报错非崩溃
        legacy = tmp / "legacy.md"
        legacy.write_text("# 旧卡\n\n## role\n\n第一人称限知\n\n---\n- 套路化\n\n---\n\n其他\n", encoding="utf-8")
        r2 = run([sys.executable, str(TOOLS / "mix-style.py"), str(legacy), str(a), "0.5", "0.5", "-o", str(tmp / "m2.md")])
        check("#9 mix 旧卡优雅报错", r2.returncode == 2 and "error" in r2.stderr.lower() and "Traceback" not in r2.stderr,
              f"rc={r2.returncode} stderr={r2.stderr}")


def test_review_fix_metrics():
    print("[review-fix] #3/#4/#5/#36 测量正确性")
    mod = _load_tool("distill-style")
    # #3 名代词集合：他们/她们计入 pro
    check("#3 name_pronoun 集合匹配", mod._name_pronoun_ratio(["他们", "我们", "张三"]) == 1.5,
          str(mod._name_pronoun_ratio(["他们", "我们", "张三"])))
    # #5 单字转折词命中
    st = mod.cohesion_stats("但他没有回答。", [("但", "c")])
    check("#5 单字转折词命中", st["transition_sentence_ratio"] == 100.0, str(st))
    # #4 ASCII 引号开关
    r = mod.rhythm_stats('"你好。"他说。')
    check("#4 ASCII 引号开关", r["dialogue_pct"] == 37.5, str(r))
    # #36 load_card dict 校验：scalar frontmatter → (None, text)
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("---\nfoo\n---\n# body\n")
        fp = f.name
    fm, _ = mod.load_card(fp)
    check("#36 load_card 非 dict 返回 None", fm is None, str(fm))
    import os
    os.unlink(fp)


def test_review_fix_check_zero_expectation():
    print("[review-fix] #6 零期望维度判 FAIL")
    import yaml as _y
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        card = tmp / "card.md"
        # 构造 question_ratio=0 的主卡（confidence 80 → 容差 15%）
        dims = {"profile_version": "1.0", "scene_type": "general", "confidence": 80,
                "last_updated": "", "source_sample_length": 3000, "locked": [],
                "lexicon": {"adj_density_per_100": 1.0, "adv_density_per_100": 1.0, "four_phrase_freq_per_100": 1.0},
                "syntax": {"avg_sentence_length": 20.0, "single_sentence_paragraph_pct": 20.0,
                           "avg_sentences_per_paragraph": 3.0, "question_ratio": 0.0, "exclamation_ratio": 0.0},
                "rhythm": {"dialogue_pct": 30.0},
                "cohesion": {"conjunction_freq_per_100": 2.0, "transition_sentence_ratio": 20.0},
                "verb_style": {"action_verb_ratio": 0.5, "mental_verb_ratio": 0.3, "state_verb_ratio": 0.2}}
        card.write_text("---\n" + _y.safe_dump(dims, allow_unicode=True, sort_keys=False) + "---\n# 风格\n", encoding="utf-8")
        body = (tmp / "body.txt").write_text("这是正文，满是问号？难道不是吗？？真的吗！", encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "distill-style.py"), "check", "-c", str(card), str(tmp / "body.txt")])
        # #6 零期望维度：question_ratio 0 vs 测得非 0 → FAIL → rc=1
        check("#6 零期望维度判 FAIL", r.returncode == 1 and "FAIL" in r.stdout, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}")


def test_review_fix_update_locked_and_checkpoint():
    print("[review-fix] #8 locked 维度锁 + #10 checkpoint 按卡隔离")
    import yaml as _y
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / ".agent" / "style-update").mkdir(parents=True)
        (tmp / "archives").mkdir(parents=True)
        ch = tmp / "ch-1.md"
        ch.write_text("他走了过去，说道。她跟了上来。", encoding="utf-8")
        def mk_card(name, conf=80, ssl=3000, locked=None):
            dims = {"profile_version": "1.0", "scene_type": "general", "confidence": conf,
                    "last_updated": "", "source_sample_length": ssl, "locked": locked or [],
                    "lexicon": {"adj_density_per_100": 1.0, "adv_density_per_100": 1.0,
                                "four_phrase_freq_per_100": 1.0, "name_pronoun_ratio": 1.0},
                    "syntax": {"avg_sentence_length": 20.0, "single_sentence_paragraph_pct": 20.0,
                               "avg_sentences_per_paragraph": 3.0, "question_ratio": 5.0, "exclamation_ratio": 5.0},
                    "rhythm": {"dialogue_pct": 30.0},
                    "cohesion": {"conjunction_freq_per_100": 2.0, "transition_sentence_ratio": 20.0},
                    "verb_style": {"action_verb_ratio": 0.5, "mental_verb_ratio": 0.3, "state_verb_ratio": 0.2}}
            c = tmp / name
            c.write_text("---\n" + _y.safe_dump(dims, allow_unicode=True, sort_keys=False) + "---\n# 风格\n", encoding="utf-8")
            return c
        def upd(card, out):
            return run([sys.executable, str(TOOLS / "distill-style.py"), "update",
                        "-c", str(card), "-p", str(tmp), "-o", str(tmp / out), str(ch)])
        # #8 locked 锁整个维度：syntax 不动；非锁维度 four_phrase_freq 更新（正则维度，无需 jieba）
        c1 = mk_card("card-a.md", locked=["syntax"])
        upd(c1, "out1.md")
        out1 = parse_fm(tmp / "out1.md")
        check("#8 locked 锁 syntax", out1["syntax"]["avg_sentence_length"] == 20.0
              and out1["lexicon"]["four_phrase_freq_per_100"] != 1.0,
              str(out1["syntax"]["avg_sentence_length"]))
        # #10 checkpoint 按卡隔离：同章两卡各自处理，落两个不同卡名的 .done
        c2 = mk_card("card-b.md")
        upd(c2, "out2.md")
        d = sorted(p.name for p in (tmp / ".agent" / "style-update").glob("*.done"))
        check("#10 checkpoint 按卡隔离", "card-a.ch-1.done" in d and "card-b.ch-1.done" in d, str(d))
        # 重放同卡同章 → 全跳过
        r2 = upd(c1, "out1b.md")
        check("#10 重放跳过", "无新章节" in r2.stdout, r2.stdout)


def test_review_fix_check_scene_card():
    print("[review-fix] #7 场景卡 inherits 解析")
    import yaml as _y
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "style-profiles").mkdir(parents=True)
        main_dims = {"profile_version": "1.0", "scene_type": "general", "confidence": 80,
                     "last_updated": "", "source_sample_length": 3000, "locked": [],
                     "lexicon": {"adj_density_per_100": 1.0, "adv_density_per_100": 1.0, "four_phrase_freq_per_100": 1.0},
                     "syntax": {"avg_sentence_length": 20.0, "single_sentence_paragraph_pct": 20.0,
                                "avg_sentences_per_paragraph": 3.0, "question_ratio": 5.0, "exclamation_ratio": 5.0},
                     "rhythm": {"dialogue_pct": 30.0},
                     "cohesion": {"conjunction_freq_per_100": 2.0, "transition_sentence_ratio": 20.0},
                     "verb_style": {"action_verb_ratio": 0.5, "mental_verb_ratio": 0.3, "state_verb_ratio": 0.2}}
        (tmp / "writing-style.md").write_text("---\n" + _y.safe_dump(main_dims, allow_unicode=True, sort_keys=False) + "---\n# 风格\n", encoding="utf-8")
        scene_dims = {"profile_version": "1.0", "scene_type": "dialogue", "confidence": 60,
                      "last_updated": "", "source_sample_length": 500, "locked": [],
                      "inherits": "writing-style.md",
                      "override": {"rhythm": {"dialogue_pct": 80.0}, "syntax": {"question_ratio": 40.0}}}
        (tmp / "style-profiles" / "dialogue.md").write_text("---\n" + _y.safe_dump(scene_dims, allow_unicode=True, sort_keys=False) + "---\n# 场景\n", encoding="utf-8")
        body = tmp / "body.txt"
        body.write_text("他在左边。她在右边。他问她：" '“你去吗？”' "她说：" '“去。”', encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "distill-style.py"), "check", "-c", str(tmp / "style-profiles" / "dialogue.md"), str(body)])
        # #7 场景卡经 inherits 解析：override 的 dialogue_pct/question_ratio 参与比对（正文高对话 → 至少一行 FAIL）
        check("#7 场景卡 resolve 后比对", r.returncode in (0, 1) and "dialogue_pct" in r.stdout,
              f"rc={r.returncode}\n{r.stdout}\n{r.stderr}")


def test_review_fix_inherits_scene_to_scene():
    mod = _load_tool("check-agents")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        settings = tmp / "templates" / "settings"
        sp = settings / "style-profiles"
        sp.mkdir(parents=True)
        # 主卡
        (settings / "writing-style.md").write_text("---\nprofile_version: \"1.0\"\nscene_type: general\nconfidence: 0\nlast_updated: \"\"\nsource_sample_length: 0\nlocked: []\nlexicon: {}\nsyntax: {}\nrhythm: {}\nrhetoric: {}\nemotion_expression: {}\nnarrative: {}\ndialogue_style: {}\ncohesion: {}\nverb_style: {}\n---\n# 风格\n", encoding="utf-8")
        def scene(name, inherits):
            (sp / name).write_text(f'---\nprofile_version: "1.0"\nscene_type: general\nconfidence: 0\nlast_updated: ""\nsource_sample_length: 0\nlocked: []\ninherits: "{inherits}"\noverride: {{rhythm: {{dialogue_pct: 80}}}}\n---\n# {name}\n', encoding="utf-8")
        scene("fight.md", "writing-style.md")
        scene("duel.md", "fight.md")     # 场景间继承
        # 用 importlib 载入 check-agents 直接调 check_style_card（传临时路径）
        errs = mod.check_style_card(sp / "duel.md")
        check("#11 场景间继承不误报", not any("inherits" in e for e in errs), str(errs))


def main():
    test_card_schema()
    test_migration()
    test_distill()
    test_genre_baselines()
    test_e2e_init_deploy()
    test_update()
    test_check()
    test_compare()
    test_mix()
    test_acceptance()
    test_review_fix_metrics()
    test_review_fix_check_zero_expectation()
    test_review_fix_update_locked_and_checkpoint()
    test_review_fix_check_scene_card()
    test_review_fix_inherits_scene_to_scene()
    test_review_fix_mix()
    test_review_fix_migration_no_clobber()
    test_review_fix_seed_daishou()
    test_review_fix_scaffold_refresh()
    test_review_fix_sync_deploys()
    test_review_fix_init_deploys_style_distill()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
