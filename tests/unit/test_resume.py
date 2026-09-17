"""BLOCKER-6: Resume idempotency."""

import tempfile

from cat_sticker_skill.models.plan import StickerPlanItem
from cat_sticker_skill.project.controller import ProjectController


def test_resume_skips_completed(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        c = ProjectController.create("p1")
        c.build_plan([
            StickerPlanItem(id="s1", caption="a", reference_type="single", reference_ids=["r"]),
            StickerPlanItem(id="s2", caption="b", reference_type="single", reference_ids=["r"]),
        ])
        c.approve_plan()
        c.execute_approved_plan({"r": b""}, dry_run=True)
        v1_before = c.manifest.stickers["s1"].active_version
        r = c.execute_approved_plan({"r": b""}, dry_run=True)
        assert r["results"]["s1"]["status"] == "skipped"
        assert c.manifest.stickers["s1"].active_version == v1_before


def test_resume_pending_lists_failed(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        c = ProjectController.create("p1")
        c.build_plan([
            StickerPlanItem(id="s1", caption="a", reference_type="single", reference_ids=["r"]),
        ])
        pending = c.resume_pending()
        assert "s1" in pending
