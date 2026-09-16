"""Tests for validator."""

from pathlib import Path

from PIL import Image

from cat_sticker_skill.validation.sticker import validate_main_image


def test_valid_passes(tmp_path):
    path = tmp_path / "sticker.png"
    # 240x240 RGBA with some transparent pixels
    import numpy as np
    arr = np.full((240, 240, 4), 100, dtype=np.uint8)
    arr[0:10, 0:10, 3] = 0  # transparent corner
    Image.fromarray(arr, "RGBA").save(path)
    result = validate_main_image(path)
    assert result.level in ("PASS", "WARN")


def test_wrong_size_warns(tmp_path):
    path = tmp_path / "sticker.png"
    Image.new("RGBA", (200, 200), (100, 100, 100, 255)).save(path)
    result = validate_main_image(path)
    assert result.level == "FAIL"


def test_missing_file_fails(tmp_path):
    result = validate_main_image(tmp_path / "nonexistent.png")
    assert result.level == "FAIL"
