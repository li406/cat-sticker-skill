# Project Governance

本仓库使用 Owner-Driven 轻量治理。

开始开发前优先读取：

1. `PRODUCT-GOAL.md`
2. `ROADMAP.md`
3. `CURRENT-STAGE.md`
4. `BACKLOG.md`

详细方法见 `docs/ops/PROJECT-OPERATING-MANUAL.md`。

## 执行原则

- 同时只推进一个 `CURRENT-STAGE`。
- 所有主要工作必须直接服务当前 Stage。
- 新问题先分为 Blocker / Important / Polish。
- Blocker 现在修。
- Important / Polish 写入 Backlog，不得阻塞当前 Stage。
- Current Stage 验收全部通过且没有 Blocker 时，必须结束 Stage。
- “还能继续优化”不是继续当前 Stage 的理由。
- 默认禁止开放式“全面找问题” Review。
- 默认 Review 只检查是否存在阻止 Current Stage 的 Blocker。

## Owner 沟通

Owner 负责产品目标、实际使用反馈和阶段验收，不要求 Owner 做底层工程判断。

技术问题必须说明：

- 用户会看到什么
- 是否阻止当前 Stage
- 是否必须现在修

## 强模型 / C2C

普通明确执行由当前 Coding Agent 自己完成。

仅在 Roadmap、复杂 Stage、架构、跨模块复杂问题、长期卡住的根因或 Stage 结束高价值 Review 时优先考虑强模型 / C2C。

不要因为“需要思考”就自动调用。

## 项目记忆

聊天不是长期项目状态。

影响未来的信息必须落盘：

- 产品方向 → `PRODUCT-GOAL.md`
- 阶段顺序 → `ROADMAP.md`
- 当前范围和验收 → `CURRENT-STAGE.md`
- 非当前事项 → `BACKLOG.md`
- 实现事实 → 代码 / tests / git

如果 Owner 只说“继续”，默认含义是：

> 继续 CURRENT-STAGE 中下一项未完成工作。

不得解释为自由寻找整个项目还有什么可以改善。
