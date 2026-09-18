"""Project controller: high-level orchestration.

The Agent calls these methods, not the low-level modules directly.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from cat_sticker_skill.config import (
    get_api_key,
    get_max_retries,
    get_request_timeout,
    get_seedream_model,
)
from cat_sticker_skill.models.plan import GenerationPlan, StickerPlanItem
from cat_sticker_skill.models.project import ProjectManifest, StickerItem, StickerVersion
from cat_sticker_skill.project import store
from cat_sticker_skill.workflow.approval import ApprovalGate, CallRecord
from cat_sticker_skill.workflow.prompt_builder import build_seedream_prompt

ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_id(name: str, label: str = "id") -> str:
    """Reject path traversal / absolute paths in IDs."""
    if not ID_PATTERN.match(name):
        raise ValueError(f"Invalid {label}: {name!r} — only letters, digits, dots, dashes, underscores allowed")
    if name.startswith("."):
        raise ValueError(f"Invalid {label}: {name!r} — cannot start with dot")
    return name


class ProjectController:
    """Orchestrates the full sticker generation workflow for one project."""

    def __init__(self, project_id: str):
        validate_id(project_id, "project_id")
        self.project_id = project_id
        self.manifest: ProjectManifest = store.load_project(project_id)
        self.plan: Optional[GenerationPlan] = None
        self.gate: Optional[ApprovalGate] = None

    # --- Project lifecycle ---

    @classmethod
    def create(cls, project_id: str, name: str = "") -> "ProjectController":
        validate_id(project_id, "project_id")
        store.create_project(project_id, name)
        return cls(project_id)

    @classmethod
    def open(cls, project_id: str) -> "ProjectController":
        return cls(project_id)

    # --- Plan management ---

    def build_plan(self, items: List[StickerPlanItem]) -> GenerationPlan:
        """Build a new generation plan. Invalidates any prior approval."""
        self.plan = GenerationPlan(project_id=self.project_id, items=items)
        self.gate = ApprovalGate(self.plan)
        # Initialize manifest sticker entries as planned
        for item in items:
            if item.id not in self.manifest.stickers:
                self.manifest.stickers[item.id] = StickerItem(id=item.id, caption=item.caption)
            else:
                self.manifest.stickers[item.id].caption = item.caption
                self.manifest.stickers[item.id].status = "planned"
        store.save_project(self.manifest)
        store.save_plan(self.plan)
        return self.plan

    def load_plan(self) -> GenerationPlan:
        self.plan = store.load_plan(self.project_id)
        self.gate = ApprovalGate(self.plan)
        return self.plan

    def approve_plan(self) -> None:
        """User explicitly approved the current plan."""
        if self.gate is None:
            self.load_plan()
        self.gate.approve()
        # Snapshot reference hashes at approval time
        mapping = store.load_ref_mapping(self.project_id)
        self.gate.plan.approved_reference_hashes = {
            rid: entry.get("sha256", "") for rid, entry in mapping.items()
        }
        store.save_plan(self.gate.plan)

    def modify_plan(self, items: List[StickerPlanItem]) -> GenerationPlan:
        """Modify plan — invalidates approval, revision +1 (single increment)."""
        if self.gate is None:
            self.load_plan()
        self.gate.invalidate_approval()  # sets approved=False AND bumps revision
        self.gate.plan.items = items
        # NOTE: do NOT increment revision again here — invalidate_approval already did it
        store.save_plan(self.gate.plan)
        return self.gate.plan

    # --- Generation ---

    def can_generate(self) -> tuple[bool, str]:
        if self.gate is None:
            return False, "No plan loaded."
        return self.gate.can_generate()

    def execute_approved_plan(
        self,
        reference_bytes: dict[str, bytes] | None = None,
        dry_run: bool = False,
        unit_price_cny: float | None = None,
    ) -> dict:
        """Execute generation for approved, non-completed items.

        Args:
            reference_bytes: optional map of reference_id -> bytes.
                If None, automatically loads from project refs/ on disk.
            dry_run: if True, use mock provider without API key
            unit_price_cny: optional cost per image

        Returns summary dict.
        """
        allowed, reason = self.can_generate()
        if not allowed:
            return {"success": False, "error": reason}

        # Re-verify reference hashes against approved snapshot
        hash_ok, hash_reason = self.check_ref_hashes_for_generation()
        if not hash_ok:
            return {"success": False, "error": hash_reason}

        if self.gate is None or self.plan is None:
            return {"success": False, "error": "No plan loaded."}

        api_key = get_api_key()
        if not dry_run and not api_key:
            return {
                "success": False,
                "error": "ARK_API_KEY not set. Use --dry-run for mock, or set the environment variable.",
                "provider_mode": "none",
            }

        provider_mode = "mock" if dry_run or not api_key else "real"

        # Auto-load reference bytes from project refs/ if not provided
        if reference_bytes is None:
            reference_bytes = {}
            for ref_id in store.load_ref_mapping(self.project_id):
                b = store.load_ref_bytes(self.project_id, ref_id)
                if b is not None:
                    reference_bytes[ref_id] = b

        ledger = self.gate.create_ledger(
            max_total_calls=self.plan.total_images * (get_max_retries() + 1),
            max_retries_per_item=get_max_retries(),
        )

        results = {}
        done_count = 0
        fail_count = 0

        for item in self.plan.items:
            validate_id(item.id, "sticker_id")

            # Skip already-successful items (resume idempotency)
            existing = self.manifest.stickers.get(item.id)
            if existing and existing.status == "done" and existing.active_version > 0:
                results[item.id] = {"status": "skipped", "reason": "already done"}
                continue

            # --- Local recovery: generated raw exists but postprocess failed ---
            # Do NOT call Seedream again — just re-run local postprocess.
            if existing and existing.status in ("generated", "processing_failed"):
                # Find the latest version with a raw generated file
                for vnum in sorted(existing.versions.keys(), reverse=True):
                    v = existing.versions[vnum]
                    raw = Path(v.generated_file) if v.generated_file else None
                    if raw and raw.exists():
                        version_dir = raw.parent
                        try:
                            self._post_process(item, version_dir, vnum)
                            results[item.id] = {"status": "done", "version": vnum, "recovered": True}
                            done_count += 1
                        except Exception as e:
                            existing.status = "processing_failed"
                            store.save_project(self.manifest)
                            results[item.id] = {"status": "processing_failed", "error": str(e)}
                            fail_count += 1
                        break
                else:
                    # No recoverable raw — fall through to fresh generation
                    pass
                continue

            # Resolve ALL reference bytes (multi-reference support)
            ref_bytes_list = []
            missing_refs = []
            for ref_id in item.reference_ids:
                if ref_id in reference_bytes:
                    ref_bytes_list.append(reference_bytes[ref_id])
                else:
                    missing_refs.append(ref_id)
            if missing_refs:
                results[item.id] = {"status": "failed", "error": f"Missing references: {missing_refs}"}
                fail_count += 1
                continue

            # Resolve character profile
            character = None
            if item.character_id and item.character_id in self.manifest.characters:
                from cat_sticker_skill.models.character import CharacterProfile
                character = CharacterProfile.from_dict(self.manifest.characters[item.character_id])

            # Compute version ONCE at start
            version = self._next_version(item.id)
            version_dir = store.sticker_version_dir(self.project_id, item.id, version)
            version_dir.mkdir(parents=True, exist_ok=True)
            raw_path = version_dir / "generated.png"

            # Build prompt with character
            prompt = build_seedream_prompt(item, character=character)

            # Bounded retry loop: 1 initial + max_retries retries = 1+max_retries attempts
            ok = False
            max_retries = get_max_retries()
            non_retryable = {"auth", "invalid_input", "invalid_image", "provider_rejected", "permission"}
            for attempt in range(1 + max_retries):
                if not ledger.can_call(item.id):
                    break
                if provider_mode == "real":
                    from cat_sticker_skill.providers.seedream import SeedreamRequest, generate_image
                    req = SeedreamRequest(
                        prompt=prompt,
                        reference_images=ref_bytes_list,
                        output_path=raw_path,
                    )
                    result = generate_image(
                        req, api_key=api_key, model=get_seedream_model(),
                        max_retries=0,
                        timeout=get_request_timeout(),
                    )
                    err_class = getattr(result, "error_class", None) or (
                        type(result.error).__name__ if result.error else ""
                    )
                    ledger.record_call(CallRecord(
                        item_id=item.id, attempt=attempt + 1, success=result.success,
                        error_class=err_class,
                        duration_seconds=result.duration_seconds,
                    ))
                    ok = result.success
                else:
                    # Mock: create synthetic image (white bg + colored block)
                    import numpy as np
                    from PIL import Image
                    arr = np.full((512, 512, 3), 255, dtype=np.uint8)
                    arr[100:400, 100:400] = [100, 100, 150]
                    Image.fromarray(arr).save(raw_path)
                    ledger.record_call(CallRecord(item_id=item.id, attempt=attempt + 1, success=True))
                    ok = True
                    break  # mock always succeeds first try

                if ok:
                    break
                err_class = getattr(result, "error_class", None) or ""
                if err_class in non_retryable:
                    break

            if ok:
                # Mark generated stage BEFORE postprocess — do NOT activate yet
                if item.id not in self.manifest.stickers:
                    self.manifest.stickers[item.id] = StickerItem(id=item.id, caption=item.caption)
                s_item = self.manifest.stickers[item.id]
                s_item.add_version(StickerVersion(
                    version=version,
                    generated_file=str(raw_path),
                ), activate=False)
                s_item.status = "generated"
                store.save_project(self.manifest)
                try:
                    self._post_process(item, version_dir, version)
                    # Only activate AFTER full postprocess success
                    s_item.mark_active(version)
                    s_item.status = "done"
                    store.save_project(self.manifest)
                    results[item.id] = {"status": "done", "version": version}
                    done_count += 1
                except Exception as e:
                    s_item.status = "processing_failed"
                    store.save_project(self.manifest)
                    results[item.id] = {"status": "processing_failed", "error": str(e)}
                    fail_count += 1
            else:
                results[item.id] = {"status": "failed"}
                fail_count += 1

        self.manifest.total_paid_generations += ledger.paid_calls_used
        self.manifest.total_retries += ledger.retry_calls_used
        store.save_project(self.manifest)

        # Partial success semantics
        if fail_count == 0:
            overall = "success"
        elif done_count > 0:
            overall = "partial"
        else:
            overall = "failed"

        return {
            "success": overall == "success",
            "overall_status": overall,
            "results": results,
            "provider_mode": provider_mode,
            "requests_sent": ledger.requests_sent,
            "successful_generations": ledger.successful_generations,
            "retry_attempts": ledger.retry_calls_used,
            "remaining_budget": ledger.remaining_budget,
        }

    def regenerate(self, sticker_id: str, reference_bytes: dict[str, bytes],
                   dry_run: bool = False) -> dict:
        """Regenerate a single sticker as a new version (bypasses resume skip)."""
        validate_id(sticker_id, "sticker_id")
        if self.plan is None:
            self.load_plan()
        item = next((i for i in self.plan.items if i.id == sticker_id), None)
        if not item:
            return {"success": False, "error": f"Sticker {sticker_id} not in plan"}

        # Mark as planned so resume-skip doesn't skip it
        existing = self.manifest.stickers.get(sticker_id)
        if existing:
            existing.status = "planned"
            store.save_project(self.manifest)

        old_items = self.plan.items
        self.plan.items = [item]
        try:
            result = self.execute_approved_plan(reference_bytes, dry_run=dry_run)
        finally:
            self.plan.items = old_items
        return result

    def _next_version(self, sticker_id: str) -> int:
        item = self.manifest.stickers.get(sticker_id)
        if item and item.versions:
            return max(item.versions.keys()) + 1
        return 1

    def _post_process(self, item: StickerPlanItem, version_dir: Path, version: int) -> None:
        """Run matting + typography + resize. Strategy:
        - legacy: generated -> text -> floodfill -> final
        - precompose: generated -> floodfill -> text -> final
        """
        from PIL import Image

        from cat_sticker_skill.matting.floodfill import remove_solid_background
        from cat_sticker_skill.typography.meme_yellow import compose_text

        raw = version_dir / "generated.png"
        cutout = version_dir / "cutout.png"
        composed = version_dir / "composed.png"
        final = version_dir / "final_240.png"
        preset = item.typography_preset or "auto"
        strategy = item.matting_strategy or "legacy"

        if strategy == "precompose":
            remove_solid_background(raw, cutout)
            compose_text(cutout, composed, item.caption, preset=preset)
        else:  # legacy
            compose_text(raw, composed, item.caption, preset=preset)
            remove_solid_background(composed, cutout)
            composed = cutout  # use cutout as final source

        img = Image.open(composed).convert("RGBA")
        img.resize((240, 240), Image.LANCZOS).save(final, "PNG")

        if item.id not in self.manifest.stickers:
            self.manifest.stickers[item.id] = StickerItem(id=item.id, caption=item.caption)
        s_item = self.manifest.stickers[item.id]
        s_item.add_version(StickerVersion(
            version=version,
            generated_file=str(raw),
            cutout_file=str(cutout),
            composed_file=str(composed),
        ), activate=False)
        s_item.active_version = version
        s_item.status = "done"
        store.save_project(self.manifest)

    # --- Version management ---

    def list_versions(self, sticker_id: str) -> List[int]:
        item = self.manifest.stickers.get(sticker_id)
        return sorted(item.versions.keys()) if item else []

    def activate_version(self, sticker_id: str, version: int) -> bool:
        item = self.manifest.stickers.get(sticker_id)
        if not item or version not in item.versions:
            return False
        item.active_version = version
        store.save_project(self.manifest)
        return True

    def get_active_final(self, sticker_id: str) -> Optional[Path]:
        """Get the final_240.png for the active version."""
        item = self.manifest.stickers.get(sticker_id)
        if not item or item.active_version == 0:
            return None
        v = item.versions.get(item.active_version)
        if not v:
            return None
        composed = Path(v.composed_file)
        return composed.parent / "final_240.png"

    def get_active_clean_image(self, sticker_id: str) -> Optional[Path]:
        """Get the raw generated.png (clean, no text) for the active version."""
        item = self.manifest.stickers.get(sticker_id)
        if not item or item.active_version == 0:
            return None
        v = item.versions.get(item.active_version)
        if not v:
            return None
        return Path(v.generated_file)

    def recompose_text(
        self,
        sticker_id: str,
        caption: str | None = None,
        y_offset: int = 0,
        x_offset: int = 0,
        font_scale: float = 1.0,
        preset: str | None = None,
        vertical_position: str | None = None,
    ) -> dict:
        """Re-compose text on the active version's cutout, no Seedream call.

        - caption change: updates manifest + plan item, invalidates approval (prompt semantic changed).
        - preset change: persists to plan item, does NOT invalidate approval (local only).
        """
        validate_id(sticker_id, "sticker_id")
        item = self.manifest.stickers.get(sticker_id)
        if not item or item.active_version == 0:
            return {"success": False, "error": "No active version"}
        v = item.versions[item.active_version]
        cutout = Path(v.cutout_file)
        composed = cutout.parent / "composed.png"
        final = cutout.parent / "final_240.png"
        if not cutout.exists():
            return {"success": False, "error": "cutout.png missing"}

        from PIL import Image

        from cat_sticker_skill.typography.meme_yellow import TypographyOptions, compose_text

        approval_invalidated = False
        if caption is not None:
            item.caption = caption
            # Update plan item caption if plan is loaded
            if self.plan is not None:
                for pi in self.plan.items:
                    if pi.id == sticker_id:
                        pi.caption = caption
                        break
                # Caption is part of Seedream prompt → invalidate approval
                if self.gate:
                    self.gate.invalidate_approval()
                    store.save_plan(self.gate.plan)
                    approval_invalidated = True
            store.save_project(self.manifest)

        if preset is not None and self.plan is not None:
            for pi in self.plan.items:
                if pi.id == sticker_id:
                    pi.typography_preset = preset
                    break
            if self.gate:
                store.save_plan(self.gate.plan)

        text = caption if caption is not None else item.caption
        opts = TypographyOptions(
            y_offset=y_offset,
            x_offset=x_offset,
            font_scale=font_scale,
        )
        if vertical_position is not None:
            opts.vertical_position = vertical_position
        compose_text(cutout, composed, text, options=opts, preset=preset)
        Image.open(composed).convert("RGBA").resize((240, 240), Image.LANCZOS).save(final, "PNG")
        return {"success": True, "file": str(final), "approval_invalidated": approval_invalidated}

    # --- Character management ---

    def _invalidate_approval_for_ref(self, ref_id: str) -> None:
        """Cross-process: load plan from disk if needed and invalidate approval
        if any item references ref_id."""
        plan_path = store.project_path(self.project_id) / "plan.json"
        if not plan_path.exists():
            return
        plan = store.load_plan(self.project_id)
        if any(ref_id in it.reference_ids for it in plan.items):
            gate = ApprovalGate(plan)
            gate.invalidate_approval()
            store.save_plan(plan)

    def _invalidate_approval_for_character(self, character_id: str) -> None:
        plan_path = store.project_path(self.project_id) / "plan.json"
        if not plan_path.exists():
            return
        plan = store.load_plan(self.project_id)
        if any(it.character_id == character_id for it in plan.items):
            gate = ApprovalGate(plan)
            gate.invalidate_approval()
            store.save_plan(plan)

    def import_character(self, char_dict: dict, replace: bool = False) -> dict:
        """Import a CharacterProfile dict. Invalidates approval if profile changes."""
        from cat_sticker_skill.models.character import CharacterProfile
        try:
            cp = CharacterProfile.from_dict(char_dict)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        cid = cp.character_id
        existing = self.manifest.characters.get(cid)
        if existing is not None and not replace:
            return {"success": False, "error": f"Character {cid} already exists (use --replace)"}
        self.manifest.characters[cid] = cp.to_dict()
        store.save_project(self.manifest)
        # Cross-process invalidate: always load plan from disk, not just self.plan
        if replace:
            self._invalidate_approval_for_character(cid)
        elif self.plan is not None:
            self._invalidate_approval_for_character(cid)
        return {"success": True, "character_id": cid}

    def list_characters(self) -> List[str]:
        return sorted(self.manifest.characters.keys())

    def show_character(self, cid: str) -> Optional[dict]:
        return self.manifest.characters.get(cid)

    # --- Ref management ---

    def add_ref(self, ref_id: str, src_path: Path, replace: bool = False) -> dict:
        """Copy a reference image into project refs/, compute SHA256.

        Refuses overwrite by default. Replace invalidates approval.
        """
        validate_id(ref_id, "ref_id")
        src = Path(src_path)
        if not src.exists():
            return {"success": False, "error": f"Source not found: {src}"}
        # Local image preflight
        try:
            from PIL import Image
            with Image.open(src) as im:
                im.verify()
            Image.open(src).load()
        except Exception as e:
            return {"success": False, "error": f"invalid_input: not a readable image ({e})"}
        # Detect MIME
        ext = src.suffix.lower().lstrip(".")
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
        mime = mime_map.get(ext, "")
        if not mime:
            return {"success": False, "error": "invalid_input: unsupported image format"}
        mapping = store.load_ref_mapping(self.project_id)
        if ref_id in mapping and not replace:
            return {"success": False, "error": f"reference {ref_id} already exists (use --replace)"}
        dst_name = f"{ref_id}.{ext}"
        dst = store.refs_dir(self.project_id) / dst_name
        dst.write_bytes(src.read_bytes())
        sha = store.compute_file_sha256(dst)
        size = dst.stat().st_size
        mapping[ref_id] = {"file": f"refs/{dst_name}", "sha256": sha, "size": size}
        store.save_ref_mapping(self.project_id, mapping)
        # Cross-process invalidate on replace
        if replace:
            self._invalidate_approval_for_ref(ref_id)
        return {"success": True, "ref_id": ref_id, "sha256": sha, "size": size}

    # --- Plan import ---

    def import_plan(self, plan_dict: dict) -> dict:
        """Import a GenerationPlan from dict. Forces approved=False."""
        items = []
        seen_ids = set()
        for raw in plan_dict.get("items", []):
            pid = raw.get("id", "")
            if not ID_PATTERN.match(pid):
                return {"success": False, "error": f"invalid_input: bad sticker id {pid!r}"}
            if pid in seen_ids:
                return {"success": False, "error": f"invalid_input: duplicate sticker id {pid}"}
            seen_ids.add(pid)
            ref_ids = raw.get("reference", {}).get("ids", [])
            if not ref_ids:
                return {"success": False, "error": f"invalid_input: {pid} has empty reference group"}
            available_refs = set(store.load_ref_mapping(self.project_id).keys())
            missing = [r for r in ref_ids if r not in available_refs]
            if missing:
                return {"success": False, "error": f"invalid_input: {pid} references missing {missing}"}
            cid = raw.get("character_id")
            if cid and cid not in self.manifest.characters:
                return {"success": False, "error": f"invalid_input: {pid} references unknown character {cid}"}
            items.append(StickerPlanItem(
                id=pid,
                reference_type=raw.get("reference", {}).get("type", "image"),
                reference_ids=ref_ids,
                caption=raw.get("caption", ""),
                emotion=raw.get("emotion", ""),
                pose=raw.get("pose", ""),
                composition=raw.get("composition", ""),
                identity_priority=raw.get("identity_priority", "high"),
                typography_preset=raw.get("typography_preset", "auto"),
                matting_strategy=raw.get("matting_strategy", "legacy"),
                status="planned",
                theme=raw.get("theme", ""),
                negative_constraints=raw.get("negative_constraints", []),
                character_id=cid,
            ))
        # Force approved=False
        plan = GenerationPlan(project_id=self.project_id, items=items)
        plan.approved_for_generation = False
        plan.approved_revision = 0
        self.plan = plan
        self.gate = ApprovalGate(plan)
        for item in items:
            if item.id not in self.manifest.stickers:
                self.manifest.stickers[item.id] = StickerItem(id=item.id, caption=item.caption)
            else:
                self.manifest.stickers[item.id].caption = item.caption
                self.manifest.stickers[item.id].status = "planned"
        store.save_project(self.manifest)
        store.save_plan(plan)
        return {"success": True, "items": len(items), "approved": False}

    # --- Resume ---

    def resume_pending(self) -> List[str]:
        """Return list of sticker IDs that need (re)generation or local postprocess."""
        pending = []
        for sid, item in self.manifest.stickers.items():
            if item.status in ("planned", "failed", "processing_failed") or item.active_version == 0:
                pending.append(sid)
        return pending

    def check_ref_hashes_for_generation(self) -> tuple[bool, str]:
        """Recompute on-disk ref SHA256 and compare against approved snapshot."""
        if self.gate is None:
            return False, "No gate"
        approved_hashes = getattr(self.gate.plan, "approved_reference_hashes", {}) or {}
        if not approved_hashes:
            return True, ""
        mapping = store.load_ref_mapping(self.project_id)
        pdir = store.project_path(self.project_id)
        for ref_id, expected in approved_hashes.items():
            entry = mapping.get(ref_id)
            if not entry:
                return False, f"approval_required: reference {ref_id} missing from refs.json"
            actual_path = pdir / entry["file"]
            if not actual_path.exists():
                return False, f"approval_required: reference {ref_id} file missing on disk"
            actual = store.compute_file_sha256(actual_path)
            if actual != expected:
                return False, f"approval_required: reference {ref_id} bytes changed since approval"
        return True, ""
