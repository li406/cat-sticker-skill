# CURRENT-STAGE

## Stage

Stage 3 — 开源发布与其他 Agent 兼容

## 唯一目标

完成后，用户能够：

> 把仓库公开到 GitHub 后，一个从没参与过开发的人（或一个新 AI Agent）clone 下来，照着 README 和 SKILL.md 就能独立跑通，不需要翻聊天记录、不需要问作者。

## 必须完成

- [ ] 找一台干净环境（或让朋友/新对话）clone 仓库，按 README Quick Start 走一遍 `doctor` + `smoke-test`，能跑通
- [ ] SKILL.md 能让一个没看过历史对话的 Agent 独立走完：看参考图 → 规划 → 批准 → 生成 → 打包
- [ ] `references/agent-compatibility.md` 只写真实实测过的环境（豆包办公任务 Windows 已实测；Codex 未实测就明确写"未验证"）
- [ ] 仓库 public 前 `privacy-check` 仍 PASS，确认无私人照片、无 API key、无真实猫图
- [ ] LICENSE（PolyForm Noncommercial）、SECURITY.md、CONTRIBUTING.md 可读且与实际一致
- [ ] README 不夸大兼容：不写"支持所有 Agent"，只写实测过的

## Allowed Scope

- 补文档、修文档里的错误命令、补缺失的依赖说明
- 修"新用户第一次跑就报错"的真实问题
- 把 Owner 实测过的环境写进兼容文档
- 仓库 public 前的最后隐私检查

## 明确不做

- 不做 Codex 双端实测（Owner 已决定不做）
- 不做 GIF / 动图 / 第二 provider / Web UI
- 不为"代码更优雅"做重构
- 不做市场推广、SEO、示例网站
- 不收集用户反馈做 SaaS 化
- 不预先写"未来支持 X"的承诺

## Owner 验收步骤

1. 用一个新的干净对话（或让朋友）clone 仓库，按 README 走 Quick Start
2. 确认 `cat-sticker doctor` 和 `cat-sticker smoke-test` 能跑通
3. 确认 SKILL.md 自己读一遍就能开始做表情，不需要翻聊天记录
4. 看一眼 `references/agent-compatibility.md`，确认没吹
5. 确认仓库 public 后，`privacy-check` 仍 PASS
6. 点 GitHub 上的 About / Releases，确认 README 首屏说清楚这是什么、怎么用、什么 license

期望：

- 新用户第一次跑不卡壳
- 文档里写的命令和实际 CLI 一致
- 没有"作者才知道"的隐藏步骤

## Blocker

只有以下问题可以阻止阶段完成：

- 干净环境 clone 下来跑不通（缺依赖、命令名错、文档和代码不一致）
- SKILL.md 引导新 Agent 做错事或卡住
- 仓库 public 后发现私人照片/key/真实猫图
- README 承诺了没实测过的兼容，导致别人用不了来骂

其他小毛病（文档措辞、排版）都是 Polish。

## Stop Condition

当：

- 所有 Owner 验收步骤完成
- 没有 Blocker

则 Stage 3 立即结束，仓库正式 public。过程中发现的 Important / Polish 进入 BACKLOG.md。
