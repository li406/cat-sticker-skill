# AGENTS.md — Development Instructions

This file guides AI coding agents (Codex, etc.) working in this repository.

## Before Starting

1. Read `MASTER-SPEC.md` — it is the authoritative product and architecture spec.
2. Read `CODEX-ROADMAP.md` — it defines the phased development order.
3. Do not change product decisions in MASTER-SPEC without owner approval.

## Hard Constraints

- **No Web UI** (no Gradio, FastAPI, React, Vue, etc.)
- **No GIF / animated output** in v1
- **No second LLM/vision API** — the host Agent does visual understanding for free
- **No SciPy** — use NumPy/Pillow stdlib for flood fill
- **No database** — JSON/YAML files for state
- **No hardcoded user paths** — use config.py
- **No API keys in code, logs, or fixtures**
- **No private photos in the repo**
- **Python 3.11+**, prefer stdlib and Pillow/NumPy only

## Project Layout

```
src/cat_sticker_skill/   # business logic
scripts/                 # thin CLI entry points
references/              # workflow documentation for Agents
assets/                  # platform presets, typography presets, schemas
tests/                   # unit + public fixtures (no paid API, no private photos)
```

## Testing

- Run `pytest` before every commit
- Run `ruff check src/` for linting
- Tests must use mocked providers — no real paid API calls
- Real paid tests are opt-in via `RUN_PAID_TESTS=1`
- New features must include tests

## When to Stop and Ask

Ask the owner before:
- Changing the payment gate (plan approval flow)
- Changing the license
- Adding a web UI
- Adding GIF support
- Adding a second image provider
- Removing the legacy flood-fill matting path
- Switching default Seedream model from 4.5

Otherwise, make minimal, maintainable decisions.
