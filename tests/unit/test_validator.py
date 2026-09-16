"""Tests for validator."""

from pathlib import Path

from PIL import Image

from cat_sticker_skill.validation.sticker import validate_main_image


def test_valid_passes(tmp_path):
    path = tmp_path / "sticker.png"
    # 240x240 RGBA with some transparency
    img = Image.new("RGBA", (240, 240), (100, 100, 100, 255))
    img.save(path)
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
