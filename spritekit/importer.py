"""Import an existing raster image (incl. an upscaled / JPEG sprite sheet) into
the .sprite text format.

Workflow:
1. Downscale the source to its *native* pixel resolution by taking the per-channel
   median of each native-pixel block (robust against JPEG ringing and upscaling).
2. Treat near-background pixels as transparent.
3. Quantise the remaining colours to <= ``max_colors`` by greedy merge, ordered by
   frequency, producing a small stable palette.
4. Slice the native image into ``cols x rows`` cells and emit one Grid per cell,
   recording each cell's coordinates on the sheet.
"""

from __future__ import annotations

import statistics
from pathlib import Path

from PIL import Image

from .grid import TRANSPARENT_CHAR, Grid
from .palette import Palette, rgb_to_hex

# Characters assigned to palette colours in the generated legend (skip ambiguous
# I/O/0/1 to keep grids readable in monospace).
_CHAR_POOL = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _block_median(px, x0: int, y0: int, bw: int, bh: int) -> tuple[int, int, int, int]:
    """Per-channel median over a block, RGBA. Transparent samples (a<128) are
    excluded from the RGB median so colour isn't pulled toward the backdrop."""
    rs, gs, bs, as_ = [], [], [], []
    for yy in range(y0, y0 + bh):
        for xx in range(x0, x0 + bw):
            r, g, b, a = px[xx, yy]
            as_.append(a)
            if a >= 128:
                rs.append(r)
                gs.append(g)
                bs.append(b)
    alpha = int(statistics.median(as_))
    if not rs:  # fully transparent block
        return (0, 0, 0, alpha)
    return (
        int(statistics.median(rs)),
        int(statistics.median(gs)),
        int(statistics.median(bs)),
        alpha,
    )


def downscale_native(img: Image.Image, native_w: int, native_h: int) -> Image.Image:
    """Return a native_w x native_h RGBA image using per-block median sampling."""
    img = img.convert("RGBA")
    W, H = img.size
    bw, bh = W / native_w, H / native_h
    px = img.load()
    out = Image.new("RGBA", (native_w, native_h))
    opx = out.load()
    for j in range(native_h):
        for i in range(native_w):
            x0, y0 = int(round(i * bw)), int(round(j * bh))
            x1, y1 = int(round((i + 1) * bw)), int(round((j + 1) * bh))
            opx[i, j] = _block_median(px, x0, y0, max(1, x1 - x0), max(1, y1 - y0))
    return out


def _dist2(a, b) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def quantize_colors(
    colors_with_counts: list[tuple[tuple[int, int, int], int]],
    max_colors: int,
    merge_tol: int = 40,
) -> list[tuple[int, int, int]]:
    """Greedy frequency-ordered merge into <= max_colors representative colours."""
    ordered = sorted(colors_with_counts, key=lambda c: -c[1])
    reps: list[tuple[int, int, int]] = []
    tol2 = merge_tol * merge_tol
    for color, _count in ordered:
        if any(_dist2(color, r) <= tol2 for r in reps):
            continue
        reps.append(color)
    if len(reps) > max_colors:
        reps = reps[:max_colors]
    return reps


def import_sheet(
    path: str | Path,
    native_w: int,
    native_h: int,
    cols: int,
    rows: int,
    palette_name: str,
    max_colors: int = 16,
    bg: tuple[int, int, int] = (255, 255, 255),
    bg_tol: int = 32,
    merge_tol: int = 40,
    palette: Palette | None = None,
) -> tuple[Palette, list[tuple[Grid, dict]]]:
    """Import a sheet. Returns the (possibly generated) palette and a list of
    (Grid, coords) where coords = {x, y, w, h} in native pixels."""
    src = Image.open(path)
    native = downscale_native(src, native_w, native_h)
    px = native.load()
    bg_tol2 = bg_tol * bg_tol

    def is_bg(c) -> bool:
        # c is RGBA; transparent pixels or near-background colour count as bg.
        if c[3] < 128:
            return True
        return _dist2(c[:3], bg) <= bg_tol2

    # Build / reuse palette.
    if palette is None:
        counts: dict[tuple[int, int, int], int] = {}
        for y in range(native_h):
            for x in range(native_w):
                c = px[x, y]
                if is_bg(c):
                    continue
                rgb = c[:3]
                counts[rgb] = counts.get(rgb, 0) + 1
        reps = quantize_colors(list(counts.items()), max_colors, merge_tol)
        colors = {f"c{idx:02d}": rgb_to_hex(rgb) for idx, rgb in enumerate(reps)}
        palette = Palette(palette_name, colors)

    opaque = palette.opaque_names()
    # Map each opaque colour name to a legend char.
    name_to_char = {name: _CHAR_POOL[i] for i, name in enumerate(opaque)}
    legend = {TRANSPARENT_CHAR: "transparent"}
    legend.update({ch: name for name, ch in name_to_char.items()})

    cell_w, cell_h = native_w // cols, native_h // rows
    results: list[tuple[Grid, dict]] = []
    for r in range(rows):
        for ccol in range(cols):
            ox, oy = ccol * cell_w, r * cell_h
            grid_rows: list[str] = []
            for y in range(cell_h):
                line = []
                for x in range(cell_w):
                    c = px[ox + x, oy + y]
                    if is_bg(c):
                        line.append(TRANSPARENT_CHAR)
                    else:
                        line.append(name_to_char[palette.nearest_name(c[:3])])
                grid_rows.append("".join(line))
            name = f"{palette_name}_r{r}_c{ccol}"
            grid = Grid(name, cell_w, cell_h, palette.name, legend, grid_rows)
            coords = {"x": ox, "y": oy, "w": cell_w, "h": cell_h}
            results.append((grid, coords))
    return palette, results
