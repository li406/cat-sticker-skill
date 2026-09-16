"""Typography: deterministic text overlay on images.

Presets are defined in assets/typography-presets/.
The meme-yellow preset: bold yellow text with black outline at bottom center.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# Default font paths to try (cross-platform)
FONT_CANDIDATES_WINDOWS = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]

FONT_CANDIDATES_UNIX = [
    "/usr/share/fonts/opentype/noto/NotoSansSC-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansSC-Bold.ttf",
    "/System/Library/Fonts/PingFang.ttc",
]


def _find_font() -> str:
    """Find an available bold Chinese font."""
    import platform

    candidates = FONT_CANDIDATES_WINDOWS if platform.system() == "Windows" else FONT_CANDIDATES_UNIX
    for path in candidates:
        if Path(path).exists():
            return path
    # Fallback to PIL default (may not support CJK)
    return ""


def compose_meme_yellow(
    input_path: Path,
    output_path: Path,
    text: str,
    bottom_margin_ratio: float = 0.06,
    font_size_ratio: float = 0.11,
    long_text_scale: float = 0.75,
) -> Path:
    """Add meme-style yellow bold text with black outline at bottom center.

    This is the verified v2 preset from the owner's workflow.
    """
    img = Image.open(input_path).convert("RGBA")
    w, h = img.size
    draw = ImageDraw.Draw(img)

    font_path = _find_font()

    # Adaptive font size based on text length
    base_size = int(w * font_size_ratio)
    char_count = len(text)
    if char_count > 8:
        font_size = int(base_size * long_text_scale)
    elif char_count > 6:
        font_size = int(base_size * 0.85)
    else:
        font_size = base_size

    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=max(2, font_size // 10))
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Position: bottom center
    x = (w - tw) // 2 - bbox[0]
    y = h - th - int(h * bottom_margin_ratio)

    # Draw with yellow fill and black outline
    stroke_w = max(3, font_size // 10)
    draw.text(
        (x, y), text,
        font=font,
        fill=(255, 210, 0),
        stroke_width=stroke_w,
        stroke_fill=(0, 0, 0),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
