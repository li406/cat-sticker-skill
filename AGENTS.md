# AGENTS.md — Project Governance & Development Instructions

## Project Governance (Owner-Driven)

本仓库使用 Owner-Driven 轻量治理。开始任何工作前优先读取：

1. `PRODUCT-GOAL.md`
2. `ROADMAP.md`
3. `CURRENT-STAGE.md`
4. `BACKLOG.md`

详细方法见 `docs/ops/PROJECT-OPERATING-MANUAL.md`。

### 执行原则

- 同时只推进一个 `CURRENT-STAGE`；所有主要工作必须直接服务当前 Stage。
- 新问题先分级：**Blocker / Important / Polish**。
- Blocker 现在修；Important / Polish 写入 `BACKLOG.md`，不阻塞当前 Stage。
- Current Stage 验收全部通过且无 Blocker 时，必须结束 Stage；"还能继续优化"不是继续的理由。
- **默认禁止**开放式"全面检查项目还有什么问题"式 Review。
- 默认 Review 只回答一个问题：**是否存在阻止 CURRENT-STAGE 验收的 Blocker？**
- 如果 Owner 只说"继续"，默认含义是继续 CURRENT-STAGE 的下一项未完成工作，不是自由找事做。

### Owner 沟通

Owner 负责产品目标、实际使用反馈和阶段验收，不要求 Owner 做底层工程判断。技术问题必须翻译成：用户会看到什么、是否阻止当前 Stage、是否必须现在修。

### 项目记忆

聊天不是长期项目状态。影响未来的信息必须落盘：产品方向 → PRODUCT-GOAL，阶段顺序 → ROADMAP，当前范围/验收 → CURRENT-STAGE，非当前事项 → BACKLOG，实现事实 → 代码/tests/git。

---

## Before Starting

1. 读上面四层治理文档，确认当前 Stage。
2. 读 `MASTER-SPEC.md`（产品与架构权威规格）。
3. 不改变 PRODUCT-GOAL 和 MASTER-SPEC 中已确认的产品决策。

## Hard Constraints（不可突破）

- **No Web UI**（no Gradio, FastAPI, React, Vue, etc.）
- **No GIF / animated output** in v1
- **No second LLM/vision API** — the host Agent does visual understanding for free
- **No SciPy** — use NumPy/Pillow stdlib for flood fill
- **No database** — JSON/YAML files for state
- **No hardcoded user paths** — use config.py
- **No API keys in code, logs, or fixtures** — only `ARK_API_KEY` env var
- **No private photos in the repo**
- Python 3.11+, prefer stdlib and Pillow/NumPy only
- License: PolyForm Noncommercial 1.0.0

## Project Layout

```
src/cat_sticker_skill/   # business logic
scripts/                 # thin CLI entry points
references/              # workflow documentation for Agents
assets/                  # platform presets, typography presets, schemas
tests/                   # unit + public fixtures (no paid API, no private photos)
```

## Testing & Verification

- Run `pytest -q` before commit
- Run `ruff check src/` for lint
- Run `python -m cat_sticker_skill.cli smoke-test` (free, mock provider)
- Run `python -m cat_sticker_skill.cli privacy-check` before any push
- Tests must use mocked providers — no real paid API calls in CI
- New features that touch core logic should include tests

## When to Stop and Ask the Owner

Ask the owner before:
- Changing the payment gate (plan approval flow)
- Changing the license
- Adding a web UI / GIF support / a second image provider
- Removing the legacy flood-fill matting path
- Switching default Seedream model from 4.5
- Anything that would cause unapproved paid API calls
- Anything that would put private photos or keys into the repo

Otherwise, make minimal, maintainable decisions that serve the CURRENT-STAGE.
