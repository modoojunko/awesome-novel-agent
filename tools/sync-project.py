#!/usr/bin/env python3
"""
同步项目空间的 agent/skill/知识库到最新版本。

用法:
  python tools/sync-project.py <project-path>            # 同步（自动更新指纹）
  python tools/sync-project.py <project-path> --check    # 只检查新鲜度
  python tools/sync-project.py <project-path> --sync     # 强制同步（同默认）

检查模式 (--check) 用 exit code 表示结果：
  0 = 已是最新
  1 = 有更新可用（或项目缺少指纹）
  2 = 项目无效

不触碰 settings/ volumes/ chapters/ archives/ prompts/ story.md。

Windows 中文路径乱码：
  如果 `python tools/sync-project.py .` 报路径乱码，改用显式路径从 skill 目录运行：
  cd C:\\Users\\modoo\\.claude\\skills\\awesome-novel
  python tools\\sync-project.py "d:\\novels\\daily\\小说项目"
"""

from __future__ import annotations  # str | None 等注解在 Python 3.9 下延迟求值，避免 import 即 TypeError

import hashlib
import subprocess
import sys
import os
import shutil
from pathlib import Path

from platforms import (
    Platform,
    convert_to_codex,
    convert_to_opencode,
    detect_platform,
    deploy_codex_skills,
    deploy_reasonix_skills,
    ensure_yaml,
    resolve_skill_home,
    rewrite_refs,
)

for s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


SKILL_HOME = resolve_skill_home()
AGENT_DIR = SKILL_HOME / "agents"
SKILL_DIR = SKILL_HOME / "skills"
KNOWLEDGE_DIR = SKILL_HOME / "knowledge"
TEMPLATE_SETTINGS_DIR = SKILL_HOME / "templates" / "settings"
TOOLS_SRC_DIR = SKILL_HOME / "tools"
# TOOLS_SRC_DIR 仅指纹 style-distiller 的 distill/compare/mix 三个脚本，避免对全部 tools/
# （init.py / platforms.py / 测试脚本等）哈希——那些不属于项目要同步的资产。
_STYLE_TOOL_NAMES = ("distill-style.py", "compare-style.py", "mix-style.py")
FINGERPRINT_FILE = Path(".agent") / ".sync-fingerprint"
VERSION_FILE = Path(".agent") / ".sync-version"


def main():
    if "-h" in sys.argv or "--help" in sys.argv or len(sys.argv) < 2:
        print(__doc__.strip())
        return

    check_only = "--check" in sys.argv

    # 平台：--platform > NOVEL_PLATFORM > SKILL_HOME 路径识别 > claude
    platform_override = None
    if "--platform" in sys.argv:
        idx = sys.argv.index("--platform")
        if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--"):
            platform_override = sys.argv[idx + 1]
        else:
            print("错误: --platform 需要一个平台名（claude|opencode|reasonix|codex）")
            sys.exit(1)
    platform_override = platform_override or os.environ.get("NOVEL_PLATFORM")
    try:
        platform = detect_platform(SKILL_HOME, platform_override)
    except ValueError as e:
        print(e)
        sys.exit(1)
    ensure_yaml(platform)

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


# ============================================================
# 指纹机制
# ============================================================

def get_latest_version() -> str | None:
    """从 git tag 获取 skill 最新版本号"""
    try:
        result = subprocess.run(
            ["git", "-C", str(SKILL_HOME), "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_version_info() -> tuple[str | None, str | None]:
    """返回 (latest_tag, version_summary)，version_summary 用于显示"""
    tag = get_latest_version()
    if tag:
        return tag, tag
    return None, "unknown"


def compute_fingerprint() -> str:
    """对 skill 源目录的所有 agent/skill/knowledge/templates/settings 文件与 style-distiller 脚本算一个 hash"""
    files = []
    for base in [AGENT_DIR, SKILL_DIR, KNOWLEDGE_DIR]:
        if base.exists():
            for f in sorted(base.rglob("*")):
                if f.is_file() and f.name != ".gitkeep":
                    files.append(f)
    for base in [TEMPLATE_SETTINGS_DIR, TOOLS_SRC_DIR]:  # templates/settings 全部纳入；TOOLS_SRC_DIR 只取 distill 三脚本
        if base.exists():
            for f in sorted(base.rglob("*")):
                if not f.is_file() or f.name == ".gitkeep":
                    continue
                if base == TOOLS_SRC_DIR and f.name not in _STYLE_TOOL_NAMES:
                    continue
                files.append(f)

    h = hashlib.sha256()
    for f in files:
        rel = f.relative_to(SKILL_HOME)
        h.update(str(rel).encode("utf-8"))
        h.update(f.read_bytes())
    return h.hexdigest()


def read_project_fingerprint(project: Path) -> tuple[str | None, str | None]:
    """返回 (fingerprint, version)"""
    fp = project / FINGERPRINT_FILE
    vp = project / VERSION_FILE
    finger = None
    version = None
    if fp.exists():
        finger = fp.read_text(encoding="utf-8").strip()
    if vp.exists():
        version = vp.read_text(encoding="utf-8").strip()
    return finger, version


def write_project_fingerprint(project: Path, fingerprint: str, version: str | None = None):
    fp = project / FINGERPRINT_FILE
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(fingerprint + "\n", encoding="utf-8")

    vp = project / VERSION_FILE
    if version:
        vp.parent.mkdir(parents=True, exist_ok=True)
        vp.write_text(version + "\n", encoding="utf-8")
    elif vp.exists():
        vp.unlink(missing_ok=True)


# ============================================================
# 检查
# ============================================================

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
        if not changes and platform.key in ("reasonix", "codex"):
            print("有更新可用（源文件变化，平台派生产物由同步时重新生成）。")
        else:
            lines = [f"有更新可用 ({len(changes)} 个文件发生变化):"]
            for f in changes:
                lines.append(f"  - {f}")
            if version_info:
                lines.append(version_info)
            print("\n".join(lines))
        sys.exit(1)


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
            continue  # 派生产物靠源指纹检测，同步时重新生成
        if platform.key == "codex" and name in ("agents", "skills"):
            continue  # TOML/SKILL.md 是派生产物，靠源指纹检测，同步时重新生成
        for item in sorted(src_dir.rglob("*.md")):
            if item.name == ".gitkeep":
                continue
            rel = item.relative_to(src_dir)
            target = dst_base / rel
            if name == "agents" and platform.key == "opencode":
                expected = convert_to_opencode(item.read_text(encoding="utf-8"))
                expected = rewrite_refs(expected, platform)
                if not target.exists() or target.read_text(encoding="utf-8") != expected:
                    changed.append(f"{name}/{rel}")
            else:
                if not target.exists() or target.read_bytes() != item.read_bytes():
                    changed.append(f"{name}/{rel}")
    return changed


# ============================================================
# 同步
# ============================================================

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
    changes.append(sync_style_assets(project))

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
    if platform.key == "opencode":
        # opencode agents 是转换产物（permission: 格式 + 引用改写），与 init 保持一致
        count = 0
        for item in sorted(AGENT_DIR.rglob("*.md")):
            if item.name == ".gitkeep":
                continue
            rel = item.relative_to(AGENT_DIR)
            dest = target / rel
            content = convert_to_opencode(item.read_text(encoding="utf-8"))
            content = rewrite_refs(content, platform)
            if dest.exists() and dest.read_text(encoding="utf-8") == content:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            count += 1
    elif platform.key == "codex":
        # codex agents 是转换产物（.codex/agents/*.toml），与 init 保持一致
        count = 0
        for item in sorted(AGENT_DIR.rglob("*.md")):
            if item.name == ".gitkeep":
                continue
            content = convert_to_codex(item.read_text(encoding="utf-8"), SKILL_HOME)
            dest = target / (item.stem + ".toml")
            if dest.exists() and dest.read_text(encoding="utf-8") == content:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            count += 1
    else:
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
    if platform.key == "codex":
        deploy_codex_skills(project_path, SKILL_HOME, platform)
        n = len(list(platform.skills_dir(project_path).rglob("SKILL.md")))
        print(f"  [OK] codex skills: {n} 个 SKILL.md 已重新生成")
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


def sync_style_assets(project: Path) -> int:
    """同步 style-distiller 资产：风格卡 + 蒸馏脚本 + 旧卡迁移钩子。

    只补缺失文件（不覆盖已有），与 init.py 的 deploy_tools/seed 守卫同语义——
    升级/迁移不破坏用户已编辑的写作风格卡与项目 tools/。
    """
    count = 0
    src_cards = TEMPLATE_SETTINGS_DIR / "style-profiles"
    if src_cards.exists():
        dst = project / "settings" / "style-profiles"
        dst.mkdir(parents=True, exist_ok=True)
        for f in src_cards.glob("*.md"):
            if not (dst / f.name).exists():
                (dst / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
                count += 1
    dst_tools = project / "tools"
    dst_tools.mkdir(parents=True, exist_ok=True)
    for name in _STYLE_TOOL_NAMES:
        src = TOOLS_SRC_DIR / name
        if src.exists() and not (dst_tools / name).exists():
            (dst_tools / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            count += 1
    try:
        from init import migrate_writing_style   # init.py main 有 __main__ 守卫，导入安全
        migrate_writing_style(project)
    except ImportError:
        pass
    if count:
        print(f"  [OK] 风格资产同步: {count} 个新文件")
    return count


def _sync_dir(src: Path, dst: Path, pattern: str) -> int:
    count = 0
    for item in sorted(src.rglob(pattern)):
        if item.name == ".gitkeep":
            continue
        rel = item.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if _sync_file(item, target):
            count += 1
    return count


def _sync_file(src: Path, dst: Path) -> bool:
    if dst.exists() and dst.read_bytes() == src.read_bytes():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


if __name__ == "__main__":
    main()
