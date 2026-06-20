"""Feature stamps: parametric parts placed on a flesh base from the rig pose.

The skeleton ``--flesh`` pass gives a clean capsule body but no *features*. This
module crosses that gap deterministically: each stamp reads a joint from the posed
rig (scaled to the sprite) and draws a feature there — eyes at the head, spiky hair
above ``head_top``, a belt at the pelvis, shaped boots at the feet. It is the
repeatable half of the hybrid detail pass; an agent then polishes what remains.

Stamps are **view-aware** (front ``down`` gets two eyes, ``left`` one, back ``up``
none) and **palette-gated** (a stamp colour that isn't in the palette is skipped),
so the same parts list works across a whole walk cycle and across characters.
"""

from __future__ import annotations

from .grid import TRANSPARENT, TRANSPARENT_CHAR, Grid
from .palette import Palette
from .selout import _CHAR_POOL

DEFAULT_PARTS = ["hair_spikes", "eyes", "collar", "belt", "boots"]


class _Canvas:
    """Mutable view over a Grid that allocates legend chars on demand."""

    def __init__(self, grid: Grid, palette: Palette):
        self.W, self.H = grid.width, grid.height
        self.rows = [list(r) for r in grid.rows]
        self.legend = dict(grid.legend)
        self.name_to_char = {v: k for k, v in self.legend.items()}
        self.free = [c for c in _CHAR_POOL if c not in self.legend]
        self.palette = palette
        self.grid = grid

    def char(self, name: str) -> str | None:
        if name in self.name_to_char:
            return self.name_to_char[name]
        if name not in self.palette.colors or not self.free:
            return None
        ch = self.free.pop(0)
        self.legend[ch] = name
        self.name_to_char[name] = ch
        return ch

    def name_at(self, x: int, y: int) -> str:
        if 0 <= x < self.W and 0 <= y < self.H:
            return self.legend.get(self.rows[y][x], TRANSPARENT)
        return TRANSPARENT

    def opaque(self, x: int, y: int) -> bool:
        return self.name_at(x, y) not in (TRANSPARENT,)

    def set(self, x: int, y: int, name: str, only_over: set[str] | None = None) -> None:
        if not (0 <= x < self.W and 0 <= y < self.H):
            return
        if only_over is not None and self.name_at(x, y) not in only_over:
            return
        ch = self.char(name)
        if ch:
            self.rows[y][x] = ch

    def to_grid(self) -> Grid:
        legend = {k: v for k, v in self.legend.items() if k != TRANSPARENT_CHAR}
        return Grid(self.grid.name, self.W, self.H, self.grid.palette, legend,
                    ["".join(r) for r in self.rows])


def _first(palette: Palette, *names: str) -> str | None:
    for n in names:
        if n in palette.colors:
            return n
    return None


# ---- individual stamps -------------------------------------------------------
def _eyes(c: _Canvas, J, view, mul, pal):
    if view == "up":
        return
    eye = _first(pal, "eye", "outline") or "outline"
    spark = _first(pal, "highlight", "eye_light", "white")
    hx, hy = J["head"]
    dx = max(1, round(mul * 1.1))
    h = max(1, round(mul * 0.9))
    xs = [hx - dx] if view == "left" else [hx - dx, hx + dx]
    for ex in xs:
        for k in range(h):
            c.set(ex, hy - 1 + k, eye, only_over={"skin", "skin_shadow", "skin_light"})
        if spark:  # a dab of white in the top of the eye
            c.set(ex, hy - 1, spark, only_over={c.name_at(ex, hy - 1)})


def _hair_spikes(c: _Canvas, J, view, mul, pal):
    hair = _first(pal, "hair") or "hair"
    tip = _first(pal, "hair_light", "hair") or "hair"
    htx, hty = J["head_top"]
    hair_names = {"hair", "hair_shadow", "hair_light"}

    def hair_top(x):
        """topmost hair pixel y in a column (else head_top y)."""
        for y in range(c.H):
            if c.name_at(x, y) in hair_names:
                return y
        return hty

    # a fan of upward spikes of varying height, anchored on the hair mass so
    # they always protrude above the dome (the Chrono-Trigger silhouette tell)
    spikes = [(-3, 2), (-2, 4), (-1, 3), (1, 5), (2, 3), (3, 2)]
    for ox, hgt in spikes:
        x = htx + round(ox * mul * 0.7)
        top = hair_top(x)
        h = max(2, round(hgt * mul * 0.7))
        for k in range(h):
            name = tip if k >= h - 1 else hair
            c.set(x, top - 1 - k, name, only_over={"transparent", "outline"})


def _headband(c: _Canvas, J, view, mul, pal):
    band = _first(pal, "headband", "trim")
    if not band:
        return
    hx, hy = J["head"]
    _, hty = J["head_top"]
    y = round((hty + hy) / 2)            # forehead, between crown and face
    half = max(2, round(mul * 2.6))
    over = {"skin", "skin_shadow", "skin_light", "hair", "hair_shadow", "hair_light"}
    for x in range(hx - half, hx + half + 1):
        c.set(x, y, band, only_over=over)


def _collar(c: _Canvas, J, view, mul, pal):
    trim = _first(pal, "trim", "tunic_light")
    if not trim:
        return
    sx_l, sy = J["shoulder_l"]
    sx_r, _ = J["shoulder_r"]
    y = sy
    for x in range(min(sx_l, sx_r), max(sx_l, sx_r) + 1):
        c.set(x, y, trim, only_over={"tunic", "tunic_shadow", "tunic_light"})


def _belt(c: _Canvas, J, view, mul, pal):
    trim = _first(pal, "belt", "trim", "trousers_shadow")
    if not trim:
        return
    px, py = J["pelvis"]
    half = max(2, round(mul * 3))
    for x in range(px - half, px + half + 1):
        for k in range(max(1, round(mul * 0.6))):
            c.set(x, py + k, trim, only_over={"tunic", "tunic_shadow", "trousers"})


def _boots(c: _Canvas, J, view, mul, pal):
    sole = _first(pal, "boots_shadow", "outline") or "outline"
    boot = _first(pal, "boots") or "boots"
    # face direction: shoes point toward the facing
    face = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}.get(view, (0, 1))
    for fk in ("foot_l", "foot_r"):
        fx, fy = J[fk]
        # toe: extend the boot one cell toward the facing
        tx, ty = fx + face[0], fy + face[1]
        c.set(tx, ty, boot, only_over={"transparent", "boots", "outline"})
        c.set(tx + face[0], ty + face[1], sole, only_over={"transparent", "boots", "outline"})
        # sole line just under a down/side foot
        if view in ("down", "left", "right"):
            c.set(fx, fy + 1, sole, only_over={"boots", "transparent"})


STAMPS = {
    "eyes": _eyes, "hair_spikes": _hair_spikes, "headband": _headband,
    "collar": _collar, "belt": _belt, "boots": _boots,
}


def apply_stamps(grid: Grid, rig, pose: str, palette: Palette,
                 parts: list[str] | None = None, view: str | None = None) -> Grid:
    parts = parts or DEFAULT_PARTS
    view = view or pose.split("_")[0]
    mul = grid.width / rig.frame_size[0]
    joints = rig.poses[pose]
    J = {name: (round(x * mul), round(y * mul)) for name, (x, y) in joints.items()}
    c = _Canvas(grid, palette)
    for part in parts:
        fn = STAMPS.get(part)
        if fn:
            fn(c, J, view, mul, palette)
    return c.to_grid()
