# BACKLOG

## Important

| ID | 问题 | 用户影响 | 何时再处理 |
|---|---|---|---|
| IMP-001 | Banner 图目前是从首张主图 crop/resize 出来的，观感像"强行拉伸"，不像专门设计的横版横幅 | 微信主页横幅难看 | Stage 1 已接受现状；若以后成为新痛点，由 Owner 单独提 |
| IMP-003 | 豆包办公任务环境是否能自动发现 SKILL.md 未实测 | 新对话能不能直接用这个 skill | Stage 3 开源前实测并写进兼容文档 |

## Polish

| ID | 问题 | 原因 | 建议 |
|---|---|---|---|
| POL-001 | Codex 环境双端验收 | Owner 已明确决定不做 Codex 端口 | 永久搁置 |
| POL-003 | 联系表 preview、运行 summary 的视觉美化 | 当前功能可用但朴素 | Stage 3 开源前再说 |
| POL-004 | Pillow `getdata()` DeprecationWarning | 升级 Pillow 14 前的警告 | 下次动到该文件时顺手改 |

## 已纳入当前 Stage（Stage 2）

以下条目原属 Backlog，现已提升为 Stage 2 必须项，从 Backlog 移出：

- ~~IMP-002 透明底白边（legacy vs precompose 私人回归）~~ → Stage 2 必须项
- ~~IMP-004 长文案/两行文案排版回归~~ → Stage 2 必须项
- ~~POL-002 更多排版 preset（clean-white / cute-soft / bold-contrast）~~ → Stage 2 至少落地一种新风格

## Future Ideas

- GIF / 动图支持（V1 明确不做，未来若 Owner 真想要再单独立项）
- 第二家图像 provider 备选（当前只用 Seedream 4.5）
- 非猫咪的宠物通用化（当前完全围绕猫设计）
- OpenSpec 接入（按 UNIVERSAL-GOVERNANCE §16，不做默认前置）

## 规则

Backlog 条目不会自动成为当前任务。

只有：

- Owner 明确提升
- 或满足 CURRENT-STAGE 的 Blocker 条件

才能进入当前执行范围。
