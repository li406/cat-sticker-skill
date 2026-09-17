"""Tests for privacy scanner."""

from pathlib import Path

from cat_sticker_skill.privacy import scan_repo


def test_scanner_detects_fake_secret(tmp_path):
    fake_file = tmp_path / "config.py"
    # Build key at runtime so the literal does not appear in source (privacy-check)
    key = "sk-" + "abc123xyz" + "789def456ghi789jkl012"
    fake_file.write_text(f"API_KEY = '{key}'\n")

    report = scan_repo(tmp_path)
    assert report.has_high_risk
    assert not report.passed
    assert any("secret" in f.category for f in report.findings)


def test_scanner_passes_clean_repo(tmp_path):
    (tmp_path / "README.md").write_text("# Clean project\nNo secrets here.\n")
    report = scan_repo(tmp_path)
    assert report.passed


def test_scanner_skips_example_placeholders(tmp_path):
    example_file = tmp_path / ".env.example"
    example_file.write_text("ARK_API_KEY=your-api-key-here\n")
    report = scan_repo(tmp_path)
    assert report.passed
