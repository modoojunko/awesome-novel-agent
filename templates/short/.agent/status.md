# 项目状态（短篇）

- **skill_version:** 4.24.1
- **length:** short
- **phase:** setup        # setup / planning / contract / writing / polishing / verifying / delivered
# phase 取值：setup（定情绪与定方向）/ planning（构思与排纲）/ contract（契约组装与审计）/ writing（分批写正文）/ polishing（去AI味与精修）/ verifying（兑现度核对与验收）/ delivered（已交付，可改稿或开下一篇）
- **current_story:**         # 当前篇目 slug（stories/ 下的目录名）
- **story_status:**          # 篇状态：empty / setting / outlined / contracted / drafted / polished / verified / delivered
- **last_quality_gap:**      # 最近一次字数降级记录（由 short-agent 从 writing-order 同步）
- **next_task:** 定情绪与定方向

## 当前篇进度

# 篇状态 = 最近已完成的阶段（子 agent order 完成后才推进）。
# 中断后重启，short-agent 读本节判断断点：判断用严格大于 `>`——状态 > 某阶段才算完成可跳步，
# 等值 = 该阶段未完成需重派。当前正在进行的阶段由 phase 表达，不入本节。
# 篇状态初始值 = 空（新篇开始重置为空）。
- **篇状态:**                  # setting / outline / contract-audit / batch-writing / polishing / verification / 全部完成
- **writing_order_id:**         # 写手执行的 order 唯一 ID，作审计参考
- **current_batch:**            # 当前批次（如 2-3 节），批间重注入契约硬规则区
