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
    [ValidateSet("claude-code", "opencode", "codex")]
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
}

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

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
