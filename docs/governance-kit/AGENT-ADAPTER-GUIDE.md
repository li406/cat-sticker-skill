# Agent Adapter Guide

同一套治理可以用于不同 Coding Agent。

## Codex

优先：

- 将 `AGENTS-GOVERNANCE-SNIPPET.md` 合并到仓库根 `AGENTS.md`
- 保留项目原有有效规则
- 详细手册放 `docs/ops/PROJECT-OPERATING-MANUAL.md`

不要把完整长手册全部塞进自动加载规则。

## 其他支持项目级规则的 Agent

把 `AGENTS-GOVERNANCE-SNIPPET.md` 放入该工具官方支持的项目级 instruction / rules 文件。

四层文件保持相同：

- PRODUCT-GOAL
- ROADMAP
- CURRENT-STAGE
- BACKLOG

不要因为换 Agent 就复制另一套项目状态。

## 不支持持久项目规则的 Agent

每次新会话先发送：

`prompts/SESSION-START-PROMPT.md`

并要求它读取仓库四层文件。

## 多 Agent 同时使用

所有 Agent 共用同一个 Git 仓库事实。

禁止分别维护：

- Codex 版 Roadmap
- 豆包版 Roadmap
- GPT 版 Current Stage

跨 Agent 的长期结论必须回写同一套四层文件。
