# v4.12.2 版本说明

> **关键词：** Codex 调度安全、子 agent 越权防护、递归自派拦截

---

## 一句话

**修复 Codex 平台多 agent 调度的失控问题：子 agent 不再能越权推进流水线或递归派生自己。所有子 agent 的 Codex TOML 注入「调度权限硬约束」（禁止 spawn_agent、禁止写非本 order 文件、禁止写 phase 字段），项目 AGENTS.md 声明 novel-agent 为唯一调度者。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **调度硬约束注入**（`tools/platforms.py`） | `convert_to_codex` 为所有子 agent 在 developer_instructions 顶部注入「调度权限硬约束」：禁止 spawn_agent（含同名递归派生）、禁止写 `.agent/task/` 非本 order 文件、禁止写 status.md 的 phase / current_step / last_volume_completed；工具范围声明改为提示性文本（Codex TOML 无工具白名单字段，文本级防线） |
| **源 agent 边界** | volume-planner 源文件 OOS 补「不调度其他 agent，不派生子 agent」；updater OOS 补「不写 status.md 的 phase 等字段」 |
| **顶层调度规则**（`templates/AGENTS.codex.md`） | 新项目 AGENTS.md 增加「调度边界（最高优先级）」：novel-agent 是唯一调度者，子 agent 禁止再派生（含同名递归） |
| **回归测试** | `test_platforms.py` 新增 3 个红绿用例（子 agent 注入硬约束、novel-agent 不注入、AGENTS.md 唯一调度者规则） |

---

## 兼容性

仅影响 Codex 平台生成的 agent 指令与项目 AGENTS.md 模板；claude / opencode / reasonix 平台产物无行为变化（源文件 OOS 增补为纯文本强化）。已有 Codex 项目执行 `sync-project.py --platform codex` 后 TOML 生效；AGENTS.md 调度边界段需重新 init 或手动补充。

---

## 验证方法

- `python tools/test_platforms.py`：94/94 通过
- `python -m py_compile tools/*.py`、`check-agents.py`、`check-conflicts.py` 通过
- 四平台重新 init：Codex 产物含硬约束，claude / opencode / reasonix 无 spawn_agent / 调度边界泄漏
