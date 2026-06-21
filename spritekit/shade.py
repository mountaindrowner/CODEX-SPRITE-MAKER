"""Auto-shade: build the lit form up from flat colour (the inverse of `layers`).

`layers` decomposes a finished sprite into its construction layers. This composes
the top of that stack: given a *flat*-coloured sprite (e.g. a skeleton flesh base),
it places the shadow tier, light tier, and highlights procedurally from a single
**light direction** and the palette's per-material ramps.

The model is **directional form-shading, not pillow-shading**. Each material's mass
is projected onto the light axis: the third of the mass *toward* the light becomes
``_light``, the third *away* becomes ``_shadow``, the middle keeps the base tone.
That keys the values to one light vector (the pro tell) instead of darkening every
edge equally (the amateur tell the guide warns against). On top, the convex edge
pixels that directly face the light get a ``_highlight``/``highlight`` dab.

Only base tones are touched, so any existing hand-shading is preserved, and a tier
is applied only when that ramp colour exists in the palette (so a material with no
``_shadow`` simply stays flat there).
"""

from __future__ import annotations

from .grid import TRANSPARENT, TRANSPARENT_CHAR, Grid
from .palette import Palette
from .selout import _CHAR_POOL, base_of

# unit vector pointing TOWARD the light source (x, y); y grows downward
LIGHTS = {
    "top": (0, -1), "bottom": (0, 1), "left": (-1, 0), "right": (1, 0),
    "top-left": (-1, -1), "top-right": (1, -1),
    "bottom-left": (-1, 1), "bottom-right": (1, 1),
}


def auto_shade(grid: Grid, palette: Palette, light: str = "top-left",
               highlights: bool = True, outline_name: str = "outline",
               shadow_frac: float = 0.34, light_frac: float = 0.34) -> Grid:
    if light not in LIGHTS:
        raise ValueError(f"unknown light {light!r}; pick one of {sorted(LIGHTS)}")
    lx, ly = LIGHTS[light]
    W, H = grid.width, grid.height

    legend = dict(grid.legend)
    name_to_char = {v: k for k, v in legend.items()}
    free = [c for c in _CHAR_POOL if c not in legend]

    def char_for(name: str) -> str | None:
        """Legend char for a colour name; allocate one if the colour exists."""
        if name in name_to_char:
            return name_to_char[name]
        if name not in palette.colors or not free:
            return None
        ch = free.pop(0)
        legend[ch] = name
        name_to_char[name] = ch
        return ch

    def boundary(x: int, y: int) -> bool:
        """True at the form's edge: off-grid, transparent, or the outline."""
        if not (0 <= x < W and 0 <= y < H):
            return True
        n = grid.color_at(x, y)
        return n == TRANSPARENT or n == outline_name

    # group base-tone pixels by material and project them onto the light axis.
    # projection s = x*lx + y*ly; higher s == closer to the light side.
    mats: dict[str, list[tuple[int, int, int]]] = {}
    for y in range(H):
        for x in range(W):
            name = grid.color_at(x, y)
            if name in (TRANSPARENT, outline_name):
                continue
            if name != base_of(name):     # already a tier -> leave hand-shading
                continue
            mats.setdefault(base_of(name), []).append((x * lx + y * ly, x, y))

    rows = [list(r) for r in grid.rows]
    for m, pts in mats.items():
        ss = [s for s, _, _ in pts]
        smin, smax = min(ss), max(ss)
        rng = smax - smin
        if rng <= 0:
            continue
        lo = smin + rng * shadow_frac          # below -> shadow
        hi = smax - rng * light_frac           # above -> light
        for s, x, y in pts:
            target = None
            if s <= lo:
                target = f"{m}_shadow"
            elif s >= hi:
                target = f"{m}_light"
                if highlights and boundary(x + lx, y) and boundary(x, y + ly):
                    for cand in (f"{m}_highlight", "highlight"):
                        if cand in palette.colors:
                            target = cand
                            break
            if not target or target not in palette.colors:
                continue
            ch = char_for(target)
            if ch:
                rows[y][x] = ch

    legend = {k: v for k, v in legend.items() if k != TRANSPARENT_CHAR}
    return Grid(grid.name, W, H, grid.palette, legend, ["".join(r) for r in rows])
