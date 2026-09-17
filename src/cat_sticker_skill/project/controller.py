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
        reference_bytes: dict[str, bytes],
        dry_run: bool = False,
        unit_price_cny: float | None = None,
    ) -> dict:
        """Execute generation for approved, non-completed items.

        Args:
            reference_bytes: map of reference_id -> image bytes
            dry_run: if True, use mock provider without API key
            unit_price_cny: optional cost per image

        Returns summary dict.
        """
        allowed, reason = self.can_generate()
        if not allowed:
            return {"success": False, "error": reason}

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
        ledger = self.gate.create_ledger(
            max_total_calls=self.plan.total_images * (get_max_retries() + 1),
            max_retries_per_item=get_max_retries(),
        )

        results = {}

        for item in self.plan.items:
            validate_id(item.id, "sticker_id")

            # Skip already-successful items (resume idempotency)
            existing = self.manifest.stickers.get(item.id)
            if existing and existing.status == "done" and existing.active_version > 0:
                results[item.id] = {"status": "skipped", "reason": "already done"}
                continue

            if not ledger.can_call(item.id):
                results[item.id] = {"status": "skipped", "reason": "budget exhausted"}
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
                continue

            # Compute version ONCE at start
            version = self._next_version(item.id)
            version_dir = store.sticker_version_dir(self.project_id, item.id, version)
            version_dir.mkdir(parents=True, exist_ok=True)
            raw_path = version_dir / "generated.png"

            # Build prompt
            prompt = build_seedream_prompt(item)

            ok = False
            if provider_mode == "real":
                from cat_sticker_skill.providers.seedream import SeedreamRequest, generate_image
                req = SeedreamRequest(
                    prompt=prompt,
                    reference_images=ref_bytes_list,
                    output_path=raw_path,
                )
                result = generate_image(
                    req, api_key=api_key, model=get_seedream_model(),
                    max_retries=0,  # retry handled by controller loop below
                    timeout=get_request_timeout(),
                )
                # Count actual HTTP attempts
                ledger.record_call(CallRecord(
                    item_id=item.id, attempt=1, success=result.success,
                    error_class=type(result.error).__name__ if result.error else "",
                    duration_seconds=result.duration_seconds,
                ))
                ok = result.success
            else:
                # Mock: create synthetic image
                import numpy as np
                from PIL import Image
                arr = np.random.randint(180, 255, (512, 512, 3), dtype=np.uint8)
                Image.fromarray(arr).save(raw_path)
                ledger.record_call(CallRecord(item_id=item.id, attempt=1, success=True))
                ok = True

            if ok:
                self._post_process(item, version_dir, version)
                results[item.id] = {"status": "done", "version": version}
            else:
                results[item.id] = {"status": "failed"}

        self.manifest.total_paid_generations += ledger.paid_calls_used
        self.manifest.total_retries += ledger.retry_calls_used
        store.save_project(self.manifest)

        return {
            "success": True,
            "results": results,
            "provider_mode": provider_mode,
            "requests_sent": ledger.requests_sent if hasattr(ledger, 'requests_sent') else ledger.paid_calls_used,
            "paid_calls": ledger.paid_calls_used,
            "retry_calls": ledger.retry_calls_used,
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
        """Run flood-fill + typography + resize. Version is passed in, not recomputed."""
        from PIL import Image

        from cat_sticker_skill.matting.floodfill import remove_solid_background
        from cat_sticker_skill.typography.meme_yellow import compose_text

        raw = version_dir / "generated.png"
        cutout = version_dir / "cutout.png"
        composed = version_dir / "composed.png"
        final = version_dir / "final_240.png"

        remove_solid_background(raw, cutout)
        compose_text(cutout, composed, item.caption)
        img = Image.open(composed).convert("RGBA")
        img.resize((240, 240), Image.LANCZOS).save(final, "PNG")

        # Update manifest with the EXPLICIT version number
        if item.id not in self.manifest.stickers:
            self.manifest.stickers[item.id] = StickerItem(id=item.id, caption=item.caption)
        s_item = self.manifest.stickers[item.id]
        s_item.status = "done"
        s_item.add_version(StickerVersion(
            version=version,
            generated_file=str(raw),
            cutout_file=str(cutout),
            composed_file=str(composed),
        ))
        s_item.active_version = version
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

    # --- Resume ---

    def resume_pending(self) -> List[str]:
        """Return list of sticker IDs that need (re)generation."""
        pending = []
        for sid, item in self.manifest.stickers.items():
            if item.status in ("planned", "failed") or item.active_version == 0:
                pending.append(sid)
        return pending
