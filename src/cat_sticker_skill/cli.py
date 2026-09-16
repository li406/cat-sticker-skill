"""CLI entry point (thin wrapper around modules)."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cat-sticker", description="Cat sticker generation skill")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("privacy-check", help="Run privacy scanner on the repo")
    sub.add_parser("version", help="Show version")

    args = parser.parse_args(argv)

    if args.command == "version":
        from cat_sticker_skill import __version__
        print(f"cat-sticker-skill {__version__}")
        return 0

    if args.command == "privacy-check":
        from pathlib import Path
        from cat_sticker_skill.privacy import scan_repo

        repo_root = Path.cwd()
        report = scan_repo(repo_root)
        for f in report.findings:
            print(f"[{f.severity}] {f.category}: {f.message} ({f.file})")
        if report.passed:
            print("PRIVACY CHECK: PASS")
            return 0
        print("PRIVACY CHECK: FAIL (HIGH risk findings)")
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
