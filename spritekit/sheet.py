"""Assemble individual frames into a packed sprite sheet + coordinate manifest."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from .grid import Grid
from .palette import Palette
from .render import render_grid


def build_sheet(
    grids: list[Grid],
    palette: Palette,
    cols: int,
    scale: int = 1,
    padding: int = 0,
) -> tuple[Image.Image, dict]:
    """Lay frames out row-major in a ``cols``-wide grid. All frames must share a
    size. Returns (image, coords) where coords maps frame name -> native x/y/w/h."""
    if not grids:
        raise ValueError("no frames to assemble")
    w, h = grids[0].width, grids[0].height
    for g in grids:
        if (g.width, g.height) != (w, h):
            raise ValueError(f"frame {g.name} size {(g.width, g.height)} != {(w, h)}")

    rows = (len(grids) + cols - 1) // cols
    cell_w, cell_h = w + padding, h + padding
    sheet_w, sheet_h = cols * cell_w - padding, rows * cell_h - padding
    sheet = Image.new("RGBA", (sheet_w * scale, sheet_h * scale), (0, 0, 0, 0))

    coords: dict[str, dict] = {}
    for idx, g in enumerate(grids):
        r, c = divmod(idx, cols)
        x, y = c * cell_w, r * cell_h
        sheet.paste(render_grid(g, palette, scale), (x * scale, y * scale))
        coords[g.name] = {"x": x, "y": y, "w": w, "h": h, "index": idx}
    manifest = {
        "frame_size": [w, h],
        "cols": cols,
        "rows": rows,
        "scale": scale,
        "padding": padding,
        "frames": coords,
    }
    return sheet, manifest


def save_sheet(
    grids: list[Grid],
    palette: Palette,
    out_png: str | Path,
    cols: int,
    scale: int = 1,
    padding: int = 0,
    coords_path: str | Path | None = None,
) -> dict:
    sheet, manifest = build_sheet(grids, palette, cols, scale, padding)
    sheet.save(out_png)
    if coords_path is None:
        coords_path = Path(out_png).with_suffix(".coords.json")
    Path(coords_path).write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
