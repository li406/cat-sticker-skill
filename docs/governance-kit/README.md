# AI 项目轻量治理框架

适用于：

- Codex
- 豆包或其他 AI Coding Agent
- 已经开发了一段时间、容易跑偏的项目
- 全新开发项目
- 使用 GitHub / Git 仓库保存长期状态的项目

## 核心思想

不要让聊天记录承担项目记忆。

项目长期状态写进仓库，Agent 每次重新读取：

1. `PRODUCT-GOAL.md` — 为什么做、V1 是什么
2. `ROADMAP.md` — 按用户结果排列阶段
3. `CURRENT-STAGE.md` — 现在唯一要完成什么
4. `BACKLOG.md` — 现在不做什么

再用一份长期行为规则约束 Agent：

- 当前阶段优先
- 新问题先分级
- 非 Blocker 不阻塞阶段
- 验收通过立即停止
- 不进行无限开放式 Review
- 强模型 / C2C 只用于高价值规划与阶段验收

## 两种使用方式

### A. 已经进行中的项目

使用：

`prompts/BROWNFIELD-MIGRATION-PROMPT.md`

它要求 Agent：

- 先只读恢复真实状态
- 不先修代码
- 将历史项目迁移到四层治理
- 清理冲突规则
- 确定一个唯一 Current Stage
- 迁移完成后停止

### B. 全新项目

使用：

`prompts/GREENFIELD-KICKOFF-PROMPT.md`

它要求 Agent：

- 先跟 Owner 梳理产品目标
- 不先陷入技术选型
- 建立四层治理文件
- 规划少量可感知阶段
- 定义第一个可验收 Stage
- 然后才开始开发

## 推荐仓库结构

```text
repo/
├─ AGENTS.md                       # Codex 等可自动读取的简版长期规则
├─ PRODUCT-GOAL.md
├─ ROADMAP.md
├─ CURRENT-STAGE.md
├─ BACKLOG.md
├─ docs/
│  └─ ops/
│     └─ PROJECT-OPERATING-MANUAL.md
└─ ...代码
```

如果使用的 Agent 不读取 `AGENTS.md`：

- 把 `UNIVERSAL-GOVERNANCE.md` 放到该 Agent 支持的项目指令位置；
- 或在项目第一次会话中让 Agent读取并遵循；
- 四层文件仍保持相同，不随 Agent 改变。

## 何时考虑 OpenSpec

先用本框架跑几个真实阶段。

只有出现这些实际问题时再考虑 OpenSpec：

- feature change 横跨很多模块
- 需求经常反复解释
- 多 Agent 对同一 change 理解不一致
- 需要 proposal/spec/design/tasks 的正式生命周期
- 四层文件已经不足以表达复杂变更

OpenSpec 应作为“复杂 change 管理层”接入，不替代 Product Goal、Roadmap、Current Stage 和 Backlog。
