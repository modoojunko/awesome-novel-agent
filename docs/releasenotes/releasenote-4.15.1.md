# v4.15.1 版本说明

> **关键词：** Landing page 重构 + 仓库命名统一

---

## 一句话

**重构 GitHub Pages landing page（问题导向文案 + 动态亮点卡轮播 + 流水线流程图），确立 Awesome Novel 品牌，并将仓库命名从 awesome-novel-skill 统一为 awesome-novel-agent。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **Landing page 重构** | `index.html` 全量重写：三大痛点支柱（怕烂尾？/ 不像你？/ 有 AI 味？）问题导向文案；Hero 右侧 5 张动态亮点卡轮播（文风蒸馏 / 剧情推演 / 伏笔跟踪 / 角色状态更新 / 本地数据安全，24px stat 网格）；六阶段流水线流程图（设定→卷纲→章纲→正文→净化→归档）；三步开始创作 + FAQ + 社区 CTA |
| **品牌确立** | 品牌名 **Awesome Novel**（Hero 品牌行 22px + 导航 + 页脚）；核心价值观三层闭环「构想由你铸就 → 文字交给智能体 → 成稿由你拍板」 |
| **命名统一** | `awesome-novel-skill` → `awesome-novel-agent` 全仓库 15 文件 53 处（README / README-en / install.sh / install.ps1 / skill.json / tools/ / LICENSE-DECLARATION / docs/tutorial.md）；顺带修复 LICENSE-DECLARATION 中 `skilll` 拼写错误 |
| **技术中文化** | 页面技术英文全部中文化：Agent → 智能体、Gate A-F → 六道闸、STEP → 步骤；平台名与命令（/awesome-novel、@novel-agent）保留 |
| **文档** | 新增 `docs/landing-page-study.md`（DeepSeek Harness landing page 设计令牌与文案方法学习总结）与 `docs/landing-page-redesign.md`（改造方案：结构图 / 文案成稿 / 完整单文件代码 / 验收清单） |

---

## 兼容性

- 无运行时逻辑变化：本次仅页面与文档改动，skill 本体、init/sync、平台适配不受影响。
- `docs/` 目录在 `.gitignore` 中，两份新文档以 `git add -f` 入库（与 `docs/tutorial.md` 同先例）。

---

## 验证方法

- HTML 标签配对校验通过（自写 parser）
- CI lint 通过：`py_compile` / `check-agents.py` / `test_platforms.py` / style-distill 测试全绿
- CI deploy 通过：GitHub Pages 已发布新页面（`https://modoojunko.github.io/awesome-novel-agent/`）
