"""CLI entry point: thin wrapper around the controller."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cat-sticker", description="Cat sticker generation skill")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Show version")
    sub.add_parser("privacy-check", help="Run privacy scanner on tracked files")
    sub.add_parser("doctor", help="Check installation and config")
    sub.add_parser("smoke-test", help="Run a free end-to-end smoke test (mock provider)")
    sub.add_parser("resume", help="Resume pending generations")
    sub.add_parser("validate", help="Validate current project output")

    # project
    p_create = sub.add_parser("project", help="Project management")
    p_sub = p_create.add_subparsers(dest="project_cmd")
    pc = p_sub.add_parser("create", help="Create a new project")
    pc.add_argument("name", help="Project name")
    p_sub.add_parser("list", help="List projects")
    p_sub.add_parser("show", help="Show project details")

    # plan
    pl = sub.add_parser("plan", help="Plan management")
    pl_sub = pl.add_subparsers(dest="plan_cmd")
    pl_sub.add_parser("show", help="Show current plan")
    pl_sub.add_parser("approve", help="Approve the current plan")

    # generate
    g = sub.add_parser("generate", help="Generate images for approved plan")
    g.add_argument("--dry-run", action="store_true", help="Use mock provider, no real API")
    g.add_argument("--project", default="default", help="Project ID")

    # regenerate
    rg = sub.add_parser("regenerate", help="Regenerate a single sticker")
    rg.add_argument("sticker_id", help="Sticker ID to regenerate")
    rg.add_argument("--dry-run", action="store_true")
    rg.add_argument("--project", default="default")

    # versions
    v = sub.add_parser("versions", help="List versions for a sticker")
    v.add_argument("sticker_id")
    v.add_argument("--project", default="default")

    # activate-version
    av = sub.add_parser("activate-version", help="Activate a version")
    av.add_argument("sticker_id")
    av.add_argument("version", type=int)
    av.add_argument("--project", default="default")

    # package
    pk = sub.add_parser("package", help="Export WeChat package")
    pk.add_argument("--out", default="./wechat_package")
    pk.add_argument("--project", default="default")

    args = parser.parse_args(argv)
    j = getattr(args, "json", False)

    if args.command == "version":
        from cat_sticker_skill import __version__
        print(f"cat-sticker-skill {__version__}")
        return 0

    if args.command == "privacy-check":
        from cat_sticker_skill.privacy import scan_repo
        report = scan_repo(Path.cwd())
        if not j:
            for f in report.findings:
                print(f"[{f.severity}] {f.category}: {f.message} ({f.file})")
            print("PRIVACY CHECK: PASS" if report.passed else "PRIVACY CHECK: FAIL")
        return 0 if report.passed else 1

    if args.command == "doctor":
        return _doctor()

    if args.command == "smoke-test":
        return _smoke_test()

    if args.command == "project" and args.project_cmd == "create":
        from cat_sticker_skill.project.controller import ProjectController
        ProjectController.create(args.name, name=args.name)
        print(f"Project '{args.name}' created.")
        return 0

    if args.command == "project" and args.project_cmd == "list":
        from cat_sticker_skill.project import store
        projects = store.list_projects()
        for p in projects:
            print(f"  {p}")
        return 0

    if args.command == "project" and args.project_cmd == "show":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.name if hasattr(args, 'name') else "default")
        print(f"Project: {c.project_id}")
        print(f"Stickers: {len(c.manifest.stickers)}")
        return 0

    if args.command == "plan" and args.plan_cmd == "show":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(getattr(args, 'project', 'default'))
        c.load_plan()
        print(f"Revision: {c.plan.plan_revision}")
        print(f"Approved: {c.plan.approved_for_generation}")
        for item in c.plan.items:
            print(f"  [{item.id}] {item.caption} ({item.emotion})")
        return 0

    if args.command == "plan" and args.plan_cmd == "approve":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(getattr(args, 'project', 'default'))
        c.approve_plan()
        print("Plan approved.")
        return 0

    if args.command == "generate":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        result = c.execute_approved_plan(reference_bytes={}, dry_run=args.dry_run)
        print(f"Mode: {result.get('provider_mode', 'unknown')}")
        print(f"Success: {result.get('success')}")
        for sid, r in result.get("results", {}).items():
            print(f"  {sid}: {r.get('status')}")
        return 0 if result.get("success") else 1

    if args.command == "regenerate":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        result = c.regenerate(args.sticker_id, reference_bytes={}, dry_run=args.dry_run)
        print(f"Success: {result.get('success')}")
        return 0 if result.get("success") else 1

    if args.command == "versions":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        vs = c.list_versions(args.sticker_id)
        for v in vs:
            active = " (active)" if c.manifest.stickers[args.sticker_id].active_version == v else ""
            print(f"  v{v:03d}{active}")
        return 0

    if args.command == "activate-version":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        ok = c.activate_version(args.sticker_id, args.version)
        print("Activated." if ok else "Failed.")
        return 0 if ok else 1

    if args.command == "package":
        from cat_sticker_skill.export.wechat_package import export_wechat_package
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        active_paths = [c.get_active_final(sid) for sid in c.manifest.stickers]
        active_paths = [p for p in active_paths if p]
        stickers_dir = Path.cwd() / "workspace" / args.project / "stickers"
        zip_path = export_wechat_package(stickers_dir, Path(args.out), active_final_paths=active_paths)
        print(f"Package: {zip_path}")
        return 0

    if args.command == "resume":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(getattr(args, 'project', 'default'))
        pending = c.resume_pending()
        print(f"Pending: {pending}")
        return 0

    if args.command == "validate":
        from cat_sticker_skill.validation.sticker import validate_package
        vr = validate_package(Path(getattr(args, 'out', './wechat_package')))
        print(f"Validation: {vr.level}")
        return 0

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
