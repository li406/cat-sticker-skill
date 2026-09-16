"""Typography: deterministic text overlay. Presets loaded from YAML (single source of truth)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


@dataclass
class TypographyOptions:
    """All typography parameters, adjustable by the Agent."""
    preset: str = "meme-yellow"
    font_size: int = 0  # 0 = auto
    font_scale: float = 1.0
    fill: Tuple[int, int, int] = (255, 210, 0)
    stroke: Tuple[int, int, int] = (0, 0, 0)
    stroke_width: int = 0  # 0 = auto (10% of font size)
    max_width_ratio: float = 0.90
    line_spacing: float = 0.15
    alignment: str = "center"  # center, left, right
    x_offset: int = 0
    y_offset: int = 0
    bottom_margin_ratio: float = 0.06
    max_lines: int = 2
    auto_wrap: bool = True


def _find_font() -> str:
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttf",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return ""


def load_presets(assets_dir: Optional[Path] = None) -> Dict[str, dict]:
    """Load typography presets from YAML files in assets/typography-presets/."""
    presets = {}
    if assets_dir is None:
        assets_dir = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "typography-presets"

    if assets_dir.exists():
        for yaml_file in sorted(assets_dir.glob("*.yaml")):
            text = yaml_file.read_text(encoding="utf-8")
            name = yaml_file.stem
            presets[name] = _parse_simple_yaml(text)

    # Built-in defaults as fallback
    presets.setdefault("meme-yellow", {
        "fill": [255, 210, 0], "stroke": [0, 0, 0], "stroke_ratio": 0.10,
        "bottom_margin_ratio": 0.06, "font_size_ratio": 0.11, "long_text_scale": 0.75,
    })
    return presets


def _parse_simple_yaml(text: str) -> dict:
    """Minimal YAML parser for flat key: value files with [list] support."""
    import ast
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        # Try list [x, y, z]
        if val.startswith("[") and val.endswith("]"):
            try:
                val = tuple(ast.literal_eval(val))
            except (SyntaxError, ValueError):
                pass
        else:
            try:
                val = float(val) if "." in val else int(val)
            except ValueError:
                pass
        result[key] = val
    return result


def compose_text(
    input_path: Path,
    output_path: Path,
    text: str,
    options: TypographyOptions | None = None,
    preset_name: str = "meme-yellow",
    bottom_margin_ratio: float = 0.06,
) -> Path:
    """Add text to image using TypographyOptions."""
    if options is None:
        options = TypographyOptions(preset=preset_name, bottom_margin_ratio=bottom_margin_ratio)

    presets = load_presets()
    p = presets.get(options.preset, presets["meme-yellow"])

    img = Image.open(input_path).convert("RGBA")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    font_path = _find_font()

    if not font_path:
        raise RuntimeError(
            "No CJK font found. Install Noto Sans SC or set font path. "
            "See README for font installation instructions."
        )

    # Determine font size
    char_count = len(text)
    base_size = options.font_size if options.font_size > 0 else int(w * float(p.get("font_size_ratio", 0.11)))
    base_size = int(base_size * options.font_scale)
    if char_count > 8:
        base_size = int(base_size * float(p.get("long_text_scale", 0.75)))
    elif char_count > 6:
        base_size = int(base_size * 0.85)

    try:
        font = ImageFont.truetype(font_path, base_size)
    except Exception:
        font = ImageFont.load_default()

    stroke_w = options.stroke_width if options.stroke_width > 0 else max(3, int(base_size * float(p.get("stroke_ratio", 0.10))))

    # Split into lines
    lines = text.split("\n") if "\n" in text else [text]
    if options.auto_wrap and len(lines) == 1 and len(text) > 6:
        # Simple wrap: split at midpoint if too long
        max_chars = int(w * options.max_width_ratio / (base_size * 0.6))
        if len(text) > max_chars and options.max_lines >= 2:
            midpoint = len(text) // 2
            # Find nearest comma or space
            for offset in range(min(5, midpoint)):
                if midpoint + offset < len(text) and text[midpoint + offset] in "，,、 ":
                    midpoint = midpoint + offset + 1
                    break
                if midpoint - offset > 0 and text[midpoint - offset] in "，,、 ":
                    midpoint = midpoint - offset + 1
                    break
            lines = [text[:midpoint], text[midpoint:]]
            lines = lines[:options.max_lines]

    # Measure
    line_widths = []
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_w)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    total_h = sum(line_heights) + (len(lines) - 1) + int(base_size * options.line_spacing)
    max_w = max(line_widths)

    # Clamp to max_width_ratio
    if max_w > w * options.max_width_ratio:
        scale = (w * options.max_width_ratio) / max_w
        new_size = int(base_size * scale)
        font = ImageFont.truetype(font_path, new_size)
        stroke_w = max(2, int(new_size * float(p.get("stroke_ratio", 0.10))))
        line_widths = []
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_w)
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])
        total_h = sum(line_heights) + (len(lines) - 1) + int(new_size * options.line_spacing)

    start_y = h - total_h - int(h * options.bottom_margin_ratio) + options.y_offset

    y = start_y
    for i, line in enumerate(lines):
        if options.alignment == "left":
            x = options.x_offset
        elif options.alignment == "right":
            x = w - line_widths[i] + options.x_offset
        else:
            x = (w - line_widths[i]) // 2 + options.x_offset
        draw.text(
            (x, y), line,
            font=font, fill=tuple(p.get("fill", [255, 210, 0])),
            stroke_width=stroke_w, stroke_fill=tuple(p.get("stroke", [0, 0, 0])),
        )
        y += line_heights[i] + int(base_size * options.line_spacing)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
