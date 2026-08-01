# {type}-order

status: pending

inputs:
  - {输入文件路径}

outputs:
  - {输出目标路径}

---

> 本文件是 order 模板。novel-agent 写 order 时用本结构；子 agent 完成后**用 Write 覆盖 `status: pending` 为 `status: DONE`**，不要删除本文件。
> 完成信号 = order 存在 且 `status: DONE` 且 outputs 全部存在非空。
