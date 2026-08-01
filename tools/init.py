#!/usr/bin/env python3
"""
awesome-novel-skill 项目初始化工具

用法: python init.py [project-path] [--genre <编号>]

从 skill 仓库复制 agent 定义、题材知识、记忆规则到用户项目目录，
创建完整的小说写作项目骨架。

不带参数时默认在当前目录初始化。
"""

import sys
import os
import re
import shutil
from pathlib import Path

# 强制 UTF-8 编码，避免 Windows 终端中文乱码
for s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


# 与 knowledge/genre-example/index.md 题材注册表保持一致（index 为权威来源）。
# 注：部分题材 ID 复用同一个 corpus 文件（如 urban-* → urban.md），无同名文件属正常。
GENRES = [
    "xianxia", "xuanhuan", "urban", "urban-romance", "urban-daily",
    "urban-farming", "urban-brained", "urban-cultivation", "urban-high-martial",
    "war-god", "western-fantasy", "ancient-politics", "historical",
    "historical-ancient", "historical-brained", "anti-japanese-war",
    "scifi-apocalypse", "suspense-crime", "suspense-paranormal", "suspense-brained",
    "game-sports", "anime-derivative", "derivative", "male-derivative",
]

def resolve_skill_home() -> Path:
    """解析技能仓库根目录。

    init.py 永远位于技能根 tools/ 下，__file__ 推导即正确来源：
      - 在仓库跑 tools/init.py  → 仓库
      - 在安装版跑 tools/init.py → 安装版
    不能用 NOVEL_SKILL_HOME 优先——install.sh 会把它持久化到 profile，
    指向陈旧/已删除的安装副本，遮蔽仓库真实来源（曾导致新项目部署旧提示词）。
    环境变量仅作异常兜底（__file__ 解析异常时）。
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


SKILL_HOME = resolve_skill_home()

SOURCE_AGENTS = SKILL_HOME / "agents"
SOURCE_KNOWLEDGE = SKILL_HOME / "knowledge"
SOURCE_TEMPLATES = SKILL_HOME / "templates"
SOURCE_MEMORY = SKILL_HOME / "memory"  # no-op since anti-ai/writer-style moved to knowledge/
SOURCE_ANTI_AI = SKILL_HOME / "knowledge" / "anti-ai"
SOURCE_GENRE_EXAMPLE = SKILL_HOME / "knowledge" / "genre-example"
SOURCE_FORMAT_SPECS = SKILL_HOME / "knowledge" / "format-specs"


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__.strip())
        return

    if len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
        project_path = Path(sys.argv[1]).resolve()
    else:
        project_path = Path.cwd()

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
    create_skeleton(project_path)

    # Step 3: 部署 agent 定义
    deploy_agents(project_path)

    # Step 4: 按题材继承记忆
    deploy_memory(project_path, genre)

    # Step 5: 按题材继承知识
    deploy_knowledge(project_path, genre)

    # Step 5.5: 按题材预填 settings 默认值（待设定阶段确认）
    seed_settings_from_genre(project_path, genre)

    # Step 6: 生成 MEMORY.md 索引
    write_memory_index(project_path)

    # Step 7: 初始化写作记忆文件
    init_memory_files(project_path)

    # Step 8: 初始化状态
    write_status(project_path)

    print(f"\n初始化完成!")
    print(f"项目路径: {project_path}")
    print(f"输入 @novel-agent 开始写作（Claude Code）")
    print(f"或在 OpenCode 中通过 @novel-agent 开始写作")


def select_genre() -> str:
    """交互式选题材"""
    print("\n可选题材:")
    for i, g in enumerate(GENRES, 1):
        print(f"  {i:2d}. {g}")

    while True:
        try:
            choice = input("\n选择题材编号: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(GENRES):
                return GENRES[idx]
        except ValueError:
            pass
        print("无效选择，请重试")


def create_skeleton(project_path: Path):
    """创建项目目录结构"""
    dirs = [
        "settings/character-setting",
        "volumes",
        "chapters",
        "prompts",
        "sandbox",
        "archives",
        ".agent/task",
        ".claude/memory",
        ".claude/knowledge",
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


# Claude Code tools 白名单 → OpenCode permission 映射
# OpenCode 语法见 https://github.com/anomalyco/opencode (agents.mdx 权限表)。
# OpenCode 默认所有权限为 ask（弹窗），此处明确 allow 需要的 + deny 不需要的。
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


def _convert_to_opencode(text: str) -> str:
    """把 Claude Code 语法 agent frontmatter 转成 OpenCode 语法。

    关键差异：
    - Claude Code 用 `tools: Read, Write, ...` 逗号串（白名单，缺省=继承全部）
    - OpenCode 用 `permission:` map（allow/ask/deny，默认 ask）
    仅处理 `tools:` 字段 → `permission:`；其余字段（name/description/role 等）原样保留
    （OpenCode 忽略未知字段，同 Claude Code 忽略 role/react 等自定义字段一致）。
    """
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) != 3:
        return text
    fm = parts[1]
    if "tools:" not in fm:
        return text
    try:
        import yaml
        data = yaml.safe_load(fm)
    except Exception:
        return text

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
    return "---" + new_fm + "---" + parts[2]


def deploy_agents(project_path: Path):
    """根据当前平台复制 agent 定义到对应目录"""
    if not SOURCE_AGENTS.exists():
        print("  ⚠️  agent 目录不存在，跳过")
        return

    # 根据 SKILL_HOME 路径判断平台：opencode 安装路径含 ".config/opencode"
    is_opencode = "opencode" in str(SKILL_HOME).lower()
    agent_dir = ".opencode/agents" if is_opencode else ".claude/agents"
    target = project_path / agent_dir
    target.mkdir(parents=True, exist_ok=True)
    for item in SOURCE_AGENTS.rglob("*"):
        if item.is_file() and item.suffix == ".md":
            rel_path = item.relative_to(SOURCE_AGENTS)
            dest = target / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = item.read_text(encoding="utf-8")
            if is_opencode:
                content = _convert_to_opencode(content)
            dest.write_text(content, encoding="utf-8")
    print(f"  ✅ 已部署 agent 定义到 {agent_dir}")


def deploy_memory(project_path: Path, genre: str):
    """初始化 memory 目录（占位，反 AI/文风已移至 knowledge）"""
    pass


def deploy_knowledge(project_path: Path, genre: str):
    """按题材拷贝参考材料 + 反 AI/文风规则到 .claude/knowledge/"""
    knowledge_dir = project_path / ".claude" / "knowledge"
    count = 0

    # 从 knowledge/format-specs/ 复制格式规范
    if SOURCE_FORMAT_SPECS.exists():
        for f in SOURCE_FORMAT_SPECS.glob("*.md"):
            shutil.copy2(f, knowledge_dir / f.name)
            count += 1

    # 题材案例
    genre_example_src = SOURCE_GENRE_EXAMPLE / f"{genre}.md"
    if genre_example_src.exists():
        shutil.copy2(genre_example_src, knowledge_dir / "genre-example.md")
        count += 1

    # 反 AI 规则：通用 + 题材 + 方法论 + 误杀防护（合并为单个 anti-ai.md）
    # 注：common-rules / anti-ai-writing / boundary-cases 是 anti-ai agent 的三个必需输入，
    #     统一合并进 .claude/knowledge/anti-ai.md，避免部署后多个失效路径。
    anti_ai_content = []
    anti_ai_content.append("# 反 AI 规则\n\n[community-defaults]\n")
    for fname in ("common-rules.md", "anti-ai-writing.md", "boundary-cases.md"):
        f = SOURCE_ANTI_AI / fname
        if f.exists():
            anti_ai_content.append(f"\n---\n\n{f.read_text(encoding='utf-8')}")

    genre_rules = SOURCE_ANTI_AI / f"{genre}.md"
    if genre_rules.exists():
        anti_ai_content.append(f"\n---\n\n[community-defaults] 题材: {genre}\n")
        anti_ai_content.append(genre_rules.read_text(encoding="utf-8"))

    if anti_ai_content:
        (knowledge_dir / "anti-ai.md").write_text(
            "\n".join(anti_ai_content), encoding="utf-8"
        )
        count += 1
        print(f"  ✅ 已继承反 AI 规则 (通用 + {genre})")

    # 文风偏好占位文件（保证文件存在；内容由 updater 归档 diff 时按作者修改追加）
    # 注：memory/ 已删除（迁移到 knowledge/），无社区默认文风，此处只落占位，
    #     writer-style.md 由 updater 首次归档时填充。
    style_placeholder = knowledge_dir / "writer-style.md"
    if not style_placeholder.exists():
        style_placeholder.write_text(
            f"# 文风偏好\n\n> 作家个人文风偏好。由 updater 在归档 diff 时追加，标注 [writer-preference]。\n\n"
            f"> [community-defaults] 题材: {genre}\n\n---\n\n",
            encoding="utf-8",
        )
        count += 1

    # 永久记忆占位文件（空，后续由 updater 晋升填充）
    permanent_memory = knowledge_dir / "permanent-memory.md"
    if not permanent_memory.exists():
        permanent_memory.write_text(
            "# 永久记忆\n\n> 从 .claude/memory/ 晋升的高频条目，"
            "内容格式与 memory 条目一致，由 updater 在兜底 sweep 时维护。\n\n"
            "---\n\n## 条目列表\n",
            encoding="utf-8",
        )
        count += 1

    # 创作方法论目录（plot-craft / scene-craft / character-craft / title-craft）
    craft_dirs = ["plot-craft", "scene-craft", "character-craft", "title-craft"]
    for dir_name in craft_dirs:
        src = SOURCE_KNOWLEDGE / dir_name
        if src.exists() and src.is_dir():
            dst = knowledge_dir / dir_name
            shutil.copytree(src, dst, dirs_exist_ok=True)
            file_count = sum(1 for _ in src.rglob("*") if _.is_file())
            count += file_count
            print(f"  ✅ 已部署 {dir_name}/ ({file_count} 个文件)")

    print(f"  ✅ 已继承 {count} 个知识文件")


def _md_section(text: str, title: str) -> str:
    """提取 markdown 某标题（任意 ## 或 ### 级别）到下一同级/更高级标题之间的正文。

    title 传纯标题名（不含 # 号），如 "叙事者角色" 或 "满足类型"。
    匹配规则：标题行 = 若干 # + 空格 + 标题名，可带尾随 #。
    """
    m = re.search(r"^(#{1,6})\s+%s\s*#*\s*$" % re.escape(title), text, re.M)
    if not m:
        return ""
    level = len(m.group(1))
    body = []
    for ln in text[m.end():].splitlines():
        h = re.match(r"^(#{1,6})\s+", ln.strip())
        if h and len(h.group(1)) <= level:
            break
        body.append(ln)
    return "\n".join(body).strip()


def _md_bullets(sec: str) -> list:
    """从 markdown 段落提取 `- xxx` 列表项内容。"""
    return [
        ln.strip().lstrip("- ").strip()
        for ln in sec.splitlines()
        if ln.strip().startswith("- ")
    ]


def seed_settings_from_genre(project_path: Path, genre: str):
    """按题材预填 settings/genre-setting.md + writing-style.md 的默认值。

    genre-example/{genre}.md 由 deploy_knowledge 已拷贝为 .claude/knowledge/genre-example.md。
    此处从其中提取叙事者角色/文风蓝图/类型禁忌/题材配置，替换 settings/ 下的占位符，
    避免 writer/prompt-crafter 在设定阶段未执行时把 `{placeholder}` 原样注入提示词。
    产出标注 [auto-seeded]，设定阶段由 updater 与作者确认调整。
    """
    ex = project_path / ".claude" / "knowledge" / "genre-example.md"
    if not ex.exists():
        return
    text = ex.read_text(encoding="utf-8")
    if "placeholder" in text.lower() or len(text.strip()) < 100:
        print(f"  ⚠️  genre-example/{genre}.md 为空模板，settings 保留占位符（请在设定阶段填写）")
        return

    # 题材显示名：优先标题行 "# 类型档案：X"，fallback 到 **label:**
    label = genre
    title_m = re.match(r"^#\s+类型档案[:：]\s*(.+)$", text, re.M)
    if title_m:
        label = title_m.group(1).strip()
    else:
        lm = re.search(r"\*\*label:\*\*\s*(\S+)", text)
        if lm:
            label = lm.group(1)

    sat = _md_bullets(_md_section(text, "满足类型"))
    rhythm = _md_section(text, "节奏规则") or "- 待设定"
    clich = _md_bullets(_md_section(text, "反套路"))
    taboo = _md_bullets(_md_section(text, "类型禁忌"))

    # genre-setting.md
    genre_out = [
        "# 题材设定",
        "",
        f"> [auto-seeded] init.py 从 genre-example/{genre}.md 生成，设定阶段请与作者确认调整。",
        "",
        f"## 选定类型",
        "",
        f"{genre} — {label}",
        "",
        "## 满足类型",
        "",
    ]
    genre_out += [f"- {s}" for s in sat] or ["- （待设定）"]
    genre_out += ["", "## 节奏规则", "", rhythm, "", "## 避免套路", ""]
    genre_out += [f"- {c}" for c in clich] or ["- （待设定）"]
    genre_out += ["", "## 类型禁忌", ""]
    genre_out += [f"- {t}" for t in taboo] or ["- （待设定）"]
    (project_path / "settings" / "genre-setting.md").write_text(
        "\n".join(genre_out) + "\n", encoding="utf-8"
    )

    # writing-style.md：叙事者角色 + 文风蓝图作为核心信条，禁忌作为易犯错误
    role = _md_section(text, "叙事者角色") or "（待设定）"
    blueprint = _md_section(text, "文风蓝图") or "（待设定）"
    style_out = [
        "# 写作风格",
        "",
        f"> [auto-seeded] init.py 从 genre-example/{genre}.md 生成，设定阶段请与作者逐项确认。",
        "",
        "## role（叙事身份）",
        "",
        role,
        "",
        "## core_principles（不可违背的写作信条）",
        "",
        blueprint,
        "",
        "## possible_mistakes（AI 易犯错误）",
        "",
    ]
    style_out += [f"- {t}" for t in taboo] or ["- （待设定）"]
    style_out += [
        "",
        "## depiction_techniques（描写层次和手法）",
        "",
        blueprint if blueprint and blueprint != "（待设定）" else "（设定阶段填写）",
        "",
    ]
    (project_path / "settings" / "writing-style.md").write_text(
        "\n".join(style_out) + "\n", encoding="utf-8"
    )
    print(f"  ✅ 已按题材预填 settings/genre-setting.md + writing-style.md 默认值（{genre}）")


def write_status(project_path: Path):
    """初始化 .agent/status.md"""
    status = """# 项目状态

- **skill_version:** 4.0
- **phase:** setup
- **current_step:** setting        # volume-planning / chapter-planning / prompt-crafting / writing / anti-ai / reviewing / archiving
- **current_volume:**
- **current_chapter:**
- **last_archived:**
- **next_task:** 填写基础设定（世界观/角色/写作风格）
"""
    (project_path / ".agent" / "status.md").write_text(status, encoding="utf-8")


def write_memory_index(project_path: Path):
    """生成 .claude/memory/MEMORY.md 占位索引"""
    memory_dir = project_path / ".claude" / "memory"
    (memory_dir / "MEMORY.md").write_text("# 写作记忆库\n\n（暂无记忆）\n", encoding="utf-8")


MEMORY_FILES = {
    "volume-memory.md": (
        "# 卷纲写作记忆\n\n> 记录卷纲规划环节中作者的反馈"
        "（冲突设计、节奏分布、章节结构等）。\n\n**相关 Agent:** volume-planner\n"
        "**相关 Skill:** volume-arc, volume-direction, volume-writing\n\n"
        "---\n\n## 条目列表\n"
    ),
    "chapter-memory.md": (
        "# 章纲写作记忆\n\n> 记录章纲规划环节中作者的反馈"
        "（场景设计、情绪节奏、伏笔安排等）。\n\n**相关 Agent:** chapter-planner\n"
        "**相关 Skill:** chapter-reference, chapter-outline, chapter-verify\n\n"
        "---\n\n## 条目列表\n"
    ),
    "prompt-memory.md": (
        "# 提示词写作记忆\n\n> 记录提示词组装环节中作者的反馈"
        "（层结构、注入规则、指令清晰度等）。\n\n**相关 Agent:** prompt-crafter\n"
        "**相关 Skill:** prompt-crafting\n\n"
        "---\n\n## 条目列表\n"
    ),
    "writing-memory.md": (
        "# 正文写作记忆\n\n> 记录正文写作和读者验收环节中作者的反馈"
        "（文风、爽点、节奏、描写等）。\n\n**相关 Agent:** writer, reader\n"
        "**相关 Skill:** writing-execution, reader-review\n\n"
        "---\n\n## 条目列表\n"
    ),
}


def init_memory_files(project_path: Path):
    """初始化 4 个写作记忆文件"""
    memory_dir = project_path / ".claude" / "memory"
    for filename, content in MEMORY_FILES.items():
        filepath = memory_dir / filename
        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
    print("  \u2705 \u5df2\u521d\u59cb\u5316 4 \u4e2a\u5199\u4f5c\u8bb0\u5fc6\u6587\u4ef6")





if __name__ == "__main__":
    main()
