#!/bin/bash
# Novel Agent Skill 安装脚本
#
# awesome-novel-agent - AI-assisted novel writing workflow system
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
    echo "平台: claude-code, opencode, codex, zcode, dsh, hermes, openclaw, deepseek-tui"
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
    zcode)
        SKILLS_DIR="$HOME/.zcode/skills"
        ;;
    dsh)
        SKILLS_DIR="$HOME/.dsh/skills"
        ;;
    *)
        echo "不支持的平台: $PLATFORM"
        usage
        ;;
esac

DEST="$SKILLS_DIR/awesome-novel"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Python 版本门槛：在任何目录创建/删除前检查（fail-fast）。
# 版本不满足时安装立即中止，而不是等 init.py / sync-project.py 执行时才报错。
# 可用 NOVEL_PYTHON 显式指定解释器（如 Homebrew 的 python3.12）。
PY_BIN="${NOVEL_PYTHON:-}"
if [ -z "$PY_BIN" ]; then
    PY_BIN="$(command -v python3 || true)"
fi
if [ -z "$PY_BIN" ]; then
    echo "错误: 未找到 python3。请先安装 Python 3.9+（https://www.python.org/downloads/）"
    exit 1
fi
if ! "$PY_BIN" "$SCRIPT_DIR/tools/check-python.py"; then
    echo "安装中止：请升级 Python 后重试。"
    exit 1
fi

# pyyaml 门槛：opencode / codex / zcode 的 agent/skill 转换依赖 pyyaml（与
# tools/platforms.py ensure_yaml 的运行时规则对齐）；claude 平台纯复制不转换、
# hermes/openclaw/deepseek-tui 未走转换，均不需要。缺失时同样在任何目录创建/
# 删除前 fail-fast，而不是等 init.py / sync-project.py 执行时才报错。
case "$PLATFORM" in
    opencode|codex|zcode|dsh)
        if ! "$PY_BIN" "$SCRIPT_DIR/tools/check-yaml.py" "$PLATFORM"; then
            echo "安装中止：缺少 pyyaml。请先执行 pip install pyyaml（系统 Python 权限受限时可用 pip install --user pyyaml），再重试。"
            exit 1
        fi
        ;;
esac

echo "安装到: $DEST"
export NOVEL_SKILL_HOME="$DEST"

# 注意：NOVEL_SKILL_HOME 只在本脚本会话内生效，不再写入 ~/.profile / ~/.bashrc 等。
# 持久化会遮蔽仓库来源（init.py 以 __file__ 解析技能根，env 优先会导致新项目部署安装版旧提示词）。

# 安全检查：DEST 必须是以 $HOME 开头的 skills/awesome-novel 路径。
# 先做无副作用的字符串校验（HOME 未设置/路径异常时在创建任何目录前即拒绝），
# 再创建父目录并复核 canonical 路径（避免全新 HOME 下 dirname 取不到导致误拒）。
HOME_NORM="${HOME%/}"
if [[ -z "$HOME_NORM" || -z "$DEST" || "$DEST" == "/" \
      || "$DEST" != "$HOME_NORM/."*"/skills/awesome-novel" ]]; then
    echo "错误：安装目标路径异常 ($DEST)，中止。"
    exit 1
fi
mkdir -p "$(dirname "$DEST")"
CANONICAL_DEST="$(cd "$(dirname "$DEST")" && pwd)/$(basename "$DEST")"
if [[ "$CANONICAL_DEST" != "$HOME_NORM/."*"/skills/awesome-novel" ]]; then
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
# memory/ 已废弃（writer-style 已迁至 knowledge/format-specs/）；保留守卫兼容旧仓库
[ -d "$SCRIPT_DIR/memory" ] && cp -r "$SCRIPT_DIR/memory" "$DEST/"

echo "安装完成!"
