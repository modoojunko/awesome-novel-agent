## 1. detect-loop skill

- [ ] 1.1 写 `skills/detect-loop.md`：触发条件、适配器接口（稿件路径入/逐片结果文件出/阈值参数）、最小干预修复纪律、锁版与沉淀流程、合规声明（验证：对照 spec 逐条核对；话术过 author-communication 对照表）
- [ ] 1.2 附结果文件格式示例（纯格式，不含真实平台协议）（验证：示例可被流程直接引用）
- [ ] 1.3 `python tools/check-agents.py`（验证：exit 0）

## 2. 调度接入

- [ ] 2.1 `skills/novel-dispatch.md` 调度表加 detect-loop 可选 phase 行 + 作者触发语义 + 断点续跑备注（验证：与既有 phase 行格式一致）
- [ ] 2.2 `agents/novel-agent.md` THINK 树补 detect-loop 分支（验证：`check-agents.py` exit 0；与 dispatch 表无冲突）

## 3. 收尾与发版

- [ ] 3.1 全量检查：`check-agents.py` + `check-conflicts.py` + `py_compile` + `test_platforms.py`（验证：全绿）
- [ ] 3.2 真机演练一次：本地送检工具（用户自备）→ 走完 修最高窗→锁版→沉淀 全流程（验证：战役记录新增一轮、回归串入库、check-chapter 复跑 exit 0）
- [ ] 3.3 发版 `chore: bump version to v4.24.0`，更新 `VERSION` 与 `docs/releasenotes/releasenote-4.24.0.md`（验证：`check-version.py` 通过）
