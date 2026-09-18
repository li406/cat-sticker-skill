# 已开发项目：轻量治理迁移指令

## 目标

把当前已经开发一段时间的项目迁移到 Owner-Driven 四层治理。

这是治理迁移，不是代码重构。

本轮完成后停止，不继续产品开发。

## Step 1：只读恢复事实

检查：

- git status / branch
- 当前代码
- tests / build 状态
- README
- AGENTS / agent instructions
- 现有产品目标
- roadmap / sprint / plan
- 当前任务
- 已知问题
- 历史 specs / reviews

不要先修代码。

## Step 2：恢复产品 North Star

基于仓库事实与 Owner 已明确需求，建立或整理：

`PRODUCT-GOAL.md`

必须说明：

- 谁使用
- 为什么做
- V1 必须实现什么
- 成功是什么
- 明确不做什么

不得因当前技术困难降低已确认产品目标。

不确定的产品问题才询问 Owner；不要让 Owner回答底层技术选型。

## Step 3：重建 Roadmap

建立：

`ROADMAP.md`

把过去已完成工作压缩成阶段摘要。

把未来工作按用户可感知结果重新排列。

每个 Stage 必须说明：

> 完成后用户比之前多能做什么？

不要建立纯代码清理 Stage，除非它是产品前进不可绕过的条件。

## Step 4：确定唯一 Current Stage

建立：

`CURRENT-STAGE.md`

从当前真实状态选择最适合继续推进的一个阶段。

优先：

- 最接近真实可用闭环
- Owner 能亲手验收
- 范围清楚
- 不要求先消灭所有历史问题

写清：

- 目标
- 必须完成
- 明确不做
- Owner 验收步骤
- Blocker
- Stop Condition

## Step 5：整理 Backlog

建立：

`BACKLOG.md`

把非当前 Stage 的：

- Important
- Polish
- Future Ideas
- 历史技术债

放入 Backlog。

不得把这些事项顺手继续执行。

## Step 6：审查长期规则

检查现有 Agent 规则是否包含：

- 所有问题都必须马上修
- 所有 review 都要全面
- 必须零问题才能继续
- 所有思考都必须调用强模型
- 可以随意扩大任务范围

如果冲突，做最小修改。

保留仍有效的安全、权限、测试和项目特定约束。

## Step 7：安装通用治理

将 `UNIVERSAL-GOVERNANCE.md` 的核心规则：

- 对 Codex：最小化合并进根 `AGENTS.md`
- 对其他 Agent：放入该 Agent 的项目级长期 instruction

详细手册保存为：

`docs/ops/PROJECT-OPERATING-MANUAL.md`

不要把完整手册全部塞进每次自动加载的短指令文件。

## Step 8：验证一致性

确认：

- Product Goal 与 Roadmap 不冲突
- Roadmap 与 Current Stage 一致
- Backlog 没有偷偷成为 Current Stage
- 旧 sprint/spec 不覆盖四层权威
- 没有开放式无限 Review 规则
- 没有非 Blocker 强制修复规则

## Step 9：Git

治理迁移完成后：

- 查看 diff
- 确认无敏感信息
- commit
- 已授权则 push

## Step 10：停止

完成后不要开始 Current Stage。

报告：

```text
治理迁移完成

Product Goal：
当前真实进度：
Current Stage：
Owner 验收方式：
Backlog 摘要：
修正的旧规则：
Git commit/push：
下一步：
```
