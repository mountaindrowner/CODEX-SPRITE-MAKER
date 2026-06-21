"""Proportions: quantify a sprite's body plan (head/torso/leg ratios, heads-tall).

Vague feedback like "the head's too big" becomes numbers: head/torso/leg heights
as a percentage of the figure, how many heads tall it is, head-vs-body width, and
the face pixel count. Measured by **row bands** — the head is the rows above the
first torso row, legs are the rows from the first leg material down — which is
robust to a material appearing in a few scattered cells.

The one thing that fools a band measure is a **weapon that shares a body colour**
(a spear shaft tinted like the boots, a blade tinted like the trim): it adds cells
in the wrong rows. Give weapons their own colours, or list them with ``ignore=`` so
they're dropped before measuring.
"""

from __future__ import annotations

from .grid import TRANSPARENT, Grid
from .selout import base_of

# material base-name -> body region. Covers the project's palettes; extend via
# the region_overrides argument if a character names parts differently.
HEAD = {"hair", "skin", "eye", "eyes", "face", "ear", "beard", "mustache",
        "hood", "hat", "helm", "helmet", "cap"}
TORSO = {"tunic", "shirt", "robe", "vest", "trim", "belt", "sash", "glove",
         "apron", "collar", "cape", "arm", "hand", "chest", "shoulder", "headband"}
LEGS = {"pants", "trousers", "leg", "legs", "boots", "boot", "shoe", "skirt", "foot"}
GROUND = {"base", "shadow", "ground", "drop"}
WEAPON = {"sword", "spear", "staff", "steel", "shaft", "blade", "bow", "weapon",
          "axe", "wand", "hilt", "gem", "orb", "crystal", "arrow", "quiver"}


def region_of(name: str, overrides: dict[str, str] | None = None) -> str:
    if overrides and name in overrides:
        return overrides[name]
    b = base_of(name)
    if b in HEAD:
        return "head"
    if b in TORSO:
        return "torso"
    if b in LEGS:
        return "legs"
    if b in GROUND:
        return "ground"
    if b in WEAPON:
        return "weapon"
    return "other"


def measure(grid: Grid, ignore: set[str] | None = None,
            overrides: dict[str, str] | None = None) -> dict:
    ignore = ignore or set()
    W, H = grid.width, grid.height

    def reg(n):
        if n in ignore:
            return "weapon"
        return region_of(n, overrides)

    # figure = opaque cells that belong to the body (drop ground + weapon)
    fig = []
    region_rows: dict[str, set[int]] = {"head": set(), "torso": set(), "legs": set()}
    face_px = 0
    for y in range(H):
        for x in range(W):
            n = grid.color_at(x, y)
            if n == TRANSPARENT:
                continue
            r = reg(n)
            if r in ("ground", "weapon"):
                continue
            fig.append((x, y))
            if r in region_rows:
                region_rows[r].add(y)
            if base_of(n) == "skin":
                face_px += 1                     # refined to the head band below

    if not fig:
        return {"empty": True}

    ys = [y for _, y in fig]
    top, bot = min(ys), max(ys)
    total = bot - top + 1
    torso_top = min(region_rows["torso"], default=bot + 1)
    leg_top = min(region_rows["legs"], default=bot + 1)
    # clamp the bands into order
    torso_top = min(torso_top, leg_top)
    head_h = max(0, torso_top - top)
    torso_h = max(0, leg_top - torso_top)
    leg_h = max(0, bot - leg_top + 1)

    def width(r0, r1):
        w = 0
        for y in range(r0, r1):
            xs = [x for x, yy in fig if yy == y]
            if xs:
                w = max(w, max(xs) - min(xs) + 1)
        return w

    head_w = width(top, torso_top)
    body_w = width(torso_top, leg_top) or width(torso_top, bot + 1)
    # face = skin only within the head band
    face = sum(1 for x, y in fig if top <= y < torso_top
               and base_of(grid.color_at(x, y)) == "skin")

    return {
        "name": grid.name, "size": f"{W}x{H}",
        "total": total, "head": head_h, "torso": torso_h, "legs": leg_h,
        "head_pct": round(100 * head_h / total),
        "torso_pct": round(100 * torso_h / total),
        "legs_pct": round(100 * leg_h / total),
        "heads_tall": round(total / head_h, 1) if head_h else None,
        "head_w": head_w, "body_w": body_w,
        "head_body_ratio": round(head_w / body_w, 2) if body_w else None,
        "face_px": face,
        "ignored": sorted(ignore),
    }


def report(m: dict) -> str:
    if m.get("empty"):
        return "PROPORTIONS  (no figure pixels found)"
    L = [f"PROPORTIONS  {m['name']}  ({m['size']})", "-" * 44,
         f"  total height   {m['total']}px",
         f"  head           {m['head']}px  ({m['head_pct']}%)   heads-tall {m['heads_tall']}",
         f"  torso          {m['torso']}px  ({m['torso_pct']}%)",
         f"  legs           {m['legs']}px  ({m['legs_pct']}%)",
         f"  head width     {m['head_w']}px   body width {m['body_w']}px   "
         f"(head/body {m['head_body_ratio']})",
         f"  face skin      {m['face_px']}px"]
    if m["ignored"]:
        L.append(f"  ignored        {', '.join(m['ignored'])}")
    # gentle guidance against the chibi look
    if m["heads_tall"] and m["heads_tall"] < 2.8:
        L.append("  note: head is large (< 2.8 heads tall) — shrink head or lengthen body")
    if m["head_body_ratio"] and m["head_body_ratio"] > 0.9:
        L.append("  note: head nearly as wide as the body — narrow the head")
    return "\n".join(L)
