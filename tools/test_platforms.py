#!/usr/bin/env python3
"""平台适配层验证脚本。

用法: python tools/test_platforms.py
返回码 0 = 全部通过，非 0 = 有失败（CI 用）。

覆盖：
- 单元：platforms 模块（配置/检测/引用改写/yaml 预检）
- 单元：check-python.py 版本门槛（安装阶段 fail-fast）
- E2E：init.py 各平台布局 + 引用改写 + reasonix 11 个 skill + codex TOML agent（含 tomllib 解析）
- E2E：sync-project.py 各平台同步 + --check
- E2E：install.sh 全新 HOME 首次安装（F1 回归）+ 版本门槛 fail-fast（P-ver 回归）+ pyyaml 安装门槛 fail-fast（Y-ver 回归）+ 缺 pyyaml 负向场景（F5 回归）
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# 强制 UTF-8 输出，避免 Windows GBK 控制台报错（AGENTS.md:79）
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from test_util import check
import test_util as _tu


def run(cmd, cwd=None, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env)


def init_project(tmp: Path, platform_key: str, genre: str = "1"):
    return run([sys.executable, str(TOOLS / "init.py"), str(tmp),
                "--genre", genre, "--platform", platform_key])


# ---------------- 单元 ----------------

def test_detect():
    print("[unit] detect_platform")
    import platforms as p
    check("override=reasonix", p.detect_platform(Path("d:/x"), "reasonix").key == "reasonix")
    check("override=opencode", p.detect_platform(Path("d:/x"), "opencode").key == "opencode")
    check("override=claude", p.detect_platform(Path("d:/x"), "claude").key == "claude")
    check("path reasonix",
          p.detect_platform(Path("d:/proj/.reasonix/skills/awesome-novel")).key == "reasonix")
    check("path opencode",
          p.detect_platform(Path("d:/proj/.config/opencode/skills/awesome-novel")).key == "opencode")
    check("default claude",
          p.detect_platform(Path("d:/code/awesome-novel-skill")).key == "claude")


def test_rewrite():
    print("[unit] rewrite_refs")
    import platforms as p
    text = "先 Read `.claude/knowledge/anti-ai.md` 和 `.claude/memory/volume-memory.md`"
    out = p.rewrite_refs(text, p.PLATFORMS["reasonix"])
    check("reasonix 改写两处",
          out == "先 Read `.reasonix/knowledge/anti-ai.md` 和 `.reasonix/memory/volume-memory.md`",
          out)
    check("claude 原样", p.rewrite_refs(text, p.PLATFORMS["claude"]) == text)
    out = p.rewrite_refs(text, p.PLATFORMS["codex"])
    check("codex 改写两处",
          out == "先 Read `.codex/knowledge/anti-ai.md` 和 `.codex/memory/volume-memory.md`",
          out)


def test_config():
    print("[unit] 平台配置")
    import platforms as p
    check("claude agents 路径",
          p.PLATFORMS["claude"].agents_dir(Path("P")) == Path("P") / ".claude" / "agents")
    check("reasonix agents=None", p.PLATFORMS["reasonix"].agents_dir(Path("P")) is None)
    check("reasonix skills 路径",
          p.PLATFORMS["reasonix"].skills_dir(Path("P")) == Path("P") / ".reasonix" / "skills")
    check("codex agents 路径",
          p.PLATFORMS["codex"].agents_dir(Path("P")) == Path("P") / ".codex" / "agents")
    check("codex skills 路径",
          p.PLATFORMS["codex"].skills_dir(Path("P")) == Path("P") / ".codex" / "skills")
    check("unknown key 抛错", _raises(p.platform_from_key, "bad-key"))
    check("检测优先显式覆盖", p.detect_platform(Path("d:/x/.reasonix/skills"), "claude").key == "claude")
    check("检测 codex 路径",
          p.detect_platform(Path("d:/x/.codex/skills/awesome-novel")).key == "codex")
    check("检测 claude 路径含 codex 子串回落 claude",
          p.detect_platform(Path("/Users/codex-dev/.claude/skills/awesome-novel")).key == "claude")


def test_yaml_precheck():
    print("[unit] ensure_yaml")
    import platforms as p
    p.ensure_yaml(p.PLATFORMS["claude"])  # claude 纯复制，不依赖 pyyaml
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("模拟缺 pyyaml")
        return real_import(name, *args, **kwargs)

    builtins.__import__ = fake_import
    try:
        check("缺 yaml 时 codex 报错", _raises_system_exit(p.ensure_yaml, p.PLATFORMS["codex"]))
        check("缺 yaml 时 opencode 报错",
              _raises_system_exit(p.ensure_yaml, p.PLATFORMS["opencode"]))
        check("缺 yaml 时 reasonix 报错",
              _raises_system_exit(p.ensure_yaml, p.PLATFORMS["reasonix"]))
    finally:
        builtins.__import__ = real_import


def test_check_python():
    """P-ver 回归：check-python.py 在安装阶段暴露版本问题，而不是执行时才报 SyntaxError。"""
    print("[unit] check-python.py 版本门槛")
    r = run([sys.executable, str(TOOLS / "check-python.py")])
    check("当前解释器通过", r.returncode == 0, (r.stdout + r.stderr)[-200:])
    r = run([sys.executable, str(TOOLS / "check-python.py"), "--min", "99.0"])
    check("超高门槛拒绝", r.returncode == 1, str(r.returncode))
    check("拒绝信息含版本号与升级提示",
          "Python 99.0" in (r.stdout + r.stderr) and "升级" in (r.stdout + r.stderr),
          (r.stdout + r.stderr)[-300:])


def test_check_yaml():
    """Y-ver 回归：check-yaml.py 在安装阶段暴露缺 pyyaml，而不是 init 时才报错。"""
    print("[unit] check-yaml.py pyyaml 门槛")
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "yaml.py").write_text('raise ImportError("blocked")\n', encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(td) + os.pathsep + env.get("PYTHONPATH", "")
        r = run([sys.executable, str(TOOLS / "check-yaml.py"), "codex"], env=env)
        check("缺 yaml exit 1", r.returncode == 1, str(r.returncode))
        check("缺 yaml 报错含 pyyaml 与 pip 提示",
              "需要 pyyaml" in (r.stdout + r.stderr)
              and "pip install pyyaml" in (r.stdout + r.stderr),
              (r.stdout + r.stderr)[-300:])
        check("缺 yaml 报错含解释器路径", sys.executable in (r.stdout + r.stderr),
              (r.stdout + r.stderr)[-300:])
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "yaml.py").write_text("# stub\n", encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(td) + os.pathsep + env.get("PYTHONPATH", "")
        r = run([sys.executable, str(TOOLS / "check-yaml.py"), "opencode"], env=env)
        check("有 yaml exit 0", r.returncode == 0, (r.stdout + r.stderr)[-200:])


def _raises(fn, *a) -> bool:
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def _raises_system_exit(fn, *a) -> bool:
    try:
        fn(*a)
        return False
    except SystemExit:
        return True


# ---------------- E2E init ----------------

def test_init_layout():
    print("[e2e] init.py 各平台布局")
    expect_map = {
        "claude":   (["agents", "knowledge", "memory"], [".reasonix"]),
        "opencode": (["agents", "knowledge", "memory"], [".claude", ".reasonix"]),
        "reasonix": (["skills", "knowledge", "memory"], [".claude"]),
        "codex":    (["agents", "knowledge", "memory"], [".claude", ".opencode", ".reasonix"]),
    }
    for key, (subs, absents) in expect_map.items():
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            r = init_project(tmp, key)
            check(f"{key} init exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
            for sub in subs:
                check(f"{key} 存在 .{key}/{sub}", (tmp / f".{key}" / sub).exists())
            check(f"{key} 存在 novel-samples/（蒸馏样本目录）", (tmp / "novel-samples").exists())
            for a in absents:
                check(f"{key} 无 {a}", not (tmp / a).exists())

    # reasonix 11 个 skill
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "reasonix")
        names = ["novel-agent", "writer", "volume-planner", "chapter-planner",
                 "prompt-crafter", "anti-ai", "reader", "updater", "style-distiller",
                 "memory-recording", "roleplay-sandbox"]  # 与 deploy_reasonix_skills 的 11 个 skill 名对应（spec 契约）
        for n in names:
            check(f"reasonix skill {n}", (tmp / ".reasonix/skills" / n / "SKILL.md").exists())
        w = (tmp / ".reasonix/skills/writer/SKILL.md").read_text(encoding="utf-8")
        check("reasonix writer 引用改写",
              ".reasonix/knowledge/" in w and ".claude/knowledge/" not in w)
        nv = (tmp / ".reasonix/skills/novel-agent/SKILL.md").read_text(encoding="utf-8")
        check("reasonix novel-agent 无 .claude 残留", ".claude" not in nv)

    # reasonix AGENTS.md 模板改写
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "reasonix")
        ag = (tmp / "AGENTS.md").read_text(encoding="utf-8")
        check("reasonix AGENTS.md 无 .opencode/agents",
              ".opencode/" not in ag and ".reasonix/skills/" in ag, ag[:200])
        cl = (tmp / "CLAUDE.md").read_text(encoding="utf-8")
        check("reasonix CLAUDE.md 无 .claude/agents",
              ".claude/agents" not in cl and ".reasonix/skills/" in cl, cl[:200])

    # claude agents 数量
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "claude")
        n = len(list((tmp / ".claude/agents").glob("*.md")))
        check(f"claude agents 数量=9", n == 9, f"实际 {n}")  # agents/ 源有 9 个 .md（spec 契约）

    # opencode agent 引用改写
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "opencode")
        w = (tmp / ".opencode/agents/writer.md").read_text(encoding="utf-8")
        check("opencode writer 引用改写",
              ".opencode/knowledge/" in w and ".claude/knowledge/" not in w)

    # codex TOML agent + skill + 模板
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "codex")
        n = len(list((tmp / ".codex/agents").glob("*.toml")))
        check("codex agents 数量=9", n == 9, f"实际 {n}")
        w = (tmp / ".codex/agents/writer.toml").read_text(encoding="utf-8")
        check("codex writer TOML 字段",
              'name = "writer"' in w and "description" in w
              and "developer_instructions" in w, w[:200])
        check("codex writer 引用改写",
              ".codex/knowledge/" in w and ".claude/knowledge/" not in w)
        all_toml = "".join(
            f.read_text(encoding="utf-8") for f in sorted((tmp / ".codex/agents").glob("*.toml"))
        )
        check("codex 全部 TOML 无 .claude 残留", ".claude" not in all_toml)
        nv = (tmp / ".codex/agents/novel-agent.toml").read_text(encoding="utf-8")
        check("codex novel-agent 调度适配",
              "spawn_agent" in nv and ".codex/agents/" in nv)
        sub_toml = "".join(
            f.read_text(encoding="utf-8")
            for f in sorted((tmp / ".codex/agents").glob("*.toml"))
            if f.name != "novel-agent.toml"
        )
        check("codex 子 agent 注入调度硬约束",
              "调度权限硬约束" in sub_toml and "spawn_agent" in sub_toml
              and "禁止使用" in sub_toml,
              "子 agent TOML 缺少禁止派生指令")
        check("codex novel-agent 不注入禁调",
              "调度权限硬约束" not in nv, "novel-agent 是唯一调度者，不应注入禁调")
        vp = (tmp / ".codex/agents/volume-planner.toml").read_text(encoding="utf-8")
        check("codex volume-planner 源 OOS 含不调度",
              "不调度其他 agent" in vp, "volume-planner 源文件缺少不调度声明")
        check("codex skill roleplay-sandbox",
              (tmp / ".codex/skills/roleplay-sandbox/SKILL.md").exists())
        check("codex skill memory-recording",
              (tmp / ".codex/skills/memory-recording/SKILL.md").exists())
        ag = (tmp / "AGENTS.md").read_text(encoding="utf-8")
        check("codex AGENTS.md 指向 .codex/agents", ".codex/agents/" in ag, ag[:200])
        check("codex AGENTS.md 唯一调度者规则", "唯一调度者" in ag, ag[:400])
        check("codex 无 CLAUDE.md", not (tmp / "CLAUDE.md").exists())
        check("codex 无 AGENTS.codex.md 模板副本",
              not (tmp / "AGENTS.codex.md").exists())
        if tomllib is not None:
            parse_ok = True
            for f in sorted((tmp / ".codex/agents").glob("*.toml")):
                try:
                    tomllib.loads(f.read_text(encoding="utf-8"))
                except Exception as e:
                    parse_ok = False
                    detail = f"{f.name}: {e}"
                    break
            check("codex TOML tomllib 可解析", parse_ok, detail if not parse_ok else "")


# ---------------- E2E sync ----------------

def test_sync():
    print("[e2e] sync-project.py 各平台同步")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "claude")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp),
                 "--platform", "claude"], cwd=str(tmp))
        check("claude sync exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        check("claude sync 生成 .claude/skills", (tmp / ".claude/skills").exists())

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "opencode")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp),
                 "--platform", "opencode"], cwd=str(tmp))
        check("opencode sync exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        w = (tmp / ".opencode/agents/writer.md").read_text(encoding="utf-8")
        check("opencode sync 保持 permission 格式",
              "permission:" in w and "tools:" not in w and ".opencode/knowledge/" in w)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "reasonix")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp),
                 "--platform", "reasonix"], cwd=str(tmp))
        check("reasonix sync exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        check("reasonix sync 保持 skill", (tmp / ".reasonix/skills/writer/SKILL.md").exists())
        check("reasonix sync 无 .claude", not (tmp / ".claude").exists())

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "codex")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp),
                 "--platform", "codex"], cwd=str(tmp))
        check("codex sync exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        w = (tmp / ".codex/agents/writer.toml").read_text(encoding="utf-8")
        check("codex sync 保持 TOML 格式",
              'name = "writer"' in w and "developer_instructions" in w
              and ".codex/knowledge/" in w and ".claude/" not in w)
        check("codex sync 无 .claude", not (tmp / ".claude").exists())

    # --check：无指纹首次 → exit 1
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "reasonix")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp),
                 "--platform", "reasonix", "--check"], cwd=str(tmp))
        check("reasonix --check 无指纹 exit 1", r.returncode == 1, str(r.returncode))


# ---------------- E2E style seed 守卫 / 脚手架同步（review #13-17 回归） ----------------

def test_style_seed_guard():
    """#13/#14 回归：init 后无占位符出货；重跑 init 不覆盖作者编辑、就地补齐占位符。"""
    print("[e2e] style seed 守卫")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "claude")
        sc = tmp / "settings" / "writing-style.md"
        text = sc.read_text(encoding="utf-8")
        check("init 后无 {role} 占位符", "{role}" not in text, text[:200])
        check("init 后无其他样式占位符",
              all(t not in text for t in ("{principle_1}", "{mistake_1}", "{depiction_techniques}")),
              text[:200])

    # 重跑 init：作者编辑保留 + 残留占位符就地补齐（不整卡覆盖）
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "claude")
        sc = tmp / "settings" / "writing-style.md"
        text = sc.read_text(encoding="utf-8")
        text = text.replace("## 叙事身份（原 role）\n\n",
                            "## 叙事身份（原 role）\n\n作者自己写的角色设定\n\n", 1)
        text += "\n- {mistake_1}\n"          # 模拟旧 init 残留占位符
        sc.write_text(text, encoding="utf-8")
        init_project(tmp, "claude")
        t2 = sc.read_text(encoding="utf-8")
        check("重跑 init 保留作者编辑", "作者自己写的角色设定" in t2, t2[:300])
        check("重跑 init 就地补齐占位符", "{mistake_1}" not in t2 and "{role}" not in t2, t2[:300])


def test_sync_style_missing_and_scaffold():
    """#15/#17 回归：sync 缺卡主卡写（待设定）不写占位符；脚手架 CLAUDE.md/skill_version 刷新。"""
    print("[e2e] sync 缺卡主卡 + 脚手架刷新")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "claude")
        sc = tmp / "settings" / "writing-style.md"
        sc.unlink()                          # 模拟缺卡项目
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp),
                 "--platform", "claude"], cwd=str(tmp))
        check("sync 缺卡 exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        check("sync 补主卡", sc.exists())
        t = sc.read_text(encoding="utf-8")
        check("补的主卡无 {role} 占位符", "{role}" not in t, t[:200])
        check("补的主卡含（待设定）", "（待设定）" in t, t[:200])

    # 脚手架刷新：CLAUDE.md 恢复 9 个 agent、status.md skill_version 更新
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "claude")
        cl = tmp / "CLAUDE.md"
        cl.write_text(cl.read_text(encoding="utf-8").replace("9 个 agent", "8 个 agent"),
                      encoding="utf-8")
        st = tmp / ".agent" / "status.md"
        st.write_text(st.read_text(encoding="utf-8")
                      .replace("skill_version:** ", "skill_version:** v0.0.0"), encoding="utf-8")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp),
                 "--platform", "claude"], cwd=str(tmp))
        check("脚手架同步 exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        check("CLAUDE.md 恢复 9 个 agent", "9 个 agent" in cl.read_text(encoding="utf-8"),
              cl.read_text(encoding="utf-8")[:200])
        st2 = st.read_text(encoding="utf-8")
        check("status.md skill_version 更新（非 v0.0.0）",
              "- **skill_version:** v0.0.0" not in st2, st2[:200])



def test_install_fresh_home():
    """F1 回归：全新 HOME（skills 目录尚不存在）首次安装不被安全校验误拒。"""
    print("[e2e] install.sh codex 全新 HOME 首次安装")
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        home.mkdir()
        stub = Path(td) / "stub"
        stub.mkdir()
        (stub / "yaml.py").write_text("# stub\n", encoding="utf-8")
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["PYTHONPATH"] = str(stub) + os.pathsep + env.get("PYTHONPATH", "")
        r = run(["bash", str(TOOLS.parent / "install.sh"), "codex"],
                cwd=str(TOOLS.parent), env=env)
        check("fresh home install exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        dest = home / ".codex" / "skills" / "awesome-novel"
        check("fresh home SKILL.md 存在", (dest / "SKILL.md").exists())
        check("fresh home agents 存在", (dest / "agents").is_dir())


def test_install_no_home():
    """P2 回归：HOME 未设置时安装脚本在创建任何目录前即拒绝（报路径异常）。"""
    print("[e2e] install.sh 无 HOME 拒绝安装")
    with tempfile.TemporaryDirectory() as td:
        stub = Path(td) / "stub"
        stub.mkdir()
        (stub / "yaml.py").write_text("# stub\n", encoding="utf-8")
        env = dict(os.environ)
        env.pop("HOME", None)
        env["PYTHONPATH"] = str(stub) + os.pathsep + env.get("PYTHONPATH", "")
        r = run(["bash", str(TOOLS.parent / "install.sh"), "codex"],
                cwd=str(TOOLS.parent), env=env)
        check("no HOME exit 1", r.returncode == 1, str(r.returncode))
        check("no HOME 报路径异常", "安装目标路径异常" in (r.stdout + r.stderr))


def test_install_python_gate():
    """P-ver 回归：版本检查失败时 install.sh 在创建/删除任何目录前即中止。"""
    print("[e2e] install.sh Python 版本门槛 fail-fast")
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        home.mkdir()
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["NOVEL_PYTHON"] = "/bin/false"
        r = run(["bash", str(TOOLS.parent / "install.sh"), "codex"],
                cwd=str(TOOLS.parent), env=env)
        check("版本门槛拒绝 exit 1", r.returncode == 1, str(r.returncode))
        check("拒绝信息含安装中止", "安装中止" in (r.stdout + r.stderr),
              (r.stdout + r.stderr)[-300:])
        dest = home / ".codex" / "skills" / "awesome-novel"
        check("拒绝时未创建目标目录", not dest.exists())


def test_install_yaml_gate():
    """Y-ver E2E 回归：缺 pyyaml 时 install.sh codex 在创建目标目录前中止。"""
    print("[e2e] install.sh pyyaml 门槛 fail-fast")
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        home.mkdir()
        block = Path(td) / "block"
        block.mkdir()
        (block / "yaml.py").write_text('raise ImportError("blocked")\n', encoding="utf-8")
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["PYTHONPATH"] = str(block) + os.pathsep + env.get("PYTHONPATH", "")
        r = run(["bash", str(TOOLS.parent / "install.sh"), "codex"],
                cwd=str(TOOLS.parent), env=env)
        check("缺 pyyaml 拒绝 exit 1", r.returncode == 1, str(r.returncode))
        check("缺 pyyaml 报安装中止", "安装中止" in (r.stdout + r.stderr)
              and "pyyaml" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-300:])
        dest = home / ".codex" / "skills" / "awesome-novel"
        check("拒绝时未创建目标目录", not dest.exists())


def test_noyaml_e2e():
    """F5 回归：缺 pyyaml 时 init --platform codex 明确报错退出，不产出损坏 TOML。"""
    print("[e2e] 缺 pyyaml 时 init --platform codex 明确报错")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "yaml.py").write_text('raise ImportError("blocked")\n', encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(tmp) + os.pathsep + env.get("PYTHONPATH", "")
        r = run([sys.executable, str(TOOLS / "init.py"), str(tmp / "proj"),
                 "--genre", "1", "--platform", "codex"], cwd=str(tmp), env=env)
        check("缺 yaml exit 1", r.returncode == 1, str(r.returncode))
        check("缺 yaml 报错信息", "需要 pyyaml" in (r.stdout + r.stderr))
        check("缺 yaml 无损坏 TOML 产物",
              not (tmp / "proj" / ".codex" / "agents" / "writer.toml").exists())


def main():
    for name, fn in [
        ("test_detect", test_detect),
        ("test_rewrite", test_rewrite),
        ("test_config", test_config),
        ("test_yaml_precheck", test_yaml_precheck),
        ("test_check_python", test_check_python),
        ("test_check_yaml", test_check_yaml),
        ("test_init_layout", test_init_layout),
        ("test_sync", test_sync),
        ("test_style_seed_guard", test_style_seed_guard),
        ("test_sync_style_missing_and_scaffold", test_sync_style_missing_and_scaffold),
        ("test_install_fresh_home", test_install_fresh_home),
        ("test_install_no_home", test_install_no_home),
        ("test_install_python_gate", test_install_python_gate),
        ("test_install_yaml_gate", test_install_yaml_gate),
        ("test_noyaml_e2e", test_noyaml_e2e),
    ]:
        try:
            fn()
        except Exception as e:
            check(f"{name} 异常", False, repr(e))
    print(f"\n结果: {_tu.PASS} 通过, {_tu.FAIL} 失败")
    sys.exit(0 if _tu.FAIL == 0 else 1)


if __name__ == "__main__":
    main()
