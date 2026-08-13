# v4.11.0 版本说明

> **关键词：** 平台适配层、三平台纯原生部署、Reasonix 完善

---

## 一句话

**把部署层做成平台感知：Claude Code / OpenCode / Reasonix 三个 coding agent 各有自己的 agent/skill/knowledge/memory 目录约定，init.py 和 sync-project.py 现在按平台部署，非 Claude 平台不再产生 `.claude/`。** Reasonix 项目从"skills 在 `.reasonix`、知识却割裂在 `.claude`"的状态，变成全部落在 `.reasonix/` 下。

---

## 这版做了什么

上一版加入了 Reasonix（DeepSeek 前缀缓存优化）支持，但只把 10 个 SKILL.md 部署到 `.reasonix/skills/`，knowledge/memory/agents 仍硬编码进 `.claude/`——Reasonix 用户初始化后看到一半框架在 `.reasonix/`、一半在 `.claude/`，像部署错了地方。根因是：**不同 coding agent 对 agent/skill/knowledge/memory 的目录约定不同，部署脚本没有做平台适配**。

这版引入共享平台适配层 `tools/platforms.py`，把部署全部改成平台感知。

---

## 具体改了什么

| 改动 | 说明 |
|------|------|
| **平台适配层 `tools/platforms.py`** | 新共享模块：平台配置表（claude→`.claude/`、opencode→`.opencode/`、reasonix→`.reasonix/`）+ 平台检测 + 引用改写 + reasonix skill 生成。加新平台只加一行配置 |
| **init.py 纯原生部署** | 新增 `--platform claude\|opencode\|reasonix`（`NOVEL_PLATFORM` 环境变量 / SKILL_HOME 路径识别兜底）；reasonix/opencode 初始化不再产生 `.claude/`；reasonix 不部署 agents（10 个 SKILL.md 即 agents） |
| **sync-project.py 平台感知** | 同步目标目录按平台走；reasonix 的 10 个 SKILL.md 是转换产物，同步时重新生成而非字节拷贝（变更检测靠源指纹） |
| **引用改写** | 部署内容里的 `.claude/knowledge/`、`.claude/memory/` 引用按平台改写（如 reasonix → `.reasonix/knowledge/`）；项目模板 CLAUDE.md/AGENTS.md、永久记忆占位一并改写 |
| **opencode 一致性** | opencode agent 的 frontmatter 转换（`tools:` → `permission:`）收进共享模块，init 和 sync 行为一致，sync 不再把转换结果回退成 Claude 格式 |
| **回归验证 `tools/test_platforms.py`** | 52 项断言：三平台布局、引用改写、reasonix 10 个 skill、sync 一致性、claude 字节保真 |

---

## 验证方法

平台适配是部署逻辑重构，最大的风险是改坏 Claude Code 的现有输出。验证刻意覆盖了三层：

1. **三平台 E2E**——`test_platforms.py` 分别 init claude/opencode/reasonix 到临时目录，断言目录布局（该有的有、不该有的没有）+ 引用改写正确
2. **claude 字节保真**——claude 平台 init 产物与改动前逐字节 diff 一致（唯一区别：不再生成多余的 `.reasonix/`）
3. **静态回归**——check-agents / check-conflicts 通过；`--platform` 非法值/缺值友好报错而非裸 traceback

---

## 兼容性保证

- ✅ 全新项目：`python tools/init.py <path> --genre <N> --platform <claude|opencode|reasonix>`，平台不指定也能靠 SKILL_HOME 路径识别兜底（默认 claude）
- ✅ 既有 Claude Code 项目：升级后行为不变（默认 claude 平台，输出逐字节一致）
- ⚠️ 已有 Reasonix 项目（v4.10 初始化）：knowledge/memory 仍留在旧 `.claude/`，需重跑新 init（`--platform reasonix`）补 `.reasonix/knowledge|memory`，手动删 `.claude/` 即完成纯原生迁移

---

## 适合视频呈现的亮点

1. **"部署层抽象"的工程范式** — 三平台目录约定抽象成配置表 + 检测 + 引用改写，加平台只加一行；"部署时转换、源文件保持 Claude Code 格式不动"的取舍贯穿始终。

2. **纯原生 vs 兼容的取舍** — 明确选择"非 Claude 平台不再产生 `.claude/`"，换取目录干净；为此入口检查（"确认平台部署目录已生成"）、项目模板、永久记忆全部平台化。

3. **回归先行的纪律** — 先写 52 项断言的验证脚本（红），再实现（绿）；三平台每个都验"该有的有、不该有的没有"，claude 逐字节保真。
