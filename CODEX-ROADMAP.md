# Codex 开发路线图 — cat-sticker-skill

> 配套文档：`MASTER-SPEC.md`  
> 原则：不要一次性实现全部功能。每个 Phase 都必须可验证、可回退，再进入下一阶段。

---

# Phase 0 — 建仓与安全骨架

## 目标

建立不会返工的项目骨架，不调用任何付费 API。

## 必做

- 初始化 repo；
- 放入 `MASTER-SPEC.md`；
- 创建 `SKILL.md` 初版；
- 创建 `AGENTS.md`；
- 创建 `README.md`；
- 放入 PolyForm Noncommercial 1.0.0 官方 LICENSE；
- `SECURITY.md`；
- `.gitignore`；
- `.env.example`；
- `pyproject.toml`；
- `src/` / `scripts/` / `references/` / `assets/` / `tests/`；
- 配置系统；
- workspace 路径策略；
- manifest/schema 初版；
- Generation Plan schema；
- Sticker item + version schema；
- privacy scanner 最小版；
- pytest；
- lint；
- GitHub Actions（只跑公开、无付费测试）。

## 验收

- `pytest` 全绿；
- repo 不含真实 Key；
- repo 不含私人图片；
- Windows 路径没有硬编码用户名；
- `privacy_check` 能故意抓出测试用 fake secret；
- Codex 能正确解释 `SKILL.md` 和 `AGENTS.md` 的不同职责。

## 禁止

- 不接 Seedream；
- 不安装 Web framework；
- 不做 GUI；
- 不做 GIF；
- 不做额外 LLM API。

---

# Phase 1 — 最小付费闭环：1 张参考图 → 1 张最终 PNG

## 目标

用最小范围验证项目真正能工作。

## 流程

1. Agent 查看 1 张参考图；
2. Agent 生成 Character Profile；
3. Agent 生成 1 个 Generation Plan item；
4. 展示给用户；
5. 用户批准；
6. Seedream 生成 1 张无字图；
7. 保存原始输出；
8. 按已验证 baseline 做背景处理；
9. `meme-yellow` 文字排版；
10. 输出 240×240 透明 PNG；
11. validate；
12. 记录状态与调用次数。

## 必做

- Seedream provider；
- 真实环境变量读取；
- timeout；
- 最小重试；
- 原始结果落盘；
- 不覆盖旧结果；
- PIL RGBA 安全处理；
- flood fill legacy baseline；
- `meme-yellow`；
- 单图 validator；
- mock provider tests；
- 真实 paid test 必须 opt-in。

## 关键验收

- 未批准计划时，不发生 Seedream 请求；
- 真正生成时只调用计划数量；
- PNG 保持透明；
- 不出现 `RGB` 转换导致黑底；
- API Key 不出现在 log；
- 失败时错误清楚，不无限重试。

---

# Phase 2 — 一整套表情 + 单张重生成 + 版本历史

## 目标

让项目真正能用于日常做一套表情。

## 新增

- N 个 Sticker item；
- Agent 自动生成文案/情绪/动作；
- plan revision/approval；
- 批量生成；
- 单张失败重试；
- 单张重生成；
- v001/v002 版本；
- 选择 active version；
- 断点恢复；
- contact sheet 总览；
- 运行 summary。

## 验收场景

9 张表情：
- 1–5 成功；
- 6 模拟失败；
- 7–9 成功。

再次执行：
- 只处理 6；
- 其他 8 张 hash 不变化。

然后重生成 3：
- 产生 `v002`；
- `v001` 仍存在；
- 其他 item 不变化。

---

# Phase 3 — 多参考图与角色一致性

## 目标

覆盖 Owner 最真实的多照片使用方式。

## 新增两种路径

### A. 每图独立扩展

例如：
- photo_01 → 3；
- photo_02 → 2；
- photo_03 → 3。

### B. 同角色多参考

例如：
- photo_01 + photo_02 + photo_03 = `cat_01 reference_group`;
- 生成 9 个。

## 要求

- Provider 接收 1..N references；
- Agent 明确记录引用关系；
- Agent 不得未经确认自动把多图合并为同角色；
- prompt 使用 Character Profile preserve/avoid；
- 保持用户允许的动作变化，但尽量守住角色特征。

## 验收

- 能从多个文件构造请求；
- 能从同一项目混用 single 和 group；
- 修改某组配置不会破坏其他组；
- manifest 可追溯每张 sticker 使用了哪些 reference。

---

# Phase 4 — 完整微信静态素材包

## 目标

从一套最终表情生成 Owner 当前上传流程所需的完整包。

## 输出

- 240×240 主图；
- 240×240 封面；
- 50×50 聊天图标；
- 750×400 banner；
- 无 120×120 thumbnail；
- preview；
- manifest；
- validation report；
- ZIP。

## 要求

- 微信规则独立 preset；
- 不把规则散落代码；
- validator PASS/WARN/FAIL；
- 未经可靠核实的 file size 规则不编造；
- README 明确“不保证审核通过”。

## 验收

- ZIP 可以解压；
- 文件齐全；
- 尺寸正确；
- 主图 alpha 正常；
- 默认没有 120×120 缩略图；
- preset version 写进 manifest。

---

# Phase 5 — 排版升级 + 背景流程 A/B + 隐私发布门

## 目标

把“能用”升级成“稳定长期用”。

## A. Typography

新增/完善：
- `clean-white`;
- `cute-soft`;
- `bold-contrast`;
- offsets；
- 两行换行；
- max width；
- long-caption regression。

Agent 可以自然语言微调单张。

## B. 背景 A/B

比较：
- legacy：加字 → flood fill；
- proposed：flood fill/matting → 加字。

必须使用 Owner 私人回归集。

只有 proposed 不劣时才改默认。

## C. 隐私发布门

- EXIF 检查；
- secret scan；
- 私人路径；
- 日志；
- 图片；
- cache；
- release check；
- CI。

## 验收

- Owner 私人回归集通过；
- 公共 golden tests 通过；
- 发布前 privacy check 无高风险项；
- 文档与实现一致。

---

# Phase 6 — 双 Agent 实机验收

## 目标

验证不是“只在开发者脑中兼容”。

## Codex

完整执行至少一次：

参考图 → plan → 批准 → 生成 → 修改单张 → 微信包。

## 豆包办公任务 / 豆包工作

完整执行至少一次：

- 打开/访问 repo；
- 读取 `SKILL.md`；
- 查看参考图；
- 建 plan；
- 调本地脚本；
- 完成静态输出。

记录：
- 是否能自动发现 Skill；
- 若不能，需要怎样的启动提示；
- 文件权限/命令执行差异；
- 图片展示差异；
- 环境变量差异。

根据实测写：
`references/agent-compatibility.md`

## 验收

README 的兼容表只写真实测试结果，不提前宣称未经测试的原生兼容。

---

# 推荐开发节奏

不要把 Phase 0–6 一次性丢给 Codex 让它“全部做完”。

推荐：

1. 先让 Codex做 Phase 0；
2. 你查看文件结构和安全边界；
3. Phase 1 只跑一个真实付费图片；
4. 成功后再进入 Phase 2；
5. Phase 2 能稳定生成整套后，再做多参考；
6. 最后再做微信完整包和智能排版。

原因：真正高风险的是“生成 API + 图像处理 + 状态恢复”，不是 README 或花哨功能。

---

# 每个 Phase 给 Codex 的固定验收要求

每阶段结束，Codex 必须报告：

1. 修改了哪些文件；
2. 为什么这样设计；
3. 测试命令；
4. 测试结果；
5. 是否发生真实付费 API 调用；
6. 如果发生，调用次数；
7. 是否发现隐私/secret 风险；
8. 尚未解决的问题；
9. 本阶段是否达到 Definition of Done；
10. 不得把“代码写了”当成“功能验证成功”。

---

# 什么时候必须停下来问 Owner

Codex 遇到以下情况必须询问：

- 要改变付费门；
- 要改变许可证；
- 要把私人数据放 repo；
- 要接第二家/第二个视觉 LLM API；
- 要新增 Web UI；
- 要加入 GIF；
- 要改变微信默认输出资产；
- 要从 4.5 baseline 切换默认 Seedream 模型；
- 要删除 legacy 背景流程；
- 无法确认一个行为会不会导致额外付费；
- 真实 API 需要超过已批准的测试调用数。

其他局部实现细节，Codex 应按 `MASTER-SPEC.md` 做最小、可维护决策，不要反复询问。

---

# 发布前最后清单

- [ ] MASTER-SPEC 与实现一致
- [ ] SKILL.md 可独立指导 Agent
- [ ] Codex 实机通过
- [ ] 豆包办公任务实机通过
- [ ] 公共 CI 通过
- [ ] 私人回归通过
- [ ] 没有 Owner 私人照片
- [ ] 没有 API Key
- [ ] 没有 EXIF/GPS 泄露
- [ ] 没有硬编码 Owner 用户路径
- [ ] PolyForm Noncommercial 许可证正确
- [ ] README 使用 source-available 表述
- [ ] 微信 preset 版本明确
- [ ] 默认不包含 thumbnail
- [ ] 不宣称保证微信审核通过
- [ ] 不包含 v1 范围外的 GIF/Web App/SaaS
