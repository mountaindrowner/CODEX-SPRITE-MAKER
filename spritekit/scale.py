"""Smooth pixel-art upscaling (EPX / Scale2x).

Doubles a Grid's resolution while rounding diagonal "stair-step" jaggies, using
only colours already present (no blurring, no new colours). This is the classic
de-blockify pass: a 32x48 sprite becomes a smoother 64x96 one.

EPX rule for each source pixel P with 4-neighbours A(up) B(right) C(left) D(down),
producing a 2x2 output block [[1,2],[3,4]] (all default to P)::

    if C==A and C!=D and A!=B: 1 = A
    if A==B and A!=C and B!=D: 2 = B
    if D==C and D!=B and C!=A: 3 = C
    if B==D and B!=A and D!=C: 4 = D

Edges are clamped (out-of-bounds neighbour == P), which simply disables rounding
at the border.
"""

from __future__ import annotations

from .grid import TRANSPARENT_CHAR, Grid


def epx_upscale(grid: Grid, times: int = 1) -> Grid:
    """Return a copy scaled up by 2**times using the EPX/Scale2x rule."""
    out = grid
    for _ in range(max(1, times)):
        out = _epx_once(out)
    return out


def _epx_once(grid: Grid) -> Grid:
    w, h = grid.width, grid.height
    src = grid.rows

    def at(x: int, y: int) -> str:
        if 0 <= x < w and 0 <= y < h:
            return src[y][x]
        return src[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]  # clamp

    new_rows: list[str] = []
    for y in range(h):
        top: list[str] = []
        bot: list[str] = []
        for x in range(w):
            p = src[y][x]
            a, b, c, d = at(x, y - 1), at(x + 1, y), at(x - 1, y), at(x, y + 1)
            p1 = p2 = p3 = p4 = p
            if c == a and c != d and a != b:
                p1 = a
            if a == b and a != c and b != d:
                p2 = b
            if d == c and d != b and c != a:
                p3 = c
            if b == d and b != a and d != c:
                p4 = d
            top.append(p1 + p2)
            bot.append(p3 + p4)
        new_rows.append("".join(top))
        new_rows.append("".join(bot))

    legend = {k: v for k, v in grid.legend.items() if k != TRANSPARENT_CHAR}
    return Grid(grid.name, w * 2, h * 2, grid.palette, legend, new_rows)
