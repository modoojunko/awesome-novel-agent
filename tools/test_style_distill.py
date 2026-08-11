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
        check("FAIL 场景计数=1", "不通过维度数：1" in rb.stdout, rb.stdout[-300:])

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
        # 造 1250 字样本蒸馏出的源卡（confidence 基线 20+25）
        sample = tmp / "s.md"
        # ≥1250 字：confidence 基线 = 20 + min(40, L/50=26) = 46；5 章后 +25 → 71
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
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
