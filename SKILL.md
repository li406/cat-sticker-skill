# Cat Sticker Skill

> Agent Skill for generating static cat stickers for WeChat.
> The Agent handles visual understanding and planning; local scripts handle paid generation, deterministic image processing, and export.

## When to Use This Skill

Use this skill when the user wants to:
- Generate static cat/animal stickers from reference photos
- Create a WeChat sticker album (表情包专辑)
- Add funny captions to animal photos in a "meme" style

Do NOT use this for:
- GIF / animated stickers
- Video content
- Web UI or design mockups
- Anything not involving animal reference photos

## Prerequisites

- `ARK_API_KEY` environment variable must be set (Volcengine / Seedream)
- Python 3.11+ with dependencies installed (`pip install -e ".[dev]"`)
- Workspace is at `CAT_STICKER_HOME` or `%LOCALAPPDATA%\CatStickerSkill\workspace`

## Workflow

### 1. Understand the Input

The user provides:
- **One or more reference photos** (cat photos)
- Optional: captions, style preferences, number of stickers

If multiple photos are provided:
- Ask the user whether they are the **same cat** (reference group) or **different cats** (independent)
- Never automatically merge photos into a reference group without user confirmation

### 2. Generate Character Profile

Visually inspect each reference photo and create a Character Profile:
- Coat color, pattern, eye color, body type
- Accessories (hats, collars)
- What must be preserved vs. what should be avoided

### 3. Create Generation Plan

Before any paid image generation:
- Design each sticker: caption, emotion, pose, composition
- Choose typography preset (default: `meme-yellow`)
- Show the user: total count, each caption, estimated cost
- Wait for approval

**Default rule: no Seedream API call until the user approves the plan.**
If the user says "just do it" / "skip approval", still build an internal plan with a hard cap on image count.

### 4. Generate Images (paid)

Call the Seedream provider script. Each request:
- Uses reference image(s) as input
- Prompt explicitly forbids text, letters, watermarks, logos
- Requests pure/white background
- Saves raw output to workspace

### 5. Local Post-processing

For each generated image:
1. Background removal (flood-fill from edges, preserve internal white areas)
2. Typography composition (text drawn locally, not by AI)
3. Resize to 240×240 with transparent background

### 6. Review and Iterate

- Generate a contact sheet (grid preview)
- Show the user all stickers
- Allow per-sticker regeneration (does not affect other stickers)
- Preserve all versions; never overwrite

### 7. Export WeChat Package

Run the export script to produce:
- 240×240 transparent PNG main images
- 240×240 white-background cover (no text)
- 50×50 icon
- 750×400 banner
- ZIP package

## Safety Rules

- API key is never logged, displayed, or written to files
- Private photos stay in workspace (outside git repo)
- Each paid generation is counted and reported
- Maximum retries per item is capped
- If plan changes after approval, re-approval is required

## Final Report Must Include

After completion, report:
- Success / failure count per sticker
- Total paid image generations
- Total retries
- Output directory path
- Validation results (PASS / WARN / FAIL)
- Any items needing manual review
