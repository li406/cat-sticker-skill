"""Validate sticker images against WeChat static preset requirements."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PIL import Image


@dataclass
class ValidationResult:
    level: str  # "PASS", "WARN", "FAIL"
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


def validate_main_image(path: Path, expected_size: tuple = (240, 240)) -> ValidationResult:
    """Validate a sticker main image against WeChat requirements."""
    result = ValidationResult(level="PASS")

    if not path.exists():
        result.add(False, f"File not found: {path}")
        return result

    try:
        img = Image.open(path)
    except Exception as e:
        result.add(False, f"Cannot open image: {e}")
        return result

    result.add(img.format == "PNG", f"Format is PNG (got {img.format})")
    result.add(img.size == expected_size, f"Size {expected_size} (got {img.size})")

    # Check alpha channel
    if img.mode == "RGBA":
        alpha = img.split()[3]
        bbox = alpha.getbbox()
        result.add(bbox is not None, "Has transparent pixels (alpha channel)")
    else:
        result.add(False, f"Has alpha channel (got {img.mode})", warn_only=True)

    # File size (soft check)
    size_kb = path.stat().st_size / 1024
    result.add(size_kb < 500, f"File size <500KB (got {size_kb:.0f}KB)", warn_only=True)

    return result
