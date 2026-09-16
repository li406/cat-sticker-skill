"""Export WeChat static sticker package.

Deterministic banner: crop/pad from a clean generated image, no stretching.
Respects active_version from project manifest.
"""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from PIL import Image

from cat_sticker_skill.validation.sticker import validate_sticker_package


def _crop_pad(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Resize to cover target then center-crop. No distortion."""
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        # Source is wider: fit height, crop width
        new_h = target_h
        new_w = int(src_w * (target_h / src_h))
    else:
        new_w = target_w
        new_h = int(src_h * (target_w / src_w))

    resized = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def export_wechat_package(
    stickers_dir: Path,
    output_dir: Path,
    cover_source: Optional[Path] = None,
    banner_source: Optional[Path] = None,
    preset_version: str = "wechat_static_v1_user_verified",
) -> Path:
    """Build a complete WeChat static sticker package.

    Uses active version from each sticker's version dirs (highest version).
    Banner is crop/padded from banner_source, not stretched.
    Raises ValueError if 0 stickers.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stickers_out = output_dir / "stickers"
    stickers_out.mkdir(exist_ok=True)

    # Collect sticker main images
    sticker_files: List[Path] = []
    for sticker_dir in sorted(stickers_dir.glob("sticker_*")):
        vdirs = sorted(sticker_dir.glob("v*"))
        if not vdirs:
            continue
        final = vdirs[-1] / "final_240.png"
        if final.exists():
            idx = sticker_dir.name.split("_")[-1]
            dst = stickers_out / f"{idx}.png"
            Image.open(final).save(dst)
            sticker_files.append(dst)

    if not sticker_files:
        raise ValueError("No stickers found to export. Generate at least one sticker first.")

    # Cover (240x240 white, no text)
    cover_path = output_dir / "cover.png"
    if cover_source and cover_source.exists():
        img = Image.open(cover_source).convert("RGB").resize((240, 240), Image.LANCZOS)
    else:
        first = sorted(stickers_dir.glob("sticker_*"))[0]
        raw = sorted(first.glob("v*/generated.png"))[0]
        img = Image.open(raw).convert("RGB").resize((240, 240), Image.LANCZOS)
    img.save(cover_path)

    # Icon (50x50 white)
    (Image.open(cover_path).resize((50, 50), Image.LANCZOS)).save(output_dir / "icon.png")

    # Banner (750x400, crop/pad not stretch)
    banner_path = output_dir / "banner.png"
    if banner_source and banner_source.exists():
        banner_img = Image.open(banner_source).convert("RGB")
        _crop_pad(banner_img, 750, 400).save(banner_path)

    # Preview
    preview_path = output_dir / "preview.png"
    n = len(sticker_files)
    cols = min(n, 5)
    rows = (n + cols - 1) // cols
    canvas = Image.new("RGBA", (cols * 240, rows * 240), (255, 255, 255, 255))
    for i, sf in enumerate(sticker_files):
        img = Image.open(sf)
        r, c = divmod(i, cols)
        canvas.paste(img, (c * 240, r * 240), img)
    canvas.convert("RGB").save(preview_path)

    # Manifest
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preset_version": preset_version,
        "sticker_count": len(sticker_files),
        "files": {
            "stickers": [f.name for f in sticker_files],
            "cover": "cover.png",
            "icon": "icon.png",
            "banner": "banner.png" if banner_path.exists() else None,
            "preview": "preview.png",
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    # Validation report
    val_result = validate_sticker_package(output_dir)
    report = {
        "level": val_result.level,
        "checks": val_result.checks,
    }
    (output_dir / "validation-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False)
    )

    # README
    readme = f"""Sticker Package
==============
Generated: {datetime.now().isoformat()}
Stickers: {len(sticker_files)}
Validation: {val_result.level}

Files:
- stickers/      240x240 transparent PNG
- cover.png      240x240 white
- icon.png       50x50 white
- banner.png     750x400 (crop/padded)
- preview.png    Grid overview
- validation-report.json

Note: Helps meet common WeChat formatting requirements.
Does not guarantee platform review approval.
"""
    (output_dir / "README.txt").write_text(readme, encoding="utf-8")

    return output_dir


def zip_package(package_dir: Path, zip_path: Path) -> Path:
    """Zip the package directory for upload."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(package_dir.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(package_dir))
    return zip_path
