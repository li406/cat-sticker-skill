"""Configuration loading and workspace path resolution.

Workspace is always outside the git repo by design.
API keys are read from environment variables only.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_workspace_root() -> Path:
    """Return the private workspace root, outside the git repo.

    Priority:
    1. CAT_STICKER_HOME environment variable
    2. Platform default:
       - Windows: %LOCALAPPDATA%\\CatStickerSkill\\workspace
       - Linux/macOS: ~/.local/share/cat-sticker-skill/workspace
    """
    override = os.environ.get("CAT_STICKER_HOME")
    if override:
        return Path(override).resolve()

    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            return Path(local) / "CatStickerSkill" / "workspace"
        return Path.home() / ".local" / "share" / "cat-sticker-skill" / "workspace"

    return Path.home() / ".local" / "share" / "cat-sticker-skill" / "workspace"


def get_api_key() -> str | None:
    """Read ARK_API_KEY from environment. Never log or echo it."""
    return os.environ.get("ARK_API_KEY")


def get_seedream_model() -> str:
    """Return configured Seedream model ID."""
    return os.environ.get("CAT_STICKER_SEEDREAM_MODEL", "doubao-seedream-4-5-251128")


def get_max_retries() -> int:
    return int(os.environ.get("CAT_STICKER_MAX_RETRIES", "2"))


def get_request_timeout() -> int:
    return int(os.environ.get("CAT_STICKER_REQUEST_TIMEOUT", "120"))


def get_unit_price_cny() -> float | None:
    raw = os.environ.get("CAT_STICKER_UNIT_PRICE_CNY")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def get_private_fixtures() -> Path | None:
    raw = os.environ.get("CAT_STICKER_PRIVATE_FIXTURES")
    return Path(raw) if raw else None


def ensure_workspace() -> Path:
    """Create workspace directories if they don't exist."""
    root = get_workspace_root()
    for sub in ("projects", "exports", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
