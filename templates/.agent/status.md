# 项目状态

- **skill_version:** 4.18.0
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

# 写新章节流程的阶段级断点信号。章节状态 = **最近已完成的阶段**（子 agent order DONE 后才推进）。
# 中断后重启动，novel-agent 读本节判断断点：判断用严格大于 `>`——状态 > 某阶段才算完成可跳步，
# 等值 = 该阶段未完成需重派。当前正在进行的阶段由 current_step 表达，不入本节。
# 章节状态初始值 = 空（新卷/新章开始重置为空，volume-planning 之前）。
- **章节状态:**                  # volume-planning / chapter-planning / prompt-crafting / writing / anti-ai / reviewing / archiving / 全部完成
- **writing_order_id:**           # writer 执行的 order 唯一 ID，作审计参考；partial 位置以 writing-order.md 的 partial_path 为准
