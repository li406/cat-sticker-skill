"""WeChat package validator: checks all assets against platform preset."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PIL import Image


@dataclass
class ValidationResult:
    level: str = "PASS"
    checks: List[str] = field(default_factory=list)

    def add(self, passed: bool, message: str, warn_only: bool = False) -> None:
        if passed:
            self.checks.append(f"PASS: {message}")
        elif warn_only:
            self.checks.append(f"WARN: {message}")
            if self.level != "FAIL":
                self.level = "WARN"
        else:
            self.checks.append(f"FAIL: {message}")
            self.level = "FAIL"


def _check_image(path: Path, expected_size: tuple[int, int], label: str,
                 must_have_alpha: bool = False, must_be_white: bool = False) -> ValidationResult:
    r = ValidationResult()
    if not path.exists():
        r.add(False, f"{label}: file not found")
        return r
    try:
        img = Image.open(path)
    except Exception as e:
        r.add(False, f"{label}: cannot open ({e})")
        return r

    r.add(img.format == "PNG", f"{label}: format PNG (got {img.format})")
    r.add(img.size == expected_size, f"{label}: size {expected_size} (got {img.size})")

    if must_have_alpha:
        if img.mode == "RGBA":
            import numpy as np
            alpha = np.array(img.split()[3])
            r.add(int(alpha.min()) < 255, f"{label}: has transparent pixels (alpha_min={int(alpha.min())})")
        else:
            r.add(False, f"{label}: has alpha channel (got {img.mode})")

    if must_be_white:
        if img.mode in ("RGB", "RGBA"):
            rgb = list(img.convert("RGB").getdata())
            avg_r = sum(p[0] for p in rgb) / len(rgb)
            avg_g = sum(p[1] for p in rgb) / len(rgb)
            avg_b = sum(p[2] for p in rgb) / len(rgb)
            r.add(avg_r > 200 and avg_g > 200 and avg_b > 200,
                  f"{label}: near-white background (avg={avg_r:.0f},{avg_g:.0f},{avg_b:.0f})",
                  warn_only=True)

    return r


def validate_sticker_package(package_dir: Path) -> ValidationResult:
    """Validate a complete WeChat sticker package directory."""
    result = ValidationResult()

    # Stickers
    stickers_dir = package_dir / "stickers"
    if not stickers_dir.exists():
        result.add(False, "stickers/ directory missing")
        return result

    sticker_files = sorted(stickers_dir.glob("*.png"))
    result.add(len(sticker_files) > 0, f"stickers: {len(sticker_files)} files found")

    for sf in sticker_files:
        sub = _check_image(sf, (240, 240), f"sticker/{sf.name}", must_have_alpha=True)
        result.checks.extend(sub.checks)
        if sub.level == "FAIL":
            result.level = "FAIL"
        elif sub.level == "WARN" and result.level == "PASS":
            result.level = "WARN"

    # Cover
    cover = package_dir / "cover.png"
    sub = _check_image(cover, (240, 240), "cover", must_be_white=True)
    result.checks.extend(sub.checks)
    if sub.level == "FAIL":
        result.level = "FAIL"

    # Icon
    icon = package_dir / "icon.png"
    sub = _check_image(icon, (50, 50), "icon", must_be_white=True)
    result.checks.extend(sub.checks)
    if sub.level == "FAIL":
        result.level = "FAIL"

    # Banner
    banner = package_dir / "banner.png"
    if banner.exists():
        sub = _check_image(banner, (750, 400), "banner")
        result.checks.extend(sub.checks)
        if sub.level == "FAIL":
            result.level = "FAIL"
    else:
        result.add(False, "banner.png missing", warn_only=True)

    # Preview
    preview = package_dir / "preview.png"
    result.add(preview.exists(), "preview.png exists")

    # Manifest
    manifest = package_dir / "manifest.json"
    result.add(manifest.exists(), "manifest.json exists")
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            result.add("preset_version" in data, "manifest has preset_version")
        except Exception:
            result.add(False, "manifest.json is valid JSON")

    return result


def validate_main_image(path: Path, expected_size: tuple = (240, 240)) -> ValidationResult:
    """Backward-compatible single-image validator."""
    return _check_image(path, expected_size, "main_image", must_have_alpha=True)
