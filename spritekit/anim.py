"""Assemble frames into an animated GIF for previewing a walk cycle."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .grid import Grid
from .palette import Palette
from .render import render_grid

# A flat magenta backdrop so transparent sprites are visible in the GIF preview
# (GIF transparency is finicky); tweak with ``bg``.
DEFAULT_BG = (40, 44, 52, 255)


def build_gif(
    grids: list[Grid],
    palette: Palette,
    out_path: str | Path,
    scale: int = 6,
    fps: float = 6.0,
    bg: tuple[int, int, int, int] | None = DEFAULT_BG,
    loop: int = 0,
) -> Path:
    if not grids:
        raise ValueError("no frames for gif")
    frames = []
    for g in grids:
        sprite = render_grid(g, palette, scale)
        if bg is not None:
            base = Image.new("RGBA", sprite.size, bg)
            base.alpha_composite(sprite)
            frames.append(base.convert("RGB"))
        else:
            frames.append(sprite)
    duration = int(1000 / fps)
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=loop,
        disposal=2,
    )
    return Path(out_path)
