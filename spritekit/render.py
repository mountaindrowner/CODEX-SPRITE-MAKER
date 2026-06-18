"""Render a Grid to a PIL image (and PNG files)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .grid import Grid
from .palette import TRANSPARENT, Palette


def render_grid(grid: Grid, palette: Palette, scale: int = 1) -> Image.Image:
    """Render at native resolution, then nearest-neighbour scale up."""
    img = Image.new("RGBA", (grid.width, grid.height), (0, 0, 0, 0))
    px = img.load()
    for y in range(grid.height):
        for x in range(grid.width):
            name = grid.color_at(x, y)
            if name == TRANSPARENT:
                continue
            rgb = palette.rgb(name)
            if rgb is None:
                continue
            px[x, y] = (rgb[0], rgb[1], rgb[2], 255)
    if scale != 1:
        img = img.resize((grid.width * scale, grid.height * scale), Image.NEAREST)
    return img


def render_to_png(
    grid: Grid, palette: Palette, out_path: str | Path, scale: int = 1
) -> Path:
    out_path = Path(out_path)
    render_grid(grid, palette, scale).save(out_path)
    return out_path
