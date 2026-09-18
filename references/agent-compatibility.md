# Agent & Environment Compatibility

This document lists what has **actually been tested**.
Anything not listed here is **not verified** — it may work, but the author has not tried it.

## Host Agents (real paid generation)

| Agent | OS | Status | Notes |
|---|---|---|---|
| Doubao desktop agent (豆包办公任务) | Windows 11 | **Verified** | End-to-end: real cat photos -> Seedream -> WeChat ZIP, Stage 1 & Stage 2 acceptance passed |
| OpenAI Codex / other coding agents | - | **Not tested** | SKILL.md is written agent-agnostic, but no real paid run has been done |

How to use with an arbitrary agent:
1. Clone the repo, `pip install -e .`
2. Set `ARK_API_KEY`
3. Tell the agent: "Read SKILL.md and follow its workflow"
4. The agent should then examine reference photos, build a plan, wait for your approval, and only then call `cat-sticker generate`.

## CI / Headless (mock only, no paid API)

| Platform | Python | Status |
|---|---|---|
| Ubuntu (GitHub Actions) | 3.11, 3.12 | Mock E2E (smoke-test) passes |
| Windows | 3.11 | Mock E2E passes |

## Runtime

- Python 3.11+ (tested on 3.11; 3.12 in CI)
- Dependencies: Pillow, NumPy (see pyproject.toml)
- CJK font required at runtime (auto-detected; see README)
- Image generation requires a Volcengine / Ark API key with Seedream access

## Known Limitations

- No GIF / animated output (v1)
- No web UI - CLI only
- Single image provider (Seedream / Ark)
- Private photos are never uploaded; they live in your local workspace