"""Selective outline recolouring (sel-out / colored line work).

Pure-black outlines on lit interior edges are a classic "amateur" tell. The
Chrono-Trigger look recolours the outline to a darker shade of the material it
borders, which makes the sprite read rich and integrated rather than stickered.

`recolor_outline` is a deterministic grid->grid pass: each ``outline`` cell is
retinted to the ``<material>_shadow`` of its dominant neighbouring material (when
that shade exists in the palette); outlines bordering only materials without a
shadow ramp (e.g. boots, trim) — and the ground/foot shadow — stay dark.
"""

from __future__ import annotations

from .grid import TRANSPARENT, TRANSPARENT_CHAR, Grid
from .palette import Palette

_SUFFIXES = ("_shadow2", "_light2", "_shadow", "_light")
_NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
_CHAR_POOL = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ0123456789"


def base_of(name: str) -> str:
    for suf in _SUFFIXES:
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


def recolor_outline(grid: Grid, palette: Palette, outline_name: str = "outline") -> Grid:
    legend = dict(grid.legend)                       # char -> name (mutable copy)
    name_to_char = {v: k for k, v in legend.items()}
    free = [c for c in _CHAR_POOL if c not in legend]
    W, H = grid.width, grid.height
    rows = [list(r) for r in grid.rows]
    for y in range(H):
        for x in range(W):
            if grid.color_at(x, y) != outline_name:
                continue
            counts: dict[str, int] = {}
            for dx, dy in _NEIGHBORS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H:
                    nm = grid.color_at(nx, ny)
                    if nm not in (TRANSPARENT, outline_name):
                        counts[base_of(nm)] = counts.get(base_of(nm), 0) + 1
            if not counts:
                continue
            target = f"{max(counts, key=counts.get)}_shadow"
            if target not in palette.colors:
                continue
            if target not in name_to_char:        # give the shade a legend char
                if not free:
                    continue
                ch = free.pop(0)
                legend[ch] = target
                name_to_char[target] = ch
            rows[y][x] = name_to_char[target]
    legend = {k: v for k, v in legend.items() if k != TRANSPARENT_CHAR}
    return Grid(grid.name, W, H, grid.palette, legend, ["".join(r) for r in rows])
