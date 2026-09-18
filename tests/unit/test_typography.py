"""Tests for typography composition."""

from pathlib import Path

from PIL import Image

from cat_sticker_skill.typography.meme_yellow import compose_text, TypographyOptions


def test_compose_creates_output(tmp_path):
    # Create a simple 200x200 white image
    input_path = tmp_path / "input.png"
    Image.new("RGBA", (200, 200), (200, 200, 200, 255)).save(input_path)

    output_path = tmp_path / "output.png"
    compose_text(input_path, output_path, "娴嬭瘯鏂囧瓧", preset="meme-yellow")

    assert output_path.exists()
    result = Image.open(output_path)
    assert result.size == (200, 200)
    assert result.mode == "RGBA"


def test_text_is_visible(tmp_path):
    input_path = tmp_path / "input.png"
    Image.new("RGBA", (200, 200), (255, 255, 255, 255)).save(input_path)

    output_path = tmp_path / "output.png"
    compose_text(input_path, output_path, "浣犲ソ", preset="meme-yellow")

    result = Image.open(output_path)
    # Bottom area should have non-white pixels (the text)
    import numpy as np
    arr = np.array(result)
    bottom = arr[170:190, :, :]
    # Some pixels should be yellow-ish (text fill)
    yellow_pixels = ((bottom[:,:,0] > 200) & (bottom[:,:,1] > 150) & (bottom[:,:,2] < 100)).sum()
    assert yellow_pixels > 0, "Should have yellow text pixels at bottom"



def test_vertical_position_top(tmp_path):
    """Text should appear in the top band when vertical_position=top."""
    import numpy as np
    input_path = tmp_path / "input.png"
    Image.new("RGBA", (200, 200), (255, 255, 255, 255)).save(input_path)

    out_bottom = tmp_path / "bottom.png"
    out_top = tmp_path / "top.png"
    compose_text(input_path, out_bottom, "test", preset="meme-yellow",
                 options=TypographyOptions(vertical_position="bottom"))
    compose_text(input_path, out_top, "test", preset="meme-yellow",
                 options=TypographyOptions(vertical_position="top"))

    arr_b = np.array(Image.open(out_bottom))
    arr_t = np.array(Image.open(out_top))
    # Non-white text pixels
    def nonwhite(a):
        return (a[:,:,:3].min(axis=2) < 240).sum()
    # bottom variant: text should be near bottom
    bottom_y_nonwhite_b = nonwhite(arr_b[160:195])
    top_y_nonwhite_b = nonwhite(arr_b[5:40])
    assert bottom_y_nonwhite_b > 0 and top_y_nonwhite_b == 0

    # top variant: text should be near top, not bottom
    bottom_y_nonwhite_t = nonwhite(arr_t[160:195])
    top_y_nonwhite_t = nonwhite(arr_t[5:40])
    assert top_y_nonwhite_t > 0 and bottom_y_nonwhite_t == 0
