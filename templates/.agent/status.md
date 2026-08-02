# 项目状态

- **skill_version:** 4.0
- **phase:** setup
- **current_step:** setting        # volume-planning / chapter-planning / prompt-crafting / writing / anti-ai / reviewing / archiving
# phase 取值：setup / outline / draft / anti-ai / review / archive / finished
# last_volume_completed 与 phase: finished 由 novel-agent 写（卷完成判定），updater 不写完成位
- **current_volume:**
- **current_chapter:**
- **last_archived:**
- **last_quality_gap:**        # 最近一次字数降级记录（由 novel-agent 从 writing-order 同步）
- **next_task:** 填写基础设定

## 当前章节进度

# 写新章节流程的阶段级断点信号（由 novel-agent 每 dispatch 前更新）。
# 中断后重启动，novel-agent 用「产出文件存在性」从最近的断点续跑，不整章重来。
- **章节状态:** setting            # chapter-planning / prompt-crafting / writing / anti-ai / reviewing / archiving / 全部完成
- **writing_order_id:**           # writer 执行的 order 唯一 ID，用于检测 writer 是否中断
- **writing_partial:**            # 中断时 writer 的部分草稿路径（archives/*.draft.partial.md），无则空
