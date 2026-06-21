"""Sprite Studio: tools for a tighter, more specific feedback loop.

Three capabilities, all built on the existing Grid/Palette:

- ``analyze`` / ``grade``  — a quantified scorecard (smoothness, symmetry, colour
  use, proportions) so vague verdicts like "too blocky" become numbers to drive.
- ``parts_sheet``          — isolate each named PART (a group of materials: hair,
  face, tunic, legs, boots ...) so we can critique/iterate one asset at a time.
- ``render_labeled``       — a zoomed render with a labelled coordinate grid
  (columns A.., rows 0..) so feedback can name exact cells, e.g. "hair tip K6".
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from .grid import TRANSPARENT_CHAR, Grid
from .palette import TRANSPARENT, Palette
from .render import render_grid

GHOST = (40, 42, 54, 255)      # faint backdrop for non-selected parts
GRIDLINE = (255, 255, 255, 60)
MAJORLINE = (255, 80, 80, 130)


# ---------------------------------------------------------------- parts --------
def default_parts(grid: Grid) -> dict[str, list[str]]:
    """Each opaque material becomes its own part (fallback when no manifest)."""
    return {n: [n] for n in sorted(grid.opaque_names_used())}


def load_parts(path: str | Path) -> dict[str, list[str]]:
    return json.loads(Path(path).read_text())["parts"]


def _mask(grid: Grid, names: set[str]) -> list[list[bool]]:
    return [[grid.color_at(x, y) in names for x in range(grid.width)]
            for y in range(grid.height)]


# ------------------------------------------------------------- analyze ---------
def analyze(grid: Grid, palette: Palette) -> dict:
    W, H = grid.width, grid.height
    opaque = [[grid.color_at(x, y) != TRANSPARENT for x in range(W)] for y in range(H)]
    n_opaque = sum(r.count(True) for r in opaque)

    # bounding box + per-row left/right edges
    rows_with = [y for y in range(H) if any(opaque[y])]
    top, bot = (rows_with[0], rows_with[-1]) if rows_with else (0, 0)
    edges = []
    for y in rows_with:
        xs = [x for x in range(W) if opaque[y][x]]
        edges.append((y, xs[0], xs[-1]))
    max_w = max((r - l + 1 for _, l, r in edges), default=0)

    # edge jitter: avg row-to-row movement of the silhouette edges (lower=smoother)
    jitter = 0.0
    for (_, l0, r0), (_, l1, r1) in zip(edges, edges[1:]):
        jitter += abs(l1 - l0) + abs(r1 - r0)
    jitter = round(jitter / max(1, len(edges) - 1), 2)

    # mirror symmetry (meaningful for front/back views)
    same = tot = 0
    for y in range(H):
        for x in range(W):
            a = grid.color_at(x, y)
            b = grid.color_at(W - 1 - x, y)
            tot += 1
            if a == b:
                same += 1
    symmetry = round(100 * same / max(1, tot), 1)

    return {
        "size": f"{W}x{H}",
        "opaque_px": n_opaque,
        "fill_pct": round(100 * n_opaque / (W * H), 1),
        "colors_used": len(grid.opaque_names_used()),
        "content_box": f"rows {top}-{bot} (h={bot - top + 1}), max_w={max_w}",
        "edge_jitter_px_per_row": jitter,
        "mirror_symmetry_pct": symmetry,
    }


def grade_report(grid: Grid, palette: Palette,
                 parts: dict[str, list[str]] | None = None) -> str:
    m = analyze(grid, palette)
    lines = [f"SCORECARD  {grid.name}", "-" * 40]
    labels = {
        "size": "size",
        "opaque_px": "opaque pixels",
        "fill_pct": "fill %",
        "colors_used": "colours used",
        "content_box": "content box",
        "edge_jitter_px_per_row": "edge jitter (lower=smoother)",
        "mirror_symmetry_pct": "mirror symmetry %",
    }
    for k, lab in labels.items():
        lines.append(f"  {lab:<30} {m[k]}")
    parts = parts or default_parts(grid)
    lines.append("  parts (colours each):")
    for part, names in parts.items():
        used = sorted(set(names) & grid.opaque_names_used())
        lines.append(f"    {part:<14} {len(used)}  [{', '.join(used)}]")
    return "\n".join(lines)


# --------------------------------------------------------- labelled view -------
def render_labeled(grid: Grid, palette: Palette, scale: int = 16,
                   step: int = 4) -> Image.Image:
    """Zoomed render with a coordinate grid: columns A,B,.. rows 0,1,.."""
    sprite = render_grid(grid, palette, scale)
    # composite over ghost so transparent cells are visible
    base = Image.new("RGBA", sprite.size, (22, 24, 30, 255))
    base.alpha_composite(sprite)
    margin = 18
    canvas = Image.new("RGBA", (base.width + margin, base.height + margin),
                       (12, 12, 16, 255))
    canvas.paste(base, (margin, margin))
    d = ImageDraw.Draw(canvas)
    for cx in range(0, grid.width + 1, step):
        x = margin + cx * scale
        d.line([(x, margin), (x, canvas.height)], fill=MAJORLINE, width=1)
        if cx < grid.width:
            d.text((x + 2, 4), _col_label(cx), fill=(220, 220, 220, 255))
    for cy in range(0, grid.height + 1, step):
        y = margin + cy * scale
        d.line([(margin, y), (canvas.width, y)], fill=MAJORLINE, width=1)
        if cy < grid.height:
            d.text((2, y + 1), str(cy), fill=(220, 220, 220, 255))
    return canvas


def _col_label(n: int) -> str:
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


# --------------------------------------------------------- parts sheet ---------
def _render_part(grid: Grid, palette: Palette, names: set[str], scale: int) -> Image.Image:
    img = Image.new("RGBA", (grid.width, grid.height), GHOST)
    px = img.load()
    for y in range(grid.height):
        for x in range(grid.width):
            name = grid.color_at(x, y)
            if name == TRANSPARENT:
                continue
            rgb = palette.rgb(name)
            if rgb is None:
                continue
            if name in names:
                px[x, y] = (rgb[0], rgb[1], rgb[2], 255)
            else:
                # ghost the rest so the part is seen in context
                px[x, y] = (90, 92, 104, 255)
    return img.resize((grid.width * scale, grid.height * scale), Image.NEAREST)


def parts_sheet(grid: Grid, palette: Palette,
                parts: dict[str, list[str]] | None = None,
                scale: int = 6) -> Image.Image:
    parts = parts or default_parts(grid)
    panels: list[tuple[str, Image.Image]] = [
        ("FULL", render_grid(grid, palette, scale))
    ]
    for part, names in parts.items():
        panels.append((part, _render_part(grid, palette, set(names), scale)))
    pad, label_h = 8, 14
    pw = grid.width * scale
    ph = grid.height * scale + label_h
    cols = min(len(panels), 5)
    rows = (len(panels) + cols - 1) // cols
    W = cols * (pw + pad) + pad
    H = rows * (ph + pad) + pad
    sheet = Image.new("RGBA", (W, H), (18, 18, 24, 255))
    d = ImageDraw.Draw(sheet)
    for i, (label, img) in enumerate(panels):
        r, c = divmod(i, cols)
        x = pad + c * (pw + pad)
        y = pad + r * (ph + pad)
        d.text((x, y), label, fill=(230, 230, 230, 255))
        bg = Image.new("RGBA", img.size, (28, 30, 38, 255))
        bg.alpha_composite(img)
        sheet.paste(bg, (x, y + label_h))
    return sheet
