"""Tests for configuration and workspace path resolution."""

import os
from pathlib import Path

from cat_sticker_skill import config


def test_workspace_default_windows(monkeypatch):
    monkeypatch.delenv("CAT_STICKER_HOME", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\testuser\\AppData\\Local")
    if os.name == "nt":
        ws = config.get_workspace_root()
        assert "CatStickerSkill" in str(ws)
        assert "workspace" in str(ws)


def test_workspace_override(monkeypatch, tmp_path):
    monkeypatch.setenv("CAT_STICKER_HOME", str(tmp_path / "mywork"))
    ws = config.get_workspace_root()
    assert ws == (tmp_path / "mywork").resolve()


def test_api_key_not_present_in_test_env(monkeypatch):
    monkeypatch.delenv("ARK_API_KEY", raising=False)
    assert config.get_api_key() is None


def test_default_model_id():
    assert "seedream" in config.get_seedream_model().lower()


def test_ensure_workspace_creates_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("CAT_STICKER_HOME", str(tmp_path / "ws"))
    root = config.ensure_workspace()
    assert root.exists()
    assert (root / "projects").exists()
    assert (root / "exports").exists()
