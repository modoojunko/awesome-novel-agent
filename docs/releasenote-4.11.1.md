# v4.11.1 版本说明

> **关键词：** README 更新、QQ 交流群、三平台文档对齐

---

## 一句话

**README 对外口径与 v4.11.0 的平台适配层对齐：文档不再只写 Claude Code / OpenCode，补上 Reasonix 的安装和集成说明；顶部新增 QQ 交流群入口。**

---

## 这版做了什么

v4.11.0 代码里已经支持 Claude Code / OpenCode / Reasonix 三平台纯原生部署，但 README 还停留在「Claude Code / OpenCode」两个平台的口径，Reasonix 用户照文档装不起来。这版纯文档改动，把 README 对齐到实际能力。

| 改动 | 说明 |
|------|------|
| **QQ 交流群入口** | README 顶部徽章 + 开篇「加入交流群」区块，群号 1006050538（2群） |
| **三平台文档对齐** | 标题、徽章、你需要什么、安装、项目结构树、FAQ 全部补齐 Reasonix；新增「Reasonix 集成」章节（项目级 `.reasonix/skills/` 部署、`init.py --platform reasonix`、`reasonix code` 开始写作、sync 升级） |
| **项目结构说明** | 结构树改为 `.claude/` / `.opencode/` / `.reasonix/` 三选一并列，注明实际只生成一套 |
| **README-en.md 同步** | 英文版平台部分（标题、徽章、What You Need、Installation）同步补 OpenCode 和 Reasonix |

---

## 兼容性

纯文档改动，无代码行为变化。

---

## 验证方法

- `tools/test_platforms.py`：52 项断言全部通过（平台适配层回归）
