# Workflow

## Overview

1. User provides reference photos
2. Agent builds Character Profile + Generation Plan
3. User approves plan (hard gate)
4. Paid generation (Seedream)
5. Local post-processing (flood-fill + typography + resize)
6. Review, iterate, regenerate
7. Export WeChat package

## Key Principles

- AI generates clean image (no text); PIL adds text locally
- Never generate text via AI (causes typos, overlap)
- Approval is a code-level hard gate, not just convention
- All state saved to workspace outside the repo
