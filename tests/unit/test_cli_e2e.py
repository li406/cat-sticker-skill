"""CLI mock E2E: simulates the real Doubao Agent workflow through CLI calls."""

import os
import tempfile
import zipfile
from pathlib import Path

from cat_sticker_skill.cli import main as cli_main


def _run(args, monkeypatch, tmp_home):
    monkeypatch.setenv("CAT_STICKER_HOME", str(tmp_home))
    monkeypatch.delenv("ARK_API_KEY", raising=False)
    return cli_main(args)


def test_full_cli_e2e(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        out = Path(tmp) / "out"

        # 1. project create
        assert _run(["project", "create", "demo"], monkeypatch, home) == 0

        # 2. create a synthetic reference image
        from PIL import Image
        import numpy as np
        ref_img = Image.new("RGB", (512, 512), (255, 255, 255))
        arr = np.array(ref_img)
        arr[100:400, 100:400] = [120, 100, 150]
        ref_path = Path(tmp) / "ref.png"
        Image.fromarray(arr).save(ref_path)

        # 3. ref add
        assert _run(["ref", "add", str(ref_path), "--id", "r1", "--project", "demo"], monkeypatch, home) == 0

        # 4. build plan (via controller directly, since CLI doesn't have plan create yet)
        from cat_sticker_skill.project.controller import ProjectController
        from cat_sticker_skill.models.plan import StickerPlanItem
        c = ProjectController.open("demo")
        c.build_plan([StickerPlanItem(
            id="s001", reference_type="single", reference_ids=["r1"],
            caption="测试", emotion="开心",
        )])

        # 5. plan show
        assert _run(["plan", "show", "--project", "demo"], monkeypatch, home) == 0

        # 6. plan approve
        assert _run(["plan", "approve", "--project", "demo"], monkeypatch, home) == 0

        # 7. generate --dry-run
        assert _run(["generate", "--dry-run", "--project", "demo"], monkeypatch, home) == 0

        # 8. verify v001 active=1
        c2 = ProjectController.open("demo")
        assert c2.manifest.stickers["s001"].active_version == 1

        # 9. regenerate
        assert _run(["regenerate", "s001", "--dry-run", "--project", "demo"], monkeypatch, home) == 0

        # 10. verify v002 exists, v001 still there
        c3 = ProjectController.open("demo")
        assert c3.manifest.stickers["s001"].active_version == 2
        assert 1 in c3.manifest.stickers["s001"].versions
        assert 2 in c3.manifest.stickers["s001"].versions

        # 11. activate v001
        assert _run(["activate-version", "s001", "1", "--project", "demo"], monkeypatch, home) == 0

        # 12. text-adjust
        assert _run(["text-adjust", "s001", "--y-offset", "-10", "--project", "demo"], monkeypatch, home) == 0

        # 13. package
        assert _run(["package", "--project", "demo", "--out", str(out)], monkeypatch, home) == 0

        # 14. verify ZIP exists
        zip_path = out / "demo-wechat-static.zip"
        assert zip_path.exists(), f"ZIP not found: {zip_path}"

        # 15. verify ZIP contents
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert any("stickers/" in n for n in names), f"No stickers in ZIP: {names}"

        # 16. resume — should say no pending
        assert _run(["resume", "--project", "demo"], monkeypatch, home) == 0
