---
name: cat-sticker-skill
description: Create static cat/animal stickers from one or more reference photos. The host Agent handles visual understanding and planning; local deterministic tools handle Seedream generation, background removal, typography, validation, and WeChat packaging.
---

# Cat Sticker Skill

> Agent Skill for generating static cat/animal stickers for WeChat.
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
- Workspace is at `CAT_STICKER_HOME` or platform default
- If `ARK_API_KEY` is not set, guide the user to set it as an environment variable or via a local `.env` file. **Do not ask the user to paste their API key into chat.**

## Quick Start

```bash
# Verify installation and config
cat-sticker doctor

# Run a free smoke test (uses mock provider, no paid API calls)
cat-sticker smoke-test

# Create a new project
cat-sticker project create my-cats

# After the Agent builds a plan and the user approves:
cat-sticker generate
```

## Workflow

### 1. Understand the Input

The user provides:
- **One or more reference photos** (cat photos)
- Desired captions / emotions / poses
- Whether photos are the same cat or different cats

The Agent examines each photo and builds a Character Profile.

### 2. Build a Generation Plan

The Agent creates a plan:
- Each sticker item: reference(s), caption, emotion, pose
- Total image count
- Estimated cost
- **Present the plan to the user and wait for explicit approval before any paid generation.**

### 3. Approval Gate (Hard)

No paid image generation occurs until:
- `approved_for_generation == true`
- `approved_revision == plan_revision`
- The run budget has not been exceeded

If the plan changes (references, count, captions, poses), the approval is automatically voided.

### 4. Generate

The controller calls the Seedream provider. Each image:
- Uses reference images as data URIs
- Requests pure/white background, no text
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
- Allow text adjustments (offset, size, preset) without new API calls

### 7. Export WeChat Package

Run:
```bash
cat-sticker package
```

Produces:
- 240×240 transparent PNG main images (active versions)
- 240×240 white-background cover (no text)
- 50×50 icon
- 750×400 banner (cropped/padded from a generated image, no distortion)
- preview contact sheet
- validation-report.json
- ZIP package

## Interaction Rules (User Experience)

The Skill executes mechanical steps, but the Agent must interact proactively:

1. **Before spending money**: Tell the user exactly how many images will be generated and estimated cost. Ask for confirmation.
2. **After each major step**: Show the user what was produced — display images/previews, state what step completed, ask for feedback.
3. **API key**: If `ARK_API_KEY` is not set, instruct the user to set it as an environment variable. **Never ask them to paste it in chat.**
4. **Per-sticker feedback**: Show contact sheet after generation. Regenerate only affected stickers.
5. **Banner**: By default, the banner is deterministically cropped/padded from a verified clean image. AI-generated banners are optional and should be flagged as such.

## Safety Rules

- API key is never logged, displayed, or written to files
- Private photos stay in workspace (outside git repo)
- Each paid generation is counted and reported
- Maximum retries per item is capped
- If plan changes after approval, re-approval is required
- No secrets in error messages or debug output

## Final Report Must Include

After completion, report:
- Project ID
- Success / failure count per sticker
- Total paid image generations
- Total retries
- Estimated cost
- Active version summary
- Validator PASS/WARN/FAIL
- Output path and ZIP path
- Manual review items
