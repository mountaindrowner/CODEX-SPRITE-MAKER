"""Command-line interface for spritekit.

Subcommands:
  render  SPRITE...            render .sprite -> PNG (scaled preview)
  import  IMAGE                import a raster sheet -> .sprite grids + palette
  diff    A.sprite B.sprite    pixel-by-pixel comparison (enforce exact emulation)
  lint    SPRITE...            validate against a style.json
  sheet   SPRITE...            assemble frames into a packed sheet + coords json
  gif     SPRITE...            assemble frames into an animated GIF
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .anim import build_gif
from .grid import Grid
from .importer import import_sheet
from .palette import TRANSPARENT, Palette, resolve_palette
from .render import render_grid, render_to_png
from .rules import Style
from .scale import epx_upscale
from .sheet import save_sheet


def _resolve_palette(grid: Grid, explicit: str | None, search_root: Path) -> Palette:
    """Find a palette: explicit path wins; else resolve the grid's declared name."""
    try:
        return resolve_palette(grid.palette, search_root, explicit)
    except FileNotFoundError as e:
        raise SystemExit(str(e))


def cmd_render(args) -> int:
    root = Path.cwd()
    for spath in args.sprites:
        grid = Grid.load(spath)
        palette = _resolve_palette(grid, args.palette, root)
        out = args.out or str(Path(spath).with_suffix(".png"))
        if len(args.sprites) > 1 and args.out:
            out = str(Path(args.out) / (Path(spath).stem + ".png"))
        render_to_png(grid, palette, out, scale=args.scale)
        print(f"rendered {spath} -> {out} (scale {args.scale})")
    return 0


def cmd_import(args) -> int:
    nw, nh = (int(v) for v in args.native.lower().split("x"))
    cols, rows = (int(v) for v in args.grid.lower().split("x"))
    bg = tuple(int(v) for v in args.bg.split(","))
    # --snap: import directly into a provided semantic palette (each native pixel
    # snaps to the nearest named colour), instead of auto-generating one.
    snap = Palette.load(args.snap) if args.snap else None
    palette, results = import_sheet(
        args.image,
        nw,
        nh,
        cols,
        rows,
        palette_name=args.name,
        max_colors=args.max_colors,
        bg=bg,  # type: ignore[arg-type]
        bg_tol=args.bg_tol,
        merge_tol=args.merge_tol,
        palette=snap,
    )
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    pal_path = Path(args.palette_out) if args.palette_out else out_dir / "palette.json"
    palette.save(pal_path)
    coords = {}
    for grid, c in results:
        grid.save(out_dir / f"{grid.name}.sprite")
        coords[grid.name] = c
    (out_dir / "frames.coords.json").write_text(
        __import__("json").dumps(coords, indent=2) + "\n"
    )
    print(
        f"imported {len(results)} frames -> {out_dir}/  "
        f"({len(palette.opaque_names())} colours -> {pal_path})"
    )
    return 0


def cmd_diff(args) -> int:
    root = Path.cwd()
    a, b = Grid.load(args.a), Grid.load(args.b)
    if (a.width, a.height) != (b.width, b.height):
        print(f"DIFFER: sizes {a.width}x{a.height} vs {b.width}x{b.height}")
        return 1
    pa = _resolve_palette(a, args.palette, root)
    pb = _resolve_palette(b, args.palette_b or args.palette, root)
    total = a.width * a.height
    mismatches = []
    for y in range(a.height):
        for x in range(a.width):
            na, nb = a.color_at(x, y), b.color_at(x, y)
            ca = None if na == TRANSPARENT else pa.rgb(na)
            cb = None if nb == TRANSPARENT else pb.rgb(nb)
            if ca != cb:
                mismatches.append((x, y, na, nb))
    matched = total - len(mismatches)
    pct = 100.0 * matched / total
    print(f"match {matched}/{total} = {pct:.2f}%")
    for x, y, na, nb in mismatches[:20]:
        print(f"  ({x},{y}): {na} != {nb}")
    if len(mismatches) > 20:
        print(f"  ... and {len(mismatches) - 20} more")
    return 0 if not mismatches else 1


def cmd_lint(args) -> int:
    style = Style.load(args.style)
    failures = 0
    for spath in args.sprites:
        grid = Grid.load(spath)
        issues = style.lint(grid)
        if issues:
            failures += 1
            print(f"FAIL {spath}")
            for i in issues:
                print(f"  - {i}")
        else:
            print(f"ok   {spath}")
    return 1 if failures else 0


def cmd_sheet(args) -> int:
    root = Path.cwd()
    grids = [Grid.load(p) for p in args.sprites]
    palette = _resolve_palette(grids[0], args.palette, root)
    manifest = save_sheet(
        grids,
        palette,
        args.out,
        cols=args.cols,
        scale=args.scale,
        padding=args.padding,
        coords_path=args.coords,
    )
    print(
        f"sheet -> {args.out}  ({manifest['cols']}x{manifest['rows']} "
        f"frames of {manifest['frame_size']}, scale {args.scale})"
    )
    return 0


def cmd_gif(args) -> int:
    root = Path.cwd()
    grids = [Grid.load(p) for p in args.sprites]
    palette = _resolve_palette(grids[0], args.palette, root)
    build_gif(grids, palette, args.out, scale=args.scale, fps=args.fps)
    print(f"gif -> {args.out}  ({len(grids)} frames @ {args.fps} fps, scale {args.scale})")
    return 0


def cmd_mirror(args) -> int:
    grid = Grid.load(args.sprite)
    name = args.name or (grid.name.replace("left", "right") if "left" in grid.name else grid.name + "_mirror")
    grid.flipped_h(name).save(args.out)
    print(f"mirrored {args.sprite} -> {args.out} (name {name})")
    return 0


def _load_parts(args):
    from .studio import load_parts
    return load_parts(args.parts) if getattr(args, "parts", None) else None


def cmd_grade(args) -> int:
    from .studio import grade_report
    root = Path.cwd()
    for spath in args.sprites:
        grid = Grid.load(spath)
        palette = _resolve_palette(grid, args.palette, root)
        print(grade_report(grid, palette, _load_parts(args)))
        print()
    return 0


def cmd_parts(args) -> int:
    from .studio import parts_sheet
    root = Path.cwd()
    grid = Grid.load(args.sprite)
    palette = _resolve_palette(grid, args.palette, root)
    parts_sheet(grid, palette, _load_parts(args), scale=args.scale).save(args.out)
    print(f"parts sheet -> {args.out}")
    return 0


def cmd_inspect(args) -> int:
    from .studio import render_labeled
    root = Path.cwd()
    grid = Grid.load(args.sprite)
    palette = _resolve_palette(grid, args.palette, root)
    render_labeled(grid, palette, scale=args.scale, step=args.step).save(args.out)
    print(f"labeled view -> {args.out} (grid every {args.step}px)")
    return 0


def cmd_layers(args) -> int:
    from . import layers as L
    root = Path.cwd()
    grid = Grid.load(args.sprite)
    palette = _resolve_palette(grid, args.palette, root)
    overrides = L.load_overrides(args.apply) if args.apply else None
    info = L.classify(grid, palette, overrides)
    print(L.report(grid, info))
    m = L.model(grid, palette, info)
    if args.json:
        L.write_sidecar(args.json, m)
        print(f"\nlayer sidecar (edit + re-run with --apply) -> {args.json}")
    if args.out:
        rig = pose = None
        if args.rig:
            from .skeleton import Rig
            rig = Rig.load(args.rig)
            pose = args.pose or next(iter(rig.poses))
        L.breakdown_sheet(grid, palette, info, scale=args.scale,
                          rig=rig, pose=pose).save(args.out)
        print(f"layer breakdown -> {args.out}")
    return 0


def cmd_skeleton(args) -> int:
    import json as _json
    from .skeleton import Rig
    root = Path.cwd()
    rig = Rig.load(args.rig)
    pose = args.pose or next(iter(rig.poses))
    if args.ratios:
        print(_json.dumps(rig.ratios(pose), indent=2))
    if args.table:
        print(rig.joint_table(pose))
    if getattr(args, "flesh", None):
        size = None
        if args.flesh_size:
            w, h = args.flesh_size.lower().split("x")
            size = (int(w), int(h))
        grid = rig.flesh(pose, size, palette=args.flesh_palette)
        grid.save(args.flesh)
        print(f"flesh ({pose}) -> {args.flesh} ({grid.width}x{grid.height})")
    if args.out:
        base = None
        if args.sprite:
            grid = Grid.load(args.sprite)
            palette = _resolve_palette(grid, args.palette, root)
            base = render_grid(grid, palette, args.scale)
        if args.worksheet and base is not None:
            img = rig.worksheet(pose, base, args.scale, step=args.step)
        elif base is not None:
            img = rig.overlay(pose, base, args.scale)
        else:
            img = rig.stick(pose, args.scale)
        img.save(args.out)
        print(f"skeleton ({pose}) -> {args.out}")
    return 0


def cmd_recolor_outline(args) -> int:
    from .selout import recolor_outline
    root = Path.cwd()
    grid = Grid.load(args.sprite)
    palette = _resolve_palette(grid, args.palette, root)
    out = recolor_outline(grid, palette)
    out.save(args.out or args.sprite)
    print(f"recolored outline {args.sprite} -> {args.out or args.sprite}")
    return 0


def cmd_ramp(args) -> int:
    import json
    from .ramp import expand
    config = json.loads(Path(args.config).read_text())
    kw = {}
    if args.hue_shift is not None:
        kw["hue_shift"] = args.hue_shift
    if args.val_step is not None:
        kw["val_step"] = args.val_step
    if args.sat_step is not None:
        kw["sat_step"] = args.sat_step
    colors = expand(config, **kw)
    out = {"name": config.get("name", "ramp"), "colors": colors}
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    opaque = [c for c in colors.values() if c]
    print(f"ramp -> {args.out} ({len(opaque)} colours; hue-shifted ramps)")
    return 0


def cmd_upscale(args) -> int:
    grid = Grid.load(args.sprite)
    up = epx_upscale(grid, times=args.times)
    if args.name:
        up.name = args.name
    up.save(args.out)
    print(f"upscaled {args.sprite} -> {args.out} ({grid.width}x{grid.height} -> {up.width}x{up.height})")
    return 0


def cmd_shade(args) -> int:
    from .shade import auto_shade
    root = Path.cwd()
    grid = Grid.load(args.sprite)
    palette = _resolve_palette(grid, args.palette, root)
    out = auto_shade(grid, palette, light=args.light, highlights=not args.no_highlights)
    out.save(args.out or args.sprite)
    print(f"auto-shaded {args.sprite} -> {args.out or args.sprite} (light {args.light})")
    return 0


def cmd_stamp(args) -> int:
    from .skeleton import Rig
    from .stamps import apply_stamps
    root = Path.cwd()
    grid = Grid.load(args.sprite)
    palette = _resolve_palette(grid, args.palette, root)
    rig = Rig.load(args.rig)
    parts = args.parts.split(",") if args.parts else None
    out = apply_stamps(grid, rig, args.pose, palette, parts=parts, view=args.view)
    out.save(args.out or args.sprite)
    print(f"stamped {args.sprite} -> {args.out or args.sprite} "
          f"(pose {args.pose}, parts {parts or 'default'})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="spritekit", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("render", help="render .sprite to PNG")
    r.add_argument("sprites", nargs="+")
    r.add_argument("--scale", type=int, default=8)
    r.add_argument("--out", help="output PNG (or dir when multiple inputs)")
    r.add_argument("--palette", help="palette.json path")
    r.set_defaults(func=cmd_render)

    im = sub.add_parser("import", help="import a raster sheet to .sprite grids")
    im.add_argument("image")
    im.add_argument("--native", required=True, help="native size WxH, e.g. 64x64")
    im.add_argument("--grid", required=True, help="sheet layout COLSxROWS, e.g. 4x4")
    im.add_argument("--name", default="imported", help="palette/sprite name prefix")
    im.add_argument("--max-colors", type=int, default=16)
    im.add_argument("--bg", default="255,255,255", help="background RGB to treat as transparent")
    im.add_argument("--bg-tol", type=int, default=32)
    im.add_argument("--merge-tol", type=int, default=40)
    im.add_argument("--snap", help="snap pixels to this palette.json instead of generating one")
    im.add_argument("--out", required=True, help="output directory")
    im.add_argument("--palette-out", help="palette.json output path")
    im.set_defaults(func=cmd_import)

    d = sub.add_parser("diff", help="pixel diff two sprites")
    d.add_argument("a")
    d.add_argument("b")
    d.add_argument("--palette")
    d.add_argument("--palette-b")
    d.set_defaults(func=cmd_diff)

    li = sub.add_parser("lint", help="validate against a style.json")
    li.add_argument("sprites", nargs="+")
    li.add_argument("--style", required=True)
    li.set_defaults(func=cmd_lint)

    sh = sub.add_parser("sheet", help="assemble a packed sprite sheet")
    sh.add_argument("sprites", nargs="+")
    sh.add_argument("--out", required=True)
    sh.add_argument("--cols", type=int, required=True)
    sh.add_argument("--scale", type=int, default=1)
    sh.add_argument("--padding", type=int, default=0)
    sh.add_argument("--coords", help="coords json output path")
    sh.add_argument("--palette")
    sh.set_defaults(func=cmd_sheet)

    mi = sub.add_parser("mirror", help="horizontally mirror a sprite (right = mirror of left)")
    mi.add_argument("sprite")
    mi.add_argument("--out", required=True)
    mi.add_argument("--name")
    mi.set_defaults(func=cmd_mirror)

    up = sub.add_parser("upscale", help="smooth 2x pixel-art upscale (EPX/Scale2x)")
    up.add_argument("sprite")
    up.add_argument("--out", required=True)
    up.add_argument("--times", type=int, default=1, help="apply EPX N times (each = x2)")
    up.add_argument("--name")
    up.set_defaults(func=cmd_upscale)

    sh = sub.add_parser("shade", help="auto-shade flat colour into lit form (directional cel-shading)")
    sh.add_argument("sprite")
    sh.add_argument("--out")
    sh.add_argument("--palette")
    sh.add_argument("--light", default="top-left",
                    help="light direction: top, top-left, left, ... (default top-left)")
    sh.add_argument("--no-highlights", action="store_true", help="skip the highlight dabs")
    sh.set_defaults(func=cmd_shade)

    st = sub.add_parser("stamp", help="place parametric feature parts on a flesh base from the rig")
    st.add_argument("sprite")
    st.add_argument("--rig", required=True)
    st.add_argument("--pose", required=True)
    st.add_argument("--out")
    st.add_argument("--palette")
    st.add_argument("--view", help="front/back/side: down|up|left|right (default: pose prefix)")
    st.add_argument("--parts", help="comma-separated: hair_spikes,eyes,collar,belt,boots")
    st.set_defaults(func=cmd_stamp)

    sk = sub.add_parser("skeleton", help="overlay/draw a skeleton rig; read its proportion ratios")
    sk.add_argument("--rig", required=True)
    sk.add_argument("--pose")
    sk.add_argument("--sprite", help="overlay on this sprite (else draw stick figure)")
    sk.add_argument("--palette")
    sk.add_argument("--out")
    sk.add_argument("--scale", type=int, default=12)
    sk.add_argument("--step", type=int, default=4, help="coordinate grid spacing (worksheet)")
    sk.add_argument("--worksheet", action="store_true", help="render a rigging worksheet (grid + labelled joints)")
    sk.add_argument("--ratios", action="store_true", help="print proportion ratios")
    sk.add_argument("--table", action="store_true", help="print the editable joint table")
    sk.add_argument("--flesh", help="rasterise the pose into a capsule-body .sprite at this path")
    sk.add_argument("--flesh-size", help="target WxH for --flesh (default 2x rig frame)")
    sk.add_argument("--flesh-palette", default="kael", help="palette name to declare on the flesh sprite")
    sk.set_defaults(func=cmd_skeleton)

    ro = sub.add_parser("recolor-outline", help="sel-out: retint outline toward bordering material shadow")
    ro.add_argument("sprite")
    ro.add_argument("--out")
    ro.add_argument("--palette")
    ro.set_defaults(func=cmd_recolor_outline)

    rp = sub.add_parser("ramp", help="generate a hue-shifted palette from a ramp config")
    rp.add_argument("config")
    rp.add_argument("--out", required=True)
    rp.add_argument("--hue-shift", type=float)
    rp.add_argument("--val-step", type=float)
    rp.add_argument("--sat-step", type=float)
    rp.set_defaults(func=cmd_ramp)

    gr = sub.add_parser("grade", help="quantified quality scorecard")
    gr.add_argument("sprites", nargs="+")
    gr.add_argument("--palette")
    gr.add_argument("--parts", help="parts manifest json")
    gr.set_defaults(func=cmd_grade)

    pa = sub.add_parser("parts", help="contact sheet isolating each part/material")
    pa.add_argument("sprite")
    pa.add_argument("--out", required=True)
    pa.add_argument("--palette")
    pa.add_argument("--parts", help="parts manifest json")
    pa.add_argument("--scale", type=int, default=6)
    pa.set_defaults(func=cmd_parts)

    ins = sub.add_parser("inspect", help="zoomed render with a labelled coordinate grid")
    ins.add_argument("sprite")
    ins.add_argument("--out", required=True)
    ins.add_argument("--palette")
    ins.add_argument("--scale", type=int, default=16)
    ins.add_argument("--step", type=int, default=4)
    ins.set_defaults(func=cmd_inspect)

    ly = sub.add_parser("layers", help="decompose a sprite into its construction layers")
    ly.add_argument("sprite")
    ly.add_argument("--out", help="render the exploded layer breakdown to this PNG")
    ly.add_argument("--json", help="write the editable layer sidecar (the place to correct)")
    ly.add_argument("--apply", help="apply an edited layer sidecar to override the auto-classification")
    ly.add_argument("--palette")
    ly.add_argument("--scale", type=int, default=6)
    ly.add_argument("--rig", help="optional rig to add a skeleton panel")
    ly.add_argument("--pose", help="pose name for the skeleton panel")
    ly.set_defaults(func=cmd_layers)

    g = sub.add_parser("gif", help="assemble an animated GIF")
    g.add_argument("sprites", nargs="+")
    g.add_argument("--out", required=True)
    g.add_argument("--scale", type=int, default=6)
    g.add_argument("--fps", type=float, default=6.0)
    g.add_argument("--palette")
    g.set_defaults(func=cmd_gif)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
