#!/usr/bin/env python3
"""平台适配层：不同 coding agent 对 agent/skill/knowledge/memory 的目录约定不同，
init.py / sync-project.py 共用本模块完成平台检测、目录派发、引用改写与 skill 生成。

支持平台（扩展新平台 = 往 PLATFORMS 加一行 + 处理 agents=None 语义）：
  - claude   → .claude/   agents=agents, knowledge, memory
  - opencode → .opencode/ agents=agents, knowledge, memory
  - reasonix → .reasonix/ agents=None（agents 即 skills）, skills=skills, knowledge, memory
  - codex    → .codex/    agents=agents（TOML 转换产物）, skills=skills, knowledge, memory
  - zcode    → .zcode/    agents=None（agents 即 skills，ZCode 无项目级 agents 目录）,
                          skills=skills, knowledge, memory
  - dsh      → .dsh/      agents=None（agents 即 skills，DeepSeek Harness 无项目级
                          agents 目录，.dsh/skills 为其项目级 skill 根）, skills=skills,
                          knowledge, memory

模块名用 platforms（复数）是刻意避开标准库 platform（单数）同名冲突。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from style_common import frontmatter_text, split_frontmatter   # 单源 frontmatter 解析（review #38）


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
    "codex":    Platform("codex", "Codex", ".codex", agents="agents",
                         skills="skills", knowledge="knowledge", memory="memory", detect_keywords=(".codex",)),
    "zcode":    Platform("zcode", "ZCode", ".zcode", agents=None,
                         skills="skills", knowledge="knowledge", memory="memory", detect_keywords=(".zcode",)),
    "dsh":      Platform("dsh", "DeepSeek Harness", ".dsh", agents=None,
                         skills="skills", knowledge="knowledge", memory="memory", detect_keywords=(".dsh",)),
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
    for plat in PLATFORMS.values():
        if any(kw in p for kw in plat.detect_keywords):
            return plat
    return PLATFORMS["claude"]


def rewrite_refs(text: str, platform: Platform) -> str:
    """部署内容里的 Claude Code 路径引用 → 平台路径。claude 原样返回。

    knowledge/memory 精确替换后，剩余裸 .claude/（禁写区、目录树说明等）
    整体替换为平台根，避免部署产物残留失效引用。
    """
    if platform.key == "claude":
        return text
    text = text.replace(".claude/knowledge/", f"{platform.root}/knowledge/")
    text = text.replace(".claude/memory/", f"{platform.root}/memory/")
    text = text.replace(".claude/", f"{platform.root}/")
    return text


def ensure_yaml(platform: Platform) -> None:
    """非 claude 平台的 agent 转换依赖 pyyaml；缺失时明确报错退出。

    claude 平台是纯复制不转换，不需要 pyyaml。init.py / sync-project.py
    在平台检测后调用本函数，避免"退出 0 却产出损坏产物"的静默故障。
    """
    if platform.key == "claude":
        return
    try:
        import yaml  # noqa: F401
    except ImportError:
        print(f"错误: {platform.label} 平台需要 pyyaml（pip install pyyaml），当前环境未安装。",
              file=sys.stderr)
        sys.exit(1)


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

    - frontmatter: 保留 name/description，tools→allowed-tools（Agent 丢弃，
      role/react/memory/knowledge 丢弃），需要加载共享 SOP 的 agent 补 read_skill
    - tools 映射: 已知名经 _REASONIX_TOOL_MAP 映射为 Reasonix 名，未知名原样保留
    - body: agent 身份段 + 内联的专属 SOP 全文
    - runAs: subagent（执行 agent）/ inline（调度者）
    """
    data, body = split_frontmatter(text)    # 单源解析（review #38：坏 split 已弃用）
    if not data:
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

    agent_body = body.strip()
    if name == "novel-agent":
        agent_body += (
            "\n\n## Reasonix 调度适配（本环境无 Agent 工具）\n"
            "在 Reasonix 环境调度子 agent 用 `run_skill` 工具：\n"
            "- `run_skill(name=\"<子agent名>\", arguments=\"{order 内容}\")` 调单个子 agent\n"
            "- 子 agent 名即 .reasonix/skills/ 下的 skill 名（writer / volume-planner / "
            "chapter-planner / prompt-crafter / anti-ai / reader / updater / style-distiller）\n"
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
    """生成 <project>/<platform.root>/skills/<name>/SKILL.md（11 个），引用改写为平台路径。

    仅 reasonix 平台调用（agents=None）。产物引用 platform.root/knowledge、memory。
    """
    if platform.key != "reasonix":
        return
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
        "style-distiller": ["style-distill"],
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


# ---------------------------------------------------------------
# ZCode skill 生成（agents + skills 源 → .zcode/skills/<name>/SKILL.md）
# ---------------------------------------------------------------

def _convert_to_zcode(text: str, inline_sops=None) -> str:
    """Claude Code agent frontmatter → ZCode skill frontmatter。

    ZCode 与 Claude Code 约定同源（目录 + SKILL.md，工具名一致），无项目级
    agents 目录——agents 即 skills。转换要点：
    - frontmatter: 保留 name/description，tools → allowed-tools（裸名原样，
      与 ZCode 工具名一致；Agent 丢弃，子 agent 无调度权，与 reasonix 同规则；
      ZCode skill 无 runAs 字段，subagent/inline 由调用方式区分）
    - body: agent 身份段 + 内联的专属 SOP 全文
    - novel-agent（入口调度者）追加 ZCode 调度适配段；其余为 subagent
    """
    data, body = split_frontmatter(text)    # 单源解析（review #38：坏 split 已弃用）
    if not data:
        return text

    name = str(data.get("name", "unknown")).strip()
    desc = str(data.get("description", "") or "").strip().replace('"', "'")
    tools_raw = str(data.get("tools", "") or "")
    allowed = []
    for t in tools_raw.split(","):
        t = t.strip()
        if not t or t == "Agent":
            continue
        if t not in allowed:
            allowed.append(t)

    fm = (
        f"---\n"
        f"name: {name}\n"
        f"description: \"{desc}\"\n"
        f"allowed-tools: {', '.join(allowed)}\n"
        f"---\n"
    )

    agent_body = body.strip()
    if name == "novel-agent":
        agent_body += (
            "\n\n## ZCode 调度适配（本环境子 agent 即 skill）\n"
            "在 ZCode 环境调度子 agent 用 `Agent` 工具：\n"
            "- 子 agent 名即 `.zcode/skills/` 下的 skill 名（writer / volume-planner / "
            "chapter-planner / prompt-crafter / anti-ai / reader / updater / style-distiller）\n"
            "- 用 Agent 工具按子 agent 名 spawn，把 order 文件内容作为它的任务输入\n"
            "- 子 agent 是隔离上下文，只读 order 与指定文件；order 文件协议（status: DONE）不变\n"
            "- 一次只调度一个任务，等 DONE 后再调度下一个；禁止把 novel-agent 本身作为子 agent 调度\n"
        )
    sop_sections = []
    for sop in (inline_sops or []):
        if sop and sop.exists():
            sop_sections.append(
                f"\n---\n\n## 执行 SOP：{sop.name}\n\n{sop.read_text(encoding='utf-8').strip()}"
            )
    return fm + "\n" + agent_body + "\n".join(sop_sections)


def _convert_zcode_inline_skill(text: str, name: str) -> str:
    """纯正文 SOP → ZCode inline skill（无 SOP 依赖的独立交互工具）。"""
    desc = ""
    for ln in text.split("\n"):
        if ln.strip().startswith("# ") and not ln.strip().startswith("## "):
            desc = ln.strip().lstrip("# ").strip()
            break
    fm = (
        f"---\n"
        f"name: {name}\n"
        f"description: \"{desc or name}（由 awesome-novel 自动生成的 ZCode skill）\"\n"
        f"---\n"
    )
    return fm + "\n" + text.strip()


def deploy_zcode_skills(project: Path, skill_home: Path, platform: Platform) -> None:
    """生成 <project>/<platform.root>/skills/<name>/SKILL.md（11 个），引用改写为平台路径。

    仅 zcode 平台调用（agents=None）。ZCode 无项目级 agents 目录，agents 即 skills，
    产物与 reasonix 同构（9 个 agent + memory-recording/roleplay-sandbox 独立工具）。
    """
    if platform.key != "zcode":
        return
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
        "style-distiller": ["style-distill"],
    }
    for agent_name, sops in exec_agents.items():
        agent_file = agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            continue
        sop_files = [skills_dir / f"{s}.md" for s in sops]
        body = _convert_to_zcode(agent_file.read_text(encoding="utf-8"),
                                 inline_sops=sop_files)
        body = rewrite_refs(body, platform)
        skill_dir = target / agent_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    novel_file = agents_dir / "novel-agent.md"
    if novel_file.exists():
        body = _convert_to_zcode(novel_file.read_text(encoding="utf-8"),
                                 inline_sops=[skills_dir / "novel-dispatch.md"])
        body = rewrite_refs(body, platform)
        skill_dir = target / "novel-agent"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    for skill_name in ("memory-recording", "roleplay-sandbox"):
        sf = skills_dir / f"{skill_name}.md"
        if sf.exists():
            body = _convert_zcode_inline_skill(sf.read_text(encoding="utf-8"), skill_name)
            body = rewrite_refs(body, platform)
            skill_dir = target / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")


# ---------------------------------------------------------------
# DeepSeek Harness（dsh）skill 生成（agents + skills 源 → .dsh/skills/<name>/SKILL.md）
# ---------------------------------------------------------------

def _convert_to_dsh(text: str, inline_sops=None) -> str:
    """Claude Code agent frontmatter → dsh skill frontmatter。

    dsh 与 ZCode 同为「agents 即 skills」：无项目级 agents 目录，skill 根为
    <project>/.dsh/skills/<name>/SKILL.md（dsh 自动发现）。差异：
    - frontmatter 只保留 name/description——dsh 不识别 allowed-tools/runAs，
      其余键仅进 metadata 不参与加载，产物保持干净
    - body: agent 身份段 + 内联的专属 SOP 全文
    - novel-agent（入口调度者）追加 dsh 调度适配段；其余为 subagent
    """
    data, body = split_frontmatter(text)    # 单源解析（review #38：坏 split 已弃用）
    if not data:
        return text

    name = str(data.get("name", "unknown")).strip()
    desc = str(data.get("description", "") or "").strip().replace('"', "'")

    fm = (
        f"---\n"
        f"name: {name}\n"
        f"description: \"{desc}\"\n"
        f"---\n"
    )

    agent_body = body.strip()
    if name == "novel-agent":
        agent_body += (
            "\n\n## DeepSeek Harness 调度适配（本环境子 agent 即 skill）\n"
            "在 dsh 环境调度子 agent 用 `subagent` 工具：\n"
            "- 子 agent 名即 `.dsh/skills/` 下的 skill 名（writer / volume-planner / "
            "chapter-planner / prompt-crafter / anti-ai / reader / updater / style-distiller）\n"
            "- 子 agent 是隔离上下文，prompt 里要求它先调用 `skill(name=\"<子agent名>\")` "
            "加载自身指令，再执行 order 文件任务\n"
            "- 把 order 文件路径与任务要求写进 prompt；order 文件协议（status: DONE）不变\n"
            "- 一次只调度一个任务，等 DONE 后再调度下一个；禁止把 novel-agent 本身作为子 agent 调度\n"
        )
    sop_sections = []
    for sop in (inline_sops or []):
        if sop and sop.exists():
            sop_sections.append(
                f"\n---\n\n## 执行 SOP：{sop.name}\n\n{sop.read_text(encoding='utf-8').strip()}"
            )
    return fm + "\n" + agent_body + "\n".join(sop_sections)


def _convert_dsh_inline_skill(text: str, name: str) -> str:
    """纯正文 SOP → dsh inline skill（无 SOP 依赖的独立交互工具）。"""
    desc = ""
    for ln in text.split("\n"):
        if ln.strip().startswith("# ") and not ln.strip().startswith("## "):
            desc = ln.strip().lstrip("# ").strip()
            break
    fm = (
        f"---\n"
        f"name: {name}\n"
        f"description: \"{desc or name}（由 awesome-novel 自动生成的 dsh skill）\"\n"
        f"---\n"
    )
    return fm + "\n" + text.strip()


def deploy_dsh_skills(project: Path, skill_home: Path, platform: Platform) -> None:
    """生成 <project>/<platform.root>/skills/<name>/SKILL.md（11 个），引用改写为平台路径。

    仅 dsh 平台调用（agents=None）。产物与 reasonix/zcode 同构
    （9 个 agent + memory-recording/roleplay-sandbox 独立工具）。
    """
    if platform.key != "dsh":
        return
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
        "style-distiller": ["style-distill"],
    }
    for agent_name, sops in exec_agents.items():
        agent_file = agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            continue
        sop_files = [skills_dir / f"{s}.md" for s in sops]
        body = _convert_to_dsh(agent_file.read_text(encoding="utf-8"),
                               inline_sops=sop_files)
        body = rewrite_refs(body, platform)
        skill_dir = target / agent_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    novel_file = agents_dir / "novel-agent.md"
    if novel_file.exists():
        body = _convert_to_dsh(novel_file.read_text(encoding="utf-8"),
                               inline_sops=[skills_dir / "novel-dispatch.md"])
        body = rewrite_refs(body, platform)
        skill_dir = target / "novel-agent"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    for skill_name in ("memory-recording", "roleplay-sandbox"):
        sf = skills_dir / f"{skill_name}.md"
        if sf.exists():
            body = _convert_dsh_inline_skill(sf.read_text(encoding="utf-8"), skill_name)
            body = rewrite_refs(body, platform)
            skill_dir = target / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")


# ---------------------------------------------------------------
# OpenCode agent 转换（Claude Code agent frontmatter → OpenCode 语法）
# ---------------------------------------------------------------

_OPENCODE_TOOL_TO_PERM = {
    "Read": "read",
    "Write": "edit",   # OpenCode 的 edit 覆盖 write/edit/apply_patch
    "Edit": "edit",
    "Glob": "glob",
    "Grep": "grep",
    "Agent": "task",   # Claude Code Agent 工具 ↔ OpenCode task
}
# 白名单外，OpenCode 下显式 deny 的权限键（避免默认 ask 弹窗）
_OPENCODE_DENY_KEYS = ["bash", "webfetch", "websearch", "list", "lsp", "skill"]


def convert_to_opencode(text: str) -> str:
    """Claude Code agent frontmatter → OpenCode 语法（tools: → permission:）。

    关键差异：
    - Claude Code 用 `tools: Read, Write, ...` 逗号串（白名单，缺省=继承全部）
    - OpenCode 用 `permission:` map（allow/ask/deny，默认 ask）
    仅处理 `tools:` 字段 → `permission:`；其余字段（name/description/role 等）原样保留。
    """
    if not text.startswith("---"):
        return text
    fm = frontmatter_text(text)              # 单源解析（review #38：坏 split 已弃用）
    if fm is None or "tools:" not in fm:
        return text
    _, body = split_frontmatter(text)

    tools_line = None
    new_lines = []
    for ln in fm.splitlines():
        if ln.strip().startswith("tools:"):
            tools_line = ln
            continue
        new_lines.append(ln)

    allowed = []
    if tools_line:
        val = tools_line.split(":", 1)[1].strip()
        allowed = [t.strip() for t in val.split(",") if t.strip()]

    perm = {}
    for key in _OPENCODE_DENY_KEYS:
        perm[key] = "deny"
    for tool in allowed:
        p = _OPENCODE_TOOL_TO_PERM.get(tool)
        if p:
            perm[p] = "allow"
    if not perm:
        perm = {"*": "deny"}

    perm_text = "permission:\n" + "".join(
        f"  {k}: {v}\n" for k, v in sorted(perm.items())
    )
    new_fm = "\n".join(new_lines).rstrip() + "\n" + perm_text
    return "---" + new_fm + "---" + body


# ---------------------------------------------------------------
# Codex agent 转换（Claude Code agent frontmatter → Codex 自定义 agent TOML）
# ---------------------------------------------------------------

_CODEX_TOOL_MAP = {
    "Read": "Read",
    "Write": "Write",
    "Edit": "Edit",
    "Glob": "Glob",
    "Grep": "Grep",
    "Agent": "spawn_agent",   # Claude Code Agent 工具 ↔ Codex spawn_agent
}

# 子 agent 注入段：Codex TOML 无工具白名单字段，只能靠指令文本声明硬约束。
# 放在 developer_instructions 最顶部，先于源文件正文与 SOP。
_CODEX_DISPATCH_BAN = """## 调度权限硬约束（最高优先级，先于本文件其余一切指令）

你是执行型子 agent，没有任何调度权。**禁止使用 `spawn_agent` 工具派生子 agent**
（包括派发与自己同名的 agent，禁止任何形式的递归派生）。你实际拥有完整工具集，
但这条禁令不因工具可用而失效。

同时禁止：
- 写 `.agent/task/` 下除本 order 以外的任何文件
- 写 `.agent/status.md` 的 `phase` / `current_step` / `last_volume_completed` 字段
  （这些字段只有 novel-agent 能写）
- 代替 novel-agent 推进流水线（写新 order、更新 phase）

你只做：
1. 读取 order 文件，执行其中指定的任务
2. 写 order 的 `outputs` 指向的文件
3. 完成后把 order 的 `status` 覆盖为 `DONE` 并结束

任务需要其他 agent 协作（如发现需要新增设定/归档/评审）时，不要自己调度——
在回复中明确告诉 novel-agent"下一步应调度谁、为什么"，由 novel-agent 调度。"""


def _toml_escape(s: str) -> str:
    """单行 TOML 基本字符串转义。"""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _toml_multiline(s: str) -> str:
    """多行 TOML 基本字符串转义（反斜杠 + 结束定界符冲突）。"""
    return s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')


def _agent_skill_paths(data: dict) -> list:
    """从 agent frontmatter 的 skills 列表提取 skills/*.md 相对路径。"""
    paths = []
    skills = data.get("skills") or []
    if not isinstance(skills, list):
        return paths
    for s in skills:
        if isinstance(s, dict):
            path = s.get("path")
        elif isinstance(s, str):
            path = s
        else:
            continue
        if isinstance(path, str) and path.startswith("skills/"):
            paths.append(Path(path))
    return paths


def convert_to_codex(text: str, skill_home: Path) -> str:
    """Claude Code agent frontmatter → Codex 自定义 agent TOML。

    - 必填字段：name / description / developer_instructions（Codex 官方约定）
    - tools：Codex agent TOML 无工具白名单字段，子 agent 注入「调度权限硬约束」
      （禁止 spawn_agent / 越权写文件），声明的工具范围仅作提示；
      Agent → spawn_agent（仅 novel-agent 持有，调度说明见适配段）
    - skills：frontmatter 声明的 SOP 内联进 developer_instructions（与 reasonix 一致）
    - 路径改写：.claude/knowledge、.claude/memory → .codex/ 对应目录
    """
    data, _body = split_frontmatter(text)    # 单源解析（review #38：坏 split 已弃用）
    if not data:
        return text

    name = str(data.get("name", "unknown")).strip()
    desc = str(data.get("description", "") or "").strip()

    tools_raw = str(data.get("tools", "") or "")
    allowed = []
    for t in tools_raw.split(","):
        t = t.strip()
        if not t:
            continue
        mapped = _CODEX_TOOL_MAP.get(t, t)
        if mapped not in allowed:
            allowed.append(mapped)

    body = _body.strip()
    if name == "novel-agent":
        body += (
            "\n\n## Codex 调度适配（本环境无 Agent 工具）\n"
            "在 Codex 环境调度子 agent 用 `spawn_agent` 工具：\n"
            "- 子 agent 名即 `.codex/agents/` 下的 TOML 名（writer / volume-planner / "
            "chapter-planner / prompt-crafter / anti-ai / reader / updater / style-distiller）\n"
            "- 把 order 文件内容作为任务消息传给子 agent；order 文件协议（status: DONE）不变\n"
            "- 一次只调度一个任务，等 DONE 后再调度下一个；禁止把 novel-agent 本身作为子 agent 调度\n"
            "- 你是本项目唯一调度者：spawn 后留意 agent 树，子 agent 若尝试再派生，立即 interrupt 并按规范重派\n"
        )
    else:
        body = _CODEX_DISPATCH_BAN + "\n\n" + body

    tool_line = ""
    if allowed:
        if name == "novel-agent":
            tool_line = (
                "\n\n（自动生成）本 agent 声明的工具范围："
                + "、".join(allowed)
                + "。你是唯一调度者，spawn_agent 只用于调度子 agent，禁止派生 novel-agent 自身。"
            )
        else:
            tool_line = (
                "\n\n（自动生成）本 agent 声明的工具范围："
                + "、".join(allowed)
                + "。Codex 自定义 agent TOML 无工具白名单字段，该声明不裁剪实际工具集；"
                "真正的约束见上文「调度权限硬约束」的禁止项。"
            )
    body += tool_line

    sop_sections = []
    for rel in _agent_skill_paths(data):
        sop = skill_home / rel
        if sop.exists():
            sop_sections.append(
                f"\n---\n\n## 执行 SOP：{sop.name}\n\n{sop.read_text(encoding='utf-8').strip()}"
            )
    instructions = body + "\n".join(sop_sections)
    instructions = rewrite_refs(instructions, PLATFORMS["codex"])

    lines = [
        f"# 由 awesome-novel 自动生成，源文件: agents/{name}.md",
        f'name = "{name}"',
        f'description = "{_toml_escape(desc)}"',
        "",
        'developer_instructions = """',
        _toml_multiline(instructions).rstrip(),
        '"""',
        "",
    ]
    return "\n".join(lines)


def deploy_codex_agents(project: Path, skill_home: Path, platform: Platform) -> None:
    """生成 <project>/<platform.root>/agents/<name>.toml（9 个），引用改写为平台路径。

    仅 codex 平台调用。Claude agent frontmatter → Codex TOML，与 sync 保持一致。
    """
    if platform.key != "codex":
        return
    agents_dir = skill_home / "agents"
    target = platform.agents_dir(project)
    if target is None:
        return
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in sorted(agents_dir.rglob("*.md")):
        if item.name == ".gitkeep":
            continue
        dest = target / (item.stem + ".toml")
        dest.write_text(
            convert_to_codex(item.read_text(encoding="utf-8"), skill_home),
            encoding="utf-8",
        )
        count += 1
    print(f"  ✅ 已部署 {count} 个 Codex agent 定义到 {target}")


def _convert_codex_inline_skill(text: str, name: str) -> str:
    """纯正文 SOP → Codex skill（SKILL.md，name/description frontmatter）。"""
    desc = ""
    for ln in text.split("\n"):
        if ln.strip().startswith("# ") and not ln.strip().startswith("## "):
            desc = ln.strip().lstrip("# ").strip()
            break
    desc_clean = desc.replace('"', "'")
    fm = (
        f"---\n"
        f"name: {name}\n"
        f"description: \"{desc_clean or name}（由 awesome-novel 自动生成的 Codex skill）\"\n"
        f"---\n"
    )
    return fm + "\n" + text.strip()


def deploy_codex_skills(project: Path, skill_home: Path, platform: Platform) -> None:
    """生成独立交互工具为 Codex skill（<project>/<platform.root>/skills/<name>/SKILL.md）。

    仅 codex 平台调用。9 个 agent 走 .codex/agents/*.toml（deploy_codex_agents），
    此处只部署不进调度链的独立工具（memory-recording、roleplay-sandbox）。
    """
    if platform.key != "codex":
        return
    skills_dir = skill_home / "skills"
    target = platform.skills_dir(project)
    if target is None:
        return
    target.mkdir(parents=True, exist_ok=True)
    for skill_name in ("memory-recording", "roleplay-sandbox"):
        sf = skills_dir / f"{skill_name}.md"
        if sf.exists():
            body = _convert_codex_inline_skill(sf.read_text(encoding="utf-8"), skill_name)
            body = rewrite_refs(body, platform)
            skill_dir = target / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    print(f"  ✅ 已部署 Codex 独立工具 skill 到 {target}")
