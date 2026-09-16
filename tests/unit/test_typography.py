"""Tests for typography composition."""

from pathlib import Path

from PIL import Image

from cat_sticker_skill.typography.meme_yellow import compose_text, PRESETS


def test_compose_creates_output(tmp_path):
    # Create a simple 200x200 white image
    input_path = tmp_path / "input.png"
    Image.new("RGBA", (200, 200), (200, 200, 200, 255)).save(input_path)

    output_path = tmp_path / "output.png"
    compose_text(input_path, output_path, "测试文字", preset="meme-yellow")

    assert output_path.exists()
    result = Image.open(output_path)
    assert result.size == (200, 200)
    assert result.mode == "RGBA"


def test_text_is_visible(tmp_path):
    input_path = tmp_path / "input.png"
    Image.new("RGBA", (200, 200), (255, 255, 255, 255)).save(input_path)

    output_path = tmp_path / "output.png"
    compose_text(input_path, output_path, "你好", preset="meme-yellow")

    result = Image.open(output_path)
    # Bottom area should have non-white pixels (the text)
    import numpy as np
    arr = np.array(result)
    bottom = arr[170:190, :, :]
    # Some pixels should be yellow-ish (text fill)
    yellow_pixels = ((bottom[:,:,0] > 200) & (bottom[:,:,1] > 150) & (bottom[:,:,2] < 100)).sum()
    assert yellow_pixels > 0, "Should have yellow text pixels at bottom"
