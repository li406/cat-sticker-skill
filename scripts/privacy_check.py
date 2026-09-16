#!/usr/bin/env python3
"""Privacy check entry point. Usage: python scripts/privacy_check.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from cat_sticker_skill.privacy import scan_repo

report = scan_repo(Path.cwd())
for f in report.findings:
    print(f"[{f.severity}] {f.category}: {f.message} ({f.file})")
if report.passed:
    print("PRIVACY CHECK: PASS")
    sys.exit(0)
print("PRIVACY CHECK: FAIL")
sys.exit(1)
