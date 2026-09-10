# short-write SOP — 正文分批写作

> short-writer 执行。按冻结契约分批产出正文，每批 2-3 节。

## Step 1: 准备

- 读 order：本批节号 + **重注入的契约硬规则区**（总指挥写入 order，未收到 → 退回 order，不自行回溯契约）
- 读 `outline.md` 本批各节行 + `manuscript.md` 尾部 300-500 字（衔接用）
- 读通用底座 + 格式规范 + 去AI口径

## Step 2: 写前两问（每节）

1. 本场景目标情绪是什么？
2. 契约中对应的技法条目是哪条、用在哪个段落？

任一答不出 → 回读契约，不硬写。

## Step 3: 逐节写作

- **三维度揉进**：发生 / 感知 / 反应织进同一段连续正文，禁止拆三段堆叠；按新动作 / 物件 / 信息 / 对话 / 视线断段
- **场景晚进早出**：第一句已处于冲突或张力之中；起床 / 赶路 / 寒暄 / 布置不展开
- **情绪直写 + 具体承接**：情绪词后接本场景特有的动作或物件；一个情绪写一次
- **所有格清除**：不写「我的心 / 我的灵魂 / 我的眼眶」；不写「我知道 / 我感到 / 我看到自己」引导小句
- **对话四功能**：每句至少完成推动情节 / 揭示性格 / 制造冲突 / 埋设伏笔之一（权力博弈与潜台词手法见 `.claude/knowledge/short-craft/dialogue-mastery.md`；钩子类型库 `.claude/knowledge/short-craft/hooks-chapter.md` / `.claude/knowledge/short-craft/hooks-paragraph.md` / 悬念设计 `.claude/knowledge/short-craft/hooks-suspense.md`；跨题材技法 `.claude/knowledge/short-craft/genre-writing-techniques.md`）
- **反转节**：一节内完成揭示；揭示时用回看 / 独白 / 物证**瞬时串线**（把前文线索一次性带回读者眼前）；冲击强度高于此前所有节
- **贯穿道具**：第三次出现（揭真相）在反转或结尾段
- **节尾必留钩**；节内情绪强度按大纲行推进

## Step 4: 机器验证（每批写完）

```bash
for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
"$PYBIN" -c "from pathlib import Path; import re; t=Path('stories/{slug}/manuscript.md').read_text(encoding='utf-8'); import sys; print('总字数', len(re.sub(r'\s','',t)))"
```

- **每节字数**：≥800（高信息密度题材 ≥500）；不足 = 该节未完成 → 补子事件 / 对话 / 回忆闪回 / 环境物件（经动作带出），禁止灌水，禁止「加感知层」式叠加
- **总字数**：全部完成后 ≥8000
- **节数守恒**：正文节数 = 大纲规划节数；发现某节不该独立存在 → 退回大纲调整，不在写作时偷减
- 禁模型估算字数；禁 `wc -c`（字节数）；无 Bash/Python 权限时声明「未完成机器字数验证」并按行数速算（每行约 15 字）

## Step 5: 完成门槛（全篇写完，未过不得进精修）

- [ ] 总字数 ≥8000（机器实测）
- [ ] 每节字数达标
- [ ] 节数 = 大纲节数
- [ ] 格式自检：小节标记统一 / 段间单换行 / 无缩进 / 无 Markdown / 对话独立成行 / 引号平台风格 / 禁用标点清零 / 无元信息词
- [ ] 写时自查：AI 套话清零 / 程度副词每千字 ≤3 / 比喻不成片 / 自检记录不落盘进正文

## 约束

- 规则冲突按契约冲突裁定表执行，不自行裁定
- 超出契约的添加用 `[AI addition: ...]` 标注
- 中断恢复：读 manuscript 已写小节数，从断节续写
