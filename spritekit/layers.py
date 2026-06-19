"""Layer decomposition: identify every construction layer of a sprite.

Finished pixel art is built up in layers, the way the master guide teaches:

    skeleton -> silhouette -> outline -> flat colour -> shading -> light -> highlights

This module reverse-engineers that stack from a finished `.sprite`: it classifies
every palette colour into a **material** (skin, hair, tunic ...) and a **role/tier**
(outline / base / shadow / light / highlight), infers the **light direction**, and
renders an exploded, labelled breakdown so the construction is legible.

The classification is a heuristic — so it is also **correctable**. ``write_sidecar``
emits a ``*.layers.json`` mapping every colour to its detected material/role/tier;
edit that file and pass it back with ``--apply`` to override the guesses. That file
is "the place to correct".
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from .grid import Grid
from .palette import TRANSPARENT, Palette, hex_to_rgb
from .selout import base_of

# Construction order — also the order panels are drawn in the breakdown sheet.
LAYER_ORDER = ["silhouette", "outline", "flats", "shading", "light", "highlights"]
ROLE_OF_LAYER = {"flats": "base", "shading": "shadow", "light": "light",
                 "highlights": "highlight"}

GHOST = (44, 46, 58, 255)
EMPTY = (90, 92, 104, 255)   # ghosted "other" pixels, so a layer is seen in context


def _lum(rgb: tuple[int, int, int]) -> float:
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def _role_from_suffix(name: str) -> str | None:
    if name.endswith(("_shadow", "_shadow2")):
        return "shadow"
    if name.endswith(("_light", "_light2")):
        return "light"
    if name.endswith("_highlight"):
        return "highlight"
    return None


def classify(grid: Grid, palette: Palette,
             overrides: dict[str, dict] | None = None,
             outline_name: str = "outline") -> dict[str, dict]:
    """Map each opaque colour name -> {material, role, tier, hex, px}.

    Heuristics, in order: explicit name suffix (``_shadow``/``_light``), then a
    per-material luminance ranking relative to the material's most-used tone.
    ``overrides`` (a colour-name -> partial dict) wins over everything.
    """
    overrides = overrides or {}
    names = sorted(grid.opaque_names_used())
    counts = {n: 0 for n in names}
    for row in grid.rows:
        for chx in row:
            nm = grid.legend[chx]
            if nm in counts:
                counts[nm] += 1

    info: dict[str, dict] = {}
    for n in names:
        rgb = palette.rgb(n) or (0, 0, 0)
        info[n] = {
            "material": base_of(n),
            "role": None,
            "tier": 0,
            "hex": "#%02x%02x%02x" % rgb,
            "px": counts[n],
            "lum": round(_lum(rgb), 1),
        }

    # 1) outline + highlight specials by name
    for n in names:
        if n == outline_name or "outline" in n:
            info[n].update(material="outline", role="outline")
        elif n == "highlight" or n.endswith("_highlight") or n == "white":
            info[n].update(role="highlight")

    # 2) explicit suffixes
    for n in names:
        if info[n]["role"]:
            continue
        r = _role_from_suffix(n)
        if r:
            info[n]["role"] = r

    # 3) per-material luminance ranking for whatever is still unroled
    by_mat: dict[str, list[str]] = {}
    for n in names:
        if info[n]["role"] in (None, "base", "shadow", "light"):
            by_mat.setdefault(info[n]["material"], []).append(n)
    for mat, group in by_mat.items():
        if mat == "outline":
            continue
        # base = the un-suffixed tone (name == material) if present, else the
        # most-used tone that isn't already tagged as a shadow/light by suffix.
        untagged = [g for g in group if info[g]["role"] is None]
        if mat in group:
            anchor = mat
        elif untagged:
            anchor = max(untagged, key=lambda g: info[g]["px"])
        else:
            anchor = max(group, key=lambda g: info[g]["px"])
        a_lum = info[anchor]["lum"]
        for n in group:
            if info[n]["role"]:           # already set by suffix
                continue
            if n == anchor:
                info[n]["role"] = "base"
            elif info[n]["lum"] < a_lum:
                info[n]["role"] = "shadow"
            else:
                info[n]["role"] = "light"

    # tiers: rank within material by luminance, base = 0
    for mat, group in by_mat.items():
        if mat == "outline":
            continue
        base = next((n for n in group if info[n]["role"] == "base"), None)
        b_lum = info[base]["lum"] if base else 0
        for n in group:
            d = info[n]["lum"] - b_lum
            info[n]["tier"] = (1 if d > 0 else -1 if d < 0 else 0) * \
                (1 if abs(d) < 60 else 2)

    for n in names:
        if info[n]["role"] is None:
            info[n]["role"] = "base"

    # 4) overrides win
    for n, ov in overrides.items():
        if n in info:
            info[n].update({k: v for k, v in ov.items()
                            if k in ("material", "role", "tier")})
    return info


def light_direction(grid: Grid, info: dict[str, dict]) -> str:
    """Infer the light source from where light/highlight vs shadow pixels sit."""
    def centroid(roles: set[str]):
        xs = ys = n = 0
        for y in range(grid.height):
            for x in range(grid.width):
                nm = grid.color_at(x, y)
                if nm != TRANSPARENT and info.get(nm, {}).get("role") in roles:
                    xs += x; ys += y; n += 1
        return (xs / n, ys / n) if n else None

    lit = centroid({"light", "highlight"})
    sha = centroid({"shadow"})
    if not lit or not sha:
        return "indeterminate (need both light and shadow tiers)"
    dx, dy = lit[0] - sha[0], lit[1] - sha[1]
    thr = max(1.0, grid.width * 0.05)
    vert = "upper" if dy < -thr else "lower" if dy > thr else ""
    horiz = "left" if dx < -thr else "right" if dx > thr else ""
    where = "-".join(p for p in (vert, horiz) if p) or "front/even"
    return f"{where} (light tiers sit {where} of the shadows)"


def model(grid: Grid, palette: Palette, info: dict[str, dict]) -> dict:
    by_mat: dict[str, list[str]] = {}
    for n, d in info.items():
        by_mat.setdefault(d["material"], []).append(n)
    ramps = {}
    for mat, group in sorted(by_mat.items()):
        ramps[mat] = sorted(group, key=lambda g: info[g]["tier"])
    return {
        "sprite": grid.name,
        "size": f"{grid.width}x{grid.height}",
        "palette": grid.palette,
        "light_direction": light_direction(grid, info),
        "layers_order": LAYER_ORDER,
        "materials": ramps,
        "colors": {n: {k: info[n][k] for k in ("material", "role", "tier", "hex", "px")}
                   for n in sorted(info)},
        "_help": "Edit a colour's material/role/tier, then re-run with --apply this file.",
    }


def report(grid: Grid, info: dict[str, dict]) -> str:
    m = model(grid, None, info)  # palette only used for ramps order, ok as None here
    lines = [f"LAYERS  {grid.name}  ({grid.width}x{grid.height})", "-" * 52,
             f"  light direction: {m['light_direction']}", ""]
    # group by role in construction order
    order = ["outline", "base", "shadow", "light", "highlight"]
    for role in order:
        members = [n for n in sorted(info) if info[n]["role"] == role]
        if not members:
            continue
        lines.append(f"  {role.upper()}")
        for n in members:
            d = info[n]
            lines.append(f"    {n:<18} {d['hex']}  {d['px']:>4}px  "
                         f"[{d['material']}, tier {d['tier']:+d}]")
    lines.append("")
    lines.append("  ramps per material (dark -> light):")
    for mat, group in m["materials"].items():
        if mat == "outline":
            continue
        chain = " -> ".join(f"{n}" for n in group)
        lines.append(f"    {mat:<12} {chain}")
    return "\n".join(lines)


# ----------------------------------------------------------- breakdown sheet ----
def _panel(grid: Grid, palette: Palette, info: dict[str, dict],
           keep, scale: int, flat=None) -> Image.Image:
    """Render one layer: pixels matching `keep(name)` in true colour (or `flat`),
    everything else opaque ghosted, transparent stays background."""
    img = Image.new("RGBA", (grid.width, grid.height), GHOST)
    px = img.load()
    for y in range(grid.height):
        for x in range(grid.width):
            name = grid.color_at(x, y)
            if name == TRANSPARENT:
                continue
            if keep(name):
                if flat:
                    px[x, y] = flat
                else:
                    rgb = palette.rgb(name) or (0, 0, 0)
                    px[x, y] = (rgb[0], rgb[1], rgb[2], 255)
            else:
                px[x, y] = EMPTY
    return img.resize((grid.width * scale, grid.height * scale), Image.NEAREST)


def _value_map(grid: Grid, palette: Palette, scale: int) -> Image.Image:
    """Grayscale luminance map — reveals the value/shading logic on its own."""
    img = Image.new("RGBA", (grid.width, grid.height), (16, 16, 20, 255))
    px = img.load()
    for y in range(grid.height):
        for x in range(grid.width):
            name = grid.color_at(x, y)
            if name == TRANSPARENT:
                continue
            v = int(_lum(palette.rgb(name) or (0, 0, 0)))
            px[x, y] = (v, v, v, 255)
    return img.resize((grid.width * scale, grid.height * scale), Image.NEAREST)


def breakdown_sheet(grid: Grid, palette: Palette, info: dict[str, dict],
                    scale: int = 6, rig=None, pose: str | None = None) -> Image.Image:
    from .render import render_grid

    def role_is(*roles):
        rs = set(roles)
        return lambda n: info.get(n, {}).get("role") in rs

    panels: list[tuple[str, Image.Image]] = []
    panels.append(("1 FULL", render_grid(grid, palette, scale)))
    if rig is not None and pose:
        base = render_grid(grid, palette, scale)
        panels.append(("2 SKELETON", rig.overlay(pose, base, scale)))
    panels.append(("3 SILHOUETTE", _panel(grid, palette, info, lambda n: True,
                                          scale, flat=(176, 180, 205, 255))))
    panels.append(("4 OUTLINE", _panel(grid, palette, info, role_is("outline"), scale)))
    panels.append(("5 FLATS", _panel(grid, palette, info, role_is("base"), scale)))
    panels.append(("6 SHADING", _panel(grid, palette, info, role_is("shadow"), scale)))
    panels.append(("7 LIGHT", _panel(grid, palette, info, role_is("light"), scale)))
    panels.append(("8 HIGHLIGHTS", _panel(grid, palette, info, role_is("highlight"), scale)))
    panels.append(("9 VALUE MAP", _value_map(grid, palette, scale)))

    pad, label_h = 8, 14
    pw, ph = grid.width * scale, grid.height * scale + label_h
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
        d.text((x, y), label, fill=(232, 232, 232, 255))
        bg = Image.new("RGBA", img.size, (28, 30, 38, 255))
        bg.alpha_composite(img.convert("RGBA"))
        sheet.paste(bg, (x, y + label_h))
    return sheet


def write_sidecar(path: str | Path, m: dict) -> None:
    Path(path).write_text(json.dumps(m, indent=2) + "\n")


def load_overrides(path: str | Path) -> dict[str, dict]:
    data = json.loads(Path(path).read_text())
    return data.get("colors", data)
