# BACKLOG

## Important

| ID | 问题 | 用户影响 | 何时再处理 |
|---|---|---|---|
| IMP-001 | Banner 图目前是从首张主图 crop/resize 出来的，观感像"强行拉伸" | 微信主页横幅难看 | Owner 已接受现状；若以后成为新痛点单独提 |

## Polish

| ID | 问题 | 原因 | 建议 |
|---|---|---|---|
| POL-001 | Codex 环境双端验收 | Owner 已明确决定不做 | 永久搁置 |
| POL-003 | 联系表 preview、运行 summary 的视觉美化 | 当前功能可用但朴素 | Stage 3 后再说 |
| POL-004 | Pillow `getdata()` DeprecationWarning | 升级 Pillow 14 前的警告 | 下次动到该文件时顺手改 |

## Stage 2 已完成事项

以下 Stage 2 必须项已由 Owner 验收关闭：

- ~~IMP-002 透明底白边回归~~ → 已验收
- ~~IMP-004 长文案自动换行~~ → 已验收
- ~~POL-002 至少一种新文案风格~~ → 白字灰边已实测对比
- ~~文字固定位置挡主体~~ → 已加 `vertical_position` top/center/bottom，commit `25755d3`，Owner 已实测重排

## Stage 3 进行中

以下事项是 Stage 3 必须项，不在此 backlog 处理：

- 干净环境 clone 跑通 Quick Start
- SKILL.md 独立可读
- `references/agent-compatibility.md` 写实
- public 前 privacy-check

## Future Ideas

- GIF / 动图支持（V1 明确不做）
- 第二家图像 provider 备选
- 非猫咪宠物通用化
- OpenSpec 接入（按 UNIVERSAL-GOVERNANCE §16，不做默认前置）

## 规则

Backlog 条目不会自动成为当前任务。只有 Owner 明确提升或满足 Blocker 条件才进入当前执行范围。
