# v4.19.0 版本说明

> **关键词：** 机器初筛 —— check-prose.py 挂入 anti-ai 流程，确定性脚本进 Phase 2 初筛与 Phase 4 复跑

---

## 一句话

v4.18.0 引入的正文检查脚本 `check-prose.py` 从「独立工具」正式挂进反 AI 管线（#117，跟踪 issue #116）：**初始化自动部署到六平台项目、Phase 2 量化前先跑脚本机器初筛、Phase 4 完稿后复跑核验**——正则和统计抓模型肉眼会漏会数错的硬指标，脚本只报告不改正文，跑不了就降级模型肉眼（非阻塞）。

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **六平台自动部署** | `init.py` 新增 `deploy_tools()`：初始化把脚本部署到 `<平台根>/tools/check-prose.py`（claude/opencode/reasonix/codex/zcode/dsh）；`sync-project.py` 新增 `sync_tools()` 同步，且**脚本本体纳入升级指纹**——不纳入的话存量项目会因指纹未变被 sync 短路，永远拿不到脚本 |
| **Phase 2 机器初筛**（skills/anti-ai.md） | 量化打分前先跑脚本：「需要修改」（硬失败，退出码 1：硬停词/黑话/模型路标/翻案句）并入 Gate A/B 命中清单进 Phase 3；「需要人工判断」（警告：语义枢轴句式、句长节奏、短段连击、开头重复、比喻扎堆、连词密度）只作「先救人再清句子」的重点段候选，不直接判违规 |
| **Phase 4 机器复跑核验** | 修改完成后取 `.anti-ai.md` 正文节（不含验收报告节，报告引用的反例会误判）复跑脚本，「需要修改」清零才通过；误杀防护豁免同样适用（命中在豁免列表标 `[SKIP: 误杀防护]`）；修改统计新增「脚本核验」行、验收清单新增对应行 |
| **降级铁律** | 脚本只报告、不改正文；阈值以 anti-ai.md 为准，脚本警告永不升级为硬 Gate；脚本缺失/无 python（Windows 先试 `python`/`py`）/无法执行 shell → 降级模型肉眼，报告标注「未跑脚本核验」（非阻塞） |
| **工程修缮** | agents/anti-ai.md 的 Input Sources 补脚本条目、流程行同步；ARCHITECTURE.md 管线图补机器初筛/复跑环节；AGENTS.md 工具清单措辞更新（不再是"独立工具非流水线环节"） |

---

## 兼容性

- 纯新增部署物 + 指令文本改动，无 schema/流程结构变更；新项目初始化直接带脚本。
- **存量项目**：跑 `python tools/sync-project.py <项目路径>` 即部署脚本（脚本纳入指纹，升级必被检测到）；skill_version 将更新为 4.19.0。
- 无 python 或禁 shell 的运行环境自动降级为模型肉眼，报告可见「未跑脚本核验」标注，不阻塞流程。
- anti-ai agent 新增运行 shell 命令的行为（跑 python 脚本）；其 `tools:` 白名单本就含 Bash，无需配置。
- 脚本仅用标准库，Windows 用 `python` 或 `py` 运行（skill 内已注记）。

---

## 验证方法

- 先红后绿：`test_platforms.py` 新增 8 项断言（六平台部署 + 内容与源一致 + sync 恢复 + 指纹感知），实现前 8 FAIL、实现后 **213 通过 0 失败**
- 静态检查全绿：check-agents / check-conflicts / check-version / check-yaml / check-python / py_compile
- E2E 实测：opencode/zcode/codex 产物中脚本引用均自动改写为平台前缀；部署出的脚本对「值得注意的是」实测退出码 1 并输出「需要修改」
- review-agent 评审闭环：2 个 P3（ARCHITECTURE 管线图滞后、Windows python3 适配）合并前修复（f177516）
- 待作者侧：任一 AI 终端实测一章（重点验证降级路径：删掉项目内脚本后跑一章，报告应标注「未跑脚本核验」而非报错）
