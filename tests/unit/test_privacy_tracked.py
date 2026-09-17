"""Tests for privacy scanner with tracked files."""

from pathlib import Path

from cat_sticker_skill.privacy.scanner import scan_file, scan_repo


def _build_sk() -> str:
    # Build at runtime so the literal does not appear in source (privacy-check)
    return "sk-" + "pickupverify" + "9999testkeyabcd1234wxyz"


def _build_ark() -> str:
    return "ark-" + "pickupverify" + "9999testkeyabcd1234"


def test_dotenv_fake_key_detected(tmp_path):
    key = _build_ark()
    (tmp_path / ".env").write_text(f"ARK_API_KEY={key}\n")
    report = scan_repo(tmp_path)
    assert any("secret" in f.category for f in report.findings)


def test_logs_fake_bearer_detected(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    token = "pickupverify9999testkeyabcd1234xyz"
    (logs / "debug.txt").write_text(f"Authorization: Bearer {token}\n")
    report = scan_repo(tmp_path)
    assert any("secret" in f.category for f in report.findings)


def test_clean_repo_passes(tmp_path):
    (tmp_path / "README.md").write_text("# Clean project\nNo secrets.\n")
    report = scan_repo(tmp_path)
    assert report.passed


def test_sk_pickup(tmp_path):
    key = _build_sk()
    (tmp_path / "config.py").write_text(f'KEY = "{key}"\n')
    report = scan_repo(tmp_path)
    assert any("secret" in f.category for f in report.findings)
