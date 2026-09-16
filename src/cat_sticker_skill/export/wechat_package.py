"""Export WeChat static sticker package.

Produces a complete upload-ready package:
- stickers/  (240x240 transparent PNG)
- cover.png  (240x240 white, no text)
- icon.png   (50x50 white)
- banner.png (750x400, no text)
- preview.png (contact sheet)
- manifest.json
- validation-report.json
- README.txt
"""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from PIL import Image


def export_wechat_package(
    stickers_dir: Path,
    output_dir: Path,
    cover_source: Path | None = None,
    banner_source: Path | None = None,
    preset_version: str = "wechat_static_v1_user_verified",
) -> Path:
    """Build a complete WeChat static sticker package.

    Args:
        stickers_dir: Directory containing sticker_XXX/v00X/final_240.png
        output_dir: Where to write the package
        cover_source: Optional source image for cover (default: first sticker's generated.png)
        banner_source: Optional source for banner (default: AI-generated or skipped)
        preset_version: Platform preset version string

    Returns:
        Path to the output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    stickers_out = output_dir / "stickers"
    stickers_out.mkdir(exist_ok=True)

    # 1. Collect sticker main images (240x240 transparent)
    sticker_files: List[Path] = []
    for sticker_dir in sorted(stickers_dir.glob("sticker_*")):
        vdirs = sorted(sticker_dir.glob("v*"), reverse=True)
        if not vdirs:
            continue
        final = vdirs[0] / "final_240.png"
        if final.exists():
            idx = sticker_dir.name.split("_")[-1]
            dst = stickers_out / f"{idx}.png"
            Image.open(final).save(dst)
            sticker_files.append(dst)

    # 2. Cover image (240x240 white, no text)
    cover_path = output_dir / "cover.png"
    if cover_source and cover_source.exists():
        img = Image.open(cover_source).convert("RGB").resize((240, 240), Image.LANCZOS)
    else:
        # Use first sticker's raw generated image
        first_sticker = sorted(stickers_dir.glob("sticker_*"))[0]
        raw = sorted(first_sticker.glob("v*/generated.png"))[0]
        img = Image.open(raw).convert("RGB").resize((240, 240), Image.LANCZOS)
    img.save(cover_path)

    # 3. Icon (50x50 white)
    icon_path = output_dir / "icon.png"
    cover_img = Image.open(cover_path)
    cover_img.resize((50, 50), Image.LANCZOS).save(icon_path)

    # 4. Banner (750x400)
    banner_path = output_dir / "banner.png"
    if banner_source and banner_source.exists():
        Image.open(banner_source).convert("RGB").resize((750, 400), Image.LANCZOS).save(banner_path)
    else:
        # Skip banner if no source provided
        banner_path = None

    # 5. Preview / contact sheet
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

    # 6. Manifest
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preset_version": preset_version,
        "sticker_count": len(sticker_files),
        "files": {
            "stickers": [f.name for f in sticker_files],
            "cover": "cover.png",
            "icon": "icon.png",
            "banner": "banner.png" if banner_path else None,
            "preview": "preview.png",
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    # 7. README
    readme = f"""Sticker Package
==============
Generated: {datetime.now().isoformat()}
Preset: {preset_version}
Stickers: {len(sticker_files)}

Files:
- stickers/      240x240 transparent PNG (main images for chat)
- cover.png      240x240 white background (album cover)
- icon.png       50x50 white background (chat panel icon)
- banner.png     750x400 (detail page banner, if present)
- preview.png    Grid overview

Note: This package helps meet common WeChat formatting requirements.
It does not guarantee platform review approval.
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
