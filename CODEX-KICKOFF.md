# 给 Codex 的首次开发指令

请把本项目当作一个受规格约束的工程任务执行。

## 首先阅读

1. `MASTER-SPEC.md`
2. `CODEX-ROADMAP.md`
3. 当前仓库内已有文件（如果仓库已存在）

`MASTER-SPEC.md` 是产品与架构的唯一权威真源；`CODEX-ROADMAP.md` 规定实施顺序。

## 本次只执行 Phase 0

不要开始 Phase 1，不要调用任何真实 Seedream/Ark API，不要产生付费请求。

Phase 0 目标：

- 建立 Agent-native Skill 项目骨架；
- 建立安全、配置、状态和测试基础；
- 让后续 Phase 1 可以在不推翻架构的情况下接入 Seedream。

必须完成：

- `SKILL.md` 初版；
- `AGENTS.md`；
- `README.md`；
- PolyForm Noncommercial 1.0.0 官方 `LICENSE`；
- `SECURITY.md`；
- `.gitignore`；
- `.env.example`；
- `pyproject.toml`；
- `src/`、`scripts/`、`references/`、`assets/`、`tests/` 基础结构；
- workspace 路径与配置模块；
- Project Manifest / Character Profile / Generation Plan / Sticker item/version 的最小 schema；
- public fixture 策略；
- `privacy_check` 最小实现；
- pytest；
- lint；
- 不使用真实私人猫图的自动测试；
- 如仓库在 GitHub，可准备不含付费 API 的 CI。

## 不得擅自做的事

- 不做 Web App / Gradio / FastAPI / React / GUI；
- 不做 GIF；
- 不接第二个视觉大模型 API；
- 不接 OpenAI/Replicate/Stable Diffusion 等图片 provider；
- 不调用真实 Seedream；
- 不把 API Key 写入任何源码、manifest、fixture 或日志；
- 不把 Owner 私人猫照片放入 repo；
- 不改变 PolyForm Noncommercial 许可证方向；
- 不把用户目录硬编码进代码；
- 不自行修改 `MASTER-SPEC.md` 的产品决策。

## 技术方向

- Python 3.11+；
- 业务逻辑放 `src/`；
- `scripts/` 为薄入口；
- 状态优先用 JSON/YAML 文件，不上数据库；
- 优先标准库和轻量依赖；
- 不引入 SciPy，除非有不可替代的明确理由；
- 不引入 Web framework；
- 所有外部可变规则配置化。

## 隐私规则

私人 workspace 必须设计在 Git repo 外。

Windows 默认建议使用类似：

`%LOCALAPPDATA%\CatStickerSkill\workspace`

同时允许 `CAT_STICKER_HOME` 覆盖。

任何测试都不得依赖真实 Owner 私人图片。

## 完成后请不要继续 Phase 1

请停在 Phase 0，并返回：

1. 文件树；
2. 每个核心文件的作用；
3. 关键架构选择；
4. 执行过的测试与完整结果摘要；
5. 是否发生任何网络/付费 API 调用（预期必须为否）；
6. privacy check 结果；
7. 仍存在的明确问题；
8. Phase 0 是否逐条满足 `CODEX-ROADMAP.md` 验收条件。

如在 Phase 0 遇到会影响隐私、许可证、付费门或 Agent 交互模型的关键缺口，先询问 Owner；普通实现细节请做最小、可维护决策，不要把问题重新发散成产品设计讨论。
