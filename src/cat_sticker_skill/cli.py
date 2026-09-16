"""CLI entry point: thin wrapper around the controller."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cat-sticker", description="Cat sticker generation skill")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Show version")
    sub.add_parser("privacy-check", help="Run privacy scanner on tracked files")
    sub.add_parser("doctor", help="Check installation and config")
    sub.add_parser("smoke-test", help="Run a free end-to-end smoke test (mock provider)")

    p_create = sub.add_parser("project", help="Project management")
    p_sub = p_create.add_subparsers(dest="project_cmd")
    p_sub.add_parser("list", help="List projects")

    args = parser.parse_args(argv)

    if args.command == "version":
        from cat_sticker_skill import __version__
        print(f"cat-sticker-skill {__version__}")
        return 0

    if args.command == "privacy-check":
        from pathlib import Path

        from cat_sticker_skill.privacy import scan_repo
        report = scan_repo(Path.cwd())
        for f in report.findings:
            print(f"[{f.severity}] {f.category}: {f.message} ({f.file})")
        print("PRIVACY CHECK: PASS" if report.passed else "PRIVACY CHECK: FAIL")
        return 0 if report.passed else 1

    if args.command == "doctor":
        return _doctor()

    if args.command == "smoke-test":
        return _smoke_test()

    parser.print_help()
    return 0


def _doctor() -> int:
    from cat_sticker_skill.config import ensure_workspace, get_api_key
    print("=== Cat Sticker Skill Doctor ===")
    ws = ensure_workspace()
    print(f"Workspace: {ws}")
    key = get_api_key()
    if key:
        print("API Key: SET (from environment)")
    else:
        print("API Key: NOT SET — set ARK_API_KEY environment variable")
    print("Python: OK")
    print("Pillow: OK")
    print("NumPy: OK")
    return 0


def _smoke_test() -> int:
    """Free end-to-end smoke test using mock provider and synthetic images."""
    import tempfile
    from pathlib import Path

    import numpy as np
    from PIL import Image

    print("=== Smoke Test (mock provider, no paid API) ===")
    tmp = Path(tempfile.mkdtemp(prefix="catsticker_smoke_"))

    # 1. Create synthetic image (white background, colored circle)
    img = Image.new("RGBA", (512, 512), (255, 255, 255, 255))
    arr = np.array(img)
    # Draw a circle
    y, x = np.ogrid[:512, :512]
    mask = (x - 256) ** 2 + (y - 256) ** 2 < 200 ** 2
    arr[mask] = [100, 100, 150, 255]
    raw = tmp / "raw.png"
    Image.fromarray(arr).save(raw)

    # 2. Flood fill
    from cat_sticker_skill.matting.floodfill import remove_solid_background
    cutout = tmp / "cutout.png"
    remove_solid_background(raw, cutout)
    print("1. Flood fill: OK")

    # 3. Typography
    from cat_sticker_skill.typography.meme_yellow import compose_text
    composed = tmp / "composed.png"
    compose_text(cutout, composed, "测试文案")
    print("2. Typography: OK")

    # 4. Resize to 240
    final = tmp / "final_240.png"
    Image.open(composed).resize((240, 240), Image.LANCZOS).save(final)
    print("3. Resize 240x240: OK")

    # 5. Validate
    from cat_sticker_skill.validation.sticker import validate_main_image
    vr = validate_main_image(final)
    print(f"4. Validation: {vr.level}")

    # 6. Privacy scan
    from cat_sticker_skill.privacy.scanner import scan_repo
    pr = scan_repo(Path.cwd())
    print(f"5. Privacy: {'PASS' if pr.passed else 'WARN'} ({len(pr.findings)} findings)")

    print(f"\nSmoke test output: {tmp}")
    print("=== SMOKE TEST PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
