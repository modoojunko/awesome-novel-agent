# v4.28.0 版本说明

> **关键词：** AGPL-3.0 许可证切换 + 第三方 LLM 服务声明

---

## 一句话

项目许可证由 GPLv3 整体切换为 AGPL-3.0，README（中英）新增第三方 LLM API & Token 服务声明——开源协议收紧一档，项目与第三方付费服务的权责边界写明。

## 这版做了什么

| 改动 | 说明 |
|------|------|
| **许可证 AGPL-3.0** | LICENSE 替换为 gnu.org 官方 AGPL-3.0 全文（与官方文本逐字节一致）。11 个文件同步：两份 LICENSE-DECLARATION、双 README 徽章与声明、install.sh / install.ps1 文件头协议声明（保留 or-later 语义）、skill.json、index.html 落地页、AGENTS.md、CONTRIBUTING.md |
| **第三方 LLM 服务声明** | README.md / README-en.md 末尾新增「第三方LLM API & Token服务说明」：项目本身不提供任何大模型、Token 付费服务；文档与示例配置中的第三方 LLM 服务商仅为技术兼容性演示；充值、API 调用、内容生成、退款、稳定性均由第三方服务商独立承担；项目不背书任何第三方付费 API；使用第三方 API 生成内容请自行遵守相关法律法规 |

## 兼容性

- 纯许可证与文档变更，无代码行为变化；安装脚本仅改注释头（bash -n 通过）
- 「个人免费、商用需作者授权」立场不变；AGPL-3.0 第 13 条（网络提供服务同样触发开源义务）与该立场一致
- docs/releasenotes/ 历史记录中的 GPLv3 表述保留不改写；AGPL 正文对 GPL 的引用属协议原文

## 测试

- CI lint 绿（含 check-version 版本一致性）；skill.json JSON 解析通过；全仓无 GPLv3 残留（历史发版记录与协议原文除外）
- LICENSE 与 https://www.gnu.org/licenses/agpl-3.0.txt 逐字节 diff 一致
- review-agent 评审两轮（PR #135 / #136）均无发现
