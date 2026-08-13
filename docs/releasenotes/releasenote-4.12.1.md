# v4.12.1 版本说明

> **关键词：** 安装体验、agent 驱动安装、/awesome-novel 统一入口

---

## 一句话

**安装不再让用户复制粘贴命令：对 AI 说「帮我安装 awesome-novel-skill」，AI 自己运行 `install.sh <平台>` 安装本体；之后在小说目录输入 `/awesome-novel`（Codex 用 `/use awesome-novel`）即可在本地初始化小说工作空间。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **agent 驱动安装** | README（中/英）、landing page、tutorial 的安装方式从「用户复制粘贴」改为「对 AI 说一句话，AI 自动运行 `./install.sh <平台>` / `install.ps1 <平台>`」 |
| **统一入口命令** | 安装完成后在小说目录输入 `/awesome-novel` 自动初始化（Codex 为 `/use awesome-novel`）；SKILL.md 检测流程与 `init.py` / `sync-project.py` 调用改为 skill 安装目录绝对路径 |
| **文档一致性修复** | Reasonix 入口统一为 `@novel-agent`（项目级部署的入口 skill 名为 novel-agent）；README-en / tutorial agent 数量统一为 8（含 anti-ai）；tutorial 平台表补齐 OpenCode / Codex / Reasonix，并补 Windows `install.ps1` 与 install.sh 兼容平台脚注 |
| **版本信息对齐** | tutorial 手册版本对齐 v4.12.0+ |

---

## 兼容性

纯文档改动，无代码行为变化；四平台安装 / 初始化流程不变。

---

## 验证方法

- 纯文档 / HTML 改动，无 Python 逻辑变更
- CI：lint（py_compile、check-agents、check-conflicts、test_platforms）通过
- Markdown 代码块围栏配对、HTML 标签目检通过
