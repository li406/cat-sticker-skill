# Changelog

## 0.2.0 (2026-09-17) — RC4 Final Gate

- BLOCKER 1: `approved_reference_hashes` persisted in plan.json; re-approved recomputes on-disk SHA256
- BLOCKER 2: `CharacterProfile.from_dict` accepts both nested and flat JSON schema
- BLOCKER 3: character/ref replace invalidates approval cross-process (loads plan from disk)
- BLOCKER 4: `StickerItem.add_version(activate=False)`; post-process failure no longer marks incomplete version active; resume recovers `generated`/`processing_failed` locally without re-paying Seedream
- BLOCKER 5: partial batch returns `success=False` (non-zero exit)
- BLOCKER 6: privacy scanner rewritten — no tests/ downgrade, private paths redacted+HIGH, unexpected tracked media gate
- BLOCKER 8: `matting_strategy` (legacy/precompose) persisted; `matting-ab` CLI command added
- BLOCKER 9: `text-adjust --caption` updates plan item and invalidates approval; `--preset` persists to plan
- BLOCKER 10: CI runs `cat-sticker smoke-test` on Ubuntu + Windows matrix
- 66 tests pass, ruff clean, privacy-check PASS, smoke-test PASS

## 0.1.0 (2026-09-16)

- Phase 0: Project skeleton established
- Initial SKILL.md, AGENTS.md, README.md
- Configuration system with workspace path resolution
- Privacy scanner minimum implementation
- Basic project manifest and data models
- pytest and ruff setup
