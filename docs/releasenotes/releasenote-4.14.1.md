# v4.14.1 版本说明

> **关键词：** 文风设定通用命令、novel-samples 蒸馏样本目录、交互文案白话化、结构树补齐

---

## 一句话

**把 #93 遗漏的 6 个功能提交补齐（文风设定决策流程泛化为通用命令、novel-samples/ 蒸馏样本专用目录、蒸馏样本限定项目空间、面向作者的交互文案去内部词、.claude/agents 工具 agent 命名对齐），并修正 v4.14.0 发布时结构树未同步的文档遗漏。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **文风设定通用命令** | "修改文风设定"不再限 setup 阶段——任何 phase 说出即进入三选流程（学我的文风 / 用模板 / 暂缓）；存量项目可用已归档正文做样本 |
| **novel-samples/ 蒸馏样本目录** | init 骨架新增专用目录（类比 sandbox/），作者把待学文风的文章放这里；蒸馏样本限定项目空间内——项目外路径提示移入，聊天粘贴自动落盘 `.agent/task/style-sample.md` |
| **交互文案白话化** | 面向作者的文案去内部词：蒸馏→学我的文风、推演沙盘→剧情推演、归档→定稿存档、画像节名白话化 |
| **agent 命名对齐** | `.claude/agents/` 5 个工具 agent 重命名对齐 `{role}-agent.md` 约定（code-reviewer→code-reviewer-agent 等），check-agents 补该目录命名校验 |
| **文档结构树补齐** | 项目结构树补 `settings/style-profiles/`（分场景风格卡 + genre-baselines 题材基线）、`settings/.style-versions/`（蒸馏版本快照）、`novel-samples/`（蒸馏样本目录）；README-en 的 agents 数量旧数字修正（7→9、8→9） |

---

## 兼容性

- 存量项目：无迁移。novel-samples/ 可按需手动创建（或由 style-distiller 在蒸馏时落盘样本）；文档结构树与实际 init 产物已对齐（`init.py` 新项目自带 style-profiles/ 与 novel-samples/）。
- 交互文案为展示层改动，不影响 order 文件协议与 agent 调度链。

---

## 验证方法

- `python tools/test_platforms.py`：159/159 通过
- `python tools/test_style_rules.py`：125/125 通过
- `python tools/test_style_distill.py`：84/84 通过
- `python tools/check-agents.py` / `check-conflicts.py` 通过；zcode 平台实测 init/sync 正常（11 个 skill，novel-agent 含新文风命令流程）
