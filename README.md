# cat-sticker-skill

> AI Agent-native cat sticker generation skill. The Agent looks at photos, plans stickers, and talks to you. Local scripts handle paid generation, background removal, text overlay, and WeChat export.

## What It Does

You give the Agent one or more cat photos. It:
1. Analyzes the cat's appearance
2. Plans stickers with captions, emotions, and poses
3. Shows you the plan for approval before spending money
4. Calls Seedream to generate clean images (no text)
5. Overlays text locally (deterministic, controllable)
6. Removes background to transparent PNG
7. Exports a WeChat-ready ZIP package

## Requirements

- Python 3.11+
- A Volcengine / Ark API key with Seedream access
- A CJK font on the system (auto-detected)

## Install

```bash
git clone https://github.com/li406/cat-sticker-skill.git
cd cat-sticker-skill
pip install -e .
```

## Quick Start

```bash
# 1. Set your API key (do NOT paste it into chat)
export ARK_API_KEY=your-key-here

# 2. Check installation
cat-sticker doctor

# 3. Free smoke test (no paid API)
cat-sticker smoke-test

# 4. Full workflow
cat-sticker project create my-cats
cat-sticker ref add cat1.jpg --id r1 --project my-cats
# Agent then builds plan, you approve:
cat-sticker plan approve --project my-cats
cat-sticker generate --project my-cats
cat-sticker package --project my-cats
```

## Use with an AI Agent

This project is **Agent-native**: the host AI agent does visual understanding, planning, and caption writing; the CLI does the paid generation and deterministic image processing.

Point your agent at this repo and tell it:

> "Read SKILL.md and follow its workflow. These are my cat photos: [attach]. Plan a sticker set, show me before spending money."

The agent will read `SKILL.md`, examine your photos, propose a plan, and wait for your approval before any paid API call.

See `references/agent-compatibility.md` for what has actually been tested.

## CLI Commands

| Command | Description |
|---|---|
| `cat-sticker doctor` | Check installation and config |
| `cat-sticker smoke-test` | Free mock E2E test |
| `cat-sticker privacy-check` | Scan tracked files for secrets |
| `cat-sticker project create <name>` | Create a new project |
| `cat-sticker project list` | List projects |
| `cat-sticker project show <name>` | Show project details |
| `cat-sticker ref add <path> --id <id> --project <p>` | Add reference image |
| `cat-sticker ref list --project <p>` | List references |
| `cat-sticker plan show --project <p>` | Show current plan |
| `cat-sticker plan approve --project <p>` | Approve plan |
| `cat-sticker generate --project <p> [--dry-run]` | Generate |
| `cat-sticker regenerate <id> --project <p> [--dry-run]` | Regenerate single sticker |
| `cat-sticker versions <id> --project <p>` | List versions |
| `cat-sticker activate-version <id> <v> --project <p>` | Activate a version |
| `cat-sticker text-adjust <id> --project <p> [--y-offset N] [--font-scale F] [--vertical-position top|center|bottom]` | Re-compose text locally (no paid API) |
| `cat-sticker resume --project <p>` | Resume pending |
| `cat-sticker validate --project <p>` | Validate output |
| `cat-sticker package --project <p> --out <dir>` | Export WeChat ZIP |
| `cat-sticker version` | Show version |

## Fonts

- **Windows**: uses `C:\Windows\Fonts\msyhbd.ttc` (Microsoft YaHei Bold)
- **Linux CI**: installs `fonts-noto-cjk` via apt
- **macOS**: uses PingFang SC if available

## API Key

- Set via `ARK_API_KEY` environment variable only
- Never paste the key into chat messages
- Never commit it to the repo

## Private Photos

Your cat photos stay outside the git repo in your local workspace (`$CAT_STICKER_HOME/projects/<id>/refs/`).

## License

PolyForm Noncommercial 1.0.0. No commercial use without permission.

## WeChat Upload

This tool helps you create the files. WeChat sticker platform approval is not guaranteed.

## Compatibility

See `references/agent-compatibility.md`. In short:

- **Verified end-to-end**: Doubao desktop agent on Windows with real cat photos and real Seedream.
- **Mock CI**: Ubuntu (Python 3.11/3.12) and Windows (Python 3.11) via GitHub Actions.
- **Not verified**: Codex and other agents (SKILL.md is written to be agent-agnostic, but untested).

## Status

v1.0 - owner-tested. Two real sticker sets made, one uploaded to WeChat.
