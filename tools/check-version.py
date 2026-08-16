#!/usr/bin/env python3
"""版本号一致性检查（arch-review 2026-08）

版本号以 VERSION 文件为唯一权威源，校验各处副本不漂移：
  1. ARCHITECTURE.md 版本头（> 当前版本：vX.Y.Z）
  2. skill.json version 字段
  3. templates/.agent/status.md 的 skill_version（sync-project 按它回写项目状态）
  4. tools/init.py write_status 的 skill_version 种子值（新项目状态文件来源）

发版时改 VERSION + 同步四处副本（chore: bump version），漏改此处会红。

用法: python tools/check-version.py
返回码 0 = 一致，1 = 有漂移（CI 用）。仅标准库。

测试注入：NOVEL_REPO_ROOT 指向迷你仓库目录（test_platforms 构造漂移场景用）。
"""

from __future__ import annotations  # str | None 注解在 Python 3.9 下延迟求值

import os
import re
import sys

from pathlib import Path

from style_common import force_utf8

force_utf8()

ROOT = Path(os.environ.get("NOVEL_REPO_ROOT") or Path(__file__).resolve().parent.parent)


def _version_from_version_file() -> str:
    """VERSION 文件 → 纯版本号（剥 v 前缀与空白）。"""
    text = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return text.lstrip("vV")


def main() -> int:
    errors = []
    version = _version_from_version_file()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print(f"❌ VERSION 文件格式异常: {version!r}（期望 vX.Y.Z）")
        return 1

    def expect(label: str, actual: str | None) -> None:
        if actual != version:
            errors.append(f"{label}: {actual or '（未找到）'} ≠ VERSION 的 {version}")

    # 1. ARCHITECTURE.md 版本头
    arch = ROOT / "ARCHITECTURE.md"
    m = re.search(r"当前版本[：:]\s*v?(\d+\.\d+\.\d+)", arch.read_text(encoding="utf-8"))
    expect("ARCHITECTURE.md 版本头", m.group(1) if m else None)

    # 2. skill.json version
    sj = ROOT / "skill.json"
    try:
        import json
        data = json.loads(sj.read_text(encoding="utf-8"))
        expect("skill.json version", str(data.get("version") or "") or None)
    except Exception as e:
        errors.append(f"skill.json 解析失败: {e}")

    # 3. templates/.agent/status.md skill_version
    status_tpl = ROOT / "templates" / ".agent" / "status.md"
    m = re.search(r"skill_version:\*\*\s*(\d+\.\d+\.\d+)",
                  status_tpl.read_text(encoding="utf-8"))
    expect("templates/.agent/status.md skill_version", m.group(1) if m else None)

    # 4. tools/init.py write_status 种子值
    init_src = ROOT / "tools" / "init.py"
    m = re.search(r"skill_version:\*\*\s*(\d+\.\d+\.\d+)",
                  init_src.read_text(encoding="utf-8"))
    expect("tools/init.py write_status 种子值", m.group(1) if m else None)

    for e in errors:
        print(f"❌ {e}")
    if errors:
        print(f"\n共 {len(errors)} 处版本漂移（以 VERSION=v{version} 为准同步）")
        return 1
    print(f"✅ 版本号一致（v{version}，五处单源对齐）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
