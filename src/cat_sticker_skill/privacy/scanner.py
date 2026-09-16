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


def scan_file(filepath: Path) -> List[PrivacyFinding]:
    findings: List[PrivacyFinding] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    for pattern, category, desc in SECRET_PATTERNS:
        for m in pattern.finditer(content):
            val = m.group()
            # Skip known test fixtures
            if "deadbeef" in val or "your-api-key" in val or "example" in val.lower():
                continue
            findings.append(PrivacyFinding("HIGH", category, f"{desc}: {val[:15]}...", str(filepath)))

    for pattern, category, desc in PATH_PATTERNS:
        for m in pattern.finditer(content):
            val = m.group()
            # Skip documentation/example paths
            if "某个用户名" in val or "username" in val.lower():
                continue
            findings.append(PrivacyFinding("MEDIUM", category, f"{desc}: {val}", str(filepath)))

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
    # Fallback: walk, excluding common dirs
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
        if suffix in TEXT_EXTENSIONS or filepath.name == ".env":
            report.findings.extend(scan_file(filepath))
        elif suffix in IMAGE_EXTENSIONS:
            report.findings.extend(check_image_exif(filepath))
        # Also check .env specifically
        if filepath.name.startswith(".env") and filepath.suffix == "":
            report.findings.extend(scan_file(filepath))

    return report
