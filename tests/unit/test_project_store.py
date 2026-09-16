"""Tests for project persistence."""

import os

from cat_sticker_skill.models.plan import StickerPlanItem
from cat_sticker_skill.project import store
from cat_sticker_skill.project.controller import ProjectController


def test_create_and_load_project(tmp_path, monkeypatch):
    monkeypatch.setenv("CAT_STICKER_HOME", str(tmp_path))
    store.create_project("test_proj", "My Cats")
    manifest = store.load_project("test_proj")
    assert manifest.project_id == "test_proj"


def test_plan_save_load(tmp_path, monkeypatch):
    monkeypatch.setenv("CAT_STICKER_HOME", str(tmp_path))
    store.create_project("test_plan")
    from cat_sticker_skill.models.plan import GenerationPlan
    plan = GenerationPlan(
        project_id="test_plan",
        items=[StickerPlanItem(id="s1", reference_type="single", caption="hi")],
    )
    store.save_plan(plan)
    loaded = store.load_plan("test_plan")
    assert len(loaded.items) == 1
    assert loaded.items[0].caption == "hi"


def test_controller_resume(tmp_path, monkeypatch):
    monkeypatch.setenv("CAT_STICKER_HOME", str(tmp_path))
    c = ProjectController.create("test_ctrl")
    pending = c.resume_pending()
    assert pending == []  # empty project


def test_atomic_write(tmp_path, monkeypatch):
    monkeypatch.setenv("CAT_STICKER_HOME", str(tmp_path))
    store.create_project("atomic_test")
    manifest = store.load_project("atomic_test")
    manifest.total_paid_generations = 5
    store.save_project(manifest)
    reloaded = store.load_project("atomic_test")
    assert reloaded.total_paid_generations == 5
