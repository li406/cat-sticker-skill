"""BLOCKER-1: Version number correctness — never 0, no overwrite."""

import tempfile
from pathlib import Path

from cat_sticker_skill.models.plan import StickerPlanItem
from cat_sticker_skill.project.controller import ProjectController
from cat_sticker_skill.project import store


def _item(iid: str = "s001") -> StickerPlanItem:
    return StickerPlanItem(id=iid, reference_type="single", reference_ids=["r1"], caption="test")


def _setup(monkeypatch, td):
    monkeypatch.setenv("CAT_STICKER_HOME", str(td))


def test_version_starts_at_1(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        _setup(monkeypatch, td)
        c = ProjectController.create("p1")
        c.build_plan([_item()])
        c.approve_plan()
        c.execute_approved_plan({"r1": b""}, dry_run=True)
        s = c.manifest.stickers["s001"]
        assert s.active_version == 1
        assert 1 in s.versions


def test_second_version_is_v002(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        _setup(monkeypatch, td)
        c = ProjectController.create("p1")
        c.build_plan([_item()])
        c.approve_plan()
        c.execute_approved_plan({"r1": b""}, dry_run=True)
        c.regenerate("s001", {"r1": b""}, dry_run=True)
        s = c.manifest.stickers["s001"]
        assert s.active_version == 2
        assert 1 in s.versions
        assert 2 in s.versions


def test_activate_version_rollback(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        _setup(monkeypatch, td)
        c = ProjectController.create("p1")
        c.build_plan([_item()])
        c.approve_plan()
        c.execute_approved_plan({"r1": b""}, dry_run=True)
        c.regenerate("s001", {"r1": b""}, dry_run=True)
        ok = c.activate_version("s001", 1)
        assert ok
        assert c.manifest.stickers["s001"].active_version == 1


def test_regenerate_only_target_item(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        _setup(monkeypatch, td)
        c = ProjectController.create("p1")
        c.build_plan([_item("s001"), _item("s002")])
        c.approve_plan()
        c.execute_approved_plan({"r1": b""}, dry_run=True)
        c.regenerate("s002", {"r1": b""}, dry_run=True)
        assert c.manifest.stickers["s001"].active_version == 1
        assert c.manifest.stickers["s002"].active_version == 2
