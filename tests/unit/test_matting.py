"""Tests for flood-fill background removal."""

from pathlib import Path

import numpy as np
from PIL import Image

from cat_sticker_skill.matting.floodfill import remove_solid_background


def test_white_bg_removed(tmp_path):
    # Create a 100x100 image: white bg with a black circle in center
    img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    arr = np.array(img)
    # Draw a black circle
    y, x = np.ogrid[:100, :100]
    mask = (x - 50) ** 2 + (y - 50) ** 2 < 400
    arr[mask] = [0, 0, 0, 255]
    input_path = tmp_path / "input.png"
    Image.fromarray(arr, "RGBA").save(input_path)

    output_path = tmp_path / "output.png"
    remove_solid_background(input_path, output_path)

    result = Image.open(output_path)
    data = np.array(result)
    # Corner should be transparent
    assert data[0, 0, 3] == 0, "Corner should be transparent"
    # Center black circle should remain
    assert data[50, 50, 3] == 255, "Center should be opaque"


def test_internal_white_preserved(tmp_path):
    # White bg, black shape with a white dot inside
    img = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
    arr = np.array(img)
    # Black square
    arr[20:80, 20:80] = [0, 0, 0, 255]
    # White dot inside the black square (should be preserved)
    arr[45:55, 45:55] = [255, 255, 255, 255]

    input_path = tmp_path / "input.png"
    Image.fromarray(arr, "RGBA").save(input_path)

    output_path = tmp_path / "output.png"
    remove_solid_background(input_path, output_path)

    result = np.array(Image.open(output_path))
    # Internal white dot should remain opaque
    assert result[50, 50, 3] == 255, "Internal white should be preserved"
    # Corner should be transparent
    assert result[0, 0, 3] == 0, "Corner should be transparent"
