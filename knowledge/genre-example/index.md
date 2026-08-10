# 题材注册表

> Phase 2 选题材时展示给作者。与 `tools/init.py` 的 `GENRES` 顺序一致（1-24），编号可直接用于 `--genre <编号>`。
> 每个条目指向 `knowledge/genre-example/` 下的 example 文件，包含 style_blueprint、genre_config、genre_taboos、prompt_segment、story_arc_templates。

| 编号 | 题材 | id | 说明 |
|------|------|----|------|
| 1 | 东方仙侠 | `xianxia` | 修仙、修道、修真等仙侠元素 |
| 2 | 传统玄幻 | `xuanhuan` | 废柴逆袭、强者重生等传统玄幻，高武世界、异世大陆 |
| 3 | 都市大类 | `urban` | 现代都市基类，子分类变体覆盖差异化字段 |
| 4 | 都市言情 | `urban-romance` | 都市情感、恋爱向 |
| 5 | 都市日常 | `urban-daily` | 都市情感、现实生活等都市文 |
| 6 | 都市种田 | `urban-farming` | 重生年代文、职场商战文、种田建设等都市文 |
| 7 | 都市脑洞 | `urban-brained` | 拥有金手指系统的男频都市脑洞奇想 |
| 8 | 都市修真 | `urban-cultivation` | 以修真为力量体系的都市文 |
| 9 | 都市高武 | `urban-high-martial` | 都市架空，全民拥有修炼体系、灵气复苏等 |
| 10 | 战神赘婿 | `war-god` | 都市向战神、兵王文 |
| 11 | 西方奇幻 | `western-fantasy` | 偏西方世界背景，包含魔法、斗气、奥术等奇幻元素 |
| 12 | 古风权谋 | `ancient-politics` | 古代朝堂、权谋、争霸等 |
| 13 | 历史大类 | `historical` | 历史文基类，子分类变体覆盖差异化字段 |
| 14 | 历史古代 | `historical-ancient` | 以种田、朝堂、智谋、争霸、科举等为主，无金手指非系统历史文 |
| 15 | 历史脑洞 | `historical-brained` | 脑洞向历史，一般有金手指 |
| 16 | 抗战谍战 | `anti-japanese-war` | 抗战时期的军事战争和间谍情报的男频小说 |
| 17 | 科幻末世 | `scifi-apocalypse` | 末世、丧尸、星际、机甲、未来科技等 |
| 18 | 悬疑刑侦 | `suspense-crime` | 男频探案、悬疑、推理 |
| 19 | 悬疑灵异 | `suspense-paranormal` | 男频探案、悬疑、恐怖、风水奇术等 |
| 20 | 悬疑脑洞 | `suspense-brained` | 脑洞向的悬疑灵异、破案探险类，以及诡异复苏、惊悚游戏、规则怪谈等 |
| 21 | 游戏体育 | `game-sports` | 网游、竞技、体育及穿入游戏或世界游戏化 |
| 22 | 动漫衍生 | `anime-derivative` | 游戏、动漫等偏二次元向的同人作品 |
| 23 | 衍生类 | `derivative` | 衍生类基类，corpus 共用 |
| 24 | 男频衍生 | `male-derivative` | 影视剧男频同人小说 |

> 编号与 `tools/init.py --genre <编号>` 一一对应；`xuanhuan-brained` 是传统玄幻的变体 corpus（`xuanhuan.md`），不在独立编号列表内。
