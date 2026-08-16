# v4.17.0 版本说明

> **关键词：** 架构评审全量落地 + 正文质量治理

---

## 一句话

基于架构师评审（P1/P2/P3）与正文提示词链路审查，完成了「引用断链与打包清单修复、版本号单源化、平台适配去重、调度契约单源、规则层级分层裁定、蒸馏态严格匹配、视角单一来源、对话密度验收对齐」等一轮系统化治理——消除多副本漂移病灶，让同一约定只维护一处；并让「文风学出来后严格匹配、视角设定后全书一致」成为正文一致性的硬保证。

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **部署引用断链修复** | 14 处裸 `knowledge/...` 引用（roleplay-sandbox、7 个格式规范文件、2 个 agent 正文）改为 `.claude/knowledge/` 部署基座；check-agents 新增部署后布局引用校验 + 孤儿知识检测 + skill.json 完整性断言（产物清单从 init.deploy_knowledge 实跑，防模型漂移） |
| **版本号单源化** | VERSION 为唯一权威，ARCHITECTURE/status 模板/init 种子/skill.json 四处对齐；新增 `check-version.py` 挂 CI；skill.json 补 knowledge/ 打包清单、平台列表补全 6 个 |
| **平台适配去重** | reasonix/zcode/dsh 三份转换器与 deploy 合一（`convert_agent_to_platform` 单源），exec_agents/子 agent 名单收敛模块级常量；init/sync/find_changes 三处共用，HEAD 基线逐字节验证零行为变更 |
| **题材空壳显式化** | 选题列表标注「档案/反 AI 规则待补」+ 部署警告；urban-cultivation/high-martial 按复用声明真正合并反 AI 规则；孤儿 knowledge 接线（3 个设定指南进 updater） |
| **调度契约单源** | novel-dispatch.md 立为唯一权威（order 类型清单/卷完成判定/断点语义），novel-agent THINK 树为执行细则，ARCHITECTURE/SKILL/README 摘要标注权威源；AGENTS.md 路径口径改为部署后路径 |
| **规则层级分层裁定（B7）** | 合规层（红线/字数/T1/认知/感官，提示词第 1-5 层）不让步；质量层（写作规范级内）按「文风 > 作者记忆偏好 > 基底铁律 > 题材基线」取舍；压缩顺序由质量层决定（先砍环境/路人/过渡，保情绪段落） |
| **正文发飘治理** | 蒸馏态（文风卡已学出）删除「风格建议（可偏离）」，严格匹配偏差≤20%；「网文风格基线」重名拆分；认知动词/因果/温度去双注入；视角类型设定阶段定义全链路传递（章纲只定 POV 角色）；anti-ai 验收补对话密度 12 句例外 + 已蒸馏按提示词渲染占比评估 |
| **术语防回潮（C5）** | check-conflicts 新增禁现断言：7 个遗留术语（4 层/9 层/Goals/hooks.md/genre_profile 等）+ 反模式句在注入侧禁现；情绪外化速查合并（D4） |
| **check 脚本自测** | check-version 11 项断言（迷你仓库注入）；install.ps1 pwsh 冒烟测试（CI ubuntu 实跑，暴露并修复了 Linux pwsh 路径拼接问题） |
| **面向作者大白话** | author-communication 规范：作者可见内容全用大白话，堵三处内部词泄漏（并行贡献） |
| **文档收敛与清理** | P3 文档漂移八项（README 双语、CONTRIBUTING、install.ps1 平台对齐等）；审计复核表 15/18 已修复标注；删除已实现的 landing-page 设计稿与 superpowers 计划文档（11 文件） |

---

## 兼容性

- 纯指令文本 + 工具脚本改动。init/sync 行为零变更（六平台 E2E 逐字节验证）；新项目直接生效。
- 已初始化项目跑 `python tools/sync-project.py <项目路径>` 同步 agent/知识/脚手架后生效（skill_version 将更新为 4.17.0）。
- `check-version.py` / `check-agents.py` 为新增/扩展校验，CI 必跑；本地可手动运行。
- 新增知识文件 `author-communication.md`，随部署进入项目 knowledge。

---

## 验证方法

- `check-agents.py` / `check-conflicts.py`（含 C5 禁现）/ `check-version.py` / `py_compile` 全绿
- `test_platforms.py` 198 通过 0 失败（六平台 init/sync E2E + install.ps1 pwsh 冒烟 + check-version 11 断言）
- `test_style_rules.py` 125 / `test_style_distill.py` 84 全绿
- 三平台（reasonix/zcode/dsh）skills 产物与基线逐字节 diff 仅含预期差异
- Mimosa 深度安全扫描 0 发现（seal 已生成）；review-agent 两轮评审发现全部修复
