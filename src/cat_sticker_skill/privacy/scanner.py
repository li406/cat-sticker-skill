"""Privacy scanner: detect secrets, private paths, and EXIF leaks before release."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class PrivacyFinding:
    severity: str  # "HIGH", "MEDIUM", "LOW"
    category: str
    message: str
    file: str = ""


@dataclass
class PrivacyReport:
    findings: List[PrivacyFinding] = field(default_factory=list)

    @property
    def has_high_risk(self) -> bool:
        return any(f.severity == "HIGH" for f in self.findings)

    @property
    def passed(self) -> bool:
        return not self.has_high_risk


# Patterns that look like API keys / secrets
SECRET_PATTERNS = [
    (re.compile(r"ark-[a-f0-9-]{20,}", re.IGNORECASE), "Volcengine/Ark API key pattern"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "OpenAI-style API key pattern"),
    (re.compile(r"AKIA[A-Z0-9]{16}"), "AWS access key pattern"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private key block"),
]

# Private path indicators
PRIVATE_PATH_PATTERNS = [
    re.compile(r"C:\\Users\\[^\\]+", re.IGNORECASE),
    re.compile(r"/home/[^/]+"),
    re.compile(r"/Users/[^/]+"),
]

SCAN_EXTENSIONS = {".py", ".md", ".yaml", ".yml", ".json", ".txt", ".toml", ".cfg", ".ini"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def check_image_exif(filepath: Path) -> List[PrivacyFinding]:
    """Check image files for EXIF metadata leaks."""
    findings: List[PrivacyFinding] = []
    try:
        from PIL import Image
        img = Image.open(filepath)
        exif = img.getexif() if hasattr(img, "getexif") else {}
        if exif:
            has_gps = any(tag in exif for tag in [0x8825, 0x0001, 0x0002])  # GPS tags
            has_camera = any(tag in exif for tag in [0x010F, 0x0110])  # Make/Model
            if has_gps:
                findings.append(PrivacyFinding(
                    severity="HIGH",
                    category="exif_gps",
                    message="Image contains GPS EXIF data",
                    file=str(filepath),
                ))
            if has_camera:
                findings.append(PrivacyFinding(
                    severity="MEDIUM",
                    category="exif_camera",
                    message="Image contains camera model EXIF data",
                    file=str(filepath),
                ))
    except Exception:
        pass
    return findings


def scan_file(filepath: Path) -> List[PrivacyFinding]:
    """Scan a single text file for secrets and private paths."""
    findings: List[PrivacyFinding] = []
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return findings

    for pattern, desc in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(PrivacyFinding(
                severity="HIGH",
                category="secret",
                message=f"Possible secret detected: {desc}",
                file=str(filepath),
            ))

    for pattern in PRIVATE_PATH_PATTERNS:
        for match in pattern.finditer(text):
            # Skip if it's clearly an example/placeholder
            matched = match.group()
            if any(skip in matched.lower() for skip in ("example", "placeholder", "your-", "xxx")):
                continue
            findings.append(PrivacyFinding(
                severity="MEDIUM",
                category="private_path",
                message=f"Private user path in source: {matched}",
                file=str(filepath),
            ))

    return findings


def scan_repo(repo_root: Path) -> PrivacyReport:
    """Scan all tracked text files in the repo for privacy issues."""
    report = PrivacyReport()
    exclude_dirs = {".git", "__pycache__", ".venv", "node_modules", "workspace", "exports", "logs"}

    for filepath in repo_root.rglob("*"):
        if not filepath.is_file():
            continue
        if any(excluded in filepath.parts for excluded in exclude_dirs):
            continue
        if filepath.suffix.lower() not in SCAN_EXTENSIONS:
            # Also check images for EXIF
            if filepath.suffix.lower() in IMAGE_EXTENSIONS:
                report.findings.extend(check_image_exif(filepath))
            continue
        report.findings.extend(scan_file(filepath))

    return report
