#!/usr/bin/env python3
"""awesome-novel-skill agent 定义静态检查

校验 agents/*.md 的 frontmatter：
  1. YAML 合法
  2. frontmatter 里引用的 skills/knowledge 路径在仓库真实存在（或是有意的占位/部署后路径）
  3. tools 字段只含合法工具名（若存在）

用法: python tools/check-agents.py
返回码 0 = 通过，非 0 = 有问题（CI 用）。

规则说明：
- agents/ 下的 .md 是 Claude Code 语法的 agent 源定义
- skills: 引用 skills/*.md（必存在）
- knowledge: 引用两类——
    (a) 仓库内相对路径（settings/、.claude/ 等，按仓库根解析，需存在）
    (b) 部署后路径（.claude/knowledge/...，由 init.py 生成，仓库可能没有源文件）
  对 (b) 类做"路径模式"白名单校验，不要求文件存在。
"""

import sys
import re
import yaml
from pathlib import Path

# 强制 UTF-8 输出，避免 Windows GBK 控制台报错
for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
SKILLS_DIR = ROOT / "skills"

# 合法工具名（Claude Code tools 白名单）
VALID_TOOLS = {
    "Read", "Write", "Edit", "Glob", "Grep", "Bash", "PowerShell",
    "WebFetch", "WebSearch", "NotebookEdit", "TodoWrite", "AskUserQuestion",
    "Skill", "Agent", "Task",
}

# 部署后生成、仓库里不一定有源文件的路径模式（白名单，不要求文件存在）
# 这些由 init.py 按题材/合并生成，或由 updater 归档时创建
DEPLOYED_PATTERNS = [
    re.compile(r"^\.claude/knowledge/(anti-ai|writer-style|genre-example|permanent-memory)\.md$"),
    re.compile(r"^\.claude/knowledge/[a-z-]+\.md$"),          # format-specs 平铺产物
    re.compile(r"^\.claude/knowledge/(plot-craft|scene-craft|character-craft|title-craft)/"),
    re.compile(r"^settings/character-setting/"),               # 每角色一个文件
    re.compile(r"^settings/(world-setting|genre-setting|writing-style|timeline|foreshadowing)\.md$"),
    re.compile(r"^settings/style-profiles/"),               # 分场景风格卡（每场景一个文件）
    re.compile(r"^settings/\.style-versions/"),             # 蒸馏版本快照目录（updater 归档时创建）
    re.compile(r"^\.agent/"),                                  # 运行时状态
    re.compile(r"^story\.md$"),
    re.compile(r"^volumes/"), re.compile(r"^chapters/"), re.compile(r"^prompts/"), re.compile(r"^archives/"),
]


def check_file(path: Path) -> list:
    errors = []
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return [f"{path.name}: 缺少 frontmatter (--- 开头)"]

    parts = text.split("---", 2)
    if len(parts) != 3:
        return [f"{path.name}: frontmatter 未正确闭合 (需两对 ---)"]

    try:
        fm = yaml.safe_load(parts[1])
    except Exception as e:
        return [f"{path.name}: frontmatter YAML 解析失败: {e}"]

    if not isinstance(fm, dict):
        return [f"{path.name}: frontmatter 不是 YAML map"]

    # name 必填
    if "name" not in fm:
        errors.append(f"{path.name}: 缺少 name 字段")

    # tools 字段合法性
    tools = fm.get("tools")
    if tools:
        names = [t.strip() for t in str(tools).split(",") if t.strip()]
        bad = [t for t in names if t not in VALID_TOOLS]
        if bad:
            errors.append(f"{path.name}: tools 含非法工具名 {bad}（合法: {sorted(VALID_TOOLS)}）")

    # skills / knowledge 路径存在性
    for key in ("skills", "knowledge"):
        entries = fm.get(key) or []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            p = entry.get("path")
            if not p:
                continue
            rel = str(p)
            # 占位符（如 {genre}）→ 跳过，init.py 会替换或属于合并产物
            if "{" in rel:
                continue
            # 部署后路径 → 白名单模式，不要求文件存在，但 settings/*.md 必须有对应模板
            if _is_deployed(rel):
                if rel.startswith("settings/") and rel.endswith(".md"):
                    # 每角色的动态文件（character-setting/）不校验模板
                    if not rel.startswith("settings/character-setting/"):
                        tpl = ROOT / "templates" / rel
                        if not tpl.exists():
                            errors.append(
                                f"{path.name}: 引用 settings/ 路径 {rel}，但 templates/settings/ 无对应模板"
                                f"（新项目 init.py 不会生成它 → 运行时必缺）"
                            )
                continue
            target = ROOT / rel
            if not target.exists():
                errors.append(f"{path.name}: 引用不存在的 {key} 路径: {rel}")

    return errors


def _is_deployed(rel: str) -> bool:
    """判断路径是否属于'部署后生成、仓库无源'的模式。"""
    rel = rel.replace("\\", "/")
    # 仓库内 skills/ 下的 .md 必须真实存在（skill 源就在仓库）
    if rel.startswith("skills/") or rel.startswith("knowledge/"):
        return False
    for pat in DEPLOYED_PATTERNS:
        if pat.match(rel):
            return True
    return False


def main() -> int:
    if not AGENTS_DIR.is_dir():
        print("⚠️  agents/ 目录不存在")
        return 1

    all_errors = []
    for f in sorted(AGENTS_DIR.glob("*.md")):
        errs = check_file(f)
        for e in errs:
            print(f"  ❌ {e}")
        all_errors.extend(errs)

    # 校验 agents/ 引用的 skills 文件是否真存在于 skills/ 目录
    refs = set()
    for f in AGENTS_DIR.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"skills/([a-z-]+\.md)", text):
            refs.add(m.group(1))
    missing_skills = [r for r in sorted(refs) if not (SKILLS_DIR / r).exists()]
    for s in missing_skills:
        print(f"  ❌ skills 引用缺失: skills/{s}")
        all_errors.append(f"skills/{s}")

    if all_errors:
        print(f"\n共 {len(all_errors)} 个问题")
        return 1
    print("✅ agent 定义全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
