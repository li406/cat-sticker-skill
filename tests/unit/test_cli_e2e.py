"""CLI mock E2E: simulates the real Doubao Agent workflow through CLI calls.

Per FINAL-BLOCKER A/§18: does NOT call ProjectController.build_plan() directly.
Uses character import + plan import CLI entry points.
"""

import json
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

        # 2. synthetic reference image
        from PIL import Image
        import numpy as np
        ref_img = Image.new("RGB", (512, 512), (255, 255, 255))
        arr = np.array(ref_img)
        arr[100:400, 100:400] = [120, 100, 150]
        ref_path = Path(tmp) / "ref.png"
        Image.fromarray(arr).save(ref_path)

        # 3. ref add
        assert _run(["ref", "add", str(ref_path), "--id", "r1", "--project", "demo"], monkeypatch, home) == 0

        # 4. character import via CLI
        char_file = Path(tmp) / "char.json"
        char_file.write_text(json.dumps({
            "character_id": "cat_01",
            "species": "cat",
            "coat_color": "grey",
            "coat_pattern": "solid",
            "eye_color": "yellow",
            "hair_length": "short",
            "body_type": "chubby",
            "face_shape": "round",
            "distinctive_markings": ["white paw"],
            "accessories": ["pointy ears"],
            "preserve": ["face shape"],
            "avoid": ["scary"],
        }), encoding="utf-8")
        assert _run(["character", "import", str(char_file), "--project", "demo"], monkeypatch, home) == 0

        # 5. plan import via CLI (must NOT be auto-approved)
        plan_file = Path(tmp) / "plan.json"
        plan_file.write_text(json.dumps({
            "items": [{
                "id": "s001",
                "reference": {"type": "image", "ids": ["r1"]},
                "caption": "测试",
                "emotion": "开心",
                "pose": "sitting",
                "composition": "centered",
                "identity_priority": "high",
                "typography_preset": "meme-yellow",
                "character_id": "cat_01",
                "status": "planned",
            }]
        }), encoding="utf-8")
        assert _run(["plan", "import", str(plan_file), "--project", "demo"], monkeypatch, home) == 0

        # 6. plan show (should show approved=False)
        assert _run(["plan", "show", "--project", "demo"], monkeypatch, home) == 0

        # 7. generate should FAIL (not approved)
        assert _run(["generate", "--dry-run", "--project", "demo"], monkeypatch, home) == 1

        # 8. plan approve
        assert _run(["plan", "approve", "--project", "demo"], monkeypatch, home) == 0

        # 9. generate --dry-run
        assert _run(["generate", "--dry-run", "--project", "demo"], monkeypatch, home) == 0

        # 10. verify v001 active=1
        from cat_sticker_skill.project.controller import ProjectController
        c2 = ProjectController.open("demo")
        assert c2.manifest.stickers["s001"].active_version == 1

        # 11. regenerate
        assert _run(["regenerate", "s001", "--dry-run", "--project", "demo"], monkeypatch, home) == 0
        c3 = ProjectController.open("demo")
        assert c3.manifest.stickers["s001"].active_version == 2
        assert 1 in c3.manifest.stickers["s001"].versions
        assert 2 in c3.manifest.stickers["s001"].versions

        # 12. activate v001
        assert _run(["activate-version", "s001", "1", "--project", "demo"], monkeypatch, home) == 0

        # 13. text-adjust (caption persistence)
        assert _run(["text-adjust", "s001", "--caption", "新文案", "--project", "demo"], monkeypatch, home) == 0
        c4 = ProjectController.open("demo")
        assert c4.manifest.stickers["s001"].caption == "新文案"

        # 14. package (must use private out, not repo CWD)
        assert _run(["package", "--project", "demo", "--out", str(out)], monkeypatch, home) == 0

        # 15. verify ZIP exists
        zip_path = out / "demo-wechat-static.zip"
        assert zip_path.exists(), f"ZIP not found: {zip_path}"

        # 16. verify ZIP contents (no self-entry, has stickers/cover/banner/icon)
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert not any(n.endswith(".zip") for n in names), f"ZIP contains itself: {names}"
            assert any("stickers/" in n for n in names), f"No stickers in ZIP: {names}"
            assert "cover.png" in names
            assert "banner.png" in names
            assert "icon.png" in names

        # 17. validate via CLI
        assert _run(["validate", "--project", "demo", "--path", str(out / "demo-wechat-static")], monkeypatch, home) == 0

        # 18. resume — should say no pending
        assert _run(["resume", "--project", "demo"], monkeypatch, home) == 0
