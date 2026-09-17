"""Project persistence: atomic JSON save/load, resume support."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from cat_sticker_skill.config import get_workspace_root
from cat_sticker_skill.models.plan import GenerationPlan
from cat_sticker_skill.models.project import ProjectManifest, StickerItem, StickerVersion


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically: temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _project_dir(project_id: str) -> Path:
    return get_workspace_root() / "projects" / project_id


def create_project(project_id: str, name: str = "") -> ProjectManifest:
    """Create a new project on disk."""
    pdir = _project_dir(project_id)
    manifest = ProjectManifest(project_id=project_id)
    data = manifest.to_dict()
    data["name"] = name
    _atomic_write_json(pdir / "project.json", data)
    (pdir / "refs").mkdir(exist_ok=True)
    (pdir / "stickers").mkdir(exist_ok=True)
    return manifest


def load_project(project_id: str) -> ProjectManifest:
    """Load project from disk. Raises FileNotFoundError if missing."""
    pdir = _project_dir(project_id)
    data = _read_json(pdir / "project.json")
    manifest = ProjectManifest(
        project_id=data["project_id"],
        created_at=data.get("created_at", ""),
        characters=data.get("characters", {}),
        total_paid_generations=data.get("total_paid_generations", 0),
        total_retries=data.get("total_retries", 0),
    )
    for sid, sdata in data.get("stickers", {}).items():
        item = StickerItem(
            id=sid,
            caption=sdata.get("caption", ""),
            status=sdata.get("status", "planned"),
            active_version=sdata.get("active_version", 0),
        )
        for vstr, vdata in sdata.get("versions", {}).items():
            item.versions[int(vstr)] = StickerVersion(
                version=int(vstr),
                generated_file=vdata.get("generated_file", ""),
                cutout_file=vdata.get("cutout_file", ""),
                composed_file=vdata.get("composed_file", ""),
                created_at=vdata.get("created_at", ""),
            )
        manifest.stickers[sid] = item
    return manifest


def save_project(manifest: ProjectManifest) -> None:
    """Atomically save project manifest."""
    pdir = _project_dir(manifest.project_id)
    data = manifest.to_dict()
    _atomic_write_json(pdir / "project.json", data)


def save_plan(plan: GenerationPlan) -> None:
    """Save generation plan."""
    pdir = _project_dir(plan.project_id)
    _atomic_write_json(pdir / "plan.json", plan.to_dict())


def load_plan(project_id: str) -> GenerationPlan:
    """Load generation plan — round-trip all fields."""
    pdir = _project_dir(project_id)
    data = _read_json(pdir / "plan.json")
    from cat_sticker_skill.models.plan import StickerPlanItem
    items = []
    for item in data.get("items", []):
        ref = item.get("reference", {})
        items.append(StickerPlanItem(
            id=item["id"],
            reference_type=ref.get("type", "single"),
            reference_ids=ref.get("ids", []),
            caption=item.get("caption", ""),
            emotion=item.get("emotion", ""),
            pose=item.get("pose", ""),
            composition=item.get("composition", ""),
            identity_priority=item.get("identity_priority", "high"),
            typography_preset=item.get("typography_preset", "auto"),
            status=item.get("status", "planned"),
            theme=item.get("theme", ""),
            negative_constraints=item.get("negative_constraints", []),
        ))
    return GenerationPlan(
        project_id=data["project_id"],
        plan_revision=data.get("plan_revision", 1),
        approved_revision=data.get("approved_revision", 0),
        approved_for_generation=data.get("approved_for_generation", False),
        items=items,
    )


def project_path(project_id: str) -> Path:
    return _project_dir(project_id)


def sticker_version_dir(project_id: str, sticker_id: str, version: int) -> Path:
    return _project_dir(project_id) / "stickers" / sticker_id / f"v{version:03d}"
