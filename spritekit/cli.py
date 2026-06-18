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
from .palette import TRANSPARENT, Palette
from .render import render_grid, render_to_png
from .rules import Style
from .sheet import save_sheet


def _resolve_palette(grid: Grid, explicit: str | None, search_root: Path) -> Palette:
    """Find a palette: explicit path wins; else styles/<name>/palette.json."""
    if explicit:
        return Palette.load(explicit)
    candidates = [
        search_root / "styles" / grid.palette / "palette.json",
        search_root / grid.palette,
    ]
    for c in candidates:
        if c.exists():
            return Palette.load(c)
    raise SystemExit(
        f"could not find palette {grid.palette!r}; pass --palette PATH"
    )


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
