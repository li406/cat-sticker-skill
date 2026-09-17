"""Tests for export edge cases and validation."""

from pathlib import Path

import numpy as np
from PIL import Image

from cat_sticker_skill.export.wechat_package import export_wechat_package, _crop_pad, zip_package


def _make_sticker_dir(base: Path, name: str, caption: str = "test"):
    sd = base / name
    v = sd / "v001"
    v.mkdir(parents=True)
    # generated.png (white bg with colored circle)
    arr = np.full((512, 512, 3), 255, dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    mask = (x - 256) ** 2 + (y - 256) ** 2 < 200 ** 2
    arr[mask] = [100, 100, 150]
    Image.fromarray(arr).save(v / "generated.png")
    # cutout.png (RGBA)
    cutout = np.full((512, 512, 4), 100, dtype=np.uint8)
    cutout[~mask] = [0, 0, 0, 0]
    Image.fromarray(cutout, "RGBA").save(v / "cutout.png")
    Image.fromarray(cutout, "RGBA").save(v / "composed.png")
    Image.fromarray(cutout, "RGBA").resize((240, 240), Image.LANCZOS).save(v / "final_240.png")


def test_export_creates_package(tmp_path):
    sd = tmp_path / "stickers_src"
    sd.mkdir()
    _make_sticker_dir(sd, "sticker_001")
    banner_src = sd / "sticker_001" / "v001" / "generated.png"

    out = tmp_path / "pkg"
    export_wechat_package(sd, out, banner_source=banner_src, cover_source=banner_src)
    assert (out / "stickers" / "001.png").exists()
    assert (out / "cover.png").exists()
    assert (out / "icon.png").exists()
    assert (out / "banner.png").exists()
    assert (out / "preview.png").exists()
    assert (out / "manifest.json").exists()
    assert (out / "validation-report.json").exists()


def test_export_zero_stickers_raises(tmp_path):
    sd = tmp_path / "empty"
    sd.mkdir()
    out = tmp_path / "pkg"
    try:
        export_wechat_package(sd, out)
        assert False, "Should have raised"
    except ValueError:
        pass


def test_crop_pad_no_distortion():
    img = Image.new("RGB", (800, 400), (255, 0, 0))
    result = _crop_pad(img, 750, 400)
    assert result.size == (750, 400)


def test_zip_package(tmp_path):
    sd = tmp_path / "stickers_src"
    sd.mkdir()
    _make_sticker_dir(sd, "sticker_001")
    banner_src = sd / "sticker_001" / "v001" / "generated.png"
    out = tmp_path / "pkg"
    export_wechat_package(sd, out, banner_source=banner_src, cover_source=banner_src)
    zp = tmp_path / "pkg" / "out.zip"
    zip_package(out, zp)
    assert zp.exists()
    assert zp.stat().st_size > 0
    import zipfile
    with zipfile.ZipFile(zp) as zf:
        names = zf.namelist()
        assert not any(n.endswith(".zip") for n in names), f"ZIP contains itself: {names}"
