"""BLOCKER-3: Multi-reference support."""

import tempfile

from cat_sticker_skill.models.plan import StickerPlanItem
from cat_sticker_skill.project.controller import ProjectController


def test_single_ref_passed(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        c = ProjectController.create("p1")
        c.build_plan([StickerPlanItem(id="s1", reference_type="single", reference_ids=["r1"])])
        c.approve_plan()
        r = c.execute_approved_plan({"r1": b"data1"}, dry_run=True)
        assert r["results"]["s1"]["status"] == "done"


def test_multi_refs_all_passed(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        c = ProjectController.create("p1")
        c.build_plan([StickerPlanItem(id="s1", reference_type="group",
                                      reference_ids=["r1", "r2", "r3"], caption="test")])
        c.approve_plan()
        r = c.execute_approved_plan({"r1": b"d1", "r2": b"d2", "r3": b"d3"}, dry_run=True)
        assert r["results"]["s1"]["status"] == "done"


def test_missing_ref_fails(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        c = ProjectController.create("p1")
        c.build_plan([StickerPlanItem(id="s1", reference_type="group",
                                      reference_ids=["r1", "r_missing"], caption="test")])
        c.approve_plan()
        r = c.execute_approved_plan({"r1": b"d1"}, dry_run=True)
        assert r["results"]["s1"]["status"] == "failed"
