"""Project controller: high-level orchestration.

The Agent calls these methods, not the low-level modules directly.
"""

from __future__ import annotations

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


class ProjectController:
    """Orchestrates the full sticker generation workflow for one project."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.manifest: ProjectManifest = store.load_project(project_id)
        self.plan: Optional[GenerationPlan] = None
        self.gate: Optional[ApprovalGate] = None

    # --- Project lifecycle ---

    @classmethod
    def create(cls, project_id: str, name: str = "") -> "ProjectController":
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
        """Modify plan — automatically invalidates approval."""
        if self.gate is None:
            self.load_plan()
        self.gate.invalidate_approval()
        self.gate.plan.items = items
        self.gate.plan.plan_revision += 1
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
        unit_price_cny: float | None = None,
    ) -> dict:
        """Execute generation for all approved items.

        Uses mock provider if no API key is configured.
        Returns a summary dict.
        """
        allowed, reason = self.can_generate()
        if not allowed:
            return {"success": False, "error": reason}

        if self.gate is None or self.plan is None:
            return {"success": False, "error": "No plan loaded."}

        ledger = self.gate.create_ledger(
            max_total_calls=self.plan.total_images + get_max_retries(),
            max_retries_per_item=get_max_retries(),
        )

        api_key = get_api_key()
        results = {}

        for item in self.plan.items:
            if not ledger.can_call(item.id):
                results[item.id] = {"status": "skipped", "reason": "budget exhausted"}
                continue

            ref_key = item.reference_ids[0] if item.reference_ids else ""
            ref_bytes_list = [reference_bytes[ref_key]] if ref_key in reference_bytes else []

            version_dir = store.sticker_version_dir(
                self.project_id, item.id, self._next_version(item.id)
            )
            version_dir.mkdir(parents=True, exist_ok=True)
            raw_path = version_dir / "generated.png"

            if api_key:
                from cat_sticker_skill.providers.seedream import SeedreamRequest, generate_image
                req = SeedreamRequest(
                    prompt=item.prompt_text() if hasattr(item, "prompt_text") else item.caption,
                    reference_images=ref_bytes_list,
                    output_path=raw_path,
                )
                result = generate_image(
                    req, api_key=api_key, model=get_seedream_model(),
                    max_retries=get_max_retries(), timeout=get_request_timeout(),
                )
                ledger.record_call(CallRecord(
                    item_id=item.id, attempt=1, success=result.success,
                    error_class=type(result.error).__name__ if result.error else "",
                    duration_seconds=result.duration_seconds,
                ))
                ok = result.success
            else:
                # Dry-run / mock: create a synthetic image
                import numpy as np
                from PIL import Image
                arr = np.random.randint(200, 255, (512, 512, 3), dtype=np.uint8)
                Image.fromarray(arr).save(raw_path)
                ledger.record_call(CallRecord(item_id=item.id, attempt=1, success=True))
                ok = True

            # Post-process
            if ok:
                self._post_process(item, version_dir)
                results[item.id] = {"status": "done", "version": self._next_version(item.id)}
            else:
                results[item.id] = {"status": "failed"}

        self.manifest.total_paid_generations += ledger.paid_calls_used
        self.manifest.total_retries += ledger.retry_calls_used
        store.save_project(self.manifest)

        return {
            "success": True,
            "results": results,
            "paid_calls": ledger.paid_calls_used,
            "retry_calls": ledger.retry_calls_used,
            "remaining_budget": ledger.remaining_budget,
        }

    def _next_version(self, sticker_id: str) -> int:
        item = self.manifest.stickers.get(sticker_id)
        if item and item.versions:
            return max(item.versions.keys()) + 1
        return 1

    def _post_process(self, item: StickerPlanItem, version_dir: Path) -> None:
        """Run flood-fill + typography + resize."""
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

        # Update manifest
        if item.id not in self.manifest.stickers:
            self.manifest.stickers[item.id] = StickerItem(id=item.id, caption=item.caption)
        s_item = self.manifest.stickers[item.id]
        s_item.status = "done"
        s_item.add_version(StickerVersion(
            version=self._next_version(item.id) - 1,
            generated_file=str(raw),
            cutout_file=str(cutout),
            composed_file=str(composed),
        ))

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

    # --- Resume ---

    def resume_pending(self) -> List[str]:
        """Return list of sticker IDs that need (re)generation."""
        pending = []
        for sid, item in self.manifest.stickers.items():
            if item.status in ("planned", "failed") or item.active_version == 0:
                pending.append(sid)
        return pending
