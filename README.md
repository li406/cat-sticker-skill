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
7. Exports a WeChat-ready package

## Quick Start

```bash
# 1. Set your API key (do NOT paste it into chat)
export ARK_API_KEY=your-key-here

# 2. Check installation
cat-sticker doctor

# 3. Free smoke test (no paid API)
cat-sticker smoke-test
```

## CLI Commands

| Command | Description |
|---|---|
| `cat-sticker doctor` | Check installation and config |
| `cat-sticker smoke-test` | Free mock E2E test |
| `cat-sticker privacy-check` | Scan tracked files for secrets |
| `cat-sticker project create <name>` | Create a new project |
| `cat-sticker project list` | List projects |
| `cat-sticker project show` | Show project details |
| `cat-sticker plan show` | Show current plan |
| `cat-sticker plan approve` | Approve plan |
| `cat-sticker generate` | Generate (requires API key) |
| `cat-sticker generate --dry-run` | Mock generate |
| `cat-sticker regenerate <id>` | Regenerate single sticker |
| `cat-sticker versions <id>` | List versions |
| `cat-sticker activate-version <id> <v>` | Activate a version |
| `cat-sticker resume` | Resume pending |
| `cat-sticker validate` | Validate output |
| `cat-sticker package` | Export WeChat ZIP |
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

Your cat photos stay outside the git repo in your local workspace.

## License

PolyForm Noncommercial 1.0.0. No commercial use without permission.

## WeChat Upload

This tool helps you create the files. WeChat sticker platform approval is not guaranteed.
