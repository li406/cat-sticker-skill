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
# 1. Set your API key
export ARK_API_KEY=your-key-here

# 2. Install
pip install -e ".[dev]"

# 3. Use with an AI Agent
# Tell the Agent: "Read SKILL.md and help me make cat stickers."
```

## Project Structure

```
├── SKILL.md              # Agent workflow SOP
├── AGENTS.md             # Development rules for coding agents
├── MASTER-SPEC.md        # Authoritative product/architecture spec
├── src/cat_sticker_skill/
├── scripts/
├── references/
├── assets/
└── tests/
```

## License

**PolyForm Noncommercial 1.0.0** — source-available, not OSI open source.
Commercial use requires separate permission.

## Disclaimer

This tool helps you produce sticker images that meet common WeChat formatting
requirements. It does not guarantee WeChat platform review approval.
