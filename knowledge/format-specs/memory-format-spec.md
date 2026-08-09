# 写作记忆格式规范

> 写作记忆系统：`memory/` 下为动态记忆（按阶段分 4 个文件），`knowledge/` 下为永久记忆（晋升后的高频条目）。每个条目记录作者在写作过程中提供的正反反馈，供后续流程参考。

---

## 一、文件结构

```
<平台目录>/
├── memory/                          # 动态记忆（各环节实时记录）
│   ├── volume-memory.md             # 卷纲环节记忆
│   ├── chapter-memory.md            # 章纲环节记忆
│   ├── prompt-memory.md             # 提示词环节记忆
│   └── writing-memory.md            # 正文写作环节记忆
│
└── knowledge/
    └── permanent-memory.md          # 永久记忆（从 memory/ 晋升的高频条目）
```

> 平台目录由 init.py 按 `--platform` 决定：Claude Code → `.claude/`、OpenCode → `.opencode/`、Reasonix → `.reasonix/`、Codex → `.codex/`。

## 二、文件头

每个文件以元信息头部开头：

```markdown
# {阶段}写作记忆

> {用途描述}

**相关 Agent:** {agent 列表}
**相关 Skill:** {skill 列表}

---

## 条目列表
```

## 三、条目格式

每条记忆包含以下字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| **阶段** | 是 | 来源阶段：卷纲 / 章纲 / 提示词 / 正文 |
| **类型** | 是 | 正面案例 / 反面案例 / 规则 |
| **领域** | 是 | 该阶段下的细分领域（见下文各文件 §四） |
| **原文** | 是 | 作者反馈原文摘要，保留关键语句 |
| **结论** | 是 | 提炼为可复用的规则或操作指引 |
| **场景** | 是 | 什么情况下这条规则适用 |
| **来源** | 是 | 触发本次记录的 Agent |
| **日期** | 是 | YYYY-MM-DD |

完整写法：

```markdown
### {序号}. {类型}：{一句话摘要}

- **阶段:** {阶段名}
- **类型:** {正面案例|反面案例|规则}
- **领域:** {领域}
- **原文:** {作者反馈原文摘要}
- **结论:** {提炼的规则}
- **场景:** {适用条件}
- **来源:** {agent 名}
- **日期:** {YYYY-MM-DD}
- **use_count:** {引用次数，晋升用}
- **last_used:** {YYYY-MM-DD，最近引用日期}
```

> `use_count` 和 `last_used` 用于追踪条目使用频率，由 agent 在引用时递增，updater 在兜底时据此执行晋升/降级。

## 四、条目生命周期

```
memory/ 条目 ──use_count >= 4──→ knowledge/permanent-memory.md
permanent-memory.md 条目 ──连 3 次 sweep 未使用──→ 标记待移除 → 作者确认后删除
```

### 4.1 晋升条件（memory → permanent）

| 条件 | 说明 |
|------|------|
| use_count >= 4 | 该条记忆已被不同 agent/环节引用 4 次以上 |
| 结论清晰可复用 | 晋升前确认结论是通用规则而非一次性场景 |
| 无冲突 | 与已有永久记忆无矛盾 |

晋升操作：从 `memory/*.md` 移除该条目，追加到 `knowledge/permanent-memory.md`，保留所有原始字段 + `[promoted YYYY-MM-DD]` 标记。

### 4.2 降级条件（permanent → 移除）

| 条件 | 说明 |
|------|------|
| 连续 3 次 sweep 中 `last_used` 未更新 | 3 个写作周期内无任何 agent 引用该条目 |
| 作者确认 | 移除前询问作者确认 |

降级操作：展示给作者确认后删除条目。如果作者认为仍有价值，重置 `skip_count = 0` 保留。

### 4.3 使用追踪规则

- agent 在引用某条记忆并应用到产出后，递增该条目的 `use_count` 并更新 `last_used`
- 同一写作环节内多次引用同一条目只计 1 次（防止同环节刷计数）
- updater sweep 时检查 `last_used`，跨环节未更新则累加 `skip_count`
