# index.html Landing Page 改造文档

> 依据 `docs/landing-page-study.md`（DeepSeek Harness 落地页学习总结）制定
> 改造对象：仓库根 `index.html`（GitHub Pages 落地页）
> 原则：**只取骨架，不照搬**——单文件、零依赖、纯 CSS + 少量原生 JS 的约束必须守住

## 1. 现状诊断

| # | 问题 | 证据 |
|---|---|---|
| P1 | 无主 CTA，访问者不知道下一步做什么 | 全页唯一链接在页脚，且无「快速开始」按钮 |
| P2 | 强调色 `#e94560` 无差别使用 | h1、feature h3、链接、安装框四处理论上是同一元素，无层级 |
| P3 | 7 张 feature 卡片平铺，无主张 | 缺少统摄全页的一句话口号 |
| P4 | 安装体验在第二屏 | 违反「代码即信任」——第一屏就该看到命令 |
| P5 | 零动效、零 hover 反馈 | 卡片/按钮无任何交互状态 |
| P6 | 无导航、无徽标、无版本信息 | 缺少「产品感」细节 |

现状优点（保留）：深色底 + 代码块方向正确；单文件零依赖；文案务实不浮夸。

## 2. 改造目标与约束

**目标**：信息层级清晰（主张 → 支柱 → 细节）、第一屏可转化（CTA + 命令可见）、交互有反馈、保持单文件。

**硬约束**：
- 单 HTML 文件，无外部 CSS/JS/字体依赖（GitHub Pages 直接托管）
- 不使用框架；JS 仅允许原生 IntersectionObserver（滚动入场）
- 不引入图片素材（仓库无版权素材，背景用 CSS 渐变 + 光晕模拟）
- 配色延续深色基调；强调色从红色系改为单一品牌色并收敛使用范围

## 3. 新页面结构

```
┌────────────────────────────────────────────┐
│ 导航: Awesome Novel · 文档 · GitHub · 快速开始 │  ← 固定顶栏 + backdrop blur
├────────────────────────────────────────────┤
│ Hero（100vh）                              │
│   徽标: v4.14 · 支持 6 平台                  │
│   H1: 和 AI 一起写小说                       │
│   副标题: 世界观→角色→章节→正文，全流程可控     │
│   [开始写作] [查看文档]                      │  ← 主 CTA 白底黑字
│   安装命令块（两行）                          │  ← 第一屏即见代码
│   背景: 径向光晕 + 网格渐隐                   │
├────────────────────────────────────────────┤
│ 概念条: 小说创作 = 大纲 + 文风 + 反AI净化      │
├────────────────────────────────────────────┤
│ 三大痛点（编号 01/02/03，问题导向标题）        │
│   01 怕烂尾？ → 全流程规划 + 9 智能体 自动推进   │
│   02 不像你？ → 文风蒸馏 + 动态记忆             │
│   03 有 AI 味？→ 去AI味/伏笔/角色/节奏四道闸    │
│ 平台支持行：Claude Code/OpenCode/Reasonix/…   │
├────────────────────────────────────────────┤
│ 开始创作（三步:安装/初始化/写作 + 常用指令）    │
├────────────────────────────────────────────┤
│ FAQ（可选）: 5 条真实问题                     │
├────────────────────────────────────────────┤
│ 页脚: GPLv3 · 个人免费 · GitHub · 文档        │
└────────────────────────────────────────────┘
```

## 4. 分区块改造方案

### 4.1 设计令牌（新增 CSS 变量）

```css
:root {
  --bg-page: #0a0a0a;            /* 由 #1a1a2e 渐变改为近黑，向 Harness 看齐 */
  --bg-surface-1: rgba(255,255,255,0.06);
  --bg-surface-2: rgba(255,255,255,0.04);
  --border-default: rgba(255,255,255,0.08);
  --border-hover: rgba(255,255,255,0.2);
  --text-primary: #fff;
  --text-description: rgba(255,255,255,0.5);   /* 层级靠透明度，不靠颜色 */
  --brand: #4d6bfe;               /* 品牌蓝仅做点缀：链接、徽标、支柱编号 */
  --radius-card: 12px;
  --radius-pill: 9999px;
}
```

> 说明：现有红色 `#e94560` 视觉辨识度不错，但需降级为「点缀中的点缀」或整体换品牌蓝。本文案按换蓝设计；若保留红色，仅允许用于 CTA 与 h1 强调，其余一律禁用。

### 4.2 Hero（重写）

- 布局：`display:grid; grid-template-columns: 60fr 40fr`（桌面），移动单列
- 左侧文案顺序：徽标（`text-description` 小字 + 版本 pill）→ h1（clamp(2.2rem, 5vw, 3.75rem)，行高 1.2）→ 副标题（两段，第二段降透明度）→ CTA 行（主按钮白底黑字 + 次按钮白 8% 透明底）→ 安装代码块
- 安装代码块（第一屏可见，只留两行最简命令）：

```
$ npx / 或 ./install.sh claude-code
```

- 右侧（桌面）用 CSS 渐变光晕占位，不加 canvas：
  - `background: radial-gradient(circle at 70% 30%, rgba(77,107,254,0.25), transparent 60%)`
  - `mix-blend-mode: screen`，配合页面底部网格背景渐隐（`linear-gradient` mask 不可用则用 `background-image` 直接画网格线 + 顶部淡出）
- 入场动画（CSS only）：`@keyframes enter { from { opacity:0; transform:translateY(24px); filter:blur(10px);} to {opacity:1; transform:none; filter:none;} }`，子元素 `animation-delay: 0.15s/0.3s/0.4s`

### 4.3 三大痛点支柱（问题导向，替换 7 张平铺卡片）

- 区块标题：`设计思路` + 一句解释
- 三列 grid，每列：编号（01/02/03，品牌蓝大字）+ **痛点提问式标题** + 该支柱下的 2–4 个小卡片（surface-1 底、`border-default` 描边、12px 圆角）
- 支柱以「作者最常见的三个困境」命名，**不直接讲技术**：
  - **01 怕烂尾？**（痛点：长篇小说写到中间失去方向，不知下一步写什么）→ 全流程协作：四维卷纲先定情绪走向/冲突阶梯/信息差/场景卡；9 个智能体分环节自动推进，你只审阅与决策；剧情推演沙盘在卡剧情时让角色演一遍
  - **02 不像你？**（痛点：AI 写出来千篇一律、不是自己的风格；反复纠正同一件事）→ 风格与记忆：导入参考样本蒸馏量化文风参数（句长/对话占比/形容词密度）；动态记忆自动沉淀每次反馈，高频规则晋升永久记忆；24 套题材画像解决「从哪开始」
  - **03 有 AI 味？**（痛点：机器腔、挖坑不填、角色前后矛盾、节奏失控）→ 质量防线：去 AI 味 六道闸 管线 + 量化评分；伏笔跟踪未兑现钩子；角色状态每章自动更新；连续高压 3 章 / 平淡 2 章触发节奏提醒
- 平台支持行独立成一行（非支柱）：Claude Code / OpenCode / Reasonix / Codex / ZCode / DSH 六徽标

**卖点推导依据（技术能力 → 作者痛点，写文案时一律先写问题再给方案）：**

| 技术能力 | 解决的作者痛点 | 依据 |
|---|---|---|
| 9 智能体 自动调度 | 不知道流程下一步做什么，手动指挥 AI 繁琐 | README「Agent 会引导你完成后续步骤」 |
| 四维卷纲 | 写到中间失去方向，长篇烂尾/跑偏 | README「规划故事骨架」 |
| 文风蒸馏 | AI 写出来不像自己的风格 | FAQ「可以用自己的写作风格吗」 |
| 动态记忆 | 反复纠正同一件事，前后矛盾 | README「越写越懂你」 |
| 24 套题材画像 | 设定无从下手，不知从哪开始 | README「预置题材画像」 |
| 去 AI 味 | 机器腔、读起来假 | FAQ「生成的文字有 AI 味怎么办」 |
| 伏笔/角色/节奏检查 | 挖坑不填、人设崩坏、读者弃书 | README「自动做的事」 |
| 剧情推演沙盘 | 卡剧情想不出合理走向 | README 指令表「跑一下推演」 |
| 纯文本 Markdown 结构 | 稿子数据被工具锁死、想手动改改不了 | README「项目结构」 |
| 一句话安装（1 分钟） | 不会编程、装不上 | FAQ「我不会编程，能装吗」 |
| 六平台适配 | 换工具就要重学一套工作流 | README 各平台集成章节 |

### 4.4 交互反馈（全站统一）

```css
/* 卡片 hover：内部遮罩浮现 */
.card { position: relative; }
.card::after {
  content: ""; position: absolute; inset: 0; border-radius: 12px;
  background: rgba(255,255,255,0.05); opacity: 0;
  transition: opacity 0.3s ease;
}
.card:hover::after { opacity: 1; }

/* 按钮 hover：径向涟漪（伪元素 scale 0→1，0.36s ease-out） */
```

### 4.5 滚动入场

- 一个 `<script>`（原生 IntersectionObserver，约 20 行）：`.reveal { opacity:0; transform:translateY(20px); transition: opacity 0.6s ease, transform 0.6s ease; }`，进入视口加 `.in` 类
- 降级策略：`prefers-reduced-motion: reduce` 时禁用所有动画

### 4.6 导航 + 页脚

- 导航：fixed 顶栏，`backdrop-filter: blur(24px)`，`background: rgba(10,10,10,0.7)`；链接：文档 / GitHub / 快速开始（锚点）
- 页脚：GPLv3 · 版权 · 两链接，保持现状内容不动

### 4.7 文案方案（完整成稿，可直接粘贴进 index.html；方法依据见 study.md §6.2）

**导航**（固定顶栏）
- 左：`Awesome Novel`；右：`文档`（README）· `GitHub` · `快速开始`（锚点 #start）

**Hero**
- 徽标（品牌行）：`Awesome Novel`（22px 粗体）+ `开源 · 支持 6 平台`（小 pill）——品牌名独立放大，主张占大标题位
- 标题：`人铸灵魂，AI行笔墨`
- 支撑句 1（价值观，三层递进：铸就 → 行文 → 拍板）：`AI 是笔，你才是作者。构想由你铸就，文字交给智能体，成稿由你拍板。`
- 支撑句 2（是什么 + 平台）：`Awesome Novel 是开源的 AI 小说创作工作流——9 个写作智能体从世界观到正文自动推进，适配 Claude Code / OpenCode / Reasonix / Codex / ZCode / DSH。`
- CTA：`开始写作`（主，白底黑字，锚点 #start）· `查看文档`（次，GitHub README）
- 安装命令块（第一屏可见）：
  ```
  $ ./install.sh <你的平台>
  ```
  `不想输命令？对 AI 说"帮我安装 awesome-novel-agent"即可，1 分钟装好。`

**概念条**
- 公式：`小说创作 = 人的构想 + AI 的笔力`
- 副句：`人铸灵魂，AI 行笔墨`
- 解释：`构想归你：世界观、角色、大纲。笔力归模型：行文、节奏、净化——Awesome Novel 把两者编排成可复现的工作流。`

**设计思路（三大痛点支柱 + 小卡片，全部「痛点 → 方案」句法）**

**01 怕烂尾？** —— `开写前有蓝图，过程中有人盯`
- 四维卷纲：`情绪走向、冲突阶梯、信息差、场景卡先规划再动笔，长篇连载不跑偏。`
- 9 智能体 自动推进：`卷纲、章纲、正文、评审、归档自动流转，你只审阅与决策，不用记流程。`
- 剧情推演沙盘：`卡剧情时让角色在沙盘里演一遍，合情合理的走向自然浮现。`

**02 不像你？** —— `导入即学会，越写越像你`
- 文风蒸馏：`把你喜欢的小说丢进样本库，自动提炼句长、对话占比等量化参数。`
- 动态记忆：`每次修改反馈自动沉淀为记忆，高频规则晋升永久规则，纠正过一次就不再犯。`
- 24 套题材画像：`仙侠、都市、悬疑、历史等预置档案，人设倾向与叙事语气直接可用。`

**03 有 AI 味？** —— `机器腔与逻辑漏洞，归档前拦下`
- 去 AI 味：`提示词组装注入反 AI 规则，成稿后 六道闸 管线检测并量化评分。`
- 伏笔跟踪：`自动扫描未兑现与新埋的钩子，提醒收束——埋的坑不会忘。`
- 角色状态：`每章归档自动更新角色状态与情绪弧线，下一章 AI 记得他经历了什么。`
- 节奏检查：`连续高压 3 章或平淡 2 章自动提醒，避免读者弃书。`

**平台支持行**
- 徽标：`Claude Code · OpenCode · Reasonix · Codex · ZCode · DeepSeek Harness`（pill）
- 流水线流程图（纯 CSS 节点卡 + 箭头，每节点：编号 + 阶段名 + 一句职责）：
  `设定（题材·世界观·角色）→ 卷纲（情绪走向·冲突阶梯）→ 章纲（场景卡·微弧线）→ 正文（提示词驱动成稿）→ 净化（去 AI 味·六道闸）→ 归档（角色状态·伏笔更新）`
- 文案：`六个平台，跑同一条流水线。换工具，创作状态无缝续写。`

**开始创作**（id="start"，三步）
- 标题：`开始创作`
- 步骤 1 `安装`：`打开任一支持的 AI 终端，对它说：` `帮我安装 awesome-novel-agent，仓库在 https://github.com/modoojunko/awesome-novel-agent`——AI 自动运行安装脚本，不用复制粘贴命令
- 步骤 2 `初始化`：`在放小说的目录输入 /awesome-novel（或"帮我写本小说"），自动生成项目骨架并进入设定讨论`
- 步骤 3 `写作`：`@novel-agent 或"帮我继续写"进入写作循环；常用指令：写下一章 / 改一下第 X 段 / 跑一下推演 / 全自动模式`

**FAQ（可选区块，问题取自 README 常见问题，全部真实）**
- `我不会编程，能装吗？` — `能。对 AI 说一句话即可完成安装，全程不用复制粘贴命令。`
- `生成的文字有 AI 味怎么办？` — `默认即"低 AI 味"配置：禁用常见机器腔句式 + 成稿自动检测；你的修改还会被记录为专属规则。`
- `可以用自己的写作风格吗？` — `可以。导入参考样本自动蒸馏，或直接写进风格文件，后续章节都按此风格。`
- `写到一半可以改设定吗？` — `随时说"改一下世界观里的 XXX"，智能体会同步更新后续章节。`
- `旧项目能迁移吗？` — `升级后自动检测旧版格式并引导迁移，原文件保留备份。`

**生态 CTA**
- 标题：`加入创作社区`
- 正文：`项目仍处于活跃迭代阶段，题材档案与反 AI 规则库持续扩充。期待与创作者一起，在开源、可复用、可组合的创作基础设施上，探索 AI 写作的上限。`
- 信任行：`个人使用免费 · GPLv3 开源 · QQ 交流群 1006050538`

**页脚**：`GPLv3 开源 · 个人使用免费 · © 2026` + `GitHub · 文档`

### 4.8 验收清单（文案）

- [ ] 标题为断言式 ≤ 8 字，解释全部交给支撑句
- [ ] 每个区块标题符合「主张 + 价值」对仗
- [ ] 支柱标题是**痛点提问**（怕烂尾？不像你？有 AI 味？），不是功能名
- [ ] 每个卖点文案遵循「**先讲解决什么问题，再讲怎么解决**」；技术名词（六道闸、蒸馏、order 文件）只允许出现在第二层小卡片，不进支柱标题与 Hero
- [ ] 支撑句使用名词堆叠（具体能力枚举），无「强大/全面/灵活」类空形容词
- [ ] CTA 无「立即/免费/限时」推销词
- [ ] 模式/支柱卡片统一「痛点 → 方案」句法
- [ ] 全页含至少一处坦诚声明（如「活跃迭代阶段」）

## 5. 设计成稿（完整单文件实现，可直接运行）

> 本节是 4.1–4.6 方案的总成：单文件、零依赖、纯 CSS 光晕替代 canvas、原生 IntersectionObserver 做滚动入场、`prefers-reduced-motion` 降级。设计手法与文案区块一一对应。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Awesome Novel — 人铸灵魂，AI行笔墨</title>
  <style>
    /* ===== 设计令牌（对应 4.1） ===== */
    :root {
      --bg-page: #0a0a0a;
      --bg-surface-1: rgba(255,255,255,.06);
      --bg-surface-2: rgba(255,255,255,.04);
      --border-default: rgba(255,255,255,.08);
      --border-hover: rgba(255,255,255,.2);
      --text-primary: #fff;
      --text-description: rgba(255,255,255,.5);
      --brand: #4d6bfe;
      --radius-card: 12px;
      --radius-pill: 9999px;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    html { scroll-behavior:smooth; }
    body {
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
      background:var(--bg-page); color:var(--text-primary); line-height:1.6;
      -webkit-font-smoothing:antialiased;
    }
    .container { width:min(100% - 48px,1140px); margin-inline:auto; }
    a { color:var(--brand); text-decoration:none; }
    a:hover { text-decoration:underline; }
    section[id] { scroll-margin-top:80px; }

    /* ===== 导航（4.6：fixed + backdrop-blur 24px） ===== */
    .nav { position:fixed; inset:0 0 auto 0; z-index:100; background:rgba(10,10,10,.7);
      backdrop-filter:blur(24px); -webkit-backdrop-filter:blur(24px);
      border-bottom:1px solid var(--border-default); }
    .nav-inner { display:flex; align-items:center; justify-content:space-between; height:56px; }
    .nav-brand { font-weight:700; font-size:16px; color:var(--text-primary); }
    .nav-links { display:flex; gap:22px; font-size:14px; }
    .nav-links a { color:var(--text-description); }
    .nav-links a:hover { color:var(--text-primary); }

    /* ===== 按钮（4.4：径向涟漪 hover） ===== */
    .btn { position:relative; display:inline-flex; align-items:center; justify-content:center; gap:6px;
      padding:10px 22px; border-radius:var(--radius-pill); font-size:15px; font-weight:500;
      border:1px solid transparent; cursor:pointer; text-decoration:none;
      overflow:hidden; isolation:isolate; }
    .btn-primary { background:#fff; color:#0a0a0a; }
    .btn-primary::after { content:""; position:absolute; top:50%; left:50%; width:150%; aspect-ratio:1;
      border-radius:50%; background:rgba(10,10,10,.12); opacity:0; z-index:-1;
      transform:translate(-50%,-50%) scale(0); transition:transform .36s ease-out,opacity .1s ease; }
    .btn-primary:hover::after { opacity:1; transform:translate(-50%,-50%) scale(1); }
    .btn-secondary { background:rgba(255,255,255,.08); color:var(--text-primary); border-color:var(--border-default); }
    .btn-secondary:hover { border-color:var(--border-hover); }

    /* ===== Hero（4.2：分层背景 + 60/40 + 入场动画） ===== */
    .hero { position:relative; display:flex; align-items:center; min-height:100svh; overflow:hidden; }
    .hero-grid { position:absolute; inset:0; background-image:
        linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px);
      background-size:48px 48px;
      mask:linear-gradient(#000 0%, #000 45%, transparent 100%);
      -webkit-mask:linear-gradient(#000 0%, #000 45%, transparent 100%); }
    .hero-glow { position:absolute; right:-12%; top:50%; width:720px; height:720px; transform:translateY(-50%);
      border-radius:50%; background:radial-gradient(circle, rgba(77,107,254,.22), transparent 62%);
      mix-blend-mode:screen; filter:blur(24px); pointer-events:none; }
    .hero-inner { position:relative; z-index:1; display:grid; grid-template-columns:60fr 40fr; gap:64px;
      align-items:center; padding:128px 0 88px; }
    .hero-brand-line { display:flex; align-items:center; gap:14px; margin-bottom:20px; }
    .hero-brand { font-size:22px; font-weight:700; letter-spacing:.2px; }
    .hero-badge { display:inline-block; padding:4px 12px; border:1px solid var(--border-default);
      border-radius:var(--radius-pill); font-size:13px; color:var(--text-description); }
    .hero h1 { font-size:clamp(2.4rem,5vw,3.75rem); line-height:1.2; letter-spacing:.2px; font-weight:700; }
    .hero-sub1 { margin-top:16px; font-size:18px; }
    .hero-sub2 { margin-top:8px; font-size:16px; color:var(--text-description); max-width:560px; }
    .hero-cta { display:flex; flex-wrap:wrap; gap:14px; margin-top:28px; }
    .hero-code { margin-top:32px; max-width:560px; }
    .code-block { background:rgba(0,0,0,.35); border:1px solid var(--border-default); border-radius:8px;
      padding:14px 18px; font-family:"SF Mono",Menlo,Consolas,monospace; font-size:14px; overflow-x:auto; }
    .code-note { margin-top:10px; font-size:13px; color:var(--text-description); }
    /* Hero 右侧亮点卡轮播（纯 CSS + 原生 JS，无图片） */
    .hero-panel { position:relative; display:flex; flex-direction:column; min-height:300px;
      border:1px solid var(--border-default); border-radius:var(--radius-card);
      background:var(--bg-surface-1); padding:24px; }
    .panel-head { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
    .tag { padding:3px 10px; border-radius:var(--radius-pill); font-size:12px;
      background:var(--bg-surface-2); border:1px solid var(--border-default); color:var(--text-description); }
    .tag-brand { color:var(--brand); border-color:rgba(77,107,254,.4); }
    .panel-meta { margin-top:auto; display:flex; flex-direction:column; gap:6px; font-size:13px; color:var(--text-description); }
    .panel-meta .warn { color:var(--brand); }
    .spotlight-viewport { position:relative; flex:1; }
    .spotlight-card { position:absolute; inset:0; display:flex; flex-direction:column;
      opacity:0; transform:translateY(12px); visibility:hidden;
      transition:opacity .5s ease, transform .5s ease; }
    .spotlight-card.active { opacity:1; transform:none; visibility:visible; }
    .spotlight-title { font-size:20px; font-weight:700; margin-bottom:14px; }
    .spotlight-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
    .stat { background:var(--bg-surface-2); border:1px solid var(--border-default);
      border-radius:8px; padding:12px 6px; text-align:center; }
    .stat b { display:block; font-size:24px; font-weight:700; color:var(--text-primary);
      line-height:1.25; letter-spacing:.2px; }
    .stat span { font-size:11px; color:var(--text-description); display:block; margin-top:2px; }
    .spotlight-dots { display:flex; justify-content:center; gap:8px; margin-top:16px; }
    .dot { width:8px; height:8px; border-radius:50%; border:1px solid var(--border-hover);
      background:transparent; cursor:pointer; padding:0; transition:background .3s ease; }
    .dot.active { background:var(--brand); border-color:var(--brand); }
    /* 入场动画：上移 24px + 模糊消散，错峰 0.15/0.3/0.4/0.5s */
    @keyframes enter { from { opacity:0; transform:translateY(24px); filter:blur(10px); }
      to { opacity:1; transform:none; filter:none; } }
    .hero-enter { animation:enter .9s ease both; }
    .hero-left > .hero-enter:nth-child(2) { animation-delay:.15s; }
    .hero-left > .hero-enter:nth-child(3) { animation-delay:.3s; }
    .hero-left > .hero-enter:nth-child(4) { animation-delay:.4s; }
    .hero-left > .hero-enter:nth-child(5) { animation-delay:.5s; }
    .hero-panel { animation:enter .9s ease both .25s; }

    /* ===== 概念条 ===== */
    .concept { padding:88px 0; text-align:center; }
    .concept-formula { font-size:clamp(1.4rem,3vw,2rem); font-weight:700; letter-spacing:.2px; }
    .concept-formula b { color:var(--brand); }
    .concept-sub { margin-top:10px; color:var(--text-description); font-size:15px; }
    .concept-desc { margin-top:18px; max-width:640px; margin-inline:auto; color:var(--text-description); font-size:15px; }

    /* ===== 区块通用 ===== */
    .section { padding:88px 0; }
    .section-title { font-size:clamp(1.6rem,3vw,2.2rem); text-align:center; }
    .section-sub { text-align:center; color:var(--text-description); margin-top:10px; }

    /* ===== 三大痛点支柱（4.3） ===== */
    .pillars { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-top:48px; }
    .pillar { position:relative; background:var(--bg-surface-1); border:1px solid var(--border-default);
      border-radius:var(--radius-card); padding:28px; }
    .pillar::after { content:""; position:absolute; inset:0; border-radius:inherit; background:rgba(255,255,255,.05);
      opacity:0; transition:opacity .3s ease; pointer-events:none; }
    .pillar:hover::after { opacity:1; }
    .pillar-num { font-size:44px; font-weight:700; color:var(--brand); line-height:1; }
    .pillar h3 { font-size:22px; margin-top:10px; }
    .pillar .promise { color:var(--text-description); font-size:14px; margin-top:4px; }
    .pillar-card { background:var(--bg-surface-2); border:1px solid var(--border-default); border-radius:8px;
      padding:12px 14px; margin-top:12px; }
    .pillar-card h4 { font-size:14px; }
    .pillar-card p { font-size:13px; color:var(--text-description); margin-top:2px; }

    /* ===== 平台支持行 ===== */
    .platforms { text-align:center; margin-top:56px; }
    .platform-badges { display:flex; flex-wrap:wrap; justify-content:center; gap:10px; margin-top:16px; }
    /* 流水线流程图：节点卡 + 箭头 */
    .pipeline { display:flex; align-items:stretch; justify-content:center; flex-wrap:wrap; margin-top:28px; }
    .pipeline-node { flex:1; min-width:120px; max-width:170px; background:var(--bg-surface-1);
      border:1px solid var(--border-default); border-radius:var(--radius-card);
      padding:14px 12px; text-align:center; position:relative; }
    .pipeline-node::after { content:""; position:absolute; inset:0; border-radius:inherit;
      background:rgba(255,255,255,.05); opacity:0; transition:opacity .3s ease; pointer-events:none; }
    .pipeline-node:hover::after { opacity:1; }
    .pipeline-step { display:block; font-size:12px; color:var(--brand); font-weight:600; }
    .pipeline-name { display:block; font-size:16px; font-weight:700; margin-top:2px; }
    .pipeline-desc { font-size:12px; color:var(--text-description); margin-top:4px; }
    .pipeline-arrow { display:flex; align-items:center; color:var(--brand); font-size:18px; padding:0 6px; }

    /* ===== 开始创作三步 ===== */
    .steps { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-top:48px; }
    .step { background:var(--bg-surface-1); border:1px solid var(--border-default); border-radius:var(--radius-card); padding:24px; }
    .step-num { font-size:14px; color:var(--brand); font-weight:600; }
    .step h4 { margin:6px 0 8px; font-size:17px; }
    .step p { font-size:14px; color:var(--text-description); }
    .step code { background:rgba(0,0,0,.35); padding:2px 6px; border-radius:4px; font-size:13px; }

    /* ===== FAQ（原生 details/summary，零 JS） ===== */
    .faq { max-width:720px; margin:40px auto 0; display:flex; flex-direction:column; gap:12px; }
    .faq details { background:var(--bg-surface-1); border:1px solid var(--border-default); border-radius:var(--radius-card); padding:16px 20px; }
    .faq summary { cursor:pointer; font-weight:500; font-size:15px; }
    .faq details p { margin-top:8px; color:var(--text-description); font-size:14px; }

    /* ===== 生态 CTA / 页脚 ===== */
    .cta-box { text-align:center; background:var(--bg-surface-1); border:1px solid var(--border-default);
      border-radius:var(--radius-card); padding:56px 32px; }
    .cta-box p { color:var(--text-description); max-width:560px; margin:14px auto 0; }
    .trust { margin-top:22px; font-size:14px; color:var(--text-description); }
    footer { text-align:center; padding:40px 0 48px; color:var(--text-description); font-size:13px;
      border-top:1px solid var(--border-default); margin-top:88px; }

    /* ===== 滚动入场（4.5） ===== */
    .reveal { opacity:0; transform:translateY(20px); transition:opacity .6s ease, transform .6s ease; }
    .reveal.in { opacity:1; transform:none; }

    /* ===== 响应式 ===== */
    @media (max-width:900px) {
      .hero-inner { grid-template-columns:1fr; gap:40px; padding:110px 0 64px; }
      .hero-panel { display:none; }
      .pillars, .steps { grid-template-columns:1fr; }
      .pipeline { flex-direction:column; align-items:center; }
      .pipeline-node { max-width:280px; width:100%; }
      .pipeline-arrow { transform:rotate(90deg); padding:6px 0; }
    }
    @media (prefers-reduced-motion:reduce) {
      .hero-enter, .hero-panel { animation:none; }
      .reveal { opacity:1; transform:none; transition:none; }
    }
  </style>
</head>
<body>
  <!-- 导航 -->
  <nav class="nav"><div class="container nav-inner">
    <a class="nav-brand" href="#">Awesome Novel</a>
    <div class="nav-links">
      <a href="https://github.com/modoojunko/awesome-novel-agent/blob/main/README.md">文档</a>
      <a href="https://github.com/modoojunko/awesome-novel-agent">GitHub</a>
      <a href="#start">快速开始</a>
    </div>
  </div></nav>

  <!-- Hero：左文案右示例面板 -->
  <header class="hero">
    <div class="hero-grid"></div>
    <div class="hero-glow"></div>
    <div class="container hero-inner">
      <div class="hero-left">
        <div class="hero-enter">
          <div class="hero-brand-line">
            <span class="hero-brand">Awesome Novel</span>
            <span class="hero-badge">开源 · 支持 6 平台</span>
          </div>
        </div>
        <div class="hero-enter"><h1>人铸灵魂，AI行笔墨</h1></div>
        <div class="hero-enter">
          <p class="hero-sub1">AI 是笔，你才是作者。构想由你铸就，文字交给智能体，成稿由你拍板。</p>
          <p class="hero-sub2">Awesome Novel 是开源的 AI 小说创作工作流——9 个写作智能体从世界观到正文自动推进，适配 Claude Code / OpenCode / Reasonix / Codex / ZCode / DSH。</p>
        </div>
        <div class="hero-enter hero-cta">
          <a class="btn btn-primary" href="#start">开始写作</a>
          <a class="btn btn-secondary" href="https://github.com/modoojunko/awesome-novel-agent/blob/main/README.md">查看文档</a>
        </div>
        <div class="hero-enter hero-code">
          <div class="code-block">$ ./install.sh &lt;你的平台&gt;</div>
          <p class="code-note">不想输命令？对 AI 说"帮我安装 awesome-novel-agent"即可，1 分钟装好。</p>
        </div>
      </div>
      <div class="hero-panel" id="spotlight">
        <div class="spotlight-viewport">
          <div class="spotlight-card active">
            <div class="panel-head">
              <span class="tag tag-brand">亮点 01</span>
              <span class="tag">文风蒸馏</span>
            </div>
            <h4 class="spotlight-title">越写越像你</h4>
            <div class="spotlight-stats">
              <div class="stat"><b>14.2</b><span>句长 / 字</span></div>
              <div class="stat"><b>38%</b><span>对话占比</span></div>
              <div class="stat"><b>6.1</b><span>形容词 / 百字</span></div>
            </div>
            <div class="panel-meta"><span>✓ 导入 3 本样本，风格自动校准</span></div>
          </div>
          <div class="spotlight-card">
            <div class="panel-head">
              <span class="tag tag-brand">亮点 02</span>
              <span class="tag">剧情推演</span>
            </div>
            <h4 class="spotlight-title">卡住了？角色先演一遍</h4>
            <div class="spotlight-stats">
              <div class="stat"><b>集市</b><span>推演场景</span></div>
              <div class="stat"><b>2 人</b><span>叶秋 · 王虎</span></div>
              <div class="stat"><b>告密</b><span>推演走向</span></div>
            </div>
            <div class="panel-meta"><span>✓ 合理走向自然浮现</span></div>
          </div>
          <div class="spotlight-card">
            <div class="panel-head">
              <span class="tag tag-brand">亮点 03</span>
              <span class="tag">伏笔跟踪</span>
            </div>
            <h4 class="spotlight-title">埋的坑，不会忘</h4>
            <div class="spotlight-stats">
              <div class="stat"><b>2 处</b><span>未兑现伏笔</span></div>
              <div class="stat"><b>9 章</b><span>最陈旧 ·「玉佩」</span></div>
              <div class="stat"><b>高</b><span>收束风险</span></div>
            </div>
            <div class="panel-meta"><span class="warn">⚠ 建议第 21 章前收束</span></div>
          </div>
          <div class="spotlight-card">
            <div class="panel-head">
              <span class="tag tag-brand">亮点 04</span>
              <span class="tag">角色状态更新</span>
            </div>
            <h4 class="spotlight-title">人设不崩，每章同步</h4>
            <div class="spotlight-stats">
              <div class="stat"><b>四层</b><span>叶秋修为</span></div>
              <div class="stat"><b>结怨</b><span>与王虎</span></div>
              <div class="stat"><b>爆发</b><span>情绪峰值</span></div>
            </div>
            <div class="panel-meta"><span>✓ 第 12 章状态已同步</span></div>
          </div>
          <div class="spotlight-card">
            <div class="panel-head">
              <span class="tag tag-brand">亮点 05</span>
              <span class="tag">本地数据安全</span>
            </div>
            <h4 class="spotlight-title">稿子就是文件</h4>
            <div class="spotlight-stats">
              <div class="stat"><b>本地</b><span>纯文本存储</span></div>
              <div class="stat"><b>0</b><span>云端上传</span></div>
              <div class="stat"><b>即走</b><span>拷贝目录迁移</span></div>
            </div>
            <div class="panel-meta"><span>✓ 编辑器随时直接改</span></div>
          </div>
        </div>
        <div class="spotlight-dots">
          <button class="dot active" aria-label="亮点 1"></button>
          <button class="dot" aria-label="亮点 2"></button>
          <button class="dot" aria-label="亮点 3"></button>
          <button class="dot" aria-label="亮点 4"></button>
          <button class="dot" aria-label="亮点 5"></button>
        </div>
      </div>
    </div>
  </header>

  <!-- 概念条 -->
  <section class="concept reveal">
    <div class="container">
      <p class="concept-formula">小说创作 = <b>人的构想</b> + <b>AI 的笔力</b></p>
      <p class="concept-sub">人铸灵魂，AI 行笔墨</p>
      <p class="concept-desc">构想归你：世界观、角色、大纲。笔力归模型：行文、节奏、净化——Awesome Novel 把两者编排成可复现的工作流。</p>
    </div>
  </section>

  <!-- 三大痛点支柱 -->
  <section class="section reveal">
    <div class="container">
      <h2 class="section-title">设计思路</h2>
      <p class="section-sub">三个最常见的写作困境，一次解决</p>
      <div class="pillars">
        <div class="pillar">
          <div class="pillar-num">01</div>
          <h3>怕烂尾？</h3>
          <p class="promise">开写前有蓝图，过程中有人盯</p>
          <div class="pillar-card"><h4>四维卷纲</h4><p>情绪走向、冲突阶梯、信息差、场景卡先规划再动笔，长篇连载不跑偏。</p></div>
          <div class="pillar-card"><h4>9 智能体 自动推进</h4><p>卷纲、章纲、正文、评审、归档自动流转，你只审阅与决策，不用记流程。</p></div>
          <div class="pillar-card"><h4>剧情推演沙盘</h4><p>卡剧情时让角色在沙盘里演一遍，合情合理的走向自然浮现。</p></div>
        </div>
        <div class="pillar">
          <div class="pillar-num">02</div>
          <h3>不像你？</h3>
          <p class="promise">导入即学会，越写越像你</p>
          <div class="pillar-card"><h4>文风蒸馏</h4><p>把你喜欢的小说丢进样本库，自动提炼句长、对话占比等量化参数。</p></div>
          <div class="pillar-card"><h4>动态记忆</h4><p>每次修改反馈自动沉淀为记忆，高频规则晋升永久规则，纠正过一次就不再犯。</p></div>
          <div class="pillar-card"><h4>24 套题材画像</h4><p>仙侠、都市、悬疑、历史等预置档案，人设倾向与叙事语气直接可用。</p></div>
        </div>
        <div class="pillar">
          <div class="pillar-num">03</div>
          <h3>有 AI 味？</h3>
          <p class="promise">机器腔与逻辑漏洞，归档前拦下</p>
          <div class="pillar-card"><h4>去 AI 味</h4><p>提示词组装注入反 AI 规则，成稿后 六道闸 管线检测并量化评分。</p></div>
          <div class="pillar-card"><h4>伏笔跟踪</h4><p>自动扫描未兑现与新埋的钩子，提醒收束——埋的坑不会忘。</p></div>
          <div class="pillar-card"><h4>角色状态</h4><p>每章归档自动更新角色状态与情绪弧线，下一章 AI 记得他经历了什么。</p></div>
          <div class="pillar-card"><h4>节奏检查</h4><p>连续高压 3 章或平淡 2 章自动提醒，避免读者弃书。</p></div>
        </div>
      </div>
      <div class="platforms">
        <div class="platform-badges">
          <span class="tag">Claude Code</span><span class="tag">OpenCode</span><span class="tag">Reasonix</span><span class="tag">Codex</span><span class="tag">ZCode</span><span class="tag">DeepSeek Harness</span>
        </div>
        <div class="pipeline">
          <div class="pipeline-node"><span class="pipeline-step">01</span><span class="pipeline-name">设定</span><p class="pipeline-desc">题材 · 世界观 · 角色</p></div>
          <span class="pipeline-arrow">→</span>
          <div class="pipeline-node"><span class="pipeline-step">02</span><span class="pipeline-name">卷纲</span><p class="pipeline-desc">情绪走向 · 冲突阶梯</p></div>
          <span class="pipeline-arrow">→</span>
          <div class="pipeline-node"><span class="pipeline-step">03</span><span class="pipeline-name">章纲</span><p class="pipeline-desc">场景卡 · 微弧线</p></div>
          <span class="pipeline-arrow">→</span>
          <div class="pipeline-node"><span class="pipeline-step">04</span><span class="pipeline-name">正文</span><p class="pipeline-desc">提示词驱动成稿</p></div>
          <span class="pipeline-arrow">→</span>
          <div class="pipeline-node"><span class="pipeline-step">05</span><span class="pipeline-name">净化</span><p class="pipeline-desc">去 AI 味 · 六道闸</p></div>
          <span class="pipeline-arrow">→</span>
          <div class="pipeline-node"><span class="pipeline-step">06</span><span class="pipeline-name">归档</span><p class="pipeline-desc">角色状态 · 伏笔更新</p></div>
        </div>
        <p style="color:var(--text-description); margin-top:18px;">六个平台，跑同一条流水线。换工具，创作状态无缝续写。</p>
      </div>
    </div>
  </section>

  <!-- 开始创作 -->
  <section class="section reveal" id="start">
    <div class="container">
      <h2 class="section-title">开始创作</h2>
      <p class="section-sub">三步，从零到第一章</p>
      <div class="steps">
        <div class="step">
          <div class="step-num">步骤 1 · 安装</div>
          <h4>对 AI 说一句话</h4>
          <p>打开任一支持的 AI 终端，说 <code>帮我安装 awesome-novel-agent，仓库在 https://github.com/modoojunko/awesome-novel-agent</code>，AI 自动运行安装脚本，不用复制粘贴命令。</p>
        </div>
        <div class="step">
          <div class="step-num">步骤 2 · 初始化</div>
          <h4>生成项目骨架</h4>
          <p>在放小说的目录输入 <code>/awesome-novel</code>（或"帮我写本小说"），自动生成世界观、角色、大纲的项目结构并进入设定讨论。</p>
        </div>
        <div class="step">
          <div class="step-num">步骤 3 · 写作</div>
          <h4>进入写作循环</h4>
          <p><code>@novel-agent</code> 或"帮我继续写"进入循环；常用指令：<code>写下一章</code> / <code>跑一下推演</code> / <code>全自动模式</code>。</p>
        </div>
      </div>
    </div>
  </section>

  <!-- FAQ -->
  <section class="section reveal">
    <div class="container">
      <h2 class="section-title">常见问题</h2>
      <div class="faq">
        <details><summary>我不会编程，能装吗？</summary><p>能。对 AI 说一句话即可完成安装，全程不用复制粘贴命令。</p></details>
        <details><summary>生成的文字有 AI 味怎么办？</summary><p>默认即"低 AI 味"配置：禁用常见机器腔句式 + 成稿自动检测；你的修改还会被记录为专属规则。</p></details>
        <details><summary>可以用自己的写作风格吗？</summary><p>可以。导入参考样本自动蒸馏，或直接写进风格文件，后续章节都按此风格。</p></details>
        <details><summary>写到一半可以改设定吗？</summary><p>随时说"改一下世界观里的 XXX"，智能体会同步更新后续章节。</p></details>
        <details><summary>旧项目能迁移吗？</summary><p>升级后自动检测旧版格式并引导迁移，原文件保留备份。</p></details>
      </div>
    </div>
  </section>

  <!-- 生态 CTA -->
  <section class="section reveal">
    <div class="container">
      <div class="cta-box">
        <h2>加入创作社区</h2>
        <p>项目仍处于活跃迭代阶段，题材档案与反 AI 规则库持续扩充。期待与创作者一起，在开源、可复用、可组合的创作基础设施上，探索 AI 写作的上限。</p>
        <div class="hero-cta" style="justify-content:center">
          <a class="btn btn-primary" href="https://github.com/modoojunko/awesome-novel-agent">GitHub</a>
          <a class="btn btn-secondary" href="https://github.com/modoojunko/awesome-novel-agent/blob/main/README.md">文档</a>
        </div>
        <p class="trust">个人使用免费 · GPLv3 开源 · QQ 交流群 1006050538</p>
      </div>
    </div>
  </section>

  <footer>
    <div class="container">
      <p>GPLv3 开源 · 个人使用免费 · © 2026 Awesome Novel</p>
      <p style="margin-top:6px"><a href="https://github.com/modoojunko/awesome-novel-agent">GitHub</a> · <a href="https://github.com/modoojunko/awesome-novel-agent/blob/main/README.md">文档</a></p>
    </div>
  </footer>

  <script>
    // 滚动入场：优先尊重系统减弱动效设置，否则 IntersectionObserver 逐块浮现
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.querySelectorAll('.reveal').forEach(el => el.classList.add('in'));
    } else {
      const io = new IntersectionObserver(entries => {
        entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
      }, { threshold: 0.15 });
      document.querySelectorAll('.reveal').forEach(el => io.observe(el));
    }

    // 亮点卡轮播：4s 自动切换 + 指示点点击 + 悬停暂停；减弱动效时静态显示第一张
    (function () {
      const panel = document.getElementById('spotlight');
      if (!panel || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      const cards = panel.querySelectorAll('.spotlight-card');
      const dots = panel.querySelectorAll('.dot');
      let i = 0, timer = null;
      function show(n) {
        cards[i].classList.remove('active'); dots[i].classList.remove('active');
        i = (n + cards.length) % cards.length;
        cards[i].classList.add('active'); dots[i].classList.add('active');
      }
      function start() { timer = setInterval(() => show(i + 1), 4000); }
      function stop() { clearInterval(timer); }
      dots.forEach((d, n) => d.addEventListener('click', () => { show(n); stop(); start(); }));
      panel.addEventListener('mouseenter', stop);
      panel.addEventListener('mouseleave', start);
      start();
    })();
  </script>
</body>
</html>
```

## 6. 整体验收清单

- [ ] 单文件零依赖，`file://` 直接打开可看
- [ ] 桌面 1280px / 移动 375px 两档肉眼检查无错位
- [ ] 第一屏内可见：徽标 + h1 + 主 CTA + 安装命令
- [ ] 强调色全页出现次数收敛（品牌蓝 ≤ 3 类元素）
- [ ] 卡片 hover / 按钮涟漪 / 滚动入场生效，且 `prefers-reduced-motion` 下全部禁用
- [ ] 文案全部中文、无错别字；原功能信息（7 项 + 平台列表）无一遗漏
- [ ] 不含版权素材（纯 CSS，无图片）

## 7. 工作量与风险

- 重写单文件，预计 ~300 行 HTML/CSS + 20 行 JS；改动集中在 `index.html`，不动仓库其他部分
- 风险低：无依赖、无构建、CI 不检查 HTML；唯一注意点是 GitHub Pages 缓存，部署后强刷可见
- 后续可选（不在本次范围）：README 徽章、英文版页、OG 图
