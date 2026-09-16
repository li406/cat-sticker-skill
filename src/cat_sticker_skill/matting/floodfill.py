"""Background matting: flood-fill based white background removal.

Uses only NumPy and Pillow (no SciPy). Preserves internal white areas
(e.g. white text) by only removing white regions connected to the image edge.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


def remove_solid_background(
    input_path: Path,
    output_path: Path,
    white_threshold: int = 235,
) -> Path:
    """Remove white background from an image, preserving internal white areas.

    Algorithm:
    1. Mark all pixels that are "white-ish" (RGB > threshold on all channels)
    2. Start BFS from all white pixels on the image border
    3. Only mark connected white regions as transparent
    4. Internal white regions (like text) stay opaque

    This is the verified legacy approach from the owner's v2 workflow.
    """
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    h, w = data.shape[:2]

    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    white_mask = (r > white_threshold) & (g > white_threshold) & (b > white_threshold)

    # BFS from edge
    visited = np.zeros((h, w), dtype=bool)
    queue: deque = deque()

    # Add all white pixels on the border
    for x in range(w):
        if white_mask[0, x] and not visited[0, x]:
            visited[0, x] = True
            queue.append((0, x))
        if white_mask[h - 1, x] and not visited[h - 1, x]:
            visited[h - 1, x] = True
            queue.append((h - 1, x))
    for y in range(h):
        if white_mask[y, 0] and not visited[y, 0]:
            visited[y, 0] = True
            queue.append((y, 0))
        if white_mask[y, w - 1] and not visited[y, w - 1]:
            visited[y, w - 1] = True
            queue.append((y, w - 1))

    # BFS
    while queue:
        cy, cx = queue.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and white_mask[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))

    # Set alpha to 0 for connected background
    data[visited, 3] = 0

    # Edge feathering: blur alpha channel to eliminate white halo
    from PIL import ImageFilter
    img_out = Image.fromarray(data, "RGBA")
    r_ch, g_ch, b_ch, a_ch = img_out.split()
    a_blurred = a_ch.filter(ImageFilter.GaussianBlur(radius=1.5))
    a_orig = np.array(a_ch)
    a_blur = np.array(a_blurred)
    new_alpha = np.minimum(a_orig, a_blur)
    rgb = np.array(img_out.convert("RGB"))
    near_white = (rgb[:,:,0] > 220) & (rgb[:,:,1] > 220) & (rgb[:,:,2] > 220)
    new_alpha[near_white & (new_alpha < 200)] = 0
    a_final = Image.fromarray(new_alpha)
    img_out = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_final))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img_out.save(output_path, "PNG")
    return output_path
