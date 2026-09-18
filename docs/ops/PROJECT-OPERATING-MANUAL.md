# Project Operating Manual — cat-sticker-skill

> 本文件是 Owner-Driven 治理的详细操作手册。`AGENTS.md` 里只有每次自动加载的最小规则；本文件供需要完整治理框架时查阅。
> 来源：AI Project Governance Kit（UNIVERSAL-GOVERNANCE.md 16 节），按本项目实际情况裁剪。

---

## 1. 角色分工

- **Owner**：决定做什么、为什么做、范围、阶段验收、方向是否改变。不承担工程判断。
- **Agent**：技术分析、实现、测试、git、把技术风险翻译成"用户会看到什么、是否阻塞当前 Stage、是否必须现在修"。

## 2. 权威四层（长期状态只在仓库，不靠聊天记忆）

1. `PRODUCT-GOAL.md` — 产品为什么存在、给谁、V1 边界
2. `ROADMAP.md` — 阶段路线，每阶段回答"用户多能做什么"
3. `CURRENT-STAGE.md` — 当前唯一活跃阶段：目标、范围、验收、Blocker、Stop Condition
4. `BACKLOG.md` — Important / Polish / Future Ideas

聊天记录、旧 sprint、旧 review、历史 handoff md 都只是参考，不覆盖四层。

## 3. 问题分级

| 级别 | 定义 | 处理 |
|---|---|---|
| **Blocker** | Current Stage 验收无法完成 / 数据损坏 / 明确安全风险 / 不修就走不下去 | 现在修 |
| **Important** | 真实有影响但不挡验收 | 写 Backlog，继续当前 Stage |
| **Polish** | 非必要重构、代码美化、低概率边缘、理论优化、当前 Stage 之外的测试增强 | Backlog 或忽略 |

判断 Owner 的一句吐槽属于哪级，是 Agent 的责任，不要把"这算不算 Blocker"甩给 Owner。

## 4. 停止规则

Current Stage 验收条件全部满足 + 无 Blocker → 必须：
1. 宣布 Stage 完成
2. Important/Polish 进 Backlog
3. 更新 ROADMAP
4. 停止继续优化当前 Stage
5. 准备下一 Stage

"还能改进"不是继续理由。

## 5. Review 规则

- **禁止**默认做"全面检查整个项目还有什么问题"。
- 默认 Review 只问：是否存在阻止 CURRENT-STAGE 验收的 Blocker？
- 只有 Owner 明确要求专项安全审计 / 架构审计 / 全局 Review，才做超出此范围的检查。

## 6. 会话启动顺序

1. `AGENTS.md`（本仓库治理入口）
2. `PRODUCT-GOAL.md`
3. `ROADMAP.md`
4. `CURRENT-STAGE.md`
5. `BACKLOG.md`
6. 只读与 Current Stage 直接相关的代码 / spec / tests

不默认把整个历史文档树（MASTER-SPEC 1100+ 行、历次 REPORT-*.md、旧 handoff）全读一遍。

## 7. "继续"的含义

Owner 只说"继续" = 继续 CURRENT-STAGE 中下一项未完成工作。
≠ 自由寻找整个项目还有什么能改。

## 8. 跨 Agent 交接格式

跨 Agent 只传增量：

```text
GOAL:
CURRENT_STAGE:
DECISION_OR_REQUEST:
ALLOWED_SCOPE:
DO_NOT:
STOP_CONDITION:
```

## 9. Git 规范

- 有意义且已验证的切片 / 治理调整 / Stage 转换后：查 diff → 跑验证 → 更新治理文档 → commit → 已授权则 push
- 绝不提交：凭据、token、本地 runtime、私人猫图、真实 API 响应样例
- commit message 写清用户影响，不只是技术改动

## 10. 付费 API 规则

- 未批准 plan 不发生真实 Seedream 请求
- 每次生成前报告预计调用次数和费用
- 失败重试有界（1 + max_retries），不无限重试
- `processing_failed` 的版本走本地恢复，不重新付费

## 11. 安全边界

- API key 只走 `ARK_API_KEY` 环境变量，不落盘、不进 log、不进 fixture
- 私人猫图只在 `$CAT_STICKER_HOME/projects/<id>/refs/`，不进 git
- push 前必须过 `privacy-check`：无 secret、无私人绝对路径、tracked 图片只允许在 `tests/public-fixtures/` 和 `assets/fixtures/`

## 12. 强模型 / 复杂任务路由

普通明确执行由当前 Agent 自己完成。以下情况才考虑交更强模型 / 单独 review：
- Roadmap 规划、复杂 Stage 定义
- 架构级决策、跨模块复杂问题
- 长时间定位不到根因的 bug
- Stage 结束时的高价值独立 review

不要因为"需要思考"就自动升级模型。
