"""Observe: trace a reference image onto the sprite grid and diff your work.

The toolkit can already `diff` two `.sprite` grids, but a *photo* of a sprite
isn't a grid. This module closes that loop so the artist (Claude) can check its
own work **objectively**, cell by cell, instead of eyeballing a blurry side-by-side:

1. ``trace_image`` snaps a reference photo (optionally one frame of a sheet) down to
   a ``cols x rows`` grid and quantises each cell to the nearest palette colour —
   "what the toolkit sees in the photo".
2. ``cell_diff`` compares that traced reference to your recreation and lists every
   mismatched cell: ``(col, row): expected -> got``.
3. ``diff_panel`` renders TRACED | MINE | DIFF (mismatched cells flagged red) so the
   gap is unmistakable.

Reuses ``importer.downscale_native`` (median per-block sampling, robust to JPEG
blur) and ``Palette.nearest_name``. Works on any reference — including your own
clean PNGs and original sprites — not just this one.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .grid import TRANSPARENT, TRANSPARENT_CHAR, Grid
from .importer import _CHAR_POOL, _dist2, downscale_native
from .palette import Palette
from .render import render_grid


def trace_image(path: str | Path, cols: int, rows: int, palette: Palette,
                frame: tuple[int, int, int, int] | None = None,
                bg: tuple[int, int, int] | None = None, bg_tol: int = 46) -> Grid:
    img = Image.open(path).convert("RGBA")
    if frame:
        img = img.crop(frame)
    native = downscale_native(img, cols, rows)
    px = native.load()
    if bg is None:                                   # auto: sample a corner cell
        bg = native.getpixel((0, 0))[:3]
    bg_tol2 = bg_tol * bg_tol

    opaque = palette.opaque_names()
    name_to_char = {n: _CHAR_POOL[i] for i, n in enumerate(opaque)}
    legend = {TRANSPARENT_CHAR: TRANSPARENT}
    legend.update({ch: n for n, ch in name_to_char.items()})

    out_rows = []
    for y in range(rows):
        line = []
        for x in range(cols):
            c = px[x, y]
            if c[3] < 128 or _dist2(c[:3], bg) <= bg_tol2:
                line.append(TRANSPARENT_CHAR)
            else:
                line.append(name_to_char[palette.nearest_name(c[:3])])
        out_rows.append("".join(line))
    return Grid("traced", cols, rows, palette.name, legend, out_rows)


def cell_diff(ref: Grid, mine: Grid) -> tuple[list[tuple[int, int, str, str]], int]:
    """Return (mismatches, total). Each mismatch = (col, row, expected, got)."""
    mism = []
    for y in range(ref.height):
        for x in range(ref.width):
            a = ref.color_at(x, y)
            b = mine.color_at(x, y)
            if a != b:
                mism.append((x, y, a, b))
    return mism, ref.width * ref.height


def _col_label(n: int) -> str:
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def diff_panel(ref: Grid, mine: Grid, palette: Palette, scale: int = 16) -> Image.Image:
    mism, _ = cell_diff(ref, mine)
    ref_img = render_grid(ref, palette, scale)
    mine_img = render_grid(mine, palette, scale)
    # diff = mine, faded, with mismatched cells boxed in red
    diff = Image.new("RGBA", mine_img.size, (24, 24, 30, 255))
    faded = mine_img.copy()
    faded.putalpha(90)
    diff.alpha_composite(faded)
    d = ImageDraw.Draw(diff)
    for (x, y, _a, _b) in mism:
        d.rectangle([x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1],
                    outline=(255, 60, 60, 255), width=2)
    panels = [("TRACED REF", ref_img), ("MINE", mine_img), ("DIFF", diff)]
    pad, lh = 10, 16
    pw, ph = ref_img.width, ref_img.height + lh
    W = len(panels) * (pw + pad) + pad
    H = ph + pad * 2
    sheet = Image.new("RGBA", (W, H), (18, 18, 24, 255))
    dd = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(panels):
        x = pad + i * (pw + pad)
        dd.text((x, 2), label, fill=(235, 235, 235, 255))
        bg = Image.new("RGBA", im.size, (40, 42, 54, 255))
        bg.alpha_composite(im.convert("RGBA"))
        sheet.paste(bg, (x, lh + pad))
    return sheet


def diff_report(ref: Grid, mine: Grid) -> str:
    mism, total = cell_diff(ref, mine)
    pct = 100.0 * (total - len(mism)) / total
    lines = [f"OBSERVE  match {total - len(mism)}/{total} = {pct:.1f}%  "
             f"({len(mism)} cells off)"]
    for (x, y, a, b) in mism:
        lines.append(f"  {_col_label(x)}{y}: want {a} got {b}")
    return "\n".join(lines)
