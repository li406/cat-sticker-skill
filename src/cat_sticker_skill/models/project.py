"""Project manifest and sticker version tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict


@dataclass
class StickerVersion:
    version: int
    generated_file: str = ""
    cutout_file: str = ""
    composed_file: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class StickerItem:
    id: str
    caption: str = ""
    status: str = "planned"
    active_version: int = 0
    versions: Dict[int, StickerVersion] = field(default_factory=dict)

    def add_version(self, version: StickerVersion) -> None:
        self.versions[version.version] = version
        self.active_version = version.version


@dataclass
class ProjectManifest:
    project_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    characters: Dict[str, dict] = field(default_factory=dict)
    stickers: Dict[str, StickerItem] = field(default_factory=dict)
    total_paid_generations: int = 0
    total_retries: int = 0

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "created_at": self.created_at,
            "characters": self.characters,
            "stickers": {
                sid: {
                    "caption": s.caption,
                    "status": s.status,
                    "active_version": s.active_version,
                    "versions": {
                        str(v): {
                            "generated_file": sv.generated_file,
                            "cutout_file": sv.cutout_file,
                            "composed_file": sv.composed_file,
                            "created_at": sv.created_at,
                        }
                        for v, sv in s.versions.items()
                    },
                }
                for sid, s in self.stickers.items()
            },
            "total_paid_generations": self.total_paid_generations,
            "total_retries": self.total_retries,
        }
