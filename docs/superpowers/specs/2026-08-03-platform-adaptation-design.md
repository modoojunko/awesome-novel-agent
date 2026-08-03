# 平台适配层设计 — init.py / sync-project.py 按 coding agent 目录约定部署

> 日期：2026-08-03
> 状态：设计已确认，待实现
> 触发：#81-8 reasonix 支持落地后，reasonix 项目初始化发现 knowledge/memory 仍落在 `.claude/`

---

## 一、问题

用户在 Reasonix 里安装 awesome-novel，初始化小说项目（`D:\novels\new`）后：
- `.reasonix/skills/` ✅ 生成了 10 个 SKILL.md（writer / novel-agent / …）
- `.claude/agents/`、`.claude/knowledge/`、`.claude/memory/` ❌ 仍按 Claude Code 约定生成

用户只用 Reasonix，期望 knowledge/memory 落在 `.reasonix/` 下。深层原因是：**不同 coding agent 对 agent / skill / knowledge / memory 的目录约定不同，部署脚本没有做平台适配**。

## 二、根因

`tools/init.py` 和 `tools/sync-project.py` 把 agents / knowledge / memory 的部署路径**硬编码为 `.claude/`**，只对两处做了平台特判：

| 位置 | 现在的特判 | 漏掉的部分 |
|------|-----------|-----------|
| init.py `deploy_agents` | `"opencode" in SKILL_HOME` → `.opencode/agents` | reasonix 不需要 agents（10 个 skill 即 agent） |
| init.py `deploy_reasonix` | skills → `.reasonix/skills/`（已转换） | 生成的 SKILL.md 内联了源文件里的 `.claude/knowledge/`、`.claude/memory/` 引用 |
| init.py `deploy_knowledge` / `init_memory_files` / `write_memory_index` / `seed_settings_from_genre` / `create_skeleton` | 无 | 全部硬编码 `.claude/` |
| sync-project.py | `IS_OPENCODE` → agents 目标目录 | skills/knowledge 硬编码 `.claude/`；完全没有 reasonix 分支 |

源文件 `agents/*.md`、`skills/*.md` 里有数十处 `.claude/knowledge/`、`.claude/memory/` 路径引用，部署到非 claude 平台时必须改写。

## 三、目标

1. 三个已有平台抽象成配置表，可扩展：
   - **Claude Code** → `.claude/`（agents / knowledge / memory / skills）
   - **OpenCode** → `.opencode/`（agents / knowledge / memory / skills）
   - **Reasonix** → `.reasonix/`（skills 即 agents；knowledge / memory）
2. **纯原生**：非 claude 平台初始化后不产生 `.claude/`。
3. 平台检测：`--platform` / `NOVEL_PLATFORM` 显式指定优先，否则按 `SKILL_HOME` 路径关键词识别。
4. 源文件保持 Claude Code 格式不动，**部署时转换 + 改写引用**（沿用 design doc「部署时转换」原则）。

## 四、`tools/platforms.py` — 新共享模块

> 注：模块名 `platforms`（复数）避开标准库 `platform` 撞名，防止后续 `import platform` 拿到本模块。

### 4.1 Platform 配置表

```python
@dataclass(frozen=True)
class Platform:
    key: str              # "claude" | "opencode" | "reasonix"
    label: str            # 显示名
    root: str             # ".claude" | ".opencode" | ".reasonix"
    agents: str | None    # "agents"；reasonix = None（agents 即 skills）
    skills: str | None    # "skills"；sync 时用
    knowledge: str        # "knowledge"
    memory: str           # "memory"
    detect_keywords: tuple  # ("reasonix",) / ("opencode",) / ()

PLATFORMS = {
    "claude":   Platform("claude", "Claude Code", ".claude",   agents="agents", skills="skills", knowledge="knowledge", memory="memory", detect_keywords=()),
    "opencode": Platform("opencode", "OpenCode",  ".opencode", agents="agents", skills="skills", knowledge="knowledge", memory="memory", detect_keywords=("opencode",)),
    "reasonix": Platform("reasonix", "Reasonix",  ".reasonix", agents=None,     skills="skills", knowledge="knowledge", memory="memory", detect_keywords=("reasonix",)),
}
```

派生路径 helper（返回 `Path`）：
- `platform.knowledge_dir(project)` → `project / root / knowledge`
- `platform.memory_dir(project)` → `project / root / memory`
- `platform.agents_dir(project)` → None（reasonix）或 `project / root / agents`
- `platform.skills_dir(project)` → `project / root / skills`

### 4.2 平台检测

```python
def detect_platform(skill_home: Path, override: str | None = None) -> Platform:
    if override:
        return PLATFORMS[override]      # 非法值报错退出
    p = str(skill_home).lower()
    if "reasonix" in p:
        return PLATFORMS["reasonix"]
    if "opencode" in p:
        return PLATFORMS["opencode"]
    return PLATFORMS["claude"]
```

优先级：`--platform` 参数 > `NOVEL_PLATFORM` 环境变量 > SKILL_HOME 路径识别 > 默认 claude。
init.py / sync-project.py 的 CLI 都加 `--platform {claude|opencode|reasonix}`。

### 4.3 引用改写

```python
def rewrite_refs(text: str, platform: Platform) -> str:
    """部署内容里的 Claude Code 路径引用 → 平台路径。仅改写 knowledge/memory。"""
    if platform.key == "claude":
        return text
    text = text.replace(".claude/knowledge/", f"{platform.root}/knowledge/")
    text = text.replace(".claude/memory/",    f"{platform.root}/memory/")
    return text
```

- **只改 `.claude/knowledge/` 和 `.claude/memory/` 两类引用**。
- `.claude/agents/` 不参与改写：部署出的内容（agents / reasonix SKILL.md）没有指向 `.claude/agents/` 的路径引用，只有 SKILL.md 源里的说明性措辞（见 §七）。
- claude 平台原样返回（零改动，回归安全）。

### 4.4 SKILL_HOME 解析 + reasonix 转换逻辑迁入

从 init.py 迁入（单一事实来源，sync-project 复用）：
- `resolve_skill_home()`（`__file__` 推导 + `NOVEL_SKILL_HOME` 兜底）
- `_convert_to_reasonix()`、`_convert_inline_skill()`、`_REASONIX_TOOL_MAP`
- `deploy_reasonix_skills(project, skill_home)` → 生成 `.reasonix/skills/<name>/SKILL.md`（10 个），改写 `.claude/knowledge|memory` 引用

签名统一收 SKILL_HOME 作参数，不依赖模块全局状态。

## 五、`tools/init.py` 改动

| 步骤 | 现在 | 改后 |
|------|------|------|
| CLI | `[project-path] [--genre N]` | 加 `--platform {claude\|opencode\|reasonix}`；`NOVEL_PLATFORM` 环境变量兜底 |
| main | 无条件 deploy 全部 | `platform = detect_platform(SKILL_HOME, override)`，各部署函数收 platform 参数 |
| create_skeleton | 硬编码 `.claude/memory`、`.claude/knowledge` | `platform.memory_dir` / `platform.knowledge_dir` |
| deploy_agents | `.claude/agents`（opencode 特判） | `platform.agents_dir`；**reasonix 跳过**（不产生 `.claude/`） |
| deploy_reasonix | 无条件生成 `.reasonix/skills/` | **仅 platform.key == "reasonix" 时运行**（claude/opencode 不产生 `.reasonix/`）；改写 `.claude/knowledge\|memory` 引用（§4.3）；novel-agent 的 Reasonix 调度适配段不变 |
| deploy_knowledge | `.claude/knowledge` | `platform.knowledge_dir` |
| write_memory_index / init_memory_files | `.claude/memory` | `platform.memory_dir` |
| seed_settings_from_genre | 读 `.claude/knowledge/genre-example.md` | `platform.knowledge_dir / "genre-example.md"` |
| 结束提示 | 硬编码 Claude Code 措辞 | 按平台输出（claude → `@novel-agent`；reasonix → `reasonix code .` 后调 `@novel-agent`） |

reasonix / opencode 纯原生结果：
```
<project>/.reasonix/            # 或 .opencode/
├── skills/                      # reasonix：10 个 SKILL.md（agents 即 skills）
├── knowledge/                   # 反 AI / 题材 / craft / format-specs（引用已改写）
└── memory/                      # MEMORY.md + 4 个写作记忆文件
```
不再生成 `.claude/`。

## 六、`tools/sync-project.py` 改动

- 顶部平台检测同 init.py（`--platform` / `NOVEL_PLATFORM` / 路径识别）。
- `AGENT_TARGET`、`sync_agents` → `platform.agents_dir`；reasonix 跳过 agents。
- `sync_skills` → `platform.skills_dir`：
  - claude / opencode：原样拷贝 `skills/*.md`（现状）。
  - **reasonix：重新生成 10 个 SKILL.md**（`deploy_reasonix_skills`），因为它们是转换产物，不是源文件原样。
- `sync_knowledge` → `platform.knowledge_dir`（平铺约定不变）。
- `find_changes` 的比对目录随平台走。**reasonix 的 skills 例外**：10 个 SKILL.md 是转换产物，源文件名/内容与部署产物不同，不能字节比对——reasonix 下 `find_changes` 只枚举 knowledge（agents 无、skills 派生），skills 的变更检测靠源指纹（`compute_fingerprint` 对源目录 hash，源变了指纹就变），sync 时无条件重新生成。
- 指纹 `compute_fingerprint` 仍对源目录 hash（与平台无关），保持不变。

## 七、`SKILL.md` 源 — 检查与措辞平台化

入口 skill 的 `.claude/` 相关措辞平台化，保证 reasonix 下 init 后的检查能通过：

- 「部署 agent 定义到 `.claude/agents/`」→「部署 agent/skill 到当前平台约定目录（Claude Code → `.claude/agents`；OpenCode → `.opencode/agents`；Reasonix → `.reasonix/skills` 由 init 生成）」
- 「确认 `.agent/status.md` 和 `.claude/agents/` 已生成」→「确认 `.agent/status.md` 与平台部署目录已生成」
- 「各 agent 定义在 `.opencode/agents/` 或 `.claude/agents/`」等 10 处 `.claude/` 措辞统一改为平台相关描述

只改说明性措辞，不改 agent 源文件路径引用（那些在部署时改写）。

## 八、边界与取舍

| 场景 | 处理 |
|------|------|
| 从 git 克隆直接跑 init.py（路径无平台关键词） | 默认 claude；用 `--platform reasonix` 显式指定 |
| reasonix 下 agents | 不部署 `.claude/agents/`（10 个 skill 即 agents），入口检查改查 `.reasonix/skills/` |
| 已在 `.claude/` 有旧数据的项目 | 不迁移旧数据；后续可手动移动或重跑 sync |
| `.claude/settings.local.json` 等 Claude Code 运行时文件 | 不在部署范围，不触碰 |
| 改写命中风险 | 仅替换 `.claude/knowledge/`、`.claude/memory/` 精确前缀，不影响其他 `.claude/` 语义 |

## 九、验证计划

1. **三平台 init 布局**：`--platform claude|opencode|reasonix` 各 init 到临时目录，核对：
   - claude：`.claude/agents|knowledge|memory` 齐全，无 `.reasonix/`
   - opencode：`.opencode/agents|knowledge|memory`，无 `.claude/`
   - reasonix：`.reasonix/skills/`（10 个）+ `knowledge` + `memory`，无 `.claude/`
2. **引用改写**：reasonix 生成的 SKILL.md 里 `.claude/knowledge/` → `.reasonix/knowledge/`、`.claude/memory/` → `.reasonix/memory/`，无残留 `.claude/` 引用
3. **sync 回归**：三个平台 `sync-project.py --check` / 同步后布局正确；reasonix 下 10 个 SKILL.md 被重新生成
4. **框架回归**：`tools/check-agents.py`、`tools/check-conflicts.py` 通过；claude 平台 init 结果与改动前 diff 一致（改写零影响）

## 十、范围外

- 不新增平台（Gemini CLI / Codex / Cursor 等）——只抽象，以后加配置一行。
- 不改 `install.sh`（reasonix 走项目级部署，与设计文档一致）。
- 不做旧项目 `.claude/` → `.reasonix/` 的自动迁移。
