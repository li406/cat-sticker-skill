# ROADMAP

当前阶段：Stage 3

## 已完成

### Stage 0 — 工具链骨架与 Mock 全链路

用户获得：

> 一套在工程上可重复验证的工具链：建项目、加参考图、导入角色、规划、批准、mock 生成、本地加字抠图、微信包导出、隐私扫描，全程不花一分钱 API 费也能跑通。CI 在 Ubuntu + Windows 矩阵全绿。

状态：done

### Stage 1 — Owner 真实猫图跑通一套并上传微信成功

用户获得：

> Owner 第一次用自己真实的猫照片 + 真实付费 Seedream，做出一套可上传微信表情开放平台的静态表情包，并完成了一次真实上传提交。

状态：done（Owner 已验收）

### Stage 2 — 换猫换风格再做一套，默认质量稳定

用户获得：

> 换一只猫、换一种文案风格再做一套，第二次做比第一次省心：透明底边缘干净、文案不挡猫脸、风格不再只有一种黄字黑边、长文案自动换行、文字位置按猫的位置自动选不挡主体。

状态：done（Owner 已验收；关键修复：vertical_position 自适应文字位置，commit `25755d3`）

## 当前

### Stage 3 — 开源发布与其他 Agent 兼容

用户获得：

> 其他 GitHub 用户/其他 AI Agent clone 这个仓库后，能照着 README 和 SKILL.md 独立跑通，不需要在群里问作者；文档写的是真实实测过的环境，不夸大兼容。

状态：active

完成条件：

- [ ] 新用户按 README Quick Start 在干净环境跑通 `doctor` + `smoke-test`
- [ ] SKILL.md 能让一个没看过聊天记录的 Agent 独立走完一次完整流程
- [ ] 真实实测过的 Agent 环境写进 `references/agent-compatibility.md`，没测过的不写
- [ ] 仓库 public 后 privacy-check 仍 PASS，无私人照片/key
- [ ] LICENSE / SECURITY / CONTRIBUTING 齐全且可读

## 后续

### Stage 4 — 按需迭代（无预定范围）

状态：planned（等 Owner 用一段时间收集真实反馈后再定）

## 路线规则

- 同时只有一个 active Stage
- 非当前问题进入 BACKLOG
- 不设没有用户价值的纯清理 Stage
