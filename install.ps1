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

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("claude-code", "opencode", "codex", "zcode", "dsh")]
    [string]$Platform
)

$HOME_DIR = $env:USERPROFILE

switch ($Platform) {
    "claude-code" {
        $DEST_DIR = "$HOME_DIR\.claude\skills\awesome-novel"
    }
    "opencode" {
        $DEST_DIR = "$HOME_DIR\.config\opencode\skills\awesome-novel"
    }
    "codex" {
        $DEST_DIR = "$HOME_DIR\.codex\skills\awesome-novel"
    }
    "zcode" {
        $DEST_DIR = "$HOME_DIR\.zcode\skills\awesome-novel"
    }
    "dsh" {
        $DEST_DIR = "$HOME_DIR\.dsh\skills\awesome-novel"
    }
}

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Python 版本门槛：在任何目录创建/删除前检查（fail-fast）。
$PY_BIN = "python"
if (-not (Get-Command $PY_BIN -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未找到 python。请先安装 Python 3.9+（https://www.python.org/downloads/）"
    exit 1
}
& $PY_BIN "$SCRIPT_DIR\tools\check-python.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "安装中止：请升级 Python 后重试。"
    exit 1
}

# pyyaml 门槛：opencode / codex / zcode / dsh 的 agent/skill 转换依赖 pyyaml（与
# tools/platforms.py ensure_yaml 的运行时规则对齐）；claude-code 纯复制不转换，不需要。
if ($Platform -in @("opencode", "codex", "zcode", "dsh")) {
    & $PY_BIN "$SCRIPT_DIR\tools\check-yaml.py" $Platform
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装中止：缺少 pyyaml。请先执行 pip install pyyaml 后重试。"
        exit 1
    }
}

Write-Host "安装到: $DEST_DIR"

# 创建目录，已存在则清空
Remove-Item -Recurse -Force $DEST_DIR -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $DEST_DIR | Out-Null

# 显式 include 列表，与 install.sh 保持一致
$INCLUDES = @("SKILL.md", "agents", "skills", "knowledge", "templates", "tools")

foreach ($item in $INCLUDES) {
    $src = Join-Path $SCRIPT_DIR $item
    if (Test-Path $src) {
        Copy-Item -Recurse $src "$DEST_DIR\"
    }
}

# memory/ 含 writer-style 等静态参考素材（可选）
$memoryDir = Join-Path $SCRIPT_DIR "memory"
if (Test-Path $memoryDir) {
    Copy-Item -Recurse $memoryDir "$DEST_DIR\"
}

Write-Host "安装完成!"
