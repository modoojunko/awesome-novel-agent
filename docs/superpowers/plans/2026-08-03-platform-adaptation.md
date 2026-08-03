# 平台适配层 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** init.py / sync-project.py 按 coding agent 平台（claude / opencode / reasonix）的目录约定部署，非 claude 平台不产生 `.claude/`。

**Architecture:** 新建共享模块 `tools/platforms.py`（平台配置表 + 平台检测 + 引用改写 + reasonix skill 生成）。init.py / sync-project.py 改为从该模块取平台并按平台派生目录部署；reasonix 的 10 个 SKILL.md 是转换产物，sync 时重新生成而非字节拷贝。SKILL.md 入口措辞平台化。源文件 agents/ + skills/ 保持 Claude Code 格式不动，部署时改写 `.claude/knowledge/`、`.claude/memory/` 引用。

**Tech Stack:** Python 3（标准库，PyYAML 可选兜底）、git bash。

**Spec:** `docs/superpowers/specs/2026-08-03-platform-adaptation-design.md`
**模块名注记：** spec 原定 `tools/platform.py`，因与标准库 `platform` 撞名，定稿为 `tools/platforms.py`（已同步 spec）。

---

## 文件结构

| 文件 | 责任 |
|------|------|
| `tools/platforms.py` | **新建**：Platform 配置表、`detect_platform`、`rewrite_refs`、`resolve_skill_home`、reasonix 转换 + `deploy_reasonix_skills` |
| `tools/init.py` | **改**：部署全走 platform（agents/knowledge/memory/skills 目录派生 + 引用改写），加 `--platform` |
| `tools/sync-project.py` | **改**：同步目标目录走 platform，reasonix 重新生成 10 个 SKILL.md |
| `tools/test_platforms.py` | **新建**：单元 + E2E 验证脚本（本计划的 TDD 载体，同时是回归工具） |
| `SKILL.md` | **改**：11 处平台相关措辞/检查 |
| `docs/superpowers/specs/2026-08-03-platform-adaptation-design.md` | 已提交（模块名已同步） |

---

## Task 1: 写验证脚本（先红后绿的基础）

**Files:**
- Create: `tools/test_platforms.py`

- [ ] **Step 1: 写完整验证脚本**

```python
#!/usr/bin/env python3
"""平台适配层验证脚本。

用法: python tools/test_platforms.py
返回码 0 = 全部通过，非 0 = 有失败（CI 用）。

覆盖：
- 单元：platforms 模块（配置/检测/引用改写）
- E2E：init.py 三平台布局 + 引用改写 + reasonix 10 个 skill
- E2E：sync-project.py 三平台同步 + --check
"""

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


def test_config():
    print("[unit] 平台配置")
    import platforms as p
    check("claude agents 路径",
          p.PLATFORMS["claude"].agents_dir(Path("P")) == Path("P") / ".claude" / "agents")
    check("reasonix agents=None", p.PLATFORMS["reasonix"].agents_dir(Path("P")) is None)
    check("reasonix skills 路径",
          p.PLATFORMS["reasonix"].skills_dir(Path("P")) == Path("P") / ".reasonix" / "skills")
    check("unknown key 抛错", _raises(p.platform_from_key, "bad-key"))
    check("检测优先显式覆盖", p.detect_platform(Path("d:/x/.reasonix/skills"), "claude").key == "claude")


def _raises(fn, *a) -> bool:
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ---------------- E2E init ----------------

def test_init_layout():
    print("[e2e] init.py 三平台布局")
    expect_map = {
        "claude":   (["agents", "knowledge", "memory"], [".reasonix"]),
        "opencode": (["agents", "knowledge", "memory"], [".claude", ".reasonix"]),
        "reasonix": (["skills", "knowledge", "memory"], [".claude"]),
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
                 "memory-recording", "roleplay-sandbox"]
        for n in names:
            check(f"reasonix skill {n}", (tmp / ".reasonix/skills" / n / "SKILL.md").exists())
        w = (tmp / ".reasonix/skills/writer/SKILL.md").read_text(encoding="utf-8")
        check("reasonix writer 引用改写",
              ".reasonix/knowledge/" in w and ".claude/knowledge/" not in w)

    # claude agents 数量
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "claude")
        n = len(list((tmp / ".claude/agents").glob("*.md")))
        check(f"claude agents 数量=8", n == 8, f"实际 {n}")

    # opencode agent 引用改写
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "opencode")
        w = (tmp / ".opencode/agents/writer.md").read_text(encoding="utf-8")
        check("opencode writer 引用改写",
              ".opencode/knowledge/" in w and ".claude/knowledge/" not in w)


# ---------------- E2E sync ----------------

def test_sync():
    print("[e2e] sync-project.py 三平台同步")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "claude")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp)], cwd=str(tmp))
        check("claude sync exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        check("claude sync 生成 .claude/skills", (tmp / ".claude/skills").exists())

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "reasonix")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp)], cwd=str(tmp))
        check("reasonix sync exit 0", r.returncode == 0, (r.stdout + r.stderr)[-400:])
        check("reasonix sync 保持 skill", (tmp / ".reasonix/skills/writer/SKILL.md").exists())
        check("reasonix sync 无 .claude", not (tmp / ".claude").exists())

    # --check：无指纹首次 → exit 1
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_project(tmp, "reasonix")
        r = run([sys.executable, str(TOOLS / "sync-project.py"), str(tmp), "--check"], cwd=str(tmp))
        check("reasonix --check 无指纹 exit 1", r.returncode == 1, str(r.returncode))


def main():
    test_detect()
    test_rewrite()
    test_config()
    test_init_layout()
    test_sync()
    print(f"\n结果: {PASS} 通过, {FAIL} 失败")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行，确认失败（红）**

Run: `python tools/test_platforms.py`
Expected: 失败。`import platforms` 抛 ModuleNotFoundError（模块还不存在），后续用例不执行；且即使跳过，init.py 还没有 `--platform` 参数会忽略它（部署成 claude 布局），E2E 断言也会失败。

- [ ] **Step 3: Commit**

```bash
git add tools/test_platforms.py
git commit -m "test: 平台适配层验证脚本（先红）"
```

---

## Task 2: 实现 `tools/platforms.py`

**Files:**
- Create: `tools/platforms.py`
- Test: `tools/test_platforms.py`（单测部分）

- [ ] **Step 1: 写模块（平台配置 + 检测 + 改写 + reasonix 生成）**

```python
#!/usr/bin/env python3
"""平台适配层：不同 coding agent 对 agent/skill/knowledge/memory 的目录约定不同，
init.py / sync-project.py 共用本模块完成平台检测、目录派发、引用改写与 Reasonix skill 生成。

支持平台（扩展新平台 = 往 PLATFORMS 加一行 + 处理 agents=None 语义）：
  - claude   → .claude/   agents=agents, knowledge, memory
  - opencode → .opencode/ agents=agents, knowledge, memory
  - reasonix → .reasonix/ agents=None（agents 即 skills）, skills=skills, knowledge, memory
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Platform:
    key: str                 # "claude" | "opencode" | "reasonix"
    label: str               # 显示名
    root: str                # 平台根目录，如 ".reasonix"
    agents: str | None       # agents 子目录；reasonix 为 None（agents 即 skills）
    skills: str | None       # skills 子目录
    knowledge: str           # knowledge 子目录
    memory: str              # memory 子目录
    detect_keywords: tuple   # SKILL_HOME 路径识别关键词

    def agents_dir(self, project: Path) -> Path | None:
        if self.agents is None:
            return None
        return project / self.root / self.agents

    def skills_dir(self, project: Path) -> Path | None:
        if self.skills is None:
            return None
        return project / self.root / self.skills

    def knowledge_dir(self, project: Path) -> Path:
        return project / self.root / self.knowledge

    def memory_dir(self, project: Path) -> Path:
        return project / self.root / self.memory


PLATFORMS = {
    "claude":   Platform("claude", "Claude Code", ".claude",   agents="agents",
                         skills="skills", knowledge="knowledge", memory="memory", detect_keywords=()),
    "opencode": Platform("opencode", "OpenCode", ".opencode", agents="agents",
                         skills="skills", knowledge="knowledge", memory="memory", detect_keywords=("opencode",)),
    "reasonix": Platform("reasonix", "Reasonix", ".reasonix", agents=None,
                         skills="skills", knowledge="knowledge", memory="memory", detect_keywords=("reasonix",)),
}


def platform_from_key(key: str) -> Platform:
    if key not in PLATFORMS:
        raise ValueError(f"未知平台: {key}，可选: {', '.join(PLATFORMS)}")
    return PLATFORMS[key]


def detect_platform(skill_home: Path, override: str | None = None) -> Platform:
    """平台检测：显式指定 > SKILL_HOME 路径关键词 > 默认 claude。"""
    if override:
        return platform_from_key(override)
    p = str(skill_home).lower()
    if "reasonix" in p:
        return PLATFORMS["reasonix"]
    if "opencode" in p:
        return PLATFORMS["opencode"]
    return PLATFORMS["claude"]


def rewrite_refs(text: str, platform: Platform) -> str:
    """部署内容里的 Claude Code 路径引用 → 平台路径。仅改 knowledge/memory，claude 原样返回。"""
    if platform.key == "claude":
        return text
    text = text.replace(".claude/knowledge/", f"{platform.root}/knowledge/")
    text = text.replace(".claude/memory/", f"{platform.root}/memory/")
    return text


def resolve_skill_home() -> Path:
    """技能仓库根目录。脚本永远位于技能根 tools/ 下。

    __file__ 推导即正确来源（仓库 / 安装版 / reasonix 项目级安装）；
    NOVEL_SKILL_HOME 仅作异常兜底（__file__ 解析异常时），不能优先——
    install.sh 会把它持久化到 profile，可能指向陈旧安装副本。
    """
    by_file = Path(__file__).resolve().parent.parent
    if (by_file / "agents").is_dir() and (by_file / "tools").is_dir():
        return by_file
    env_home = os.environ.get("NOVEL_SKILL_HOME")
    if env_home:
        cand = Path(env_home)
        if (cand / "agents").is_dir() and (cand / "tools").is_dir():
            return cand
    return by_file


# ---------------------------------------------------------------
# Reasonix skill 生成（agents + skills 源 → .reasonix/skills/<name>/SKILL.md）
# ---------------------------------------------------------------

_REASONIX_TOOL_MAP = {
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "edit_file",
    "Glob": "glob",
    "Grep": "grep",
}


def _convert_to_reasonix(text: str, run_as: str = "subagent", inline_sops=None) -> str:
    """Claude Code agent frontmatter → Reasonix skill frontmatter。

    - frontmatter: 保留 name/description，tools→allowed-tools（Agent 丢弃），
      需要加载共享 SOP 的 agent 补 read_skill
    - body: agent 身份段 + 内联的专属 SOP 全文
    - runAs: subagent（执行 agent）/ inline（调度者）
    """
    parts = text.split("---", 2)
    if len(parts) != 3:
        return text
    try:
        import yaml
        data = yaml.safe_load(parts[1])
    except Exception:
        return text
    if not isinstance(data, dict):
        return text

    name = str(data.get("name", "unknown")).strip()
    desc = str(data.get("description", "")).strip().replace('"', "'")
    tools_raw = str(data.get("tools", "") or "")
    allowed = []
    for t in tools_raw.split(","):
        t = t.strip()
        if not t or t == "Agent":
            continue
        mapped = _REASONIX_TOOL_MAP.get(t, t)
        if mapped not in allowed:
            allowed.append(mapped)
    if name in ("volume-planner", "chapter-planner", "prompt-crafter", "updater"):
        if "read_skill" not in allowed:
            allowed.append("read_skill")

    fm = (
        f"---\n"
        f"name: {name}\n"
        f"description: \"{desc}\"\n"
        f"runAs: {run_as}\n"
        f"allowed-tools: [{', '.join(allowed)}]\n"
        f"---\n"
    )

    agent_body = parts[2].strip()
    if name == "novel-agent":
        agent_body += (
            "\n\n## Reasonix 调度适配（本环境无 Agent 工具）\n"
            "在 Reasonix 环境调度子 agent 用 `run_skill` 工具：\n"
            "- `run_skill(name=\"<子agent名>\", arguments=\"{order 内容}\")` 调单个子 agent\n"
            "- 子 agent 名即 .reasonix/skills/ 下的 skill 名（writer / volume-planner / "
            "chapter-planner / prompt-crafter / anti-ai / reader / updater）\n"
            "- 子 agent 是 subagent 类型，run_skill 的 arguments 会作为它唯一的 task 输入\n"
            "- 并发调度只读子 agent 可用 `parallel_tasks`；order 文件协议（status: DONE）不变\n"
        )
    sop_sections = []
    for sop in (inline_sops or []):
        if sop and sop.exists():
            sop_sections.append(
                f"\n---\n\n## 执行 SOP：{sop.name}\n\n{sop.read_text(encoding='utf-8').strip()}"
            )
    return fm + "\n" + agent_body + "\n".join(sop_sections)


def _convert_inline_skill(text: str, name: str) -> str:
    """纯正文 SOP → Reasonix inline skill。"""
    desc = ""
    for ln in text.split("\n"):
        if ln.strip().startswith("# ") and not ln.strip().startswith("## "):
            desc = ln.strip().lstrip("# ").strip()
            break
    fm = (
        f"---\n"
        f"name: {name}\n"
        f"description: \"{desc or name}（由 awesome-novel 自动生成的 inline skill）\"\n"
        f"runAs: inline\n"
        f"---\n"
    )
    return fm + "\n" + text.strip()


def deploy_reasonix_skills(project: Path, skill_home: Path, platform: Platform) -> None:
    """生成 <project>/<platform.root>/skills/<name>/SKILL.md（10 个），引用改写为平台路径。

    仅 reasonix 平台调用（agents=None）。产物引用 platform.root/knowledge、memory。
    """
    agents_dir = skill_home / "agents"
    skills_dir = skill_home / "skills"
    target = platform.skills_dir(project)
    if target is None:
        return
    target.mkdir(parents=True, exist_ok=True)

    exec_agents = {
        "writer": ["writing-execution"],
        "volume-planner": ["volume-arc", "volume-direction", "volume-writing"],
        "chapter-planner": ["chapter-reference", "chapter-outline", "chapter-verify"],
        "prompt-crafter": ["prompt-crafting", "prompt-audit"],
        "anti-ai": ["anti-ai"],
        "reader": ["reader-review"],
        "updater": ["updater-archive", "updater-setting", "updater-rollback"],
    }
    for agent_name, sops in exec_agents.items():
        agent_file = agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            continue
        sop_files = [skills_dir / f"{s}.md" for s in sops]
        body = _convert_to_reasonix(agent_file.read_text(encoding="utf-8"),
                                    run_as="subagent", inline_sops=sop_files)
        body = rewrite_refs(body, platform)
        skill_dir = target / agent_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    novel_file = agents_dir / "novel-agent.md"
    if novel_file.exists():
        body = _convert_to_reasonix(novel_file.read_text(encoding="utf-8"),
                                    run_as="inline",
                                    inline_sops=[skills_dir / "novel-dispatch.md"])
        body = rewrite_refs(body, platform)
        skill_dir = target / "novel-agent"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    for skill_name in ("memory-recording", "roleplay-sandbox"):
        sf = skills_dir / f"{skill_name}.md"
        if sf.exists():
            body = _convert_inline_skill(sf.read_text(encoding="utf-8"), skill_name)
            body = rewrite_refs(body, platform)
            skill_dir = target / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
```

- [ ] **Step 2: 运行单测，确认通过（绿）**

Run: `python tools/test_platforms.py`
Expected: 单测三段（detect / rewrite / config）全 ok；E2E 段仍失败（init.py / sync-project.py 还没改）。最终 exit 非 0 属预期。

- [ ] **Step 3: Commit**

```bash
git add tools/platforms.py
git commit -m "feat: tools/platforms.py 平台适配层（配置表/检测/引用改写/reasonix skill 生成）"
```

---

## Task 3: 重构 `tools/init.py` 为平台感知

**Files:**
- Modify: `tools/init.py`
- Test: `tools/test_platforms.py`（E2E init 部分）

- [ ] **Step 1: 替换头部 import 与平台常量**

删除 init.py 里的 `resolve_skill_home()` 函数（原约 16 行），并在 imports 后加：

```python
from platforms import (
    Platform,
    detect_platform,
    deploy_reasonix_skills,
    rewrite_refs,
    resolve_skill_home,
)
```

> `PLATFORMS` 不导入（init.py 只用 `detect_platform` 返回的 Platform 实例）。模块级 `SKILL_HOME = resolve_skill_home()`（原第 59 行）保持不动，import 后自动解析到 platforms 里的实现。

同时删除 init.py 中已迁走的函数/常量（`deploy_reasonix`、`_deploy_inline_skill`、`_convert_to_reasonix`、`_convert_inline_skill`、`_REASONIX_TOOL_MAP` 整段），`_OPENCODE_TOOL_TO_PERM`、`_convert_to_opencode` 保留。

- [ ] **Step 2: 更新 docstring 用法行**

把 docstring 里的「用法: python init.py [project-path] [--genre <编号>]」改为：

```
用法: python init.py [project-path] [--genre <编号>] [--platform <claude|opencode|reasonix>]

平台缺省：--platform > NOVEL_PLATFORM > SKILL_HOME 路径识别 > claude。
```

只改用法行与平台说明，docstring 其余部分不动。

- [ ] **Step 3: 重写 main() 的平台解析与调用**

```python
def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__.strip())
        return

    if len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
        project_path = Path(sys.argv[1]).resolve()
    else:
        project_path = Path.cwd()

    # 平台：--platform > NOVEL_PLATFORM > SKILL_HOME 路径识别 > claude
    platform_override = None
    if "--platform" in sys.argv:
        idx = sys.argv.index("--platform")
        if idx + 1 < len(sys.argv):
            platform_override = sys.argv[idx + 1]
    platform_override = platform_override or os.environ.get("NOVEL_PLATFORM")
    platform = detect_platform(SKILL_HOME, platform_override)
    print(f"平台: {platform.label}")

    # 解析可选参数
    genre = None
    if "--genre" in sys.argv:
        idx = sys.argv.index("--genre")
        if idx + 1 < len(sys.argv):
            try:
                genre = GENRES[int(sys.argv[idx + 1]) - 1]
            except (IndexError, ValueError):
                print(f"无效题材编号，可选 1-{len(GENRES)}")
                sys.exit(1)

    if project_path.exists():
        print(f"目录已存在，将在其中创建缺失的文件和目录")
    else:
        project_path.mkdir(parents=True)

    print(f"初始化小说项目: {project_path}")
    print(f"技能仓库: {SKILL_HOME}")

    # Step 1: 选题材
    if genre is None:
        genre = select_genre()
    else:
        print(f"题材: {genre}")

    # Step 2: 创建骨架
    create_skeleton(project_path, platform)

    # Step 3: 部署 agent 定义
    deploy_agents(project_path, platform)

    # Step 3.5: 部署 Reasonix skills（仅 reasonix 平台）
    if platform.key == "reasonix":
        deploy_reasonix_skills(project_path, SKILL_HOME, platform)

    # Step 4: 按题材继承记忆
    deploy_memory(project_path, genre)

    # Step 5: 按题材继承知识
    deploy_knowledge(project_path, genre, platform)

    # Step 5.5: 按题材预填 settings 默认值
    seed_settings_from_genre(project_path, genre, platform)

    # Step 6: 生成 MEMORY.md 索引
    write_memory_index(project_path, platform)

    # Step 7: 初始化写作记忆文件
    init_memory_files(project_path, platform)

    # Step 8: 初始化状态
    write_status(project_path)

    print(f"\n初始化完成!")
    print(f"项目路径: {project_path}")
    if platform.key == "claude":
        print("输入 @novel-agent 开始写作（Claude Code）")
    elif platform.key == "opencode":
        print("在 OpenCode 中通过 @novel-agent 开始写作")
    else:
        print("在 Reasonix 中运行 `reasonix code`，然后调用 @novel-agent 开始写作")
```

- [ ] **Step 4: create_skeleton 平台化**

```python
def create_skeleton(project_path: Path, platform: Platform):
    """创建项目目录结构"""
    dirs = [
        "settings/character-setting",
        "volumes",
        "chapters",
        "prompts",
        "sandbox",
        "archives",
        ".agent/task",
        str(platform.memory_dir(project_path)),
        str(platform.knowledge_dir(project_path)),
    ]
    for d in dirs:
        (project_path / d).mkdir(parents=True, exist_ok=True)

    # Copy template files into project (skip migration/ — old project upgrade only)
    if SOURCE_TEMPLATES.exists():
        for item in SOURCE_TEMPLATES.rglob("*"):
            if item.is_file() and item.name != ".gitkeep":
                rel_path = item.relative_to(SOURCE_TEMPLATES)
                if rel_path.parts[0] == "migration":
                    continue
                target = project_path / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
        print("  ✅ 已拷贝项目模板")
```

- [ ] **Step 5: deploy_agents 平台化**

```python
def deploy_agents(project_path: Path, platform: Platform):
    """根据当前平台复制 agent 定义到对应目录"""
    if not SOURCE_AGENTS.exists():
        print("  ⚠️  agent 目录不存在，跳过")
        return
    agent_dir = platform.agents_dir(project_path)
    if agent_dir is None:
        # reasonix：agents 即 skills（deploy_reasonix_skills 生成），不部署 .claude/agents
        print("  ℹ️  reasonix 平台不部署 agent 定义（agents 即 .reasonix/skills/）")
        return
    agent_dir.mkdir(parents=True, exist_ok=True)
    is_opencode = platform.key == "opencode"
    for item in SOURCE_AGENTS.rglob("*"):
        if item.is_file() and item.suffix == ".md":
            rel_path = item.relative_to(SOURCE_AGENTS)
            dest = agent_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = item.read_text(encoding="utf-8")
            if is_opencode:
                content = _convert_to_opencode(content)
                content = rewrite_refs(content, platform)
            dest.write_text(content, encoding="utf-8")
    print(f"  ✅ 已部署 agent 定义到 {agent_dir}")
```

- [ ] **Step 6: deploy_knowledge / seed_settings_from_genre / write_memory_index / init_memory_files 平台化**

三处改动（其余函数体不变）：

```python
def deploy_knowledge(project_path: Path, genre: str, platform: Platform):
    """按题材拷贝参考材料 + 反 AI/文风规则到平台 knowledge 目录"""
    knowledge_dir = platform.knowledge_dir(project_path)
    # ……函数体其余部分不变，仅首行 knowledge_dir 取值改为上式……
```

```python
def seed_settings_from_genre(project_path: Path, genre: str, platform: Platform):
    ex = platform.knowledge_dir(project_path) / "genre-example.md"
    # ……其余不变……
```

```python
def write_memory_index(project_path: Path, platform: Platform):
    """生成 <平台>/memory/MEMORY.md 占位索引"""
    memory_dir = platform.memory_dir(project_path)
    (memory_dir / "MEMORY.md").write_text("# 写作记忆库\n\n（暂无记忆）\n", encoding="utf-8")
```

```python
def init_memory_files(project_path: Path, platform: Platform):
    """初始化 4 个写作记忆文件"""
    memory_dir = platform.memory_dir(project_path)
    for filename, content in MEMORY_FILES.items():
        filepath = memory_dir / filename
        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
    print("  ✅ 已初始化 4 个写作记忆文件")
```

注意同步改函数签名处：`deploy_knowledge(project_path, genre)` → `(project_path, genre, platform)`，`seed_settings_from_genre`、`write_memory_index`、`init_memory_files` 加 `platform` 参数，并确认 main() 调用已按 Step 3 传参。

- [ ] **Step 7: 运行 E2E init 用例，确认绿**

Run: `python tools/test_platforms.py`
Expected: `[e2e] init.py 三平台布局` 段全 ok（三平台布局、reasonix 10 个 skill、引用改写、claude agents=8、opencode 改写）。

- [ ] **Step 8: Commit**

```bash
git add tools/init.py
git commit -m "feat: init.py 平台感知部署（--platform，reasonix/opencode 纯原生不产生 .claude/）"
```

---

## Task 4: 重构 `tools/sync-project.py` 为平台感知

**Files:**
- Modify: `tools/sync-project.py`
- Test: `tools/test_platforms.py`（E2E sync 部分）

- [ ] **Step 1: 顶部 import + 平台检测**

两处替换：
1. 原第 37 行 `SKILL_HOME = Path(__file__).parent.parent` → `SKILL_HOME = resolve_skill_home()`
2. 删除 `IS_OPENCODE` / `AGENT_TARGET` 两行（原 44-46 行），并在 imports 后加：

```python
from platforms import (
    Platform,
    detect_platform,
    deploy_reasonix_skills,
    resolve_skill_home,
)
```

> `rewrite_refs` 不需要导入——`deploy_reasonix_skills` 内部已做引用改写。`SKILL_DIR` / `KNOWLEDGE_DIR` / `AGENT_DIR` 等源目录常量保持不动（它们是源，与平台无关）。

- [ ] **Step 2: main() 加平台解析并下传**

```python
def main():
    if "-h" in sys.argv or "--help" in sys.argv or len(sys.argv) < 2:
        print(__doc__.strip())
        return

    check_only = "--check" in sys.argv

    # 平台：--platform > NOVEL_PLATFORM > SKILL_HOME 路径识别 > claude
    platform_override = None
    if "--platform" in sys.argv:
        idx = sys.argv.index("--platform")
        if idx + 1 < len(sys.argv):
            platform_override = sys.argv[idx + 1]
    platform_override = platform_override or os.environ.get("NOVEL_PLATFORM")
    platform = detect_platform(SKILL_HOME, platform_override)

    # 处理 Windows 中文路径乱码：从 os.environ 重新取当前目录
    raw_arg = sys.argv[1]
    if raw_arg == "." and os.environ.get("PWD"):
        pwd = os.environ["PWD"]
        if os.path.exists(pwd):
            raw_arg = pwd
    project_path = Path(raw_arg).resolve()
    if not project_path.exists():
        print(f"错误: 路径不存在: {project_path}")
        sys.exit(2)

    status_file = project_path / ".agent" / "status.md"
    if not status_file.exists():
        print(f"错误: {project_path} 不是有效的小说项目（缺少 .agent/status.md）")
        sys.exit(2)

    if check_only:
        check_freshness(project_path, platform)
        return

    do_sync(project_path, platform)
```

- [ ] **Step 3: find_changes 平台化 + reasonix skills 跳过枚举**

```python
def find_changes(project: Path, platform: Platform) -> list[str]:
    """返回与源不同的文件列表（相对路径）。reasonix 的 skills 是派生产物，不枚举。"""
    changed = []
    targets = {
        "agents": platform.agents_dir(project),
        "skills": platform.skills_dir(project),
        "knowledge": platform.knowledge_dir(project),
    }
    src_dirs = {
        "agents": AGENT_DIR,
        "skills": SKILL_DIR,
        "knowledge": KNOWLEDGE_DIR,
    }
    for name in ("agents", "skills", "knowledge"):
        dst_base = targets[name]
        src_dir = src_dirs[name]
        if dst_base is None or not src_dir.exists():
            continue
        if platform.key == "reasonix" and name == "skills":
            continue  # 派生产物靠源指纹检测，不同步时重新生成
        for item in sorted(src_dir.rglob("*.md")):
            if item.name == ".gitkeep":
                continue
            rel = item.relative_to(src_dir)
            target = dst_base / rel
            if not target.exists() or target.read_bytes() != item.read_bytes():
                changed.append(f"{name}/{rel}")
    return changed
```

- [ ] **Step 4: check_freshness 传 platform + reasonix 空变更提示**

```python
def check_freshness(project: Path, platform: Platform):
    current = compute_fingerprint()
    stored, stored_ver = read_project_fingerprint(project)
    latest_ver, _ = get_version_info()

    if stored is None:
        print("项目缺少同步指纹，无法判断新鲜度。运行 sync-project.py 同步后生成。")
        sys.exit(1)

    version_diff = latest_ver and stored_ver and stored_ver != latest_ver
    version_info = ""
    if version_diff:
        version_info = f"  [版本] 项目记录: {stored_ver}  →  最新: {latest_ver}"
    elif latest_ver and not stored_ver:
        version_info = f"  [版本] 最新: {latest_ver}（项目未记录版本）"

    if current == stored:
        if version_diff:
            print(f"文件已是最新。{version_info}")
            sys.exit(1)
        print("已是最新。")
        sys.exit(0)
    else:
        changes = find_changes(project, platform)
        if not changes and platform.key == "reasonix":
            print("有更新可用（源文件变化，reasonix skill 由同步时重新生成）。")
        else:
            lines = [f"有更新可用 ({len(changes)} 个文件发生变化):"]
            for f in changes:
                lines.append(f"  - {f}")
            if version_info:
                lines.append(version_info)
            print("\n".join(lines))
        sys.exit(1)
```

- [ ] **Step 5: do_sync / sync_agents / sync_skills / sync_knowledge 平台化**

```python
def do_sync(project: Path, platform: Platform):
    print(f"项目: {project}")
    print(f"来源: {SKILL_HOME}")

    latest_ver, _ = get_version_info()
    if latest_ver:
        print(f"版本: {latest_ver}")
    print()

    current_fp = compute_fingerprint()
    stored_fp, stored_ver = read_project_fingerprint(project)

    version_changed = latest_ver and stored_ver and stored_ver != latest_ver

    if stored_fp == current_fp and not version_changed:
        print("[i] 已是最新，无需同步。")
        return

    changes = []
    changes.append(sync_agents(project, platform))
    changes.append(sync_skills(project, platform))
    changes.append(sync_knowledge(project, platform))

    total = sum(c for c in changes if c > 0)

    if total > 0 or stored_fp != current_fp or version_changed:
        write_project_fingerprint(project, current_fp, latest_ver)

    print(f"\n完成。共同步 {total} 个文件。版本: {latest_ver or 'unknown'}")
    if total > 0:
        print("提示: 下次写作时生效。")


def sync_agents(project_path: Path, platform: Platform) -> int:
    """同步 agent 定义到当前平台对应的目录"""
    if not AGENT_DIR.exists():
        print("  [!] agents 源目录不存在，跳过")
        return 0
    target = platform.agents_dir(project_path)
    if target is None:
        print("  [i] reasonix 平台无 agents 目录（agents 即 skills）")
        return 0
    target.mkdir(parents=True, exist_ok=True)
    count = _sync_dir(AGENT_DIR, target, "*.md")
    if count > 0:
        print(f"  [OK] agent 定义: {count} 个文件已更新（{platform.root}/agents）")
    else:
        print("  [i] agent 定义: 已是最新")
    return count


def sync_skills(project_path: Path, platform: Platform) -> int:
    if platform.key == "reasonix":
        deploy_reasonix_skills(project_path, SKILL_HOME, platform)
        n = len(list(platform.skills_dir(project_path).rglob("SKILL.md")))
        print(f"  [OK] reasonix skills: {n} 个 SKILL.md 已重新生成")
        return n
    target = platform.skills_dir(project_path)
    target.mkdir(parents=True, exist_ok=True)
    if not SKILL_DIR.exists():
        print("  [!] skills 源目录不存在，跳过")
        return 0
    count = _sync_dir(SKILL_DIR, target, "*.md")
    if count > 0:
        print(f"  [OK] skill 文件: {count} 个文件已更新")
    else:
        print("  [i] skill 文件: 已是最新")
    return count


def sync_knowledge(project_path: Path, platform: Platform) -> int:
    target = platform.knowledge_dir(project_path)
    target.mkdir(parents=True, exist_ok=True)
    if not KNOWLEDGE_DIR.exists():
        print("  [!] knowledge 源目录不存在，跳过")
        return 0
    count = 0

    # 平铺到平台 knowledge 根的目录（部署约定与 init.py 的 deploy_knowledge 一致）。
    FLAT_SUBDIRS = {"format-specs"}

    for f in KNOWLEDGE_DIR.glob("*.md"):
        if _sync_file(f, target / f.name):
            count += 1
    for subdir in KNOWLEDGE_DIR.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("."):
            if subdir.name in FLAT_SUBDIRS:
                for f in sorted(subdir.glob("*.md")):
                    if _sync_file(f, target / f.name):
                        count += 1
            else:
                sub_target = target / subdir.name
                sub_target.mkdir(parents=True, exist_ok=True)
                count += _sync_dir(subdir, sub_target, "*.md")
    if count > 0:
        print(f"  [OK] 知识库: {count} 个文件已更新")
    else:
        print("  [i] 知识库: 已是最新")
    return count
```

- [ ] **Step 6: 运行 E2E sync 用例，确认绿**

Run: `python tools/test_platforms.py`
Expected: `[e2e] sync-project.py 三平台同步` 段全 ok（claude 生成 `.claude/skills`、reasonix 保持 skill 且无 `.claude`、`--check` 无指纹 exit 1）。

- [ ] **Step 7: Commit**

```bash
git add tools/sync-project.py
git commit -m "feat: sync-project.py 平台感知同步（reasonix 重新生成 skills）"
```

---

## Task 5: SKILL.md 入口措辞平台化

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: 逐处替换（11 处，old → new）**

> 行号以当前 SKILL.md 为准，编辑时按内容定位。

| # | 原文（片段） | 改为 |
|---|------------|------|
| 1 (L44) | `确认 .agent/status.md 和 .opencode/agents/ 已生成` | `确认 .agent/status.md 与平台部署目录已生成（Claude Code → .claude/agents/；OpenCode → .opencode/agents/；Reasonix → .reasonix/skills/）` |
| 2 (L59) | `3. 部署 agent 定义到 .opencode/agents/（OpenCode）或 .claude/agents/（Claude Code）` | `3. 部署 agent/skill 到当前平台约定目录（Claude Code → .claude/agents/；OpenCode → .opencode/agents/；Reasonix 不部署 agents，agents 即 .reasonix/skills/）` |
| 3 (L60) | `4. 按题材继承反 AI 规则和文风偏好到 .claude/knowledge/` | `4. 按题材继承反 AI 规则和文风偏好到平台 knowledge 目录（.claude/knowledge/ / .opencode/knowledge/ / .reasonix/knowledge/）` |
| 4 (L61) | `5. 按题材继承格式规范、题材案例到 .claude/knowledge/` | `5. 按题材继承格式规范、题材案例到平台 knowledge 目录` |
| 5 (L62) | `6. 创建空白的写作记忆文件（.claude/memory/*.md）` | `6. 创建空白的写作记忆文件（平台 memory 目录）` |
| 6 (L63) | `7. 创建永久记忆占位文件（.claude/knowledge/permanent-memory.md）` | `7. 创建永久记忆占位文件（平台 knowledge 目录）` |
| 7 (L136) | `old/settings/anti-ai.yaml → .claude/knowledge/anti-ai.md` | `old/settings/anti-ai.yaml → 平台 knowledge/anti-ai.md（.claude / .opencode / .reasonix）` |
| 8 (L164) | `- [ ] .claude/knowledge/anti-ai.md 存在（迁移自旧 anti-ai.yaml）` | `- [ ] 平台 knowledge/anti-ai.md 存在（迁移自旧 anti-ai.yaml）` |
| 9 (L224 结构图) | `└── .claude/` + `.opencode/` 两段 | 改三选一结构图（见下） |
| 10 (L244) | `各 agent 定义在 .opencode/agents/（OpenCode）或 .claude/agents/（Claude Code）` | `各 agent 定义在平台约定目录（Claude Code → .claude/agents/；OpenCode → .opencode/agents/；Reasonix → .reasonix/skills/）` |
| 11 (L260) | `**Edit** 写 settings/、.claude/ 下的内容文件` | `**Edit** 写 settings/、平台目录下的内容文件` |

结构图（#9）改为：

```
├── .claude/             # Claude Code 用（平台一，三选一）
│   ├── agents/          # Agent 定义
│   ├── knowledge/       # 反 AI 规则、文风偏好、永久记忆、格式规范
│   └── memory/          # 写作动态记忆
├── .opencode/           # OpenCode 用（平台二，三选一，同 .claude 结构）
│   └── agents/           # Agent 定义
└── .reasonix/           # Reasonix 用（平台三，三选一）
    ├── skills/          # 10 个 SKILL.md（agents 即 skills）
    ├── knowledge/       # 反 AI 规则、文风偏好、永久记忆、格式规范
    └── memory/          # 写作动态记忆
```

> 说明：实际项目只会出现其中一套（由 init.py --platform 决定）；图上并排列出三种。

- [ ] **Step 2: 验证无残留硬编码**

Run: `grep -n "\.claude/" SKILL.md`
Expected: 剩余 `.claude/` 只出现在「三选一说明」的合法列举里（如 `.claude/knowledge/`、`.claude/agents/`），不再有「部署到 .claude/」「确认 .claude/agents/ 已生成」这类硬编码指令。同时 `grep -n "\.opencode/" SKILL.md` 同理只剩说明性列举。

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "docs: SKILL.md 平台相关措辞平台化（三选一目录说明）"
```

---

## Task 6: 全量回归 + 收尾

**Files:**
- Modify: `docs/superpowers/plans/2026-08-03-platform-adaptation.md`（本文档）
- 可能：`tools/test_platforms.py`

- [ ] **Step 1: 全量跑验证脚本**

Run: `python tools/test_platforms.py`
Expected: 全部 ok，`结果: N 通过, 0 失败`，exit 0。

- [ ] **Step 2: 框架静态回归**

Run:
```bash
python tools/check-agents.py
python tools/check-conflicts.py
```
Expected: 两者都返回 0（源文件未改，应为通过）。

- [ ] **Step 3: claude 布局与改动前一致性抽查**

Run:
```bash
rm -rf /tmp/pa-claude && python tools/init.py /tmp/pa-claude --genre 1 --platform claude
find /tmp/pa-claude/.claude -type f | wc -l
```
Expected: `.claude/agents` 8 个文件、`.claude/knowledge` 全量、`.claude/memory` 5 个文件；无 `.reasonix/`。claude 平台 init 产物与改动前一致（rewrite_refs 对 claude 零影响）。

- [ ] **Step 4: reasonix 真实项目冒烟（可选，手动）**

在 `D:\novels\new` 跑：
```bash
python D:/novels/new/.reasonix/skills/awesome-novel/tools/init.py --platform reasonix --genre 1 .
```
Expected: `.reasonix/knowledge/`、`.reasonix/memory/` 生成，`.claude/` 不再新增。确认 `.reasonix/skills/*/SKILL.md` 引用为 `.reasonix/knowledge/`。

- [ ] **Step 5: 更新计划内文档状态并提交**

```bash
git add tools/ tools/docs 2>/dev/null; git status --short
```
若 test_platforms.py 有迭代，单独提交；无改动则跳过。

- [ ] **Step 6: 汇总验证结果**

向用户汇报：三平台布局断言、引用改写、sync 回归、check 脚本结果。标记本计划 Task 1-6 全部完成。

---

## 自检记录

- **Spec 覆盖：** §4（platforms.py）→ Task 2；§5（init.py）→ Task 3；§6（sync-project.py）→ Task 4；§7（SKILL.md）→ Task 5；§9（验证）→ Task 1/6。§8 边界（从克隆跑显式 --platform、reasonix 不部署 agents、无迁移）→ 已体现在对应实现。
- **占位符扫描：** 无 TBD/TODO；所有改动步骤给了完整代码。
- **类型一致性：** `deploy_reasonix_skills(project, skill_home, platform)` 在 platforms.py / init.py / sync-project.py 三处签名一致；`detect_platform(skill_home, override)`、`rewrite_refs(text, platform)`、`platform.agents_dir / skills_dir / knowledge_dir / memory_dir` 命名一致。
