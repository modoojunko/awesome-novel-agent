# v4.26.0 版本说明

> **关键词：** 短篇知识补齐 —— 写作深度参考 11 篇、十大题材风格包全交付、跨篇作者偏好记忆

---

## 一句话

短篇流水线的「软件」补齐：写手设计钩子/情绪/反转有了 11 篇深度参考可查，十大题材风格包全部交付（每包含情绪链库），作者跨篇的口味偏好第一次被记住——不再每写一篇重述一遍。

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **写作深度参考 11 篇** | `knowledge/short/craft/` 新增：hooks 三件套（章节钩子类型库 / 段落钩子 / 悬念设计）、emotional-methods（情感三板斧：羁绊铺设/情感撕裂/余韵钝痛）、reversal-toolkit（反转类型与铺垫）、villain-and-reveal（反派模板+四种揭露机制）、dialogue-mastery（对话权力博弈/潜台词/声线）、genre-writing-formulas（冷门题材结构骨架兜底）、genre-writing-techniques（跨题材技法）、submission-craft（投稿范式：导语四维骨架/付费点卡位）、quality-checklist（成稿清单）。全部接入 short-planner / short-writer / short-editor |
| **十大题材风格包全交付** | 新增 9 包：世情打脸 / 复仇打脸 / 总裁豪门 / 宅斗宫斗 / 民俗怪谈 / 悬疑 / 甜宠 / 双男主 / 沙雕脑洞（拼音 slug）。每包在包原 10 节之上新增**情绪链库**（2-3 条命名情绪弧、每条 5 个具名阶段，从节奏骨架提炼），招式库保持「公式+真实例」成对。`init.py --length short --genre 1-10` 全部可用，交互选题同步支持 |
| **跨篇作者偏好记忆** | `<平台>/memory/author-feedback.md`：init 种子生成 → 每篇交付时 short-agent 追加作者明确反馈（「原文 → 结论」一行，不臆造）→ short-planner 组装契约时取用相关条目。修掉「每写一篇重述一遍偏好」的结构性缺失 |

## 兼容性

- 纯增量：长篇路径零变化；短篇既有产物布局不变（craft 目录 2→13 个文件、genres 目录 2→11 个文件，sync 按目录级比对自动覆盖）
- 非交互环境（AI 终端）不带 `--genre` 初始化短篇：自动回落注册表 1 号（追妻火葬场）并显式提示；需要其他题材显式传 `--genre 1-10`
- 来源：新增内容为获赠资产改写，文件头标注出处，公开/商用前需原作者确认

## 测试

- check-agents / check-conflicts / check-version / py_compile 全绿；test_platforms **516/516**（新增：craft 13 文件、题材 11 文件、记忆种子、genre 2 可用断言）
- review-agent 评审 8 条 findings（2×P1：非交互 EOF 裸 traceback、拆文管线字段残留；P2 断链/过时注释；P3 文案）全部修复
