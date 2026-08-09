<p align="center">
  <strong>awesome-novel</strong><br>
  <em>和 AI 一起写小说 —— 支持 Claude Code / OpenCode / Reasonix / Codex</em>
</p>

<p align="center">
  <a href="README-en.md"><img src="https://img.shields.io/badge/English-README-blue?style=flat-square" alt="English README"></a>
  <a href="https://docs.anthropic.com/en/docs/claude-code/overview"><img src="https://img.shields.io/badge/Claude%20Code-%E2%9C%93%20%E6%94%AF%E6%8C%81-6B46C1?style=flat-square" alt="Claude Code"></a>
  <a href="#opencode"><img src="https://img.shields.io/badge/OpenCode-%E2%9C%93%20%E6%94%AF%E6%8C%81-4A90D9?style=flat-square" alt="OpenCode"></a>
  <a href="#reasonix-集成"><img src="https://img.shields.io/badge/Reasonix-%E2%9C%93%20%E6%94%AF%E6%8C%81-16A34A?style=flat-square" alt="Reasonix"></a>
  <a href="#codex-集成"><img src="https://img.shields.io/badge/Codex-%E2%9C%93%20%E6%94%AF%E6%8C%81-10A37F?style=flat-square" alt="Codex"></a>
  <br>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL%203.0-blue?style=flat-square" alt="GPL 3.0"></a>
  <br>
  <a href="#加入交流群"><img src="https://img.shields.io/badge/QQ%E4%BA%A4%E6%B5%81%E7%BE%A4-1006050538-12B7F5?style=flat-square" alt="QQ交流群 1006050538"></a>
</p>

> **个人使用免费** — 本 Skill 对个人用户完全免费。<br>
> **商业使用** — 请联系作者获取授权。

让 AI 成为你的小说创作搭档,从世界观搭建到角色塑造，从章节规划到正文写作，一步步陪你完成整部小说。

## 加入交流群

遇到问题、交流写作心得、催更或提建议，欢迎进群，作者常在。

> **QQ 交流群 2群：`1006050538`**
> 进群后可直接提问，或和大伙儿分享你写的小说。

<!-- 开篇示例：修仙小说节选 + 配图 -->
<div align="center">

<table><tr>
<td width="200" valign="top" style="border:0;padding:8px">
  <img src="reference/images/我靠炼丹逆天改命.png" width="200" alt="修仙小说《我靠炼丹逆天改命》" style="border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.3)">
</td>
<td valign="middle" align="left" style="border:0;padding:8px">
<blockquote style="border-left:3px solid #d4875e;margin:0;padding:8px 20px;text-align:left;max-width:440px;font-size:15px;line-height:1.8;color:#e8d5c0">
<p style="margin:4px 0">
他放下草药，站起来，朝着王虎离开的方向追了几步。王虎听到脚步声回头，还没来得及说话，叶秋的拳头已经到了——一拳结结实实砸在他脸上。
</p>
<p style="margin:4px 0">
王虎整个人往后退了两步，捂着脸，嘴边的笑僵在半道上。
</p>
<p style="margin:4px 0">
"你——"
</p>
<p style="margin:4px 0">
叶秋没让他把话说完。第二拳挥出去的时候，旁边那两个跟班已经反应过来了。一左一右扑上来抱住他的胳膊，把他往后拖。王虎趁机一脚踹在他肚子上，叶秋弓着腰往后退了两步，膝盖一软跪在地上。
</p>
<p style="margin:8px 0 0 0;font-size:13px;color:#94a3b8">—— 摘自《我靠炼丹逆天改命》第一卷第一章 · 由 awesome-novel 生成</p>
</blockquote>
</td>
</tr></table>

</div>

<video src="https://raw.githubusercontent.com/modoojunko/awesome-novel-skill/main/reference/video/4.0%E5%AE%A3%E4%BC%A0%E8%A7%86%E9%A2%91.mp4" controls width="100%" style="max-width: 640px; display: block; margin: 24px auto; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);"></video>

---

> **如果这个项目对你有帮助，可以请我喝杯咖啡 ☕**  
> 一杯咖啡，不是合同。不影响 issue 优先级和功能方向。
>
> <img src="reference/images/wechat-pay.jpg" width="200" alt="微信收款码" style="border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.1)">

---

## 你需要什么

- 安装了 [Claude Code](https://docs.anthropic.com/zh-CN/docs/claude-code/overview)、[OpenCode](https://github.com/sglaboratory/opencode)、**Reasonix** 或 **Codex** 的电脑
- 大概 1 分钟完成安装


## 安装

**Claude Code：**
```bash
git clone https://github.com/modoojunko/awesome-novel-skill.git && cd awesome-novel-skill && ./install.sh claude-code
```

**OpenCode：**
```bash
git clone https://github.com/modoojunko/awesome-novel-skill.git && cd awesome-novel-skill && ./install.sh opencode
```

**Reasonix：**

Reasonix 的 skill 是**项目级部署**（装在每个小说项目的 `.reasonix/skills/`），不走 install.sh。克隆仓库后直接用 init.py 初始化小说项目：

```bash
git clone https://github.com/modoojunko/awesome-novel-skill.git && cd awesome-novel-skill
python tools/init.py <小说项目路径> --platform reasonix
cd <小说项目路径> && reasonix code
```

> 用 `--genre <编号>` 指定预置题材，不传则交互式选题材。装好后在项目目录里输入 `@novel-agent` 开始写作。

**Codex：**

Codex 的 skill 是**用户级安装**（`~/.codex/skills/awesome-novel/`），小说项目内的 agents/skills/knowledge/memory 则在初始化时**项目级部署**到 `.codex/`：

```bash
git clone https://github.com/modoojunko/awesome-novel-skill.git && cd awesome-novel-skill && ./install.sh codex
python tools/init.py <小说项目路径> --platform codex
cd <小说项目路径>  # 然后在 Codex 中调用 @novel-agent 开始写作
```

或者手动复制（以 Claude Code 为例）：
```bash
git clone https://github.com/modoojunko/awesome-novel-skill.git
cd awesome-novel-skill
mkdir -p ~/.claude/skills/awesome-novel
cp -r agents ~/.claude/skills/awesome-novel/
cp -r skills ~/.claude/skills/awesome-novel/
cp -r templates ~/.claude/skills/awesome-novel/
cp -r knowledge ~/.claude/skills/awesome-novel/
[ -d memory ] && cp -r memory ~/.claude/skills/awesome-novel/
cp -r tools ~/.claude/skills/awesome-novel/
cp SKILL.md ~/.claude/skills/awesome-novel/
echo "安装完成!"
```

> **OpenCode 用户注意：** 安装路径为 `~/.config/opencode/skills/awesome-novel/`，初始化后 agent 定义部署在项目 `.opencode/agents/` 下，OpenCode 自动发现。详情见下方 [OpenCode 集成](#opencode) 说明。

> **Codex 用户注意：** skill 安装到 `~/.codex/skills/awesome-novel/`，初始化后 8 个自定义 agent 以 TOML 形式部署在项目 `.codex/agents/` 下，Codex 自动发现。详情见下方 [Codex 集成](#codex-集成) 说明。

看到 "安装完成" 就可以了。

> **看到这个项目觉得有用？** 顺手点个 Star，这样它会出现在你的 GitHub 首页，让更多人发现。
> {: .prompt-info }

## 开始写小说

安装后，打开终端，在**你想放小说项目的目录**下启动 Claude Code、OpenCode 或 Reasonix，然后说一句：

> **帮我写本小说**

系统会自动加载写作流程。后续再进入该项目时，说 `@novel-agent` 或 **"帮我继续写"** 就能从中断处恢复。

Agent 会引导你完成后续步骤。系统由 8 个 AI Agent 协作驱动，自动检测进度、调度任务，你只需确认方向和审阅内容。

```
novel-agent（总指挥 — 顶层入口，由 @novel-agent 加载）
  ├─ setup 阶段 → 调度 updater（设定写入）
  ├─ outline 阶段 → 调度 volume-planner（卷纲）→ chapter-planner（章纲）
  ├─ draft 阶段 → 调度 prompt-crafter（提示词）→ writer（正文）
  ├─ anti-ai 阶段 → 调度 anti-ai（去 AI 味）
  ├─ review 阶段 → 调度 reader（深度评审，可选）
  └─ archive 阶段 → 调度 updater（归档 + lore-keeping）
```

novel-agent 只负责调度和验证，不直接写内容。子 agent 各司其职，完成后把 order 标记为 `status: DONE` 通知完成。

### 一次性设定

第一次写小说时，Agent 会和你聊这几个方面。**不用一次性想好全部**，想不到的跳过，后面随时补：

1. **题材选择** — 仙侠、都市、悬疑、历史……说你脑子里想的那个就行。Agent 会按题材类型自动配置写作风格和节奏模板。也可以直接从 24 套预置题材画像里选一个，省去手动调风格的步骤
2. **世界观** — 故事发生在什么世界？有什么特殊规则？（比如"修仙世界，灵根决定天赋"）
3. **主要角色** — 主角是谁？TA 是什么样的人？Agent 会逐个角色和你讨论性格、能力、成长经历
4. **写作风格** — 偏好更偏描写还是更偏对话、更古风还是更现代？也可以导入你喜欢的小说来提取文风

### 项目结构

设定聊完后，Agent 会在当前目录下创建你的小说项目，结构如下：

```
{你的小说文件夹}/
├── story.md              # 项目总索引（元信息/主线/卷规划）
├── CLAUDE.md             # 项目级 CLAUDE.md（tools 白名单）
├── settings/             # 设定文件
│   ├── world-setting.md  # 世界观
│   ├── writing-style.md  # 写作风格
│   ├── genre-setting.md  # 题材设定
│   ├── timeline.md       # 时间线
│   └── character-setting/ # 角色档案
│       └── <id>.md       # 每角色一个文件
├── volumes/              # 卷纲（情绪走向/冲突阶梯/信息差/场景卡）
├── chapters/             # 章纲
├── prompts/              # 提示词
├── sandbox/              # 剧情推演记录（可选，作者卡剧情时调用）
├── archives/             # 正文（定稿）
├── .agent/               # Agent 进度 + 任务通信
│   ├── status.md         # 进度标记（phase/volume/chapter）
│   └── task/             # 子 agent 间 order 文件
├── .opencode/            # OpenCode 用（四选一，由 init.py --platform 决定）
│   ├── agents/           # 8 个 Agent 定义（初始化时部署）
│   ├── knowledge/        # 格式规范、反 AI 规则、文风偏好、永久记忆
│   └── memory/           # 写作动态记忆
├── .claude/              # Claude Code 用（四选一）
│   ├── agents/           # 8 个 Agent 定义（初始化时部署）
│   ├── knowledge/        # 格式规范、反 AI 规则、文风偏好、永久记忆
│   └── memory/           # 写作动态记忆（各环节作者反馈）
│       ├── volume-memory.md
│       ├── chapter-memory.md
│       ├── prompt-memory.md
│       └── writing-memory.md
├── .reasonix/            # Reasonix 用（四选一）
    ├── skills/           # 10 个 SKILL.md（agents 即 skills）
    ├── knowledge/        # 格式规范、反 AI 规则、文风偏好、永久记忆
    └── memory/           # 写作动态记忆
└── .codex/               # Codex 用（四选一）
    ├── agents/           # 8 个自定义 agent（TOML，初始化时部署）
    ├── skills/           # 独立交互工具（memory-recording、roleplay-sandbox）
    ├── knowledge/        # 格式规范、反 AI 规则、文风偏好、永久记忆
    └── memory/           # 写作动态记忆
```

这些全是纯文本 Markdown 文件，你可以直接用编辑器打开看或手动改。实际项目只生成一套平台目录（由 `init.py --platform` 决定），`.claude/` / `.opencode/` / `.reasonix/` / `.codex/` 不会同时存在。

### 规划故事骨架

设定聊完后，Agent 帮你规划整体故事结构。规划分四个维度同时推进：

1. **情绪走向** — 读者读这卷从头到尾情绪怎么变化？爽卷就是"压抑→压抑→提升→打脸→装逼"，悬疑卷就是"紧张→逼近→震惊→舒缓"
2. **冲突阶梯** — 核心冲突拆成 2-4 层逐级升高的障碍，每层比前一层更难，层间有关键转折点
3. **信息差** — 明确"谁知道什么、谁不知道什么"。卷定义起点→终点，每章演绎信息差的动态变化（设→用→揭→新）
4. **场景卡** — 每章拆成 2-5 个场景卡，每卡三要素：主角想干啥、有什么拦着他、有什么悬念让读者想看下去

> **不知道结局？** 告诉 Agent"我只知道开头"，它照样帮你规划第一卷。

### 逐章写作循环（Agent 协作）

多 Agent 协作自动推进，novel-agent（总指挥）按进度调度子 agent，你只需审阅和决策：

| 步骤 | 负责 Agent | 做什么 |
|------|-----------|--------|
| **① 章纲** | chapter-planner | （由 novel-agent 调度）继承卷的情绪走向/冲突阶梯/信息差位置，设计章内微弧线、小冲突阶梯和信息差动态变化，拆成场景卡。你看完后说"可以"或"改一下" |
| **② 提示词** | prompt-crafter | （由 novel-agent 调度）根据章纲、反 AI 规则和文风偏好，组装 6 元素纯净提示词 |
| **③ 写正文** | writer | （由 novel-agent 调度）按提示词写完整一章 |
| **④ 去 AI 味** | anti-ai | （由 novel-agent 调度）Gate A-F 管线检测清除 AI 痕迹，量化评分定级 |
| **⑤ 审阅** | reader（可选） | （由 novel-agent 调度）10 维 60+ 细项深度评审，对照章纲/设定/前文逐条诊断 |
| **⑥ 归档** | updater | （由 novel-agent 调度）你确认后归档定稿，自动更新角色状态、追加情绪弧线、合并文风偏好、检测钩子健康和卷边界 |

**调度规则：** `@novel-agent` 是顶层入口，由主 AI 加载后扮演总指挥角色。novel-agent 通过 Agent 工具调度子 agent，不直接代劳写作任务。子 agent 完成后把 order 覆盖为 `status: DONE`（不删除文件），novel-agent 检测到后自动推进下一阶段。

第一章写完后，Agent 会问"下一章继续吗？"

### 自动做的事（Agent 维护）

- **去 AI 味**（prompt-crafter + writer + anti-ai）：提示词组装时注入反 AI 规则，正文生成时自查，独立 anti-ai agent 做 Gate A-F 管线检测和量化评分定级
- **动态记忆**（多 agent + updater）：各 agent 在对话中实时记录你的写作偏好和反馈（正反案例），归档时 updater 兜底清理、去重压缩。高频使用的规则自动晋升为永久记忆（`.claude/knowledge/permanent-memory.md`），越写越懂你
- **记伏笔**（updater）：归档时自动扫描未兑现/新埋的钩子，检测陈旧度和集中收束风险
- **管角色状态**（updater）：每章归档后自动追加角色状态历史、情绪弧线和人际关系变化。下一章写作时 Agent 知道最新状态
- **节奏检查**（updater）：连续高压超过 3 章或连续平淡超过 2 章，提醒你调整
- **卷边界检测**（updater）：整卷完成后自动输出报告，询问下一卷方向

### 常用指令

| 你说 | AI 做什么 |
|------|-----------|
| "帮我写本小说" | 首次加载技能 + 创建项目 + 设定讨论 |
| "@novel-agent" 或 "帮我继续写" | 进入 / 恢复写作循环 |
| "写下一章" | 开始写最新一章 |
| "跑一下推演" 或 "剧情推演" | 角色推演沙盘——卡剧情时让角色演一遍 |
| "改一下第 X 段" | 修改指定段落 |
| "这章写完了" 或 "归档" | 确认本章完成 |
| "看看进度" | 查看当前写了多少 |
| "导入这本小说" | 导入已有草稿继续写 |
| "迁移项目" | 从旧版自动迁移到 4.0 格式 |
| "solo" 或 "你全权写" | 进入全自动模式，不打断你确认 |

## 两种协作模式

| 模式 | 触发词 | 行为 |
|------|--------|------|
| **步步确认**（默认） | — | 每做一步都等你点头才继续 |
| **全部授权** | "你全权决定" | 流程节点还在，Agent 代按确认，不经你手 |

随时可以切换，跟 Agent 说一声就行。

## 更高阶的玩法

### 预置题材画像

不想从头设定写作风格？Agent 在一次性设定阶段就会问你用不用预置风格。项目内置 24 套题材档案，每套包含角色人设倾向、叙事语气和章节提示词模板。涵盖仙侠、都市、悬疑、历史、科幻末世、西方奇幻等主流类型。

## 常见问题

**Q: 我不会编程，能装吗？**

能。上面那几行命令复制粘贴到终端，回车就行。唯一的前提是你的电脑上已经装好了 Claude Code、OpenCode、Reasonix 或 Codex。

**Q: 我升级了技能，之前写的小说项目怎么迁移到新格式？**

升级后首次在当前项目目录启动时，Agent 会自动检测旧版格式，引导你完成迁移。核心逻辑：旧文件整体挪到 `old/` 目录保留备份，在原地初始化新项目骨架，再逐字段将旧版设定转换到新版格式。已归档的正文直接拷贝，正在写的不迁移。确认迁移无误后可手动删除 `old/` 目录。

**Q: 写到一半可以改设定吗？**

可以。随时跟 Agent 说"改一下世界观里的 XXX"或"这个角色的性格我想调整"，它会帮你更新。

**Q: 生成的文字有 AI 味怎么办？**

默认配置就是"低 AI 味"——禁止了常见机器腔句式、写完后自动检测。动态记忆系统会记录你如何修改 AI 原文，提炼为你的专属规则，后续自动规避。

**Q: 可以用自己的写作风格吗？**

可以。项目创建后有专门的写作风格文件，你可以把自己的偏好写进去，后面所有章节都会按这个风格来。

## Star History

<a href="https://star-history.com/#modoojunko/awesome-novel-skill">
  <img src="https://api.star-history.com/svg?repos=modoojunko/awesome-novel-skill&type=date" alt="Star History">
</a>

## 致谢

本项目部分设计受到 [InkOS](https://github.com/Narcooo/inkos) 的启发——包括 AI 味检测体系、伏笔/钩子追踪、题材配置和分层技法模型。感谢 [@Narcooo](https://github.com/Narcooo) 的优秀工作。

## 贡献

欢迎参与贡献！详情请查看 [CONTRIBUTING.md](./CONTRIBUTING.md)。

| 方式 | 说明 |
|------|------|
| [Bug 反馈](https://github.com/modoojunko/awesome-novel-skill/issues/new) | 报告功能异常、安装问题 |
| [功能建议](https://github.com/modoojunko/awesome-novel-skill/issues/new) | 提出新功能或改进想法 |
| [素材扩充](https://github.com/modoojunko/awesome-novel-skill/issues) | 补充题材档案、文风特征库 |
| [提交 PR](https://github.com/modoojunko/awesome-novel-skill/pulls) | 修复 bug、优化代码或文档 |

### 写作风格贡献（作家）

如果你是有创作经验的作家，欢迎为反AI写作库贡献题材正反例：

**贡献内容：** `knowledge/anti-ai/{genre}.md` — 你所在题材的高频AI病句正反例

**贡献格式：**
```markdown
# {题材名}反AI规则

> 适用题材：{genre-id}

## 高频AI病句正反例

### 1. {问题类型}

❌ "AI味的写法"
✅ "真人感的写法"

## 写作要点

1. **{要点}** — 说明
```

**正反例原则：**
- ❌ 要具体：给真实的AI味句子，不是抽象描述
- ✅ 要可执行：给可复制的真人感写法，不是"要自然"
- 每类问题包含一对对照，同一场景、同一情绪，转化清晰

**提交方式：**
1. Fork 项目
2. 在 `knowledge/anti-ai/` 下新建或编辑题材文件
3. 提交 PR，标题格式：`反AI: 添加{题材名}正反例`

见 [knowledge/anti-ai/README.md](./knowledge/anti-ai/README.md)。

### 代码贡献（程序员）

**项目结构：**
```
awesome-novel-skill/
├── agents/              # 多 Agent 协作
│   ├── novel-agent.md   # 总指挥
│   ├── volume-planner.md# 叙事架构师
│   ├── chapter-planner.md# 场景设计师
│   ├── prompt-crafter.md# 提示词工程师
│   ├── writer.md        # 写手
│   ├── anti-ai.md       # 反 AI 编辑
│   ├── reader.md        # 测试读者
│   └── updater.md       # 档案管理员
├── skills/               # Agent 技能 SOP + 交互式工具
├── knowledge/            # 知识库（→ 项目 .claude/knowledge/）
│   ├── format-specs/    # 格式规范
│   ├── scene-craft/     # 场景写作方法论（四步转化后注入输出·写作规范）
│   ├── plot-craft/      # 剧情设计（与作者讨论）
│   ├── character-craft/ # 角色设定（与作者讨论）
│   ├── title-craft/     # 取书名（与作者讨论）
│   ├── genre-example/   # 题材案例
│   └── anti-ai/         # 反AI写作库（通用规则 + 题材正反例）
├── memory/               # 动态记忆（→ 项目 .claude/memory/）
│   └── writer-style
└── tools/                # 工具脚本
```

**开发规范：**
- 代码遵循 PEP 8（Python）或项目既有风格
- 所有子技能修改需更新对应 SKILL.md
- 新增功能需更新 README 和 CONTRIBUTING.md

**提交方式：**
1. Fork 项目，创建功能分支
2. 提交 PR，标题格式：`类型: 简短描述`（feat/fix/refactor/docs/test）
3. PR 描述包含：改了什么、为什么改、测试方式

## OpenCode 集成

本 skill 也支持 [OpenCode](https://github.com/sglaboratory/opencode)（第三方开源的 AI 编码 CLI 工具）。

### 安装

```bash
git clone https://github.com/modoojunko/awesome-novel-skill.git && cd awesome-novel-skill && ./install.sh opencode
```

安装到 `~/.config/opencode/skills/awesome-novel/`。

### 初始化项目

在目标目录运行 init.py（使用完整路径或设置 `NOVEL_SKILL_HOME` 环境变量）：

```bash
python ~/.config/opencode/skills/awesome-novel/tools/init.py . --genre <编号>
```

### 开始写作

初始化完成后，在 OpenCode 中通过 `@novel-agent` 或 Task 工具调用 novel-agent 进入写作循环。

### 项目结构差异

OpenCode 项目与 Claude Code 项目结构一致，唯一区别是 agent 定义部署在 `.opencode/agents/` 而非 `.claude/agents/`。三个平台共享同一套写作流程和知识库。

### Agent 技能贡献

本 Skill 由多个子技能模块组成，每个模块可独立改进：

| 模块 | 路径 | 贡献方向 |
|------|------|---------|
| Agent/Skill | `agents/` + `skills/` | 改进 agent 定义、新增 skill SOP |
| 角色推演沙盘 | `skills/roleplay-sandbox.md` | 改进推演交互协议、触发条件 |
| 格式规范 | `knowledge/format-specs/` | 改进各环节规范文档 |
| 场景写法 | `knowledge/scene-craft/` | 新增/改进场景写作方法论（四步转化后注入输出·写作规范） |
| 剧情设计 | `knowledge/plot-craft/` | 新增/改进剧情设计方法论（与作者讨论） |
| 角色设定 | `knowledge/character-craft/` | 新增/改进角色设定方法论 |
| 反AI写作库 | `knowledge/anti-ai/` | 新增题材正反例、丰富通用规则及方法论 |
| 题材画像 | `knowledge/genre-example/` | 新增题材档案、丰富配置内容 |

**贡献流程：**
1. 阅读目标模块的 SKILL.md 了解当前逻辑
2. 在测试项目（如有）中验证改动效果
3. 提交 PR，附上改动说明和验证结果

**Skill 贡献原则：**
- 改动需有明确的问题驱动（"因为XX问题，所以改XX"）
- 新增功能需向后兼容，不破坏现有项目
- 复杂改动先提 Issue 讨论再实现

## Reasonix 集成

本 skill 也支持 Reasonix（DeepSeek 专属终端 AI agent，借助字节稳定前缀缓存优化推理成本）。

与 Claude Code / OpenCode 不同，Reasonix 的 skill 是**项目级部署**——每个小说项目初始化时生成 `.reasonix/skills/`（10 个 SKILL.md，agents 即 skills），不装到全局。

### 安装框架源码

```bash
git clone https://github.com/modoojunko/awesome-novel-skill.git && cd awesome-novel-skill
```

### 初始化项目

在项目目录（或指定路径）运行 init.py，指定 Reasonix 平台：

```bash
python tools/init.py <小说项目路径> --genre <编号> --platform reasonix
```

### 开始写作

初始化完成后，进入项目目录启动 Reasonix：

```bash
cd <小说项目路径> && reasonix code
```

然后通过 `@novel-agent` 进入写作循环。Reasonix 环境里 novel-agent 用 `run_skill` 调度子 agent，调度协议与其余平台一致。

### 项目结构差异

Reasonix 项目把 agent 定义以 skill 形式部署在 `.reasonix/skills/`，不产生 `.claude/`：

```
.reasonix/
├── skills/               # 10 个 SKILL.md（agents 即 skills）
│   ├── novel-agent/SKILL.md
│   ├── writer/SKILL.md
│   ├── volume-planner/SKILL.md
│   └── ...
├── knowledge/            # 反 AI 规则、文风偏好、永久记忆、格式规范
└── memory/               # 写作动态记忆
```

升级时用 `python tools/sync-project.py <小说项目路径> --platform reasonix` 同步最新框架。

## Codex 集成

本 skill 也支持 [Codex](https://developers.openai.com/codex)（OpenAI 的 AI 编码 agent）。skill 本体**用户级安装**，小说项目内的 agents/skills/knowledge/memory 全部**项目级部署**在 `.codex/`。

### 安装

```bash
git clone https://github.com/modoojunko/awesome-novel-skill.git && cd awesome-novel-skill && ./install.sh codex
```

安装到 `~/.codex/skills/awesome-novel/`。

### 初始化项目

```bash
python tools/init.py <小说项目路径> --genre <编号> --platform codex
```

初始化后 8 个自定义 agent 以 Codex 官方 TOML 格式部署到项目 `.codex/agents/*.toml`（`name` / `description` / `developer_instructions`），独立交互工具（memory-recording、roleplay-sandbox）部署为 `.codex/skills/<name>/SKILL.md`，反 AI 规则、文风偏好、格式规范与写作记忆分别落在 `.codex/knowledge/`、`.codex/memory/`。

### 开始写作

在 Codex 中打开项目目录，调用 `@novel-agent` 进入写作循环。Codex 环境里 novel-agent 用 `spawn_agent` 调度子 agent（agent 名 = `.codex/agents/*.toml` 的 name），order 文件协议与其余平台一致。

### 项目结构差异

```
.codex/
├── agents/               # 8 个自定义 agent（TOML）
│   ├── novel-agent.toml
│   ├── writer.toml
│   ├── volume-planner.toml
│   └── ...
├── skills/               # 独立交互工具（memory-recording、roleplay-sandbox）
├── knowledge/            # 反 AI 规则、文风偏好、永久记忆、格式规范
└── memory/               # 写作动态记忆
```

升级时用 `python tools/sync-project.py <小说项目路径> --platform codex` 同步最新框架。
