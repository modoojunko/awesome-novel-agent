#!/usr/bin/env python3
"""
awesome-novel-skill 项目初始化工具

用法: python init.py [project-path] [--genre <编号>] [--platform <claude|opencode|reasonix|codex>]

平台缺省：--platform > NOVEL_PLATFORM > SKILL_HOME 路径识别 > claude。

从 skill 仓库复制 agent 定义、题材知识、记忆规则到用户项目目录，
创建完整的小说写作项目骨架。

不带参数时默认在当前目录初始化。
"""

import sys
import os
import re
import shutil
from pathlib import Path

from platforms import (
    Platform,
    convert_to_opencode,
    detect_platform,
    deploy_codex_agents,
    deploy_codex_skills,
    deploy_reasonix_skills,
    ensure_yaml,
    rewrite_refs,
    resolve_skill_home,
)

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

# 题材中文名（展示给作者用，与 GENRES 一一对应；知识库 genre-example 文件同源）
GENRE_LABELS = {
    "xianxia": "东方仙侠",
    "xuanhuan": "传统玄幻",
    "urban": "都市大类",
    "urban-romance": "都市言情",
    "urban-daily": "都市日常",
    "urban-farming": "都市种田",
    "urban-brained": "都市脑洞",
    "urban-cultivation": "都市修真",
    "urban-high-martial": "都市高武",
    "war-god": "战神赘婿",
    "western-fantasy": "西方奇幻",
    "ancient-politics": "古风权谋",
    "historical": "历史大类",
    "historical-ancient": "历史古代",
    "historical-brained": "历史脑洞",
    "anti-japanese-war": "抗战谍战",
    "scifi-apocalypse": "科幻末世",
    "suspense-crime": "悬疑刑侦",
    "suspense-paranormal": "悬疑灵异",
    "suspense-brained": "悬疑脑洞",
    "game-sports": "游戏体育",
    "anime-derivative": "动漫衍生",
    "derivative": "衍生类",
    "male-derivative": "男频衍生",
}

SKILL_HOME = resolve_skill_home()

SOURCE_AGENTS = SKILL_HOME / "agents"
SOURCE_KNOWLEDGE = SKILL_HOME / "knowledge"
SOURCE_TEMPLATES = SKILL_HOME / "templates"
SOURCE_ANTI_AI = SKILL_HOME / "knowledge" / "anti-ai"
SOURCE_GENRE_EXAMPLE = SKILL_HOME / "knowledge" / "genre-example"
SOURCE_FORMAT_SPECS = SKILL_HOME / "knowledge" / "format-specs"


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print(__doc__.strip())
        return

    project_arg = None
    platform_override = None
    genre_num = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--platform":
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                print("错误: --platform 需要一个平台名（claude|opencode|reasonix|codex）")
                sys.exit(1)
            platform_override = args[i + 1]
            i += 2
            continue
        if a == "--genre":
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                genre_num = args[i + 1]
                i += 2
                continue
            print("错误: --genre 需要一个题材编号")
            sys.exit(1)
        if not a.startswith("--") and project_arg is None:
            project_arg = a
        i += 1

    project_path = Path(project_arg).resolve() if project_arg else Path.cwd()
    platform_override = platform_override or os.environ.get("NOVEL_PLATFORM")
    try:
        platform = detect_platform(SKILL_HOME, platform_override)
    except ValueError as e:
        print(e)
        sys.exit(1)
    ensure_yaml(platform)
    print(f"平台: {platform.label}")

    # 解析可选参数
    genre = None
    if genre_num is not None:
        try:
            genre = GENRES[int(genre_num) - 1]
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
        print(f"题材: {GENRE_LABELS.get(genre, genre)}（{genre}）")

    # Step 1.5: 旧 4 字段 writing-style.md → 新格式（必须先于模板拷贝/题材预填，否则旧卡被覆盖）
    migrate_writing_style(project_path)

    # Step 2: 创建骨架
    create_skeleton(project_path, platform)

    # Step 3: 部署 agent 定义（codex 为 TOML 转换产物，reasonix agents 即 skills）
    if platform.key == "codex":
        deploy_codex_agents(project_path, SKILL_HOME, platform)
    else:
        deploy_agents(project_path, platform)

    # Step 3.5: 部署平台 skills（reasonix 生成 11 个 SKILL.md；codex 只部署独立工具）
    if platform.key == "reasonix":
        deploy_reasonix_skills(project_path, SKILL_HOME, platform)
    elif platform.key == "codex":
        deploy_codex_skills(project_path, SKILL_HOME, platform)

    # Step 3.6: 部署风格工具脚本到项目 tools/（style-distiller / anti-ai 用）
    deploy_tools(project_path)

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
    elif platform.key == "codex":
        print("在 Codex 中打开项目目录，调用 @novel-agent 开始写作")
    else:
        print("在 Reasonix 中运行 `reasonix code`，然后调用 @novel-agent 开始写作")


def select_genre() -> str:
    """交互式选题材"""
    print("\n可选题材:")
    for i, g in enumerate(GENRES, 1):
        print(f"  {i:2d}. {GENRE_LABELS[g]}（{g}）")

    while True:
        try:
            choice = input("\n选择题材编号: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(GENRES):
                return GENRES[idx]
        except ValueError:
            pass
        print("无效选择，请重试")


def _rewrite_template_refs(text: str, platform: Platform) -> str:
    """项目模板里的 Claude Code/OpenCode 路径引用 → 平台路径。claude 原样返回。"""
    if platform.key == "claude":
        return text
    if platform.key == "reasonix":
        text = text.replace(".claude/agents/", ".reasonix/skills/")
        text = text.replace(".opencode/agents/", ".reasonix/skills/")
    elif platform.key == "codex":
        text = text.replace(".claude/agents/", ".codex/agents/")
        text = text.replace(".opencode/agents/", ".codex/agents/")
    else:  # opencode
        text = text.replace(".claude/agents/", f"{platform.root}/agents/")
    return rewrite_refs(text, platform)


# 根级脚手架（平台 agent 配置/模板生成物）随模板刷新；settings/ 等用户内容保留不覆盖
_GENERATED_SCAFFOLD = {"CLAUDE.md", "AGENTS.md", "AGENTS.codex.md"}


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
        "tools",
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
                if target.exists() and item.name not in _GENERATED_SCAFFOLD:
                    continue          # 已存在不覆盖（settings/ 等用户内容），脚手架文件随模板刷新
                target.parent.mkdir(parents=True, exist_ok=True)
                if platform.key == "codex" and item.name == "CLAUDE.md":
                    # Codex 项目不生成 CLAUDE.md（Codex 只读 AGENTS.md）
                    continue
                if item.name == "AGENTS.codex.md":
                    # 模板源仅用于生成 codex 项目的 AGENTS.md，不复制进项目
                    continue
                if platform.key == "codex" and item.name == "AGENTS.md":
                    codex_tpl = SOURCE_TEMPLATES / "AGENTS.codex.md"
                    if codex_tpl.exists():
                        content = codex_tpl.read_text(encoding="utf-8")
                        content = _rewrite_template_refs(content, platform)
                        with open(target, "w", encoding="utf-8", newline="") as f:
                            f.write(content)
                        continue
                if item.name in ("CLAUDE.md", "AGENTS.md") and platform.key != "claude":
                    with open(item, encoding="utf-8", newline="") as f:
                        content = f.read()
                    content = _rewrite_template_refs(content, platform)
                    with open(target, "w", encoding="utf-8", newline="") as f:
                        f.write(content)
                else:
                    shutil.copy2(item, target)
        print("  ✅ 已拷贝项目模板")


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
                content = convert_to_opencode(content)
                content = rewrite_refs(content, platform)
            dest.write_text(content, encoding="utf-8")
    print(f"  ✅ 已部署 agent 定义到 {agent_dir}")


_DEPLOY_TOOLS = ["distill-style.py", "compare-style.py", "mix-style.py"]  # 现有文件才拷，缺省跳过


def deploy_tools(project_path: Path) -> None:
    """拷贝风格工具脚本到项目 tools/（style-distiller / anti-ai 用 Bash 调）。"""
    src = SKILL_HOME / "tools"
    dst = project_path / "tools"
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for name in _DEPLOY_TOOLS:
        f = src / name
        if f.exists():
            (dst / name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
            n += 1
    if n:
        print(f"  ✅ 已部署风格工具脚本到 tools/（{n} 个）")


def deploy_memory(project_path: Path, genre: str):
    """初始化 memory 目录（占位，反 AI/文风已移至 knowledge）"""
    pass


def deploy_knowledge(project_path: Path, genre: str, platform: Platform):
    """按题材拷贝参考材料 + 反 AI/文风规则到 <平台>/knowledge/"""
    knowledge_dir = platform.knowledge_dir(project_path)
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
        content = rewrite_refs(
            "# 永久记忆\n\n> 从 .claude/memory/ 晋升的高频条目，"
            "内容格式与 memory 条目一致，由 updater 在兜底 sweep 时维护。\n\n"
            "---\n\n## 条目列表\n",
            platform,
        )
        permanent_memory.write_text(content, encoding="utf-8")
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

    # style-distill 提示词模板（蒸馏段 2 / Gate G 清单 / 注入模板）
    style_distill_src = SKILL_HOME / "knowledge" / "style-distill"
    if style_distill_src.exists():
        dst = knowledge_dir / "style-distill"
        shutil.copytree(style_distill_src, dst, dirs_exist_ok=True)
        count += sum(1 for _ in style_distill_src.rglob("*") if _.is_file())
        print("  ✅ 已部署 style-distill/ 提示词模板")

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


def _write_new_style_card(path: Path, role: str, principles: list, mistakes: list,
                          depiction: str, seeded: bool = True) -> None:
    """写新格式写作风格卡（frontmatter 量化层 + 正文定性层）。
    confidence=0 → 提示词只走定性层，直到首次蒸馏。"""
    prefix = "> [auto-seeded] 由 init.py 按题材预填，量化层留空，首次蒸馏后由 style-distiller 填充。\n\n" if seeded else ""
    principles_txt = "\n".join(f"- {p}" for p in principles) if principles else ("" if not seeded else "- {principle_1}")
    mistakes_txt = "\n".join(f"- {m}" for m in mistakes) if mistakes else ("" if not seeded else "- {mistake_1}")
    content = f"""---
profile_version: "1.0"
scene_type: general
source_sample_length: 0
confidence: 0
last_updated: ""
locked: []

lexicon: {{ adj_density_per_100: 0, adv_density_per_100: 0, four_phrase_freq_per_100: 0, preferred_words: [], banned_words: [], name_pronoun_ratio: 0 }}
syntax: {{ avg_sentence_length: 0, sentence_length_dist: {{}}, single_sentence_paragraph_pct: 0, avg_sentences_per_paragraph: 0, question_ratio: 0, exclamation_ratio: 0 }}
rhythm: {{ dialogue_pct: 0, action_pct: 0, environment_pct: 0, inner_thought_pct: 0, narration_pct: 0 }}
rhetoric: {{ metaphor_density_per_100: 0, metaphor_preference: "", sensory_dist: "" }}
emotion_expression: {{ direct_pct: 0, action_physiology_pct: 0, environment_projection_pct: 0 }}
narrative: {{ perspective: "", focal_character: "", inner_monologue_style: "" }}
dialogue_style: {{ tag_style: "", avg_dialogue_length: 0, interrupt_freq_per_100: 0, subtext_ratio: 0, direct_address_freq_per_100: 0 }}
cohesion: {{ conjunction_freq_per_100: 0, transition_sentence_ratio: 0, paragraph_bridge_style: "" }}
verb_style: {{ action_verb_ratio: 0, mental_verb_ratio: 0, state_verb_ratio: 0, strength: "" }}
---

# 写作风格

{prefix}## 叙事身份（原 role）

{role}

## 硬约束（原 core_principles）

{principles_txt}

## AI 易犯错误（原 possible_mistakes）

{mistakes_txt}

## 描写层次和手法（原 depiction_techniques）

{depiction}

## few-shot 例句

- （蒸馏后由 style-distiller 填入标志性例句）
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seed_settings_from_genre(project_path: Path, genre: str, platform: Platform):
    """按题材预填 settings/genre-setting.md + writing-style.md 的默认值。

    genre-example/{genre}.md 由 deploy_knowledge 已拷贝为 <平台>/knowledge/genre-example.md。
    此处从其中提取叙事者角色/文风蓝图/类型禁忌/题材配置，替换 settings/ 下的占位符，
    避免 writer/prompt-crafter 在设定阶段未执行时把 `{placeholder}` 原样注入提示词。
    产出标注 [auto-seeded]，设定阶段由 updater 与作者确认调整。
    """
    ex = platform.knowledge_dir(project_path) / "genre-example.md"
    if not ex.exists():
        return
    text = ex.read_text(encoding="utf-8")
    if "placeholder" in text.lower() or len(text.strip()) < 100:
        print(f"  ⚠️  genre-example/{genre}.md 为空模板，settings 保留占位符（请在设定阶段填写）")
        return

    # 题材显示名：优先标题行 "# 类型档案：X"，fallback 到 **label:**，再 fallback 中文注册名
    label = GENRE_LABELS.get(genre, genre)
    title_m = re.match(r"^#\s+类型档案[:：]\s*(.+)$", text, re.M)
    if title_m:
        title = title_m.group(1).strip()
        if title != "unknown":
            label = title
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

    # writing-style.md → 新格式（frontmatter 量化层 + 正文定性层）
    # 守卫：卡已存在且正文无未填充 {...} 占位符 → 已有实质内容（迁移产物/作者编辑），不覆盖。
    # 注：frontmatter 量化层恒含 `{ ... }` 内联字典，不能以 `"{" in text` 判未填；
    #     须按正文占位符 token（{role}/{principle_1}/{mistake_1}/{depiction_techniques}）判断。
    role = _md_section(text, "叙事者角色") or "（待设定）"
    blueprint = _md_section(text, "文风蓝图") or "（待设定）"
    style_card = project_path / "settings" / "writing-style.md"
    _STYLE_CARD_PLACEHOLDERS = ("{role}", "{principle_1}", "{mistake_1}", "{depiction_techniques}", "（待设定）")
    filled = style_card.exists() and not any(
        tok in style_card.read_text(encoding="utf-8") for tok in _STYLE_CARD_PLACEHOLDERS
    )
    if filled:
        print("  ✅ writing-style.md 已有实质内容，跳过题材预填（保留迁移/编辑结果）")
    else:
        _write_new_style_card(
            style_card,
            role=role or "{role}",
            principles=[blueprint] if blueprint else [],
            mistakes=taboo,
            depiction=blueprint or "{depiction_techniques}",
        )
    print(f"  ✅ 已按题材预填 settings/genre-setting.md + writing-style.md 默认值（{genre}）")


def migrate_writing_style(project_path: Path) -> None:
    """旧 4 字段 writing-style.md → 新格式（仅当旧格式：无 frontmatter）。
    旧版备份到 settings/.style-versions/v0_migrated.md。"""
    card = project_path / "settings" / "writing-style.md"
    if not card.exists():
        return
    text = card.read_text(encoding="utf-8")
    if text.lstrip().startswith("---"):          # 已是新格式
        return
    # 旧标题带中文后缀（如 "## role（叙事身份）"），按完整标题提取
    # 段落回退：旧 seed 把 core_principles/possible_mistakes 写成裸段落（非 bullet），
    # _md_bullets 抽不到 bullet 会返回 []，抽不到时保留整段原文（零损失）。
    # 缺节（_md_section 返回空）回退空串而非 {role}/{depiction_techniques} 占位符——
    # 占位符会被 seed 守卫误判为未填而在同一 run 内覆盖迁移产物。
    role = _md_section(text, "role（叙事身份）") or ""
    _core = _md_section(text, "core_principles（不可违背的写作信条）")
    _mist = _md_section(text, "possible_mistakes（AI 易犯错误）")
    principles = _md_bullets(_core) or ([_core.strip()] if _core.strip() else [])
    mistakes = _md_bullets(_mist) or ([_mist.strip()] if _mist.strip() else [])
    depiction = _md_section(text, "depiction_techniques（描写层次和手法）") or ""
    vers = project_path / "settings" / ".style-versions"
    vers.mkdir(parents=True, exist_ok=True)
    (vers / "v0_migrated.md").write_text(text, encoding="utf-8")
    _write_new_style_card(card, role, principles, mistakes, depiction, seeded=False)
    print("  ✅ 旧 4 字段 writing-style.md 已迁移到新格式（confidence=0，旧版已备份）")


def write_status(project_path: Path):
    """初始化 .agent/status.md"""
    status = """# 项目状态

- **skill_version:** 4.13.0
- **phase:** setup
- **current_step:** setting        # volume-planning / chapter-planning / prompt-crafting / writing / anti-ai / reviewing / archiving
# phase 取值：setup / outline / draft / anti-ai / review / archive / finished
# last_volume_completed 与 phase: finished 由 novel-agent 写（卷完成判定），updater 不写完成位
- **current_volume:**
- **current_chapter:**
- **last_archived:**
- **last_quality_gap:**        # 最近一次字数降级记录（由 novel-agent 从 writing-order 同步）
- **next_task:** 填写基础设定（世界观/角色/写作风格）
"""
    (project_path / ".agent" / "status.md").write_text(status, encoding="utf-8")


def write_memory_index(project_path: Path, platform: Platform):
    """生成 <平台>/memory/MEMORY.md 占位索引"""
    memory_dir = platform.memory_dir(project_path)
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


def init_memory_files(project_path: Path, platform: Platform):
    """初始化 4 个写作记忆文件"""
    memory_dir = platform.memory_dir(project_path)
    for filename, content in MEMORY_FILES.items():
        filepath = memory_dir / filename
        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
    print("  \u2705 \u5df2\u521d\u59cb\u5316 4 \u4e2a\u5199\u4f5c\u8bb0\u5fc6\u6587\u4ef6")





if __name__ == "__main__":
    main()
