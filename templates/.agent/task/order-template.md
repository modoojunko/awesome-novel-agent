# {type}-order

status: pending

inputs:
  - {输入文件路径}

outputs:
  - {输出目标路径}

resume_from: {writer 中断恢复时填 partial 文件路径；其他场景留空}

---

> 本文件是 order 模板。novel-agent 写 order 时用本结构；子 agent 完成后**用 Write 覆盖 `status: pending` 为 `status: DONE`**，不要删除本文件。
> 完成信号 = order 存在 且 `status: DONE` 且 outputs 全部存在非空。
> `resume_from` 可选：writer 是唯一长输出阶段，中断后重派时填 `archives/*.draft.partial.md` 路径，writer 从该 partial 续写不重头；其他阶段留空。
