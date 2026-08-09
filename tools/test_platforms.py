#!/usr/bin/env python3
"""平台适配层验证脚本。

用法: python tools/test_platforms.py
返回码 0 = 全部通过，非 0 = 有失败（CI 用）。

覆盖：
- 单元：platforms 模块（配置/检测/引用改写/yaml 预检）
- E2E：init.py 各平台布局 + 引用改写 + reasonix 10 个 skill + codex TOML agent（含 tomllib 解析）
- E2E：sync-project.py 各平台同步 + --check
- E2E：install.sh 全新 HOME 首次安装（F1 回归）+ 缺 pyyaml 负向场景（F5 回归）
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    tomllib = None

TOOLS = Path(__file__).resolve().parent
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
            for a in absents:
                check(f"{key} 无 {a}", not (tmp / a).exists())

    # reasonix 10 个 skill
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "reasonix")
        names = ["novel-agent", "writer", "volume-planner", "chapter-planner",
                 "prompt-crafter", "anti-ai", "reader", "updater",
                 "memory-recording", "roleplay-sandbox"]  # 与 deploy_reasonix_skills 的 10 个 skill 名对应（spec 契约）
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
        check(f"claude agents 数量=8", n == 8, f"实际 {n}")  # agents/ 源有 8 个 .md（spec 契约）

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
        check("codex agents 数量=8", n == 8, f"实际 {n}")
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
        check("codex skill roleplay-sandbox",
              (tmp / ".codex/skills/roleplay-sandbox/SKILL.md").exists())
        check("codex skill memory-recording",
              (tmp / ".codex/skills/memory-recording/SKILL.md").exists())
        ag = (tmp / "AGENTS.md").read_text(encoding="utf-8")
        check("codex AGENTS.md 指向 .codex/agents", ".codex/agents/" in ag, ag[:200])
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


# ---------------- E2E install.sh / 负向场景 ----------------

def test_install_fresh_home():
    """F1 回归：全新 HOME（skills 目录尚不存在）首次安装不被安全校验误拒。"""
    print("[e2e] install.sh codex 全新 HOME 首次安装")
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        home.mkdir()
        env = dict(os.environ)
        env["HOME"] = str(home)
        r = run(["bash", str(TOOLS.parent / "install.sh"), "codex"],
                cwd=str(TOOLS.parent), env=env)
        check("fresh home install exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        dest = home / ".codex" / "skills" / "awesome-novel"
        check("fresh home SKILL.md 存在", (dest / "SKILL.md").exists())
        check("fresh home agents 存在", (dest / "agents").is_dir())


def test_install_no_home():
    """P2 回归：HOME 未设置时安装脚本在创建任何目录前即拒绝（报路径异常）。"""
    print("[e2e] install.sh 无 HOME 拒绝安装")
    env = dict(os.environ)
    env.pop("HOME", None)
    r = run(["bash", str(TOOLS.parent / "install.sh"), "codex"],
            cwd=str(TOOLS.parent), env=env)
    check("no HOME exit 1", r.returncode == 1, str(r.returncode))
    check("no HOME 报路径异常", "安装目标路径异常" in (r.stdout + r.stderr))


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
        ("test_init_layout", test_init_layout),
        ("test_sync", test_sync),
        ("test_install_fresh_home", test_install_fresh_home),
        ("test_install_no_home", test_install_no_home),
        ("test_noyaml_e2e", test_noyaml_e2e),
    ]:
        try:
            fn()
        except Exception as e:
            check(f"{name} 异常", False, repr(e))
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
