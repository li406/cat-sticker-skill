"""Typography: deterministic text overlay on images.

Supports multiple presets:
- meme-yellow: bold yellow + black outline (verified baseline)
- clean-white: white text with subtle shadow
- cute-soft: rounded soft pink/pastel
- bold-contrast: high-contrast bold black/white
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Font candidates
FONT_CANDIDATES_WINDOWS = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
]
FONT_CANDIDATES_UNIX = [
    "/usr/share/fonts/opentype/noto/NotoSansSC-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansSC-Bold.ttf",
]

# Preset definitions
PRESETS = {
    "meme-yellow": {
        "fill": (255, 210, 0),
        "stroke": (0, 0, 0),
        "stroke_ratio": 0.10,
        "bottom_margin_ratio": 0.06,
        "font_size_ratio": 0.11,
        "long_text_scale": 0.75,
    },
    "clean-white": {
        "fill": (255, 255, 255),
        "stroke": (80, 80, 80),
        "stroke_ratio": 0.06,
        "bottom_margin_ratio": 0.06,
        "font_size_ratio": 0.10,
        "long_text_scale": 0.80,
    },
    "cute-soft": {
        "fill": (255, 182, 193),
        "stroke": (255, 255, 255),
        "stroke_ratio": 0.08,
        "bottom_margin_ratio": 0.06,
        "font_size_ratio": 0.10,
        "long_text_scale": 0.80,
    },
    "bold-contrast": {
        "fill": (255, 255, 255),
        "stroke": (0, 0, 0),
        "stroke_ratio": 0.12,
        "bottom_margin_ratio": 0.06,
        "font_size_ratio": 0.12,
        "long_text_scale": 0.70,
    },
}


def _find_font() -> str:
    import platform
    candidates = FONT_CANDIDATES_WINDOWS if platform.system() == "Windows" else FONT_CANDIDATES_UNIX
    for path in candidates:
        if Path(path).exists():
            return path
    return ""


def compose_text(
    input_path: Path,
    output_path: Path,
    text: str,
    preset: str = "meme-yellow",
    bottom_margin_ratio: float = 0.06,
) -> Path:
    """Add text to image using named preset.

    Supports multi-line text (split by \\n).
    """
    p = PRESETS.get(preset, PRESETS["meme-yellow"])

    img = Image.open(input_path).convert("RGBA")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    font_path = _find_font()

    lines = text.split("\n") if "\n" in text else [text]
    char_count = max(len(l) for l in lines)

    base_size = int(w * p["font_size_ratio"])
    if char_count > 8:
        font_size = int(base_size * p["long_text_scale"])
    elif char_count > 6:
        font_size = int(base_size * 0.85)
    else:
        font_size = base_size

    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    stroke_w = max(3, int(font_size * p["stroke_ratio"]))

    # Measure total text block
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_w)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    total_h = sum(line_heights) + (len(lines) - 1) * int(font_size * 0.15)
    max_w = max(line_widths)

    # Position: bottom center
    start_y = h - total_h - int(h * bottom_margin_ratio)

    y = start_y
    for i, line in enumerate(lines):
        x = (w - line_widths[i]) // 2
        draw.text(
            (x, y), line,
            font=font, fill=p["fill"],
            stroke_width=stroke_w, stroke_fill=p["stroke"],
        )
        y += line_heights[i] + int(font_size * 0.15)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
