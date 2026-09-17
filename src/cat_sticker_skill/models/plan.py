"""Generation Plan: the approved plan before any paid image generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StickerPlanItem:
    id: str
    reference_type: str  # "single" or "group"
    reference_ids: List[str] = field(default_factory=list)
    caption: str = ""
    emotion: str = ""
    pose: str = ""
    composition: str = ""
    identity_priority: str = "high"
    typography_preset: str = "auto"
    matting_strategy: str = "legacy"  # "legacy" or "precompose"
    status: str = "planned"
    theme: Optional[str] = None
    negative_constraints: List[str] = field(default_factory=list)
    character_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reference": {"type": self.reference_type, "ids": self.reference_ids},
            "caption": self.caption,
            "emotion": self.emotion,
            "pose": self.pose,
            "composition": self.composition,
            "identity_priority": self.identity_priority,
            "typography_preset": self.typography_preset,
            "matting_strategy": self.matting_strategy,
            "status": self.status,
            "theme": self.theme,
            "negative_constraints": self.negative_constraints,
            "character_id": self.character_id,
        }


@dataclass
class GenerationPlan:
    project_id: str
    plan_revision: int = 1
    approved_revision: int = 0
    approved_for_generation: bool = False
    approved_reference_hashes: Dict[str, str] = field(default_factory=dict)
    items: List[StickerPlanItem] = field(default_factory=list)

    @property
    def total_images(self) -> int:
        return len(self.items)

    @property
    def needs_reapproval(self) -> bool:
        return self.plan_revision != self.approved_revision

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "plan_revision": self.plan_revision,
            "approved_revision": self.approved_revision,
            "approved_for_generation": self.approved_for_generation,
            "approved_reference_hashes": self.approved_reference_hashes,
            "items": [item.to_dict() for item in self.items],
        }
