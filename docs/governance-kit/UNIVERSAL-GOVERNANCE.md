# Universal Owner-Driven AI Project Governance

## 1. 角色

Owner 负责：

- 产品想解决什么问题
- 用户体验
- 产品范围
- 阶段验收
- 是否改变方向

Agent 负责：

- 技术分析
- 实现
- 测试
- Git
- 技术风险分类
- 把技术问题翻译成用户影响

Owner 不需要充当工程师。

---

## 2. 长期项目状态

长期状态只保存在仓库，不依赖聊天记忆。

权威四层：

1. `PRODUCT-GOAL.md`
2. `ROADMAP.md`
3. `CURRENT-STAGE.md`
4. `BACKLOG.md`

聊天、旧计划、历史 sprint、旧 review 只能作为参考，不能自动覆盖当前四层权威。

---

## 3. PRODUCT-GOAL

保存：

- 产品为什么存在
- 给谁使用
- V1 必须实现什么
- 成功是什么
- 明确不做什么

除非 Owner 明确改变产品方向，否则 Agent 不得因实现困难改变 Product Goal。

---

## 4. ROADMAP

只保存阶段级路线。

每个阶段必须回答：

> 这一阶段完成以后，用户比上一阶段多能做什么？

不要把 Roadmap 变成几百个工程 task 的清单。

---

## 5. CURRENT-STAGE

任何时候只能有一个唯一 Current Stage。

必须包含：

- 唯一目标
- Allowed Scope
- 明确不做
- Owner 可执行的验收步骤
- Blocker 定义
- Stop Condition

默认所有开发工作必须直接服务 Current Stage。

---

## 6. BACKLOG

保存：

- Important
- Polish
- Future Ideas
- 当前阶段明确不处理的事项

Backlog 条目不能因为被记录就自动进入当前开发。

---

## 7. 问题分级

### Blocker

满足至少一个：

- Current Stage 核心验收无法完成
- 明显数据损坏或丢失
- 明确安全风险
- 不修就无法继续当前阶段

处理：现在修。

### Important

真实有影响，但不阻止 Current Stage。

处理：写入 Backlog，继续当前阶段。

### Polish

包括：

- 非必要重构
- 代码美化
- 小 UI 优化
- 低概率边缘情况
- 理论性能优化
- 非当前阶段测试增强

处理：Backlog 或忽略，不阻塞阶段。

---

## 8. 停止规则

当：

- Current Stage 验收条件全部满足
- 没有 Blocker

则必须：

1. 宣布 Stage 完成
2. Important / Polish 进入 Backlog
3. 更新 Roadmap
4. 停止继续优化当前 Stage
5. 准备下一 Stage

“还能继续改进”不是继续当前阶段的理由。

---

## 9. Review 规则

默认禁止：

> 全面检查项目还有什么问题。

默认 Review 问题：

> 是否存在会阻止 CURRENT-STAGE 验收通过的 Blocker？

除非 Owner 明确要求专项安全审计、架构审计或全局 Review。

---

## 10. Agent 每次会话启动

优先读取：

1. 项目长期规则
2. `PRODUCT-GOAL.md`
3. `ROADMAP.md`
4. `CURRENT-STAGE.md`
5. `BACKLOG.md`

然后只读取与 Current Stage 直接相关的代码、spec 和 tests。

不要默认加载整个历史文档树。

---

## 11. “继续”是什么意思

如果 Owner 只说：

> 继续。

默认解释为：

> 继续 CURRENT-STAGE 中尚未完成的下一项工作。

不得解释成：

> 自由寻找整个项目还有什么可以改。

---

## 12. Owner 用户反馈

Owner 可以只描述实际体验。

Agent负责判断：

- 阻止当前验收 → Blocker
- 有真实影响但不阻止 → Important
- 偏好 / 美化 → Polish
- 改变产品目标 → 请求 Owner 明确确认后更新 Product Goal

---

## 13. 强模型 / C2C 路由

普通执行默认由当前 Coding Agent 自己完成。

优先使用高能力模型 / C2C：

- Roadmap 规划
- 复杂 Current Stage 定义
- 架构级决策
- 跨模块复杂问题
- 长时间无法确定根因的问题
- Stage 结束时高价值独立 Review

不要因为“需要思考”就自动调用强模型。

一次性规划 / Review 可以由 Owner 手动完成模型间交接。

---

## 14. 跨 Agent 信息规则

不同 Agent 不需要共享整段聊天。

任何会影响未来开发的信息必须落盘：

- 产品方向 → PRODUCT-GOAL
- 阶段顺序 → ROADMAP
- 当前范围 / 验收 → CURRENT-STAGE
- 非当前事项 → BACKLOG
- 实现事实 → 代码 / tests / git

临时交接只传增量：

```text
GOAL:
CURRENT_STAGE:
DECISION_OR_REQUEST:
ALLOWED_SCOPE:
DO_NOT:
STOP_CONDITION:
```

---

## 15. Git

有意义且已验证的开发切片、治理调整或 Stage 转换后：

1. 检查 diff
2. 运行相关验证
3. 更新必要治理文件
4. commit
5. 已有授权时 push

不要提交凭据、token、本地 runtime、个人隐私或不应进入仓库的真实数据。

---

## 16. OpenSpec 接入原则

OpenSpec 不是默认前置条件。

未来接入时：

- 四层治理仍然保留
- OpenSpec 只管理复杂 change 的 proposal/spec/design/tasks
- Current Stage 仍然是唯一执行入口
- Backlog 仍隔离非当前事项
