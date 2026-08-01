# updater-setting-sop

规划时设定变更的标准操作流程。

## 一、输入检查

| 检查项 | 通过条件 | 失败处理 |
|--------|---------|---------|
| `.agent/task/setting-update-order.md` | 存在 | 报错给 novel-agent |
| order 中指定的目标文件 | 存在或可创建 | 报路径错误 |

## 二、Order 解析

`setting-update-order.md` 结构：

```yaml
type: character | world | timeline | genre | style | memory
action: create | modify | delete
target: settings/character-setting/{id}.md  # 或其他文件路径
content: |
  # 要写入/追加的内容（结构化）
reason: 作者/卷纲/章纲要求
```

## 三、设定更新流程

### 场景 A: 新增角色

1. 检查 `settings/character-setting/` 下 ID 是否唯一
2. 如冲突 → 报作者确认是否覆盖
3. 创建角色文件, 使用标准模板：

   ```markdown
   # {角色名}

   ## 基础信息
   - **ID:** {唯一标识}
   - **登场卷/章:** vol-{N}-ch-{M}
   - **阵营:** {阵营}

   ## 角色定位
   - **核心动机:** ...
   - **与主角关系:** ...

   ## 能力/特质
   - ...

   ## 出场记录
   - vol-{N}-ch-{M}: 首次出场
   ```

4. 如果该角色与其他角色有关联 → 同步追加关系到相关角色文件

### 场景 B: 修改世界观/题材/风格

1. 读现有文件，确认修改不矛盾
2. 如果新内容与已有内容冲突：
   - 轻微不一致 → 追加说明，标注 `[updated]`
   - 原则性矛盾 → STOP，展示冲突点给作者
3. 无冲突 → 追加或替换指定段落

### 场景 C: 追加时间线事件

1. 读 `settings/timeline.md` 现有内容
2. 按时间顺序插入新事件
3. 如果事件涉及角色 → 同步到角色文件标记

### 场景 D: 直接修改记忆

1. 读 `.claude/memory/` 目标文件
2. 追加内容标注 `[writer-preference]`
3. 不走 diff（作者指定的规则直接生效）

### 场景 E: 删除设定

1. 确认删除范围
2. 检查是否有其他文件引用被删除内容
3. 有关联依赖 → 展示引用链给作者确认
4. 无依赖或已确认 → 执行删除

## 四、一致性检查（通用）

任何设定变更后检查：

- [ ] 新内容不与现有 `settings/` 下文件矛盾
- [ ] 新角色 ID 不与已有角色重复
- [ ] 世界观修改不导致已写章节产生逻辑矛盾（标注可能受影响的章节）
- [ ] memory 修改不混用 `[community-defaults]` 和 `[writer-preference]` 标记

## 五、验收清单

- [ ] 变更已按 order 要求执行
- [ ] 新创建的文件格式正确
- [ ] 无未解决的冲突（所有冲突已展示给作者）
- [ ] 有关联更新（如新角色→关系同步）已执行
- [ ] order 已标记 DONE
