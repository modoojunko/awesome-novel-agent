# Tasks: 2026-09-10-add-short-scan-analyze

## 1. 部署机制

- [ ] 1.1 platforms.py：`SHORT_STANDALONE_SKILLS = ("short-scan", "short-analyze")` + `deploy_standalone_skills(project, skill_home, platform, names)`（`_convert_standalone_skill` + rewrite_refs → `<skills_dir>/<name>/SKILL.md`）；`deploy_inline_skills(short)` 内挂独立工具。验证：inline 平台 short init 出 8 个 skill 目录
- [ ] 1.2 init.py：short 流程部署独立工具（全平台统一走助手）。验证：7 平台产物含两工具
- [ ] 1.3 sync-project.py：短篇 sync_skills 补独立工具再部署；find_changes 短篇分支补两文件比对。验证：篡改检出 / sync 恢复

## 2. 扫榜 SOP（skills/short-scan.md）

- [ ] 2.1 流程主体：平台方向确认三形态（S1）、三级数据来源与降级标注（S2）、单平台失败跳过（S2.4）
- [ ] 2.2 七维分析 + 平台调性对照（S3）；报告模板含时效三件套与风口预警（S4）
- [ ] 2.3 选题匹配：复杂度分级 + 传播风险兜底（S5）
- [ ] 2.4 附录：内置市场知识（跨平台调性表 / 平台简介公式 / 题材爆款公式，获赠包 real-market-data.md 压缩内联）

## 3. 拆文 SOP（skills/short-analyze.md）

- [ ] 3.1 输入与路由：原文获取 / 字数三档（A1）；题材标尺加载 short-genres（A2）
- [ ] 3.2 续跑检查与原文备份（A2.1 / A3）
- [ ] 3.3 五阶段管道与逐阶段完成标志（A4）；崩溃安全写盘协议（A5）
- [ ] 3.4 产出文件树（analysis/{书名}/ 五件）与 `_meta.json` schema（A6）
- [ ] 3.5 三道验收闸门（A7）

## 4. 接线与测试

- [ ] 4.1 SKILL.md 短篇分支补可选工具说明（不进调度链声明）。验证：grep
- [ ] 4.2 test_platforms：7 平台独立工具部署断言；inline 数量 6→8；claude/opencode/codex/grok skills 目录断言；长篇回归不含两工具。验证：全绿
- [ ] 4.3 全链回归：py_compile / check-agents / check-conflicts / test_platforms
- [ ] 4.4 推 PR + review-agent 评审；**按作者要求不合入**（合并时机待短篇主链路真机实测后决策）
