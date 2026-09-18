# BACKLOG

## Important

| ID | 问题 | 用户影响 | 何时再处理 |
|---|---|---|---|
| IMP-001 | Banner 图目前是从首张主图 crop/resize 出来的，观感像"强行拉伸"，不像专门设计的横版横幅 | 微信主页横幅难看，影响整个表情包页面观感 | Stage 1 验收时若 Owner 明确觉得 banner 不行，当场修；否则进 Stage 2 |
| IMP-002 | 透明底主图在某些背景下残留白边，flood-fill 抠图不透彻 | 微信聊天里表情边缘发灰/发白 | Stage 2 用真实猫图做 legacy vs precompose 私人回归，选定默认策略 |
| IMP-003 | 豆包办公任务环境是否能自动发现 SKILL.md 未实测 | 换个新对话能不能直接用这个 skill | Stage 1 验收顺带记录；Stage 3 写进兼容文档 |
| IMP-004 | 长文案/两行文案换行、文字 max-width 回归 | 文案长时排版溢出或挡住猫 | Stage 2 排版打磨时统一处理 |

## Polish

| ID | 问题 | 原因 | 建议 |
|---|---|---|---|
| POL-001 | Codex 环境双端验收 | Owner 已明确决定不做 Codex 端口 | 永久搁置，除非 Owner 重新提起 |
| POL-002 | 更多排版 preset（clean-white / cute-soft / bold-contrast） | 目前主要靠 auto | Stage 2 按需加，不预先铺 |
| POL-003 | 联系表 preview、运行 summary 的视觉美化 | 当前功能可用但朴素 | Stage 3 开源前再说 |
| POL-004 | Pillow `getdata()` DeprecationWarning | 升级 Pillow 14 前的警告 | 下次动到该文件时顺手改 |

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
