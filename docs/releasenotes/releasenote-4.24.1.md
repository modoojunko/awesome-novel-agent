# v4.24.1 版本说明

> **关键词：** Windows 平台修复 —— 静态检查跨平台一致 + 安装器 PS 5.1 兼容

---

## 一句话

两个 Windows 专项修复：check-agents 的部署产物清单改用正斜杠路径，Windows 上孤儿检测不再全量误报；install.ps1 补 UTF-8 BOM，Windows PowerShell 5.1（系统默认 shell）不再解析失败。macOS/Linux 行为零变化。

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **check-agents 部署集路径统一正斜杠（#128）** | `_deployed_knowledge_files()` 产物清单 `str()` → `as_posix()`。Windows 上反斜杠路径与引用扫描（正斜杠）永远失配，孤儿检测与引用校验全量误报（实测报 96 个孤儿 exit 1，而 ubuntu CI 全绿）；修复后两平台行为一致 |
| **install.ps1 补 UTF-8 BOM（#129）** | 无 BOM 的 UTF-8 在 PowerShell 5.1 按 ANSI/GBK 解码，脚本内中文提示串直接 ParserError，安装器完全无法运行；补 BOM 后 PS 5.1 与 pwsh 7 双通，内容零改动 |

## 兼容性

- 纯修复：macOS/Linux 全平台行为不变（`as_posix()` 与 `str()` 在 POSIX 下等价）；不涉及项目格式，无迁移。
- 外部贡献：两处修复均来自 @qikairo7（Leo）的 Windows 11 真机实测。

## 测试

- 修复分支上 check-agents / check-conflicts / test_platforms 全绿（290 通过 0 失败）；合入后 main CI 全绿。
- Windows 11 真机验证：check-agents 96 误报 → 0；install.ps1 ParserError → 正常安装落位（SKILL.md + agents + tools）。
