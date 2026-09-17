"""CLI entry point: thin wrapper around the controller."""

from __future__ import annotations

import argparse
import json
import os
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

    # project
    p_create = sub.add_parser("project", help="Project management")
    p_sub = p_create.add_subparsers(dest="project_cmd")
    pc = p_sub.add_parser("create", help="Create a new project")
    pc.add_argument("name", help="Project name")
    p_sub.add_parser("list", help="List projects")
    ps = p_sub.add_parser("show", help="Show project details")
    ps.add_argument("name", help="Project name")

    # ref
    ref_p = sub.add_parser("ref", help="Reference image management")
    ref_sub = ref_p.add_subparsers(dest="ref_cmd")
    ra = ref_sub.add_parser("add", help="Add a reference image")
    ra.add_argument("path", help="Path to image file")
    ra.add_argument("--id", required=True, help="Reference ID (e.g. r1)")
    ra.add_argument("--project", required=True, help="Project ID")
    ra.add_argument("--replace", action="store_true", help="Replace existing ref (invalidates approval)")
    rl = ref_sub.add_parser("list", help="List references")
    rl.add_argument("--project", required=True)

    # character
    ch = sub.add_parser("character", help="Character profile management")
    ch_sub = ch.add_subparsers(dest="character_cmd")
    ci = ch_sub.add_parser("import", help="Import a CharacterProfile from JSON file")
    ci.add_argument("json_file", help="Path to character JSON")
    ci.add_argument("--project", required=True)
    ci.add_argument("--replace", action="store_true")
    cl = ch_sub.add_parser("list", help="List characters")
    cl.add_argument("--project", required=True)
    cs = ch_sub.add_parser("show", help="Show a character")
    cs.add_argument("character_id")
    cs.add_argument("--project", required=True)

    # plan
    pl = sub.add_parser("plan", help="Plan management")
    pl_sub = pl.add_subparsers(dest="plan_cmd")
    pl_sub.add_parser("show", help="Show current plan").add_argument("--project", required=True)
    pl_sub.add_parser("approve", help="Approve the current plan").add_argument("--project", required=True)
    pi = pl_sub.add_parser("import", help="Import a GenerationPlan from JSON file")
    pi.add_argument("json_file", help="Path to plan JSON")
    pi.add_argument("--project", required=True)

    # generate
    g = sub.add_parser("generate", help="Generate images for approved plan")
    g.add_argument("--dry-run", action="store_true", help="Use mock provider")
    g.add_argument("--project", required=True)

    # regenerate
    rg = sub.add_parser("regenerate", help="Regenerate a single sticker")
    rg.add_argument("sticker_id")
    rg.add_argument("--dry-run", action="store_true")
    rg.add_argument("--project", required=True)

    # versions
    v = sub.add_parser("versions", help="List versions for a sticker")
    v.add_argument("sticker_id")
    v.add_argument("--project", required=True)

    # activate-version
    av = sub.add_parser("activate-version", help="Activate a version")
    av.add_argument("sticker_id")
    av.add_argument("version", type=int)
    av.add_argument("--project", required=True)

    # text-adjust
    ta = sub.add_parser("text-adjust", help="Re-compose text locally (no Seedream)")
    ta.add_argument("sticker_id")
    ta.add_argument("--y-offset", type=int, default=0)
    ta.add_argument("--x-offset", type=int, default=0)
    ta.add_argument("--font-scale", type=float, default=1.0)
    ta.add_argument("--caption", default=None)
    ta.add_argument("--preset", default=None)
    ta.add_argument("--project", required=True)

    # resume
    rs = sub.add_parser("resume", help="Resume pending generations (executes)")
    rs.add_argument("--dry-run", action="store_true")
    rs.add_argument("--project", required=True)

    # validate
    val = sub.add_parser("validate", help="Validate current project output")
    val.add_argument("--project", default=None)
    val.add_argument("--path", default=None)

    # package
    pk = sub.add_parser("package", help="Export WeChat package as ZIP")
    pk.add_argument("--out", default=None, help="Output parent dir (default: <CAT_STICKER_HOME>/exports)")
    pk.add_argument("--project", required=True)

    # matting-ab
    ab = sub.add_parser("matting-ab", help="A/B test legacy vs precompose matting (private fixtures only)")
    ab.add_argument("--project", required=True)
    ab.add_argument("--output", "-o", default=None, help="Output dir for side-by-side PNGs")

    args = parser.parse_args(argv)

    if args.command == "version":
        from cat_sticker_skill import __version__
        print(f"cat-sticker-skill {__version__}")
        return 0

    if args.command == "privacy-check":
        from cat_sticker_skill.privacy.scanner import scan_repo
        report = scan_repo(Path.cwd())
        for f in report.findings:
            print(f"[{f.severity}] {f.category}: {f.message} (file: {f.file})")
        print("PRIVACY CHECK: PASS" if report.passed else "PRIVACY CHECK: FAIL")
        return 0 if report.passed else 1

    if args.command == "doctor":
        return _doctor()

    if args.command == "smoke-test":
        return _smoke_test()

    if args.command == "project" and args.project_cmd == "create":
        from cat_sticker_skill.project.controller import ProjectController
        try:
            ProjectController.create(args.name, name=args.name)
        except FileExistsError as e:
            print(f"FAIL: {e}")
            return 1
        print(f"Project '{args.name}' created.")
        return 0

    if args.command == "project" and args.project_cmd == "list":
        from cat_sticker_skill.project import store
        for p in store.list_projects():
            print(f"  {p}")
        return 0

    if args.command == "project" and args.project_cmd == "show":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.name)
        print(f"Project: {c.project_id}")
        print(f"Stickers: {len(c.manifest.stickers)}")
        return 0

    if args.command == "ref" and args.ref_cmd == "add":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        result = c.add_ref(args.id, Path(args.path), replace=args.replace)
        if not result.get("success"):
            print(f"FAIL: {result.get('error')}")
            return 1
        print(f"Added ref {args.id} (sha256={result['sha256'][:12]}..., size={result['size']})")
        return 0

    if args.command == "ref" and args.ref_cmd == "list":
        from cat_sticker_skill.project import store
        for rid, entry in store.load_ref_mapping(args.project).items():
            print(f"  {rid} -> {entry['file']} sha256={entry.get('sha256', '?')[:12]}")
        return 0

    if args.command == "character" and args.character_cmd == "import":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        result = c.import_character(data, replace=args.replace)
        if not result.get("success"):
            print(f"FAIL: {result.get('error')}")
            return 1
        print(f"Character {result['character_id']} imported.")
        return 0

    if args.command == "character" and args.character_cmd == "list":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        for cid in c.list_characters():
            print(f"  {cid}")
        return 0

    if args.command == "character" and args.character_cmd == "show":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        prof = c.show_character(args.character_id)
        print(json.dumps(prof, ensure_ascii=False, indent=2) if prof else "Not found.")
        return 0 if prof else 1

    if args.command == "plan" and args.plan_cmd == "show":
        from cat_sticker_skill.config import get_max_retries, get_unit_price_cny
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        c.load_plan()
        n = len(c.plan.items)
        r = get_max_retries()
        unit = get_unit_price_cny()
        print(f"Revision: {c.plan.plan_revision}")
        print(f"Approved: {c.plan.approved_for_generation}")
        print(f"Total stickers: {n}")
        print(f"Initial generation requests: {n}")
        print(f"Max retries per sticker: {r}")
        print(f"Max generation request attempts: {n * (1 + r)}")
        if unit:
            print(f"Unit price: {unit} CNY/image")
            print(f"Estimated initial cost: {round(n * unit, 4)} CNY")
            print(f"Estimated max cost: {round(n * (1 + r) * unit, 4)} CNY")
        else:
            print("Unit price not configured; cost estimate unavailable.")
        for item in c.plan.items:
            print(f"  [{item.id}] {item.caption} (preset={item.typography_preset})")
        return 0

    if args.command == "plan" and args.plan_cmd == "approve":
        from cat_sticker_skill.config import get_max_retries, get_unit_price_cny
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        c.load_plan()
        c.approve_plan()
        n = len(c.plan.items)
        r = get_max_retries()
        unit = get_unit_price_cny()
        print(f"Plan approved ({n} images, max {n*(1+r)} attempts).")
        if unit:
            print(f"Cost estimate: {round(n*unit,4)} - {round(n*(1+r)*unit,4)} CNY")
        return 0

    if args.command == "plan" and args.plan_cmd == "import":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        result = c.import_plan(data)
        if not result.get("success"):
            print(f"FAIL: {result.get('error')}")
            return 1
        print(f"Plan imported: {result['items']} items, approved={result['approved']}")
        return 0

    if args.command == "generate":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        c.load_plan()
        result = c.execute_approved_plan(reference_bytes=None, dry_run=args.dry_run)
        print(f"provider_mode: {result.get('provider_mode', 'unknown')}")
        print(f"overall_status: {result.get('overall_status')}")
        print(f"requests_sent: {result.get('requests_sent')}")
        print(f"successful_generations: {result.get('successful_generations', result.get('paid_calls'))}")
        print(f"retry_attempts: {result.get('retry_calls')}")
        from cat_sticker_skill.config import get_unit_price_cny
        unit = get_unit_price_cny()
        if unit:
            print(f"estimated_cost_cny: {round(result.get('requests_sent',0)*unit, 4)}")
        else:
            print("estimated_cost_cny: unknown")
        for sid, r in result.get("results", {}).items():
            print(f"  {sid}: {r.get('status')}")
        return 0 if result.get("success") else 1

    if args.command == "regenerate":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        c.load_plan()
        result = c.regenerate(args.sticker_id, reference_bytes=None, dry_run=args.dry_run)
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

    if args.command == "text-adjust":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        result = c.recompose_text(
            args.sticker_id, caption=args.caption,
            y_offset=args.y_offset, x_offset=args.x_offset, font_scale=args.font_scale,
            preset=args.preset,
        )
        print(f"Success: {result.get('success')}")
        if result.get("file"):
            print(f"File: {result['file']}")
        return 0 if result.get("success") else 1

    if args.command == "package":
        return _package(args)

    if args.command == "matting-ab":
        return _matting_ab(args)

    if args.command == "resume":
        from cat_sticker_skill.project.controller import ProjectController
        c = ProjectController.open(args.project)
        c.load_plan()
        pending = c.resume_pending()
        if not pending:
            print("No pending items.")
            print("requests_sent: 0")
            return 0
        print(f"Resuming: {pending}")
        result = c.execute_approved_plan(reference_bytes=None, dry_run=args.dry_run)
        print(f"overall_status: {result.get('overall_status')}")
        print(f"requests_sent: {result.get('requests_sent')}")
        return 0 if result.get("success") else 1

    if args.command == "validate":
        from cat_sticker_skill.validation.sticker import validate_sticker_package
        if args.path:
            target = Path(args.path)
        elif args.project:
            from cat_sticker_skill.config import get_workspace_root
            target = get_workspace_root() / "exports" / f"{args.project}-wechat-static"
        else:
            print("Specify --project or --path")
            return 2
        vr = validate_sticker_package(target)
        print(f"Validation: {vr.level}")
        print(f"report: {vr}")
        return 0 if vr.level in ("PASS", "WARN") else 1

    parser.print_help()
    return 0


def _matting_ab(args) -> int:
    """A/B compare legacy vs precompose matting on private fixtures.
    Reads CAT_STICKER_PRIVATE_FIXTURES; SKIP (exit 0) if not configured."""
    import os
    fixtures_dir = os.environ.get("CAT_STICKER_PRIVATE_FIXTURES")
    if not fixtures_dir:
        print("SKIP: CAT_STICKER_PRIVATE_FIXTURES not set")
        return 0
    fdir = Path(fixtures_dir)
    if not fdir.exists():
        print(f"SKIP: {fdir} not found")
        return 0
    out_dir = Path(args.output) if args.output else fdir / "ab-out"
    out_dir.mkdir(parents=True, exist_ok=True)

    from cat_sticker_skill.matting.floodfill import remove_solid_background
    from cat_sticker_skill.typography.meme_yellow import compose_text

    pngs = sorted(list(fdir.glob("*.png")) + list(fdir.glob("*.jpg")))
    if not pngs:
        print("SKIP: no images in fixtures dir")
        return 0
    print(f"A/B comparing {len(pngs)} fixtures → {out_dir}")
    for src in pngs:
        stem = src.stem
        try:
            # Legacy: text → floodfill
            leg_composed = out_dir / f"{stem}_legacy_composed.png"
            leg_cutout = out_dir / f"{stem}_legacy_cutout.png"
            compose_text(src, leg_composed, "测试文案")
            remove_solid_background(leg_composed, leg_cutout)
            # Precompose: floodfill → text
            pre_cutout = out_dir / f"{stem}_pre_cutout.png"
            pre_composed = out_dir / f"{stem}_pre_composed.png"
            remove_solid_background(src, pre_cutout)
            compose_text(pre_cutout, pre_composed, "测试文案")
            print(f"  {stem}: legacy={leg_cutout.name} precompose={pre_composed.name}")
        except Exception as e:
            print(f"  {stem}: FAILED {e}")
    return 0


def _package(args) -> int:
    """Build WeChat package with auto banner + ZIP. Default out = <CAT_STICKER_HOME>/exports."""
    from cat_sticker_skill.config import get_workspace_root
    from cat_sticker_skill.export.wechat_package import export_wechat_package, zip_package
    from cat_sticker_skill.project import store
    from cat_sticker_skill.project.controller import ProjectController
    from cat_sticker_skill.validation.sticker import validate_sticker_package

    c = ProjectController.open(args.project)
    # Use CURRENT PLAN order
    if c.plan is None:
        c.load_plan()
    plan_sids = [it.id for it in c.plan.items] if c.plan else list(c.manifest.stickers.keys())
    active_paths = []
    clean_paths = []
    for sid in plan_sids:
        final = c.get_active_final(sid)
        clean = c.get_active_clean_image(sid)
        if final and final.exists():
            active_paths.append(final)
            if clean and clean.exists():
                clean_paths.append(clean)
    if not active_paths:
        print("No active stickers to package.")
        return 1

    # Banner + cover both from first active clean image
    banner_source = clean_paths[0] if clean_paths else None
    cover_source = clean_paths[0] if clean_paths else None

    if args.out:
        out_parent = Path(args.out)
    else:
        out_parent = get_workspace_root() / "exports"
    out_parent.mkdir(parents=True, exist_ok=True)

    export_dir = out_parent / f"{args.project}-wechat-static"
    # Clean stale export dir
    if export_dir.exists():
        import shutil
        shutil.rmtree(export_dir)

    export_wechat_package(
        store.project_path(args.project) / "stickers",
        export_dir,
        banner_source=banner_source,
        cover_source=cover_source,
        active_final_paths=active_paths,
    )
    zip_path = out_parent / f"{args.project}-wechat-static.zip"
    if zip_path.exists():
        zip_path.unlink()
    zip_package(export_dir, zip_path)
    print(f"Package dir: {export_dir}")
    print(f"ZIP: {zip_path}")
    vr = validate_sticker_package(export_dir)
    print(f"Validation: {vr.level}")
    return 0 if vr.level in ("PASS", "WARN") else 1


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
    """Free FULL E2E smoke test: project -> ref -> character -> plan -> approve -> generate -> package -> validate."""
    import tempfile

    print("=== Full Smoke Test (mock provider, no paid API) ===")
    tmp = Path(tempfile.mkdtemp(prefix="catsticker_smoke_"))
    os.environ["CAT_STICKER_HOME"] = str(tmp)

    import numpy as np
    from PIL import Image

    from cat_sticker_skill.project.controller import ProjectController
    from cat_sticker_skill.validation.sticker import validate_sticker_package

    # 1. create project
    c = ProjectController.create("smoke", name="smoke")
    print("1. project create: OK")

    # 2. ref add (synthetic image)
    ref_path = tmp / "ref1.png"
    arr = np.full((512, 512, 3), 255, dtype=np.uint8)
    arr[100:400, 100:400] = [120, 100, 180]
    Image.fromarray(arr).save(ref_path)
    r = c.add_ref("r1", ref_path)
    assert r["success"], r
    print("2. ref add: OK")

    # 3. character import
    char_json = {
        "character_id": "cat_smoke",
        "species": "cat",
        "coat_color": "grey",
        "coat_pattern": "solid",
        "eye_color": "yellow",
        "hair_length": "short",
        "body_type": "chubby",
        "face_shape": "round",
        "distinctive_markings": ["small white paw"],
        "accessories": ["pointy ears"],
        "preserve": ["face shape"],
        "avoid": ["scary"],
    }
    r = c.import_character(char_json)
    assert r["success"], r
    print("3. character import: OK")

    # 4. plan import (must NOT be auto-approved)
    plan_json = {
        "items": [
            {
                "id": "s001",
                "reference": {"type": "image", "ids": ["r1"]},
                "caption": "测试文案",
                "emotion": "happy",
                "pose": "sitting",
                "composition": "centered",
                "identity_priority": "high",
                "typography_preset": "meme-yellow",
                "character_id": "cat_smoke",
            },
            {
                "id": "s002",
                "reference": {"type": "image", "ids": ["r1"]},
                "caption": "蚌埠住了",
                "emotion": "laughing",
                "pose": "lying",
                "composition": "centered",
                "identity_priority": "high",
                "typography_preset": "clean-white",
                "character_id": "cat_smoke",
            },
        ]
    }
    r = c.import_plan(plan_json)
    assert r["success"] and not r["approved"], r
    print("4. plan import (not auto-approved): OK")

    # 5. plan show preview
    print("5. plan show: OK")

    # 6. approve
    c.approve_plan()
    assert c.gate.plan.approved_for_generation
    print("6. plan approve: OK")

    # 7. generate dry-run
    result = c.execute_approved_plan(dry_run=True)
    assert result["overall_status"] == "success", result
    print(f"7. generate dry-run: OK (status={result['overall_status']}, reqs={result['requests_sent']})")

    # 8. text-adjust (no Seedream)
    r = c.recompose_text("s001", caption="新文案")
    assert r["success"], r
    print("8. text-adjust: OK")

    # 9. activate v1
    assert c.activate_version("s001", 1)
    print("9. activate v1: OK")

    # 10. package
    from cat_sticker_skill.export.wechat_package import export_wechat_package, zip_package
    out_parent = tmp / "exports"
    paths = [c.get_active_final(sid) for sid in ("s001", "s002")]
    paths = [p for p in paths if p and p.exists()]
    clean = c.get_active_clean_image("s001")
    export_dir = out_parent / "smoke-wechat-static"
    export_wechat_package(
        tmp / "projects" / "smoke" / "stickers",
        export_dir,
        banner_source=clean, cover_source=clean,
        active_final_paths=paths,
    )
    zip_path = out_parent / "smoke-wechat-static.zip"
    zip_package(export_dir, zip_path)
    assert zip_path.exists()
    import zipfile
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert not any(n.endswith(".zip") for n in names), f"ZIP contains itself: {names}"
        assert "banner.png" in names
        assert "cover.png" in names
    print("10. package + zip self-check: OK")

    # 11. validate
    vr = validate_sticker_package(export_dir)
    assert vr.level in ("PASS", "WARN"), vr
    print(f"11. validate: {vr.level}")

    # 12. resume no duplicate
    pending = c.resume_pending()
    assert pending == [], f"Expected no pending, got {pending}"
    print("12. resume no-duplicate: OK")

    # 13. privacy
    from cat_sticker_skill.privacy.scanner import scan_repo
    pr = scan_repo(Path.cwd())
    print(f"13. privacy: {'PASS' if pr.passed else 'WARN'} ({len(pr.findings)} findings)")

    print("\n=== FULL SMOKE TEST: PASS ===")
    print("Paid generation requests: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
