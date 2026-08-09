#!/bin/bash
# Novel Agent Skill 安装脚本
#
# awesome-novel-skill - AI-assisted novel writing workflow system
# Copyright (C) 2026  modoojunko
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

set -e

usage() {
    echo "用法: $0 <平台>"
    echo "平台: claude-code, opencode, codex, hermes, openclaw, deepseek-tui"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

PLATFORM="$1"

case "$PLATFORM" in
    claude-code)
        SKILLS_DIR="$HOME/.claude/skills"
        ;;
    hermes)
        SKILLS_DIR="$HOME/.hermes/skills"
        ;;
    openclaw)
        SKILLS_DIR="$HOME/.openclaw/skills"
        ;;
    deepseek-tui)
        SKILLS_DIR="$HOME/.deepseek/skills"
        ;;
    opencode)
        SKILLS_DIR="$HOME/.config/opencode/skills"
        ;;
    codex)
        SKILLS_DIR="$HOME/.codex/skills"
        ;;
    *)
        echo "不支持的平台: $PLATFORM"
        usage
        ;;
esac

DEST="$SKILLS_DIR/awesome-novel"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "安装到: $DEST"
export NOVEL_SKILL_HOME="$DEST"

# 注意：NOVEL_SKILL_HOME 只在本脚本会话内生效，不再写入 ~/.profile / ~/.bashrc 等。
# 持久化会遮蔽仓库来源（init.py 以 __file__ 解析技能根，env 优先会导致新项目部署安装版旧提示词）。

# 安全检查：DEST 必须是以 $HOME 开头的 skills/awesome-novel 路径。
# 先创建父目录，避免全新 HOME（skills 目录尚不存在）时 dirname 取不到导致误拒。
mkdir -p "$(dirname "$DEST")"
CANONICAL_DEST="$(cd "$(dirname "$DEST")" && pwd)/$(basename "$DEST")"
if [[ -z "$DEST" || "$DEST" == "/" || "$CANONICAL_DEST" != "$HOME/."*"/skills/awesome-novel" ]]; then
    echo "错误：安装目标路径异常 ($DEST)，中止。"
    exit 1
fi

# 创建技能目录，已存在则清空
rm -rf "$DEST"
mkdir -p "$DEST"

# 复制运行时需要的文件（include list，避免泄露仓库元数据）
cp "$SCRIPT_DIR/SKILL.md" "$DEST/"
cp -r "$SCRIPT_DIR/agents" "$DEST/"
cp -r "$SCRIPT_DIR/skills" "$DEST/"
cp -r "$SCRIPT_DIR/knowledge" "$DEST/"
cp -r "$SCRIPT_DIR/templates" "$DEST/"
cp -r "$SCRIPT_DIR/tools" "$DEST/"
# memory/ 含 writer-style 等静态参考素材，不包含 anti-ai（已迁至 knowledge/anti-ai/）
[ -d "$SCRIPT_DIR/memory" ] && cp -r "$SCRIPT_DIR/memory" "$DEST/"

echo "安装完成!"
