# 猫咪表情包 Agent Skill — MASTER SPEC

> 状态：v1.0 立项基线  
> 日期：2026-09-16  
> 文档性质：项目唯一权威产品/架构规格（Single Source of Truth）  
> 工作名称：`cat-sticker-skill`（仅为开发占位名，正式仓库名可后改）  
> 适用对象：Codex、豆包电脑版/豆包 App「办公任务 / 豆包工作」等具备图片理解、本地文件/脚本执行能力的 AI Agent  
> 原始事实参考：《表情包工具方案交接文档.md》（2026-09-16）

---

## 0. 权威性与变更规则

1. 本文档是 v1 开发的唯一产品与架构基线。
2. `README.md`、`SKILL.md`、`AGENTS.md`、代码注释和实现不得与本文档冲突。
3. 如果实现中发现本文档存在真实缺口：
   - 不得自行扩大产品范围；
   - 不得自行改变隐私边界、付费执行门、许可证或用户数据位置；
   - 优先选择最小实现；
   - 对会影响用户体验、数据安全、API 成本、生成结果或兼容性的关键缺口，先向 Owner 询问。
4. 已经明确的决策不重复询问。
5. 任何外部平台规则（微信、Seedream API、Agent Skill 规范）必须视为可变依赖，不得在核心逻辑里散落硬编码。
6. 本项目优先满足 Owner 的个人使用需求；其他 GitHub 用户可以自行修改适配，但不得反向驱动 v1 变复杂。

---

# 1. 产品定位

## 1.1 项目是什么

本项目是一个 **AI Agent 原生的猫咪静态表情包制作 Skill + 本地图像处理工具包**。

它不是：
- Web App；
- 本地桌面 GUI；
- SaaS；
- 独立聊天机器人；
- 需要用户手动使用命令行的普通 CLI 产品。

它的主要交互界面是 **AI Agent 本身**。

用户通过自然语言和参考图片与 Agent 交互，Agent 负责理解需求、查看图片、规划表情、生成文案、选择视觉策略；本仓库负责提供可重复、可验证、可调用的脚本和规则，完成付费生图、本地图像处理、素材校验与导出。

## 1.2 第一优先级用户

第一优先级是 Owner 本人。

设计优先级：

1. Owner 的真实使用体验；
2. 生成质量与稳定性；
3. 隐私和 API 安全；
4. 少浪费付费图片生成；
5. 可维护性与可复现；
6. 其他 Agent/其他 GitHub 用户的通用性。

## 1.3 一级目标 Agent 环境

v1 一级目标：

- OpenAI Codex；
- 豆包电脑版 / 豆包 App 的「办公任务 / 豆包工作」Agent 场景。

兼容策略：

- 核心工作流以 `SKILL.md` 表达；
- Agent 若支持 Skill 自动发现，可自动加载；
- Agent 若不支持或未验证自动发现，只要能读取项目文件并运行脚本，用户可明确要求其先读取 `SKILL.md`，仍应可完整执行；
- 不把任何单一 Agent 的私有 UI/协议写入核心业务逻辑。

注意：v1 不要求证明所有 Agent 都原生支持同一套 Skill 自动发现机制。

---

# 2. 已确认的 v1 产品边界

## 2.1 必须支持

- 静态 PNG 表情；
- 1 张或多张参考图片；
- 同一张参考图扩展生成多张表情；
- 多张照片分别扩展指定数量；
- 多张同一角色照片作为共同参考，以一致性为优先；
- Agent 自己进行视觉理解；
- Agent 自动生成文案；
- 用户可提供文字文案作为参考；
- 用户可提供图片形式的梗图/文案/视觉参考，由宿主 Agent 理解；
- 生成付费图片前先给用户查看完整 Generation Plan；
- 用户可以修改计划后再生成；
- 用户若明确要求“直接生成”，可跳过逐项确认，但仍需建立内部 Generation Plan 和预算边界；
- Seedream 图生图/多参考图生成；
- AI 只生成无文字原图；
- 本地文字排版；
- 透明背景处理；
- 单张失败重试；
- 单张不满意重生成；
- 版本历史；
- 断点恢复；
- 微信静态素材导出；
- 素材规格校验；
- 总览预览图；
- ZIP 打包；
- API Key 与私人图片保护；
- 私人回归测试；
- 公共无隐私测试；
- 发布前隐私扫描。

## 2.2 v1 明确不做

- GIF / 动图；
- 视频表情；
- Web UI；
- Gradio；
- FastAPI Web 服务；
- React/Vue 前端；
- 独立桌面 GUI；
- 微信自动登录/自动投稿；
- SaaS；
- 账户系统；
- 云同步；
- 多人协作；
- 手机 App；
- OpenAI/Replicate/ComfyUI/Stable Diffusion 等第二生图 Provider 的实际实现；
- 额外视觉理解 API；
- 为文案生成单独调用额外 LLM API；
- 自动判断并强制合并“多张照片是不是同一只猫”。

未来版本可以扩展，但不得拖慢 v1。

---

# 3. 核心设计原则

## 3.1 Agent 做认知，脚本做确定性工作

### 宿主 Agent 负责

- 看参考图；
- 理解猫咪外观；
- 理解用户主题；
- 判断图片场景；
- 根据用户指令判断图片之间的关系；
- 生成 Character Profile；
- 生成表情文案；
- 设计情绪、动作、构图；
- 选择参考图片；
- 建立 Generation Plan；
- 选择 Typography Preset；
- 查看输出并做语义/视觉判断；
- 和用户讨论修改；
- 判断某张是否“不像”“不够好笑”“风格不对”。

### 本地工具负责

- Seedream API 调用；
- 图片下载/落盘；
- 请求重试与超时；
- 成本/调用数量记录；
- 背景透明化；
- alpha 处理；
- 图片尺寸处理；
- 文字测量；
- 自动换行；
- 文字描边；
- 文字定位；
- PNG 导出；
- 封面/图标/banner 生成；
- manifest/state；
- 版本管理；
- validator；
- 预览图；
- ZIP；
- 隐私扫描。

原则：**Agent 已经能完成的视觉理解与语言任务，不额外付费调用第二个视觉/文本模型。**

## 3.2 付费请求必须晚于计划

默认情况下，所有 Seedream 付费生成请求必须发生在 Generation Plan 展示给用户并获批准之后。

允许例外：用户明确说“直接生成”“不用给我看计划，直接做”等。即使如此：
- Agent 仍需先内部建立计划；
- 必须有明确生成数量；
- 必须有重试上限；
- 不能无限调用。

## 3.3 AI 不负责生成最终中文文字

Seedream prompt 必须明确要求：
- 不生成任何文字；
- 不生成英文字母；
- 不生成水印；
- 不生成 logo；
- 不随机增加无关装饰。

最终文字由本地排版引擎生成。

## 3.4 不覆盖好结果

- 单张重生成不得重做其他表情；
- 新版本不得覆盖旧版本；
- 任意时刻可以切回旧版本。

---

# 4. 参考图片与生成模式

v1 不使用简单的“模式 A/模式 B”产品定义，统一使用 **Reference Groups + Generation Plan**。

## 4.1 模式：单图扩展

示例：
- `photo_01` → 生成 3 个表情。

允许 Seedream改变：
- 表情；
- 动作；
- 姿势；
- 角度；
- 构图。

必须尽量保持：
- 毛色；
- 花纹；
- 脸部关键特征；
- 身体特征；
- 用户要求保持的配饰。

## 4.2 模式：多图分别扩展

示例：
- `photo_01` → 3 张；
- `photo_02` → 2 张；
- `photo_03` → 3 张。

最终形成 8 个独立 Sticker item。

## 4.3 模式：同一角色多参考图

用户明确说明几张照片是同一只猫，或用户确认 Agent 的建议后：

- 多张图组成一个 `reference_group`；
- 共同用于保持角色一致性；
- 可生成任意计划数量。

Agent 可以建议“这些看起来像同一角色”，但 v1 **不得未经用户确认自动把多张图合并成同一角色组**。

## 4.4 混合模式

一个项目可以同时包含：
- 多个独立参考图；
- 一个或多个 reference group；
- 每个来源不同的生成数量。

---

# 5. Character Profile

Character Profile 由宿主 Agent根据参考图和用户信息生成，不调用额外视觉 API。

它是提示词和一致性约束的结构化中间层，不是“品种鉴定”。

建议 Schema：

```yaml
character_id: cat_01
display_name: null
source_refs:
  - photo_01
  - photo_02
observable_features:
  coat_color: ""
  coat_pattern: ""
  eye_color: ""
  hair_length: ""
  body_type: ""
  face_shape: ""
  distinctive_markings: []
  accessories: []
identity_constraints:
  preserve: []
  avoid: []
uncertain_features: []
notes: ""
```

规则：

- 只记录可观察特征；
- 不确定的品种、年龄、性别等不得假装确定；
- 用户明确提供的信息优先于 Agent 猜测；
- `identity_constraints.preserve` 会进入生成 prompt；
- `avoid` 用于减少乱加服饰、乱改毛色、乱变成长毛猫等。

---

# 6. Generation Plan

## 6.1 目的

Generation Plan 是任何付费图片生成前的计划真源。

Agent先用便宜的语言/视觉理解能力把表情设计完整，再花 Seedream 图片生成费用。

## 6.2 每个 Sticker 至少包含

```yaml
id: sticker_001
reference:
  type: single | group
  ids:
    - photo_01
caption: "不想上班"
emotion: "生无可恋"
pose: "趴着，轻微侧头"
composition: "中近景，主体居中偏上，为底部文字留空间"
identity_priority: high
typography_preset: auto
status: planned
```

可选：
- `theme`;
- `negative_constraints`;
- `seedream_prompt_hint`;
- `notes`.

## 6.3 Plan 版本与审批

建议项目状态保存：

```yaml
plan_revision: 3
approved_revision: 3
approved_for_generation: true
```

如果 Agent 在批准后修改了：
- caption；
- reference；
- 数量；
- 动作；
- 生成策略；

则 `plan_revision` 增加，原批准失效。

纯排版微调不必重新批准 Seedream 生成。

## 6.4 默认交互

Agent 应先向用户展示：
- 表情总数量；
- 每条文案；
- 情绪；
- 动作；
- 主要参考；
- 预计付费生成张数；
- 重试预算。

用户可以用自然语言修改，例如：
- “第 3 个换成几点了还不下班。”
- “第 6 个不要。”
- “第二张照片多做两个。”
- “这四张都是同一只猫，统一风格。”

确认后才进入图片生成。

---

# 7. Seedream Provider

## 7.1 v1 Provider

v1 只实际实现：
- Volcengine / Ark / Seedream。

现有已验证 baseline：
- Seedream 4.5。

模型 ID 必须配置化，不得在业务逻辑中写死。

未来可测试新模型，但 v1 不因新模型存在而自动替换已验证 baseline。

## 7.2 配置

建议环境变量：

```text
ARK_API_KEY=
CAT_STICKER_SEEDREAM_MODEL=
CAT_STICKER_HOME=
```

可选：

```text
CAT_STICKER_MAX_RETRIES=
CAT_STICKER_REQUEST_TIMEOUT=
CAT_STICKER_UNIT_PRICE_CNY=
```

要求：
- `.env` 不进 Git；
- API Key 不进 manifest；
- API Key 不进日志；
- API Key 不作为普通 CLI 参数回显；
- 不硬编码 Owner 用户目录。

## 7.3 多图输入

Provider 接口必须从第一版支持：
- 单 reference；
- 多 reference。

不要把 API 抽象限制为单图，即使最初测试先跑单图。

## 7.4 Prompt 规则

Agent负责生成语义内容，本地 provider 构造最终请求时至少补强：

- 保持参考角色真实特征；
- 指定情绪/动作；
- 指定构图；
- 简洁纯色/白色背景（按 matting 策略）；
- 禁止任何文字；
- 禁止英文字母；
- 禁止 logo；
- 禁止水印；
- 禁止无关装饰；
- 避免额外肢体、额外猫、错误配饰（除非计划要求）。

---

# 8. 背景处理

## 8.1 已验证基线

历史已验证：
- 纯白背景；
- RGB 三通道 >235 作为白色候选；
- 从边缘进行 flood fill；
- 仅删除与边缘连通的白色区域；
- 比 rembg 直接作用于“已经加字的图片”更可靠，因为 rembg 曾误删白字。

## 8.2 v1 开发要求

不得直接废弃已验证方案。

必须保留：
- `legacy`：AI 原图 → 加字 → flood fill；
- `precompose-matting`：AI 原图 → 去背景 → 加字。

使用 Owner 私人回归集进行 A/B。

如果 `precompose-matting` 在：
- 猫毛边缘；
- 白色区域保留；
- 文字完整性；
- 透明效果；
- 最终微信效果

均不差于 legacy，则可将其升级为默认。

升级前必须保留 legacy fallback。

## 8.3 新方案目标

背景算法不应永远硬编码“纯白”。

设计为 `solid_background_matting`：
- 从边缘估计背景颜色；
- 基于颜色距离确定候选；
- 从边缘 flood fill；
- 只删除外部连通区域；
- 保留主体内部相近颜色。

v1 先保证白底稳定；自动背景色估计可在后续阶段开启。

## 8.4 背景策略

至少预留：

- `solid_remove`：默认；
- `keep`：保留原背景；
- `advanced`：未来。

v1 不要求实现复杂 AI matting。

---

# 9. Typography 系统

## 9.1 原则

Agent判断“风格”，本地规则引擎负责“执行”。

Agent 不直接自由生成一堆不可复现的 RGB/字号参数作为默认路径。

## 9.2 Preset

至少需要：

- `meme-yellow`：真实照片梗图风，黄色粗体 + 黑描边；
- `clean-white`；
- `cute-soft`；
- `bold-contrast`。

初期可以只把 `meme-yellow` 做到完整稳定，其余先作为最小可用 preset。

## 9.3 开源字体

不得打包或依赖 Windows 微软雅黑作为公开项目字体。

建议默认使用允许再分发的开源中文字体，例如 Noto Sans CJK / Noto Sans SC 系列，并保留字体许可证。

若字体不随仓库分发，也必须提供清晰安装/发现逻辑。

## 9.4 参数

底层排版接口必须支持：

- font；
- fill；
- stroke；
- stroke width；
- font size；
- max width；
- line spacing；
- alignment；
- anchor；
- x/y offset；
- bottom margin；
- auto wrap。

因此用户可以直接对 Agent 说：
- “005 的字小一点。”
- “003 往上移。”
- “换成黄字黑边。”
- “这一条分两行。”

无需 GUI。

## 9.5 默认排版

历史 baseline：
- 底部居中；
- 距底部约 6%；
- 字号与图片宽度相关；
- 长文字缩小；
- 黑色描边约字号 10%。

所有值做成 preset/config，不散落硬编码。

---

# 10. Sticker 状态与版本

每个 Sticker 独立管理。

建议：

```yaml
id: sticker_003
caption: "几点了还不下班"
status: composed
active_version: 2
versions:
  - 1
  - 2
```

目录示意：

```text
sticker_003/
  v001/
    generated.png
    cutout.png
    composed.png
  v002/
    generated.png
    cutout.png
    composed.png
  current.json
```

要求：

- 重生成 003 不能改变其他 item；
- 旧版本保留；
- 能切换 current；
- 失败不会破坏上一版成功结果。

---

# 11. Project Manifest 与 Workspace

## 11.1 私人 Workspace 必须在 Git 仓库之外

默认 Windows 建议：

```text
%LOCALAPPDATA%\CatStickerSkill\workspace
```

允许环境变量：

```text
CAT_STICKER_HOME
```

覆盖默认路径。

不得硬编码：
- `C:\Users\某个用户名\...`
- Owner 真实用户名；
- 开发机特有目录。

## 11.2 Workspace 保存

- 原始参考图；
- 中间图片；
- 生成版本；
- manifest；
- plan；
- previews；
- exports；
- 非敏感运行记录。

## 11.3 Manifest 不保存

- API Key；
- Authorization Header；
- signed URL（若存在敏感凭据）；
- base64 图片；
- 不必要的绝对私人路径。

---

# 12. 隐私与安全

这是发布门槛，不是可选优化。

## 12.1 私人图片

Owner 的猫照片和私人回归素材：
- 永远不进公开仓库；
- 默认就在 repo 外 workspace；
- 不进入 GitHub Actions；
- 不作为 public fixture；
- 不复制到 `tests/`。

## 12.2 EXIF

公开 demo/fixture 如来自真实照片：
- 必须 strip EXIF/metadata；
- 不得保留 GPS、设备、拍摄时间等不必要信息。

优先使用专门制作的 synthetic/public fixture。

## 12.3 日志

禁止记录：
- API Key；
- Authorization；
- 完整 base64；
- 敏感 signed URL；
- 私人图片二进制；
- 不必要的用户目录绝对路径。

可以记录：
- request_id；
- model；
- item id；
- duration；
- status；
- error code；
- retry count；
- configured cost estimate。

## 12.4 发布前隐私扫描

提供 `privacy_check` / `release_check`：

至少检查：
- `.env`;
- 常见 API Key 模式；
- 私人 workspace 路径；
- 图片大文件；
- EXIF；
- 日志；
- manifest；
- 本地绝对路径；
- 意外缓存；
- 用户私有回归目录。

发现高风险内容应非零退出，阻止 release。

## 12.5 Git 基线

`.gitignore` 至少包含：
- `.env`;
- `.venv`;
- Python cache；
- build artifacts；
- workspace；
- exports；
- logs；
- local/private fixtures；
- IDE 临时文件。

但安全不能只依赖 `.gitignore`，核心策略仍是私人 workspace 在 repo 外。

---

# 13. 成本与重试安全门

## 13.1 不硬编码价格

图片模型价格会变化。

`unit_price_cny` 必须配置化。

如果未配置：
- 显示预计请求张数；
- 显示“单价未配置，无法准确估算费用”；
- 不伪造价格。

## 13.2 生成预算

至少设置：
- planned image count；
- max retries per item；
- max total paid generations per run。

例如计划 9 张，最多每张 1 次额外重试，则明确上限。

达到上限后停止，不无限重试。

## 13.3 失败策略

可自动重试：
- 网络临时错误；
- 5xx；
- 明确可重试限流；
- 临时下载错误。

不应盲目自动重试：
- Key 无效；
- 参数错误；
- 余额/权限；
- 用户取消；
- 明确内容策略错误；
- 连续重复同类错误。

---

# 14. 微信静态导出

## 14.1 v1 baseline

以 Owner 刚完成的真实上传流程作为当前项目 baseline：

- 表情主图：240×240，透明 PNG；
- 封面图：240×240，白底、无文字；
- 聊天图标：50×50，白底；
- 详情页横幅：750×400，无文字；
- **不默认生成 120×120 缩略图**。

重要：
- 这不是对微信未来官方规范永久不变的声明；
- 它是 `wechat_static_v1_user_verified` preset；
- 微信规则必须独立配置，可更新。

## 14.2 Preset

建议：

```text
assets/platform-presets/wechat-static.yaml
```

字段至少包含：
- preset version；
- verified date；
- asset types；
- dimensions；
- background rules；
- format；
- optional file size limits；
- count rules；
- notes。

如果当前官方文件大小限制未被可靠核实，不得编造；可标记 `unknown` / `not_enforced`，等待后续验证。

## 14.3 Validator

至少检查：
- 文件存在；
- PNG 可读取；
- 尺寸；
- alpha（主图）；
- 背景规则；
- 命名；
- 数量；
- 文件大小（仅当 preset 有可靠规则）；
- 文字是否超画布；
- 图片是否损坏。

输出分级：
- PASS；
- WARN；
- FAIL。

不得因为本项目 validator PASS 就宣称“保证微信审核通过”。

---

# 15. 预览与人工复核

没有 GUI，但必须生成适合 Agent 和用户查看的中间产物：

- contact sheet / 九宫格/多宫格总览；
- 每张最终 composed PNG；
- 表情 ID 与 caption 对照表；
- validator report。

Agent完成生成后应先展示/打开预览，再进行最终打包。

用户可以自然语言指定修改项。

---

# 16. 输出包

最终 export 建议：

```text
exports/<project-id>/
  stickers/
    001.png
    002.png
    ...
  cover.png
  icon.png
  banner.png
  preview.png
  manifest.json
  validation-report.json
  README.txt
```

然后打包：
- `<project-id>-wechat-static.zip`

`README.txt` 可说明：
- 每个文件用途；
- 生成时间；
- preset 版本；
- 本工具不保证平台审核结果。

---

# 17. Agent Skill 结构

建议仓库：

```text
cat-sticker-skill/
├─ SKILL.md
├─ AGENTS.md
├─ MASTER-SPEC.md
├─ README.md
├─ LICENSE
├─ CHANGELOG.md
├─ SECURITY.md
├─ CONTRIBUTING.md
├─ pyproject.toml
├─ .env.example
├─ .gitignore
│
├─ src/
│  └─ cat_sticker_skill/
│     ├─ cli.py
│     ├─ config.py
│     ├─ models/
│     ├─ providers/
│     │  └─ seedream.py
│     ├─ project/
│     ├─ matting/
│     ├─ typography/
│     ├─ export/
│     ├─ validation/
│     └─ privacy/
│
├─ scripts/
│  ├─ generate.py
│  ├─ compose.py
│  ├─ validate.py
│  ├─ preview.py
│  ├─ package.py
│  └─ privacy_check.py
│
├─ references/
│  ├─ workflow.md
│  ├─ generation-plan.md
│  ├─ character-profile.md
│  ├─ prompt-rules.md
│  ├─ typography.md
│  ├─ image-processing.md
│  ├─ wechat-static.md
│  ├─ privacy-security.md
│  └─ troubleshooting.md
│
├─ assets/
│  ├─ platform-presets/
│  ├─ typography-presets/
│  └─ schemas/
│
└─ tests/
   ├─ unit/
   ├─ public-fixtures/
   ├─ golden/
   └─ integration/
```

原则：
- 业务逻辑放 `src/`；
- `scripts/` 只做薄入口，避免复制业务逻辑；
- `SKILL.md` 负责“Agent 如何工作”；
- `AGENTS.md` 负责“Codex 如何开发这个仓库”；
- `MASTER-SPEC.md` 负责“产品和架构不能被随意改变的真源”。

---

# 18. SKILL.md 必须包含的行为契约

`SKILL.md` 至少告诉 Agent：

1. 什么情况下使用本 Skill；
2. 输入可以是一张或多张参考图；
3. 如何询问/理解 reference group；
4. 不确定多图关系时不得擅自合并；
5. 如何生成 Character Profile；
6. 如何生成 Generation Plan；
7. 如何向用户预览计划；
8. 默认未经用户批准不得调用付费 Seedream；
9. 用户明确要求直接生成时如何安全跳过；
10. 如何调用本地脚本；
11. 如何处理单张失败；
12. 如何重生成单张而不影响其他图片；
13. 如何做排版微调；
14. 如何运行 validator；
15. 如何生成预览；
16. 如何打包；
17. 如何保护私人图片/API Key；
18. 最终回复必须报告：
   - 成功/失败数量；
   - 发生的付费生成次数；
   - 重试次数；
   - 输出目录；
   - validator 结果；
   - 是否还有 WARN/需要人工检查。

---

# 19. AGENTS.md 必须包含的开发约束

至少：

- 先读 `MASTER-SPEC.md`；
- 未获 Owner 明确批准不得改变范围；
- 不把 Web UI 加回 v1；
- 不增加额外视觉 LLM API；
- 不增加 GIF；
- 不更改许可证；
- 不把私人 fixture 放 repo；
- 不进行真实付费 API 测试，除非明确授权；
- 单元/集成测试默认 mock provider；
- 新功能必须有测试；
- 不把模型 ID/价格/微信规格散落硬编码；
- Python 兼容目标 3.11+；
- 优先标准库/Pillow/NumPy/轻量 HTTP client；
- 不引入 SciPy，除非能证明必要；
- 任何 secret 不进入日志/测试快照；
- 完成每阶段必须运行测试并提供证据。

---

# 20. 技术基线

建议：

- Python >=3.11；
- Pillow；
- NumPy；
- 一个明确维护的 HTTP client/官方 Ark SDK（二选一，由实现阶段根据 Seedream API 现状选择）；
- pytest；
- ruff（或同类轻量 lint）；
- 可选 `pydantic` 用于 Schema，但不要为了小项目过度引入框架。

避免：
- Web framework；
- GUI framework；
- SciPy（若 flood fill 可用 NumPy/Pillow/标准库实现）；
- 大型数据库。

状态保存优先：
- JSON/YAML 文件；
- 无需 SQLite，除非后续出现明确需求。

---

# 21. 测试策略

## 21.1 公共测试

GitHub 可运行：
- synthetic/public fixture；
- unit tests；
- golden tests；
- validator tests；
- typography tests；
- background tests；
- project state/version tests；
- secret/privacy scanner tests。

不调用付费 API。

## 21.2 Provider 测试

默认：
- mock HTTP；
- fixture response；
- 验证 request schema；
- 验证重试逻辑；
- 验证错误分类。

真实 API：
- 必须 opt-in；
- 例如 `RUN_PAID_TESTS=1`；
- CI 默认禁用；
- 需要真实 Key 时从环境变量读取；
- 不将响应私人图作为仓库 fixture。

## 21.3 Owner 私人回归测试

仓库外：

```text
CAT_STICKER_PRIVATE_FIXTURES=<private path>
```

用于比较：
- legacy vs new matting；
- 文字完整性；
- 猫毛边缘；
- 尺寸；
- alpha；
- 透明黑底 bug；
- 长文字；
- 真实 Owner 成品视觉效果。

不得上传 GitHub。

---

# 22. 关键历史 Bug 必须转为自动测试

来自现有实践：

1. rembg 曾导致白色文字缺失；
2. AI 直接生成中文字会出现错字/残字/遮挡主体；
3. `convert("RGB")` 可能破坏透明通道并造成黑底；
4. Seedream 可能乱加元素/英文；
5. 黑底/白底背景处理行为不同；
6. Windows Git/路径问题可能影响安装使用。

前 1、3、背景处理必须形成自动回归测试。

第 2、4 主要通过 prompt 约束 + Agent视觉复核，不假装能够仅靠像素规则完全验证。

---

# 23. License

已确认：

- 使用 **PolyForm Noncommercial 1.0.0**；
- 允许个人/非商业使用、修改、分享；
- 商业使用需要版权持有人单独授权；
- Owner 保留自行商业化和单独商业授权权利。

README 必须使用准确表述：
- `source-available` / 源码公开；
- 不声称为 OSI Open Source。

不要使用 MIT，因为 MIT 允许商业使用。

许可证文件应使用官方文本，不自行改写许可证条款。

---

# 24. 文档与隐私中的身份信息

公开仓库不得自行写入 Owner：
- 真实姓名；
- 住址；
- Windows 用户名；
- 私人邮箱；
- 私人猫照片；
- 未公开的艺术家账户信息。

如 LICENSE/README 需要 Copyright Holder：
- 先使用占位符；
- 由 Owner 在发布前自行决定公开名称/昵称。

---

# 25. Definition of Done — v1

v1 只有同时满足以下条件才算完成：

1. 在 Codex 中可以从参考图开始走完整流程；
2. 在豆包办公任务环境至少完成一次实际兼容性验证；
3. 不需要 Web UI；
4. 单图可生成一套静态表情；
5. 多图可按“分别扩展”工作；
6. 多图可按“统一角色 reference group”工作；
7. 生成前默认可以查看并修改 Generation Plan；
8. 未批准时不会调用付费生成；
9. 单张重生成不影响其他 item；
10. 旧版本不会被覆盖；
11. 文本由本地引擎生成；
12. 微信静态素材可以完整导出；
13. 默认不生成 120×120 缩略图；
14. validator 可运行并给出 PASS/WARN/FAIL；
15. 能生成整套预览；
16. 能生成 ZIP；
17. API Key 不进仓库/manifest/log；
18. 私人图片不进 repo；
19. 公共测试通过；
20. Owner 私人回归测试通过；
21. release privacy scan 通过；
22. LICENSE 使用 PolyForm Noncommercial 1.0.0；
23. README 明确不保证微信审核；
24. 不包含 GIF/Web App/SaaS 等超范围功能。

---

# 26. 延后事项 / Backlog

非 v1：

- GIF；
- 动态表情；
- 更多生图 provider；
- 复杂 AI matting；
- 自动投稿微信；
- 更多平台导出；
- 云端；
- GUI；
- 自动角色识别/聚类；
- prompt A/B 智能优化；
- 自动相似度去重；
- 更丰富艺术字体；
- 多角色同框高级控制。

Backlog 不应提前污染核心实现。

---

# 27. 已知待外部继续验证事项

以下不是 v1 开工阻塞项：

1. 豆包“办公任务”对 `SKILL.md` 的原生自动发现/安装机制是否与 Agent Skills 标准完全一致；
   - v1 通过“让 Agent 先读取 SKILL.md + 调本地脚本”保证可运行；
   - 实机验证后再补兼容说明。

2. 微信表情开放平台当前官方静态素材规范的最新公开正文；
   - v1 采用 Owner 实际上传成功流程作为 preset baseline；
   - 以后拿到官方规范再更新 preset。

3. Seedream 新模型相对 4.5 的质量/价格收益；
   - 不阻塞；
   - 先以已验证模型为 baseline；
   - 后续用相同私人回归集 A/B。

---

# 28. 外部事实核验记录（2026-09-16）

本项目设计基于以下已核实方向：

- OpenAI 2026 年 Skills 文档：`SKILL.md` 是可复用 workflow 的核心，Skills 可以携带资源/脚本，并采用 Agent Skills 开放格式；
- Codex 支持 Agent/Skills，并使用 `AGENTS.md` 指导仓库内开发工作；
- 字节 Seed 2026-06-23 官方说明：Seed2.1 面向真实生产力/Agent 场景，已在豆包产品上线；可在豆包电脑版或豆包 App 使用“办公任务”模式；
- Seedream 当前支持参考图/多图类图像创作能力，因此 v1 Provider 接口不得限制为单参考图。

这些事实只用于确认架构可行性；具体 API 参数和产品 UI 在实现时仍需以当时官方文档和实际环境为准。

---

# 29. 开发总原则（一句话版）

**让 Agent 负责“看懂、想好、和用户沟通”，让代码负责“花钱生成时可控、图片处理时确定、输出时可验证、发布时不泄密”。**
