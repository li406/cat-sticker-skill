"""Tests for privacy scanner with tracked files."""

from pathlib import Path

from cat_sticker_skill.privacy.scanner import scan_file, scan_repo


def test_dotenv_fake_key_detected(tmp_path):
    (tmp_path / ".env").write_text("ARK_API_KEY=ark-abc123def456ghi789jkl012\n")
    report = scan_repo(tmp_path)
    assert any("secret" in f.category for f in report.findings)


def test_logs_fake_bearer_detected(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "debug.txt").write_text("Authorization: Bearer abcdef1234567890abcdef1234567890\n")
    report = scan_repo(tmp_path)
    assert any("secret" in f.category for f in report.findings)


def test_clean_repo_passes(tmp_path):
    (tmp_path / "README.md").write_text("# Clean project\nNo secrets.\n")
    report = scan_repo(tmp_path)
    assert report.passed


def test_sk_pickup(tmp_path):
    (tmp_path / "config.py").write_text('KEY = "sk-abc123def456ghi789jkl012mnop345"\n')
    report = scan_repo(tmp_path)
    assert any("secret" in f.category for f in report.findings)
