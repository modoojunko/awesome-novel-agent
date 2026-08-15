# v4.16.0 版本说明

> **关键词：** 设定阶段作者确认门禁

---

## 一句话

从 0 到 1 新书流程中，设定（世界观/题材/角色/文风）写入完成后，novel-agent 会先展示设定摘要给作者确认，作者明确确认后才进入卷纲规划——补齐了设定阶段缺失的「产出后作者确认」门禁，与卷纲/章纲/文风/归档等环节对齐。

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **设定确认门禁** | `SKILL.md` 设定讨论流程：order DONE 只代表写入完成；novel-agent 展示设定摘要（文件清单对照 order outputs 逐项列出 + 世界观/题材/角色/文风要点）给作者确认，作者明确确认（"可以/没问题/就这样"）后才推进 phase → outline |
| **决策树细化** | `agents/novel-agent.md` THINK setup 分支新增确认门禁四条路径：solo 全自动豁免 / 明确确认（含"之前已确认过"重启路径）/ 模糊回复（"差不多""你看着办"）追问不放过，未明确前一律视为未确认 / 修改走 updater 重写再展示确认（受 §七 断路器约束，多轮不满意暂停请作者给最终文案）；显式豁免「以实际文件为准推进」规则 |
| **幂等与断点** | 新增幂等约定（phase=setup + setting-update-order DONE + outputs 非空 = 待确认，中断重启直接展示，不新增状态字段）；`skills/novel-dispatch.md` 断点续跑表加 setup 行；VERIFY 补 setup 特例回声（order 缺失但 outputs 存在 → 直接展示确认，不重派） |
| **文档** | `ARCHITECTURE.md` order DONE 推进处括注 setup 例外 |

---

## 兼容性

- 纯指令文本改动，无运行时逻辑变化（init/sync/平台适配不受影响）。
- `templates/` 无变更，新项目直接生效；已初始化项目跑 `sync-project.py` 同步 agent 定义后生效。

---

## 验证方法

- `check-agents.py` / `check-conflicts.py` / `py_compile` 全绿
- `test_platforms.py` 187 通过 0 失败（六平台 init/sync E2E 含 novel-agent 调度适配）
- 提示词工程师两轮检视（方案审 + 落地验收）+ review-agent 独立审查（No findings）
