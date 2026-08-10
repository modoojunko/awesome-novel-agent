# v4.12.3 版本说明

> **关键词：** Python 版本门槛、安装阶段 fail-fast、3.9 兼容

---

## 一句话

**Python 版本问题从"执行时报错"提前到"安装时报错"：新增 `tools/check-python.py` 版本门槛，`install.sh` / `install.ps1` 在创建/删除任何文件前先检查解释器版本；同时修复 `sync-project.py` 在 Python 3.9 下 import 即 TypeError 的意外依赖（补 `from __future__ import annotations`），3.9 用户无需升级即可运行。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **版本门槛脚本**（`tools/check-python.py`） | 新增独立检查脚本（默认要求 Python 3.9+，`--min` 供测试覆盖），版本不满足时输出明确的升级提示 |
| **安装 fail-fast**（`install.sh` / `install.ps1`） | 两个安装脚本在任何目录创建/删除前先运行版本检查，不满足立即中止；`install.sh` 支持 `NOVEL_PYTHON` 指定解释器（如 Homebrew 的 python3.12） |
| **3.9 兼容修复**（`tools/sync-project.py`） | 补上与 `platforms.py` 一致的 `from __future__ import annotations`，`str \| None` 注解在 Python 3.9 下不再 import 即抛 TypeError |
| **文档**（README / README-en） | 前置要求补充 "Python 3.9+（推荐 3.11+）"，说明安装脚本会先检查版本 |
| **回归测试** | `test_platforms.py` 新增版本门槛单元用例与"版本不满足时 install.sh 不创建任何目录"负向 E2E |

---

## 兼容性

无平台行为变化（claude / opencode / reasonix / codex 产物不变）。macOS 系统自带 Python 3.9.6 已验证 `init` / `sync` / `--check` 全通过；安装门槛仅对 <3.9 的解释器生效。已安装旧版 skill 的用户需要重跑 `install.sh`（`tools/` 不参与项目级同步）才能拿到修复后的脚本。

---

## 验证方法

- Python 3.9.6：`init.py` / `sync-project.py` / `sync-project.py --check` 全通过（修复前 import 即 TypeError）
- `python tools/test_platforms.py`：100/100 通过
- `install.sh` 用系统 Python 3.9.6 安装成功；`NOVEL_PYTHON=/bin/false` 模拟版本不满足时在创建目标目录前中止
