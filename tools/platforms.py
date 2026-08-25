#!/usr/bin/env python3
"""平台适配层：不同 coding agent 对 agent/skill/knowledge/memory 的目录约定不同，
init.py / sync-project.py 共用本模块完成平台检测、目录派发、引用改写与 skill 生成。

支持平台（目录约定在 PLATFORMS 注册表声明，一行一条）：
  - claude   → .claude/   agents=agents, knowledge, memory
  - opencode → .opencode/ agents=agents, knowledge, memory
  - reasonix → .reasonix/ agents=None（agents 即 skills）, skills=skills, knowledge, memory
  - codex    → .codex/    agents=agents（TOML 转换产物）, skills=skills, knowledge, memory
  - zcode    → .zcode/    agents=None（agents 即 skills，ZCode 无项目级 agents 目录）,
                          skills=skills, knowledge, memory
  - dsh      → .dsh/      agents=None（agents 即 skills，DeepSeek Harness 无项目级
                          agents 目录，.dsh/skills 为其项目级 skill 根）, skills=skills,
                          knowledge, memory
  - grok     → .grok/     agents=agents（Markdown 转换产物，Grok Build 原生发现路径）,
                          skills=skills, knowledge, memory

扩展新平台（除 PLATFORMS 加一行外，按目录约定二选一）：
  - agents 即 skills 型：_DISPATCH_SECTIONS 加调度适配段 + _convert_standalone_skill
    的 description 后缀，deploy_inline_skills 自动覆盖
  - 独立 agents 目录型：仿 convert_to_opencode/convert_to_codex/convert_to_grok 写转换器，
    并在 init.main 与 sync-project.sync_agents/sync_skills 各接一行分发

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
    key: str                 # "claude" | "opencode" | "reasonix" | "grok"
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
    "grok":     Platform("grok", "Grok Build", ".grok", agents="agents",
                         skills="skills", knowledge="knowledge", memory="memory", detect_keywords=(".grok",)),
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
# inline-skill 平台生成（reasonix / zcode / dsh）
# agents + skills 源 → <平台根>/skills/<name>/SKILL.md（11 个）
# 三平台产物同构，差异集中在 _INLINE_PLATFORM_SPEC 差异表：
#   - frontmatter：zcode 带 allowed-tools（裸名）；reasonix 另带 runAs 且工具名
#     经 _REASONIX_TOOL_MAP 映射、规划类 agent 补 read_skill；dsh 只留 name/description
#   - novel-agent 调度适配段文本按平台注入
# ---------------------------------------------------------------

_REASONIX_TOOL_MAP = {
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "edit_file",
    "Glob": "glob",
    "Grep": "grep",
}

# 子 agent 名单单源：novel-agent 各平台调度适配段与 Codex 调度说明共用
# （新增执行 agent 只改这里 + EXEC_AGENT_SOPS，无需逐平台改文案）
SUBAGENT_NAMES = (
    "writer", "volume-planner", "chapter-planner", "prompt-crafter",
    "anti-ai", "reader", "updater", "style-distiller",
)

# agent → 专属 SOP 映射单源（三平台 deploy 与 Codex SOP 内联共用此契约）
EXEC_AGENT_SOPS = {
    "writer": ["writing-execution"],
    "volume-planner": ["volume-arc", "volume-direction", "volume-writing"],
    "chapter-planner": ["chapter-reference", "chapter-outline", "chapter-verify"],
    "prompt-crafter": ["prompt-crafting", "prompt-audit"],
    "anti-ai": ["anti-ai"],
    "reader": ["reader-review"],
    "updater": ["updater-archive", "updater-setting", "updater-rollback"],
    "style-distiller": ["style-distill"],
}

# reasonix 需加载共享 SOP 的 agent（frontmatter 补 read_skill 工具）
_READ_SKILL_AGENTS = ("volume-planner", "chapter-planner", "prompt-crafter", "updater")

# 不进调度链的独立交互工具（各平台均按 inline skill 部署）
STANDALONE_SKILLS = ("memory-recording", "roleplay-sandbox")

# 各平台 novel-agent 调度适配段（{names} 注入 SUBAGENT_NAMES）
_DISPATCH_SECTIONS = {
    "reasonix": (
        "\n\n## Reasonix 调度适配（本环境无 Agent 工具）\n"
        "在 Reasonix 环境调度子 agent 用 `run_skill` 工具：\n"
        "- `run_skill(name=\"<子agent名>\", arguments=\"{order 内容}\")` 调单个子 agent\n"
        "- 子 agent 名即 .reasonix/skills/ 下的 skill 名（{names}）\n"
        "- 子 agent 是 subagent 类型，run_skill 的 arguments 会作为它唯一的 task 输入\n"
        "- 并发调度只读子 agent 可用 `parallel_tasks`；order 文件协议（status: DONE）不变\n"
    ),
    "zcode": (
        "\n\n## ZCode 调度适配（本环境子 agent 即 skill）\n"
        "在 ZCode 环境调度子 agent 用 `Agent` 工具：\n"
        "- 子 agent 名即 `.zcode/skills/` 下的 skill 名（{names}）\n"
        "- 用 Agent 工具按子 agent 名 spawn，把 order 文件内容作为它的任务输入\n"
        "- 子 agent 是隔离上下文，只读 order 与指定文件；order 文件协议（status: DONE）不变\n"
        "- 一次只调度一个任务，等 DONE 后再调度下一个；禁止把 novel-agent 本身作为子 agent 调度\n"
    ),
    "dsh": (
        "\n\n## DeepSeek Harness 调度适配（本环境子 agent 即 skill）\n"
        "在 dsh 环境调度子 agent 用 `subagent` 工具：\n"
        "- 子 agent 名即 `.dsh/skills/` 下的 skill 名（{names}）\n"
        "- 子 agent 是隔离上下文，prompt 里要求它先调用 `skill(name=\"<子agent名>\")` "
        "加载自身指令，再执行 order 文件任务\n"
        "- 把 order 文件路径与任务要求写进 prompt；order 文件协议（status: DONE）不变\n"
        "- 一次只调度一个任务，等 DONE 后再调度下一个；禁止把 novel-agent 本身作为子 agent 调度\n"
    ),
}


def _allowed_tools(data: dict, name: str, platform_key: str) -> list | None:
    """agent frontmatter tools → 平台 allowed-tools 名单。dsh 无此字段返回 None。

    Agent（调度工具）统一丢弃——子 agent 无调度权；reasonix 经 _REASONIX_TOOL_MAP
    映射为平台工具名并给规划类 agent 补 read_skill（加载共享 SOP 用）。
    """
    if platform_key == "dsh":
        return None
    tools_raw = str(data.get("tools", "") or "")
    tool_map = _REASONIX_TOOL_MAP if platform_key == "reasonix" else {}
    allowed = []
    for t in tools_raw.split(","):
        t = t.strip()
        if not t or t == "Agent":
            continue
        mapped = tool_map.get(t, t)
        if mapped not in allowed:
            allowed.append(mapped)
    if platform_key == "reasonix" and name in _READ_SKILL_AGENTS \
            and "read_skill" not in allowed:
        allowed.append("read_skill")
    return allowed


def _convert_agent_to_skill(text: str, platform_key: str, inline_sops=None) -> str:
    """Claude Code agent frontmatter → inline-skill 平台（reasonix/zcode/dsh）skill。

    - frontmatter: 保留 name/description；role/react/memory/knowledge 丢弃；
      工具字段差异见 _allowed_tools（reasonix 另带 runAs：novel-agent=inline，其余 subagent）
    - body: agent 身份段 + novel-agent 调度适配段 + 内联的专属 SOP 全文
    """
    data, body = split_frontmatter(text)    # 单源解析（review #38：坏 split 已弃用）
    if not data:
        return text

    name = str(data.get("name", "unknown")).strip()
    desc = str(data.get("description", "") or "").strip().replace('"', "'")
    allowed = _allowed_tools(data, name, platform_key)

    fm_lines = [
        "---",
        f"name: {name}",
        f'description: "{desc}"',
    ]
    if platform_key == "reasonix":
        fm_lines.append(f"runAs: {'inline' if name == 'novel-agent' else 'subagent'}")
    if allowed is not None:
        joined = ", ".join(allowed)
        fm_lines.append(f"allowed-tools: [{joined}]" if platform_key == "reasonix"
                        else f"allowed-tools: {joined}")
    fm = "\n".join(fm_lines) + "\n---\n"

    agent_body = body.strip()
    if name == "novel-agent":
        # {names} 是唯一占位符；调度段文本含字面 `{order 内容}`，用 safe 替换防 str.format 报 KeyError
        agent_body += _DISPATCH_SECTIONS[platform_key].replace(
            "{names}", " / ".join(SUBAGENT_NAMES))
    sop_sections = []
    for sop in (inline_sops or []):
        if sop and sop.exists():
            sop_sections.append(
                f"\n---\n\n## 执行 SOP：{sop.name}\n\n{sop.read_text(encoding='utf-8').strip()}"
            )
    return fm + "\n" + agent_body + "\n".join(sop_sections)


def _convert_standalone_skill(text: str, name: str, platform_key: str) -> str:
    """纯正文 SOP → 平台 inline skill（不进调度链的独立交互工具）。"""
    desc = ""
    for ln in text.split("\n"):
        if ln.strip().startswith("# ") and not ln.strip().startswith("## "):
            desc = ln.strip().lstrip("# ").strip()
            break
    suffix = {
        "reasonix": "（由 awesome-novel 自动生成的 inline skill）",
        "zcode": "（由 awesome-novel 自动生成的 ZCode skill）",
        "dsh": "（由 awesome-novel 自动生成的 dsh skill）",
    }[platform_key]
    fm = (
        f"---\n"
        f"name: {name}\n"
        f"description: \"{desc or name}{suffix}\"\n"
    )
    if platform_key == "reasonix":
        fm += "runAs: inline\n"
    fm += "---\n"
    return fm + "\n" + text.strip()


def deploy_inline_skills(project: Path, skill_home: Path, platform: Platform) -> bool:
    """生成 <project>/<platform.root>/skills/<name>/SKILL.md（11 个），引用改写为平台路径。

    仅 reasonix/zcode/dsh 调用（agents=None，agents 即 skills）；其余平台返回 False。
    产物 = 9 个 agent（EXEC_AGENT_SOPS 8 执行 + novel-agent 内联 novel-dispatch）
    + STANDALONE_SKILLS 独立工具，frontmatter/调度适配段差异见差异表注释。
    """
    if platform.key not in _DISPATCH_SECTIONS:
        return False
    agents_dir = skill_home / "agents"
    skills_dir = skill_home / "skills"
    target = platform.skills_dir(project)
    if target is None:
        return False
    target.mkdir(parents=True, exist_ok=True)

    for agent_name, sops in EXEC_AGENT_SOPS.items():
        agent_file = agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            continue
        sop_files = [skills_dir / f"{s}.md" for s in sops]
        body = _convert_agent_to_skill(agent_file.read_text(encoding="utf-8"),
                                       platform.key, inline_sops=sop_files)
        body = rewrite_refs(body, platform)
        skill_dir = target / agent_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    novel_file = agents_dir / "novel-agent.md"
    if novel_file.exists():
        body = _convert_agent_to_skill(novel_file.read_text(encoding="utf-8"),
                                       platform.key,
                                       inline_sops=[skills_dir / "novel-dispatch.md"])
        body = rewrite_refs(body, platform)
        skill_dir = target / "novel-agent"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    for skill_name in STANDALONE_SKILLS:
        sf = skills_dir / f"{skill_name}.md"
        if sf.exists():
            body = _convert_standalone_skill(sf.read_text(encoding="utf-8"), skill_name,
                                             platform.key)
            body = rewrite_refs(body, platform)
            skill_dir = target / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return True


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


def convert_agent_to_platform(text: str, platform: Platform,
                              skill_home: Path | None = None) -> str:
    """agent 源内容 → 平台部署内容（init.deploy_agents / sync.sync_agents / find_changes 共用单份逻辑）。

    - opencode: frontmatter → permission 格式 + 引用改写
    - codex: → TOML（SOP 内联需 skill_home；convert_to_codex 内部已含引用改写）
    - grok: → Grok Build agent Markdown（SOP 内联需 skill_home；convert_to_grok 内部已含引用改写）
    - 其余平台（claude）: 原样（纯复制）
    """
    if platform.key == "opencode":
        return rewrite_refs(convert_to_opencode(text), platform)
    if platform.key == "codex":
        if skill_home is None:
            raise ValueError("codex 平台 agent 转换需要 skill_home（SOP 内联）")
        return convert_to_codex(text, skill_home)
    if platform.key == "grok":
        if skill_home is None:
            raise ValueError("grok 平台 agent 转换需要 skill_home（SOP 内联）")
        return convert_to_grok(text, skill_home)
    return text


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
            f"- 子 agent 名即 `.codex/agents/` 下的 TOML 名（{' / '.join(SUBAGENT_NAMES)}）\n"
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


# ---------------------------------------------------------------
# Grok Build agent 转换（Claude Code agent frontmatter → Grok .grok/agents/*.md）
# Grok 发现路径：项目 .grok/agents/*.md；调度工具：spawn_subagent（深度上限 1）
# ---------------------------------------------------------------

_GROK_TOOL_MAP = {
    "Read": "read_file",
    "Write": "write",
    "Edit": "search_replace",
    "Glob": "list_dir",
    "Grep": "grep",
    "Agent": "Agent",            # frontmatter 指令；模型调用名仍是 spawn_subagent
    "Bash": "run_terminal_command",
}

_GROK_DISPATCH_BAN = """## 调度权限硬约束（最高优先级，先于本文件其余一切指令）

你是执行型子 agent，没有任何调度权。**禁止使用 `spawn_subagent` 工具派生子 agent**
（包括派发与自己同名的 agent，禁止任何形式的递归派生）。Grok Build 的子代理深度上限为 1，
即便调用也会失败；这条禁令不因工具可见而失效。

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
在回复中明确告诉 novel-agent"下一步应调度谁、为什么"，由 novel-agent 调度。

工具对应：创建/覆盖文件用 `write`，局部修改用 `search_replace`，列目录用 `list_dir`，搜索用 `grep`。"""


def _yaml_quote(s: str) -> str:
    """YAML 双引号标量转义。"""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def convert_to_grok(text: str, skill_home: Path) -> str:
    """Claude Code agent frontmatter → Grok Build 项目级 agent Markdown。

    - 必填字段：name / description（Grok 官方约定）
    - tools：YAML 列表，Agent 保留为 Grok 的子代理授权指令
    - disallowedTools：子 agent 用 Agent 禁止子代理工具族
    - skills：Claude 的 path 对象列表与 Grok 的 skill 名列表不兼容，SOP 内联进正文后丢弃
    - 其余 Claude 私有字段（role/react/memory/knowledge）丢弃，避免 Grok 解析失败
    - novel-agent 注入 spawn_subagent 调度适配段；子 agent 注入调度硬约束
    - 路径改写：.claude/knowledge、.claude/memory → .grok/ 对应目录
    """
    data, _body = split_frontmatter(text)
    if not data:
        return rewrite_refs(text, PLATFORMS["grok"])

    name = str(data.get("name", "unknown")).strip()
    desc = str(data.get("description", "") or "").strip()

    tools_raw = str(data.get("tools", "") or "")
    allowed = []
    for t in tools_raw.split(","):
        t = t.strip()
        if not t:
            continue
        mapped = _GROK_TOOL_MAP.get(t, t)
        if name != "novel-agent" and mapped == "Agent":
            continue
        if mapped not in allowed:
            allowed.append(mapped)

    body = _body.strip()
    if name == "novel-agent":
        body += (
            "\n\n## Grok Build 调度适配（本环境无 Agent 工具）\n"
            "在 Grok Build 环境调度子 agent 用 `spawn_subagent` 工具：\n"
            f"- 子 agent 名即 `.grok/agents/` 下的 Markdown 名（{' / '.join(SUBAGENT_NAMES)}）\n"
            "- 调用 `spawn_subagent(subagent_type=\"<子agent名>\", prompt=<order 路径与任务要求>, "
            "isolation=\"none\")`\n"
            "- isolation 必须是 none（共享工作区，子 agent 写回同一项目）；禁止 worktree\n"
            "- 把 order 文件路径与任务要求写进 prompt；order 文件协议（status: DONE）不变\n"
            "- 一次只调度一个任务，等 DONE 后再调度下一个；禁止把 novel-agent 本身作为子 agent 调度\n"
            "- 你必须在**主会话**中运行：Grok 子代理不能再派子代理（深度上限 1），"
            "novel-agent 若被 spawn 为子代理，调度链会断裂\n"
            "- 工具对应：读文件 `read_file`，写/覆盖 `write`，搜索 `grep`，列目录 `list_dir`\n"
        )
    else:
        body = _GROK_DISPATCH_BAN + "\n\n" + body

    if allowed:
        if name == "novel-agent":
            body += (
                "\n\n（自动生成）本 agent 声明的工具范围："
                + "、".join(allowed)
                + "。你是唯一调度者，spawn_subagent 只用于调度子 agent，禁止派生 novel-agent 自身。"
            )
        else:
            body += (
                "\n\n（自动生成）本 agent 声明的工具范围："
                + "、".join(allowed)
                + "。子 agent 禁止 spawn_subagent。"
            )

    sop_sections = []
    for rel in _agent_skill_paths(data):
        sop = skill_home / rel
        if sop.exists():
            sop_sections.append(
                f"\n---\n\n## 执行 SOP：{sop.name}\n\n{sop.read_text(encoding='utf-8').strip()}"
            )
    instructions = body + "\n".join(sop_sections)
    instructions = rewrite_refs(instructions, PLATFORMS["grok"])

    fm_lines = [
        "---",
        f"name: {name}",
        f"description: {_yaml_quote(desc)}",
    ]
    if allowed:
        fm_lines.append("tools:")
        for t in allowed:
            fm_lines.append(f"  - {t}")
    if name != "novel-agent":
        fm_lines.append("disallowedTools:")
        fm_lines.append("  - Agent")
        fm_lines.append("agentsMd: false")
    else:
        fm_lines.append("agentsMd: true")
    fm_lines.append("---")
    return "\n".join(fm_lines) + "\n\n" + instructions + "\n"


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
    """生成独立交互工具为 skill（<project>/<platform.root>/skills/<name>/SKILL.md）。

    codex / grok 调用。9 个 agent 走独立 agents 目录，此处只部署不进调度链的
    独立工具（memory-recording、roleplay-sandbox）。
    """
    if platform.key not in ("codex", "grok"):
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
            if platform.key == "grok":
                body = body.replace("Codex skill", "Grok Build skill")
            body = rewrite_refs(body, platform)
            skill_dir = target / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    print(f"  ✅ 已部署 {platform.label} 独立工具 skill 到 {target}")
