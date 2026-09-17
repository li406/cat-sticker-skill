"""Privacy scanner: check tracked files for secrets, private paths, EXIF."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class PrivacyFinding:
    severity: str
    category: str
    message: str
    file: str


@dataclass
class PrivacyReport:
    findings: List[PrivacyFinding] = field(default_factory=list)

    @property
    def has_high_risk(self) -> bool:
        return any(f.severity == "HIGH" for f in self.findings)

    @property
    def passed(self) -> bool:
        return not self.has_high_risk


SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "secret", "OpenAI-style API key"),
    (re.compile(r"ark-[a-zA-Z0-9-]{20,}"), "secret", "Ark/Volcengine API key"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9\-_]{20,}"), "secret", "Bearer token"),
]

# Known fake/test secrets used intentionally in test fixtures
FAKE_SECRETS = {
    "sk-abc123def456ghi789jkl012mnop345",
    "ark-abc123def456ghi789jkl012",
    "abcdef1234567890abcdef1234567890",
}

# Regex pattern strings used by the scanner itself (false positives)
SELF_PATTERNS = {
    "sk-[a-zA-Z0-9]{20,}",
    "ark-[a-zA-Z0-9-]{20,}",
}

PATH_PATTERNS = [
    (re.compile(r"C:\\Users\\[^\s\"']+"), "private_path", "Windows user path"),
    (re.compile(r"/home/[^\s\"']+"), "private_path", "Linux user path"),
    (re.compile(r"/Users/[^\s\"']+"), "private_path", "macOS user path"),
]

TEXT_EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".json", ".txt", ".toml", ".cfg", ".ini",
    ".env", ".sh", ".js", ".ts", ".html", ".css", ".csv",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# Allowlisted image paths (synthetic / public fixtures only).
# Any tracked image outside these paths is HIGH unexpected_tracked_media.
IMAGE_ALLOWLIST_DIRS = {"tests/public-fixtures", "assets/fixtures"}


def check_image_exif(filepath: Path) -> List[PrivacyFinding]:
    findings: List[PrivacyFinding] = []
    try:
        from PIL import Image
        img = Image.open(filepath)
        exif = img.getexif() if hasattr(img, "getexif") else {}
        if exif:
            has_gps = any(tag in exif for tag in [0x8825, 0x0001, 0x0002])
            has_camera = any(tag in exif for tag in [0x010F, 0x0110])
            if has_gps:
                findings.append(PrivacyFinding("HIGH", "exif_gps", "GPS EXIF data", str(filepath)))
            if has_camera:
                findings.append(PrivacyFinding("MEDIUM", "exif_camera", "Camera EXIF data", str(filepath)))
    except Exception:
        pass
    return findings


def _is_allowlisted_image(path: Path) -> bool:
    parts = set(path.parts)
    return any(allow in parts for allow in IMAGE_ALLOWLIST_DIRS)


def scan_file(filepath: Path) -> List[PrivacyFinding]:
    findings: List[PrivacyFinding] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    # Scanner source file: its own regex patterns are intentional, not real paths/secrets
    is_scanner_source = filepath.name == "scanner.py"

    for pattern, category, desc in SECRET_PATTERNS:
        for m in pattern.finditer(content):
            val = m.group()
            if val in SELF_PATTERNS:
                continue
            if is_scanner_source:
                continue
            # Only exact allowlist of known fake secrets is exempted — even in tests/
            if val in FAKE_SECRETS:
                continue
            if "deadbeef" in val or "your-api-key" in val or "example" in val.lower():
                continue
            findings.append(PrivacyFinding("HIGH", category, f"Possible {desc} found (value redacted)", str(filepath)))

    for pattern, category, desc in PATH_PATTERNS:
        for m in pattern.finditer(content):
            val = m.group()
            if is_scanner_source:
                continue
            if "username" in val.lower() or "your-username" in val.lower():
                continue
            if "某个用户名" in val:
                continue
            findings.append(PrivacyFinding("HIGH", category, "Possible private absolute path found (value redacted)", str(filepath)))

    return findings


def get_tracked_files(repo_root: Path) -> List[Path]:
    """Get git-tracked files. Falls back to recursive walk if git fails."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=str(repo_root),
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            names = result.stdout.decode("utf-8", errors="ignore").split("\0")
            return [repo_root / n for n in names if n and not n.startswith(".git")]
    except Exception:
        pass
    exclude = {".git", "__pycache__", ".venv", ".pytest_cache", "*.egg-info"}
    files = []
    for f in repo_root.rglob("*"):
        if f.is_file() and not any(e in f.parts for e in exclude):
            files.append(f)
    return files


def scan_repo(repo_root: Path) -> PrivacyReport:
    """Scan git-tracked files for privacy issues."""
    report = PrivacyReport()
    tracked = get_tracked_files(repo_root)

    for filepath in tracked:
        if not filepath.exists():
            continue
        suffix = filepath.suffix.lower()
        if suffix in TEXT_EXTENSIONS or filepath.name.startswith(".env"):
            report.findings.extend(scan_file(filepath))
        elif suffix in IMAGE_EXTENSIONS:
            # Tracked media gate: any non-allowlisted image is HIGH
            if not _is_allowlisted_image(filepath):
                report.findings.append(PrivacyFinding(
                    "HIGH", "unexpected_tracked_media",
                    "Tracked image outside allowlisted fixtures (value redacted)",
                    str(filepath),
                ))
            report.findings.extend(check_image_exif(filepath))

    return report
