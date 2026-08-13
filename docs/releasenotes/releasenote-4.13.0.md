# v4.13.0 版本说明

> **关键词：** style-distiller 双态重构、验收/渲染正确性、init/sync 回归修复、校验闸门补齐

---

## 一句话

**style-distiller 完成 LLM 双态重构（未蒸馏卡走正文定性注入 / 蒸馏卡走案例 2 量化渲染），并基于全量 code review（11 路扫描、56 条）修复验收误判链、渲染伪数据、新项目/存量项目回归与校验闸门失效；同批收敛契约文档矛盾（认知动词 ≤2次/章、字数 ±10% 单源、8 段场景卡、T1 词表）。**

---

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **style-distiller 双态** | confidence=0 → 正文定性四字段注入（现状不变）；confidence>0 → 案例 2 渲染（量化节 + 声音层透传 + §6.0b 正文回退）；决策 A 单位统一 0-100 百分数 |
| **验收正确性**（`style_verify.py`） | 字符串布尔收敛补「；」「违反了」白名单；数值收敛拒绝 bool（`True` 不再当 1 条违反）；pick_best 不再把 `'3.0'` 当 0 选中最差轮 |
| **渲染正确性**（`style_render.py`） | 缺键/越界值不再伪造「0 字/0%」假实测（跳过该行）；区间 half-up 舍入（5/15/25 卡值修复）；few_shot 按 type 分组渲染、缺键标「（未填写）」；conf=0 分支补测试 |
| **init/sync 回归** | seed 守卫三态（裸模板预填/seed 卡就地补齐/作者卡保留），不再带 `{role}` 占位符出货、不再整卡覆盖作者编辑；sync 缺卡主卡写「（待设定）」；脚手架 CLAUDE.md/AGENTS.md/skill_version 纳入指纹同步 |
| **校验闸门**（`check-agents.py`） | `--project` 校验运行态卡；密度字段/负桶/重复键/rhythm 缺键/override 值校验补齐；BOM 口径对齐 init |
| **契约收敛** | 认知动词「无例外」→「关键情绪节点 ≤2次/章」；字数 80%/±10% 统一为 ±10% 单源；chapter-outline 8 段场景卡；「落点」字段指向实际字段 emotional_hook；T1 词表/默默微微阈值对齐 common-rules |
| **单源化**（`style_common.py`） | frontmatter 解析（坏 split 退役）/SCENE_INJECTION/决策 A 单位/UTF-8 收敛为单一共享实现；9 维 schema 自模板读取；删幽灵字段 direct_address_freq_per_100 与 deploy_memory 死桩 |
| **治理** | VERSION/releasenote 对齐 4.13.0；AGENTS.md 工具清单补全 8 个脚本；README 结构树/ARCHITECTURE/install.sh 注释修正 |

---

## 兼容性

- 存量项目：`sync-project.py` 会将 CLAUDE.md/AGENTS.md/skill_version 刷新到当前版本；写作风格卡为不覆盖策略（仅补缺卡，已有卡不更新）。
- 旧 jieba 蒸馏卡（confidence>0 无声音层）：渲染走 §6.0b 正文回退，不破坏。
- 已安装旧版 skill 的用户需要重跑 `install.sh` 才能拿到修复后的 `tools/`（`tools/` 不参与项目级同步）。

---

## 验证方法

- `python tools/test_style_rules.py`：125/125 通过（含收敛/渲染/回退/分组用例）
- `python tools/test_style_distill.py`：82/82 通过
- `python tools/test_platforms.py`：118/118 通过（含 seed 守卫/脚手架同步 E2E）
- `python tools/check-agents.py` / `check-conflicts.py`：全绿
