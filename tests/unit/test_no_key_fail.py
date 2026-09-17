"""BLOCKER-11: No API key = hard fail on real generate. Privacy: path traversal."""

import tempfile

from cat_sticker_skill.models.plan import StickerPlanItem
from cat_sticker_skill.project.controller import ProjectController, validate_id


def test_no_api_key_real_generate_fails(monkeypatch):
    monkeypatch.delenv("ARK_API_KEY", raising=False)
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        c = ProjectController.create("p1")
        c.build_plan([StickerPlanItem(id="s1", caption="a", reference_type="single", reference_ids=["r"])])
        c.approve_plan()
        r = c.execute_approved_plan({"r": b""}, dry_run=False)
        assert r["success"] is False
        assert "ARK_API_KEY" in r.get("error", "")


def test_dry_run_works_without_key(monkeypatch):
    monkeypatch.delenv("ARK_API_KEY", raising=False)
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("CAT_STICKER_HOME", td)
        c = ProjectController.create("p1")
        c.build_plan([StickerPlanItem(id="s1", caption="a", reference_type="single", reference_ids=["r"])])
        c.approve_plan()
        r = c.execute_approved_plan({"r": b""}, dry_run=True)
        assert r["success"] is True
        assert r["provider_mode"] == "mock"


def test_path_traversal_rejected():
    import pytest
    with pytest.raises(ValueError):
        validate_id("../etc", "project_id")
    with pytest.raises(ValueError):
        validate_id("..\\windows", "project_id")
    with pytest.raises(ValueError):
        validate_id("/absolute/path", "project_id")
    assert validate_id("my-project_01", "project_id") == "my-project_01"
