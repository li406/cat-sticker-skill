# 全新项目：轻量治理启动指令

## 目标

从项目第一天建立可持续的 Owner-Driven 开发方式。

先弄清产品，再开始写代码。

## Phase 1：Product Discovery

先与 Owner 讨论：

1. 这个产品给谁使用？
2. 用户最核心想完成什么？
3. 为什么现有方式不够？
4. V1 如果只能做 3–5 件事，是什么？
5. 哪些明确不属于 V1？
6. Owner 最后怎样亲手判断“这个版本能用了”？

不要先把对话带到：

- 框架
- 数据库
- 状态管理
- CI
- 云架构
- 目录结构

除非这些技术约束直接限制产品目标。

## Phase 2：建立 PRODUCT-GOAL

写：

`PRODUCT-GOAL.md`

用用户语言，不写大段技术设计。

让 Owner 确认。

## Phase 3：建立 ROADMAP

把 V1 拆成少量垂直 Stage。

优先：

```text
Stage 1：最小核心流程可使用
Stage 2：核心数据真实保存/读取
Stage 3：第二个主要能力
Stage 4：关键失败与恢复
Stage 5：真实使用测试
Stage 6：V1 收尾
```

实际阶段按项目调整。

每个阶段必须产生用户可感知结果。

## Phase 4：建立 CURRENT-STAGE

只定义 Stage 1。

必须包含：

- 唯一目标
- Allowed Scope
- 明确不做
- Owner 验收步骤
- Blocker
- Stop Condition

第一个 Stage 应尽量形成最小但完整的用户闭环。

## Phase 5：建立 BACKLOG

把：

- 暂不实现功能
- 技术优化
- Future Ideas
- Polish

统一放入 Backlog。

## Phase 6：安装长期治理

将通用治理核心规则写入当前 Agent 的项目级 instruction。

Codex 项目优先使用根 `AGENTS.md`。

详细手册：

`docs/ops/PROJECT-OPERATING-MANUAL.md`

## Phase 7：技术设计

只有产品目标和第一个 Stage 已确定后，再选择：

- 技术栈
- 数据存储
- 项目结构
- 测试方式

原则：

优先最简单、足够支撑 V1 的实现。

不要为了未来可能需求提前搭大型架构。

## Phase 8：开始开发

开始后所有工作只推进 CURRENT-STAGE。

新问题遵守：

- Blocker → 现在修
- Important → Backlog
- Polish → Backlog / 忽略

## Phase 9：阶段验收

Owner 实际测试。

如果验收通过且没有 Blocker：

- Stage done
- 更新 Roadmap
- 保存 Backlog
- 定义下一 Stage
- 建议新开会话

不要继续无限优化 Stage 1。

## Phase 10：何时考虑 OpenSpec

至少先经历若干真实 Stage。

只有当轻量治理出现真实不足，再评估 OpenSpec。

不要为了“显得专业”提前引入流程。
