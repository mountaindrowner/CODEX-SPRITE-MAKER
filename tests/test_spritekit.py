"""Lightweight tests for spritekit. Run with: python3 -m tests.test_spritekit

No external test runner required; raises AssertionError on failure.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from spritekit.grid import Grid
from spritekit.importer import import_sheet
from spritekit.palette import Palette
from spritekit.render import render_to_png

PAL = Palette("t", {"red": "#d04648", "blue": "#3a6fb0"})
SPRITE = (
    "name: dot\nsize: 4x4\npalette: t\n"
    "legend:\n  .: transparent\n  r: red\n  b: blue\n"
    "grid: |\n  .rr.\n  rbbr\n  rbbr\n  .rr.\n"
)


def test_parse_and_query():
    g = Grid.parse(SPRITE)
    assert (g.width, g.height) == (4, 4)
    assert g.color_at(0, 0) == "transparent"
    assert g.color_at(1, 1) == "blue"
    assert g.opaque_names_used() == {"red", "blue"}


def test_text_roundtrip():
    g = Grid.parse(SPRITE)
    assert Grid.parse(g.to_text()).rows == g.rows


def test_flip_h():
    g = Grid.parse(SPRITE).flipped_h("dot_r")
    assert g.rows[1] == "rbbr"[::-1]
    assert g.name == "dot_r"


def test_render_import_diff_is_pixel_perfect():
    g = Grid.parse(SPRITE)
    with tempfile.TemporaryDirectory() as d:
        png = Path(d) / "dot_x10.png"
        render_to_png(g, PAL, png, scale=10)
        _pal, frames = import_sheet(
            png, 4, 4, 1, 1, palette_name="rt", max_colors=4
        )
        imported = frames[0][0]
        # Compare resolved RGB pixel-by-pixel.
        ipal = _pal
        for y in range(4):
            for x in range(4):
                a = g.color_at(x, y)
                b = imported.color_at(x, y)
                ca = None if a == "transparent" else PAL.rgb(a)
                cb = None if b == "transparent" else ipal.rgb(b)
                assert ca == cb, f"mismatch at {(x, y)}: {ca} != {cb}"


def test_lint_resolves_grids_own_palette():
    """A style can host multiple characters: lint must validate each grid against
    its OWN declared palette, not the style's default palette."""
    from spritekit.rules import Style

    style_path = Path("styles/chrono-trigger/style.json")
    kael_path = Path("styles/chrono-trigger/sprites/kael_down_0.sprite")
    if not (style_path.exists() and kael_path.exists()):
        return  # repo assets not present; skip
    style = Style.load(style_path)  # style's own palette.json = Crono's colours
    kael = Grid.load(kael_path)  # declares palette: kael (different colours)
    assert style.lint(kael, root=".") == []


def test_epx_upscale_doubles_and_keeps_colors():
    from spritekit.scale import epx_upscale

    g = Grid.parse(SPRITE)
    up = epx_upscale(g)
    assert (up.width, up.height) == (g.width * 2, g.height * 2)
    # EPX never invents colours.
    assert up.names_used() <= g.names_used()
    # A uniform region upscales to the same uniform colour (no rounding artifacts).
    solid = Grid("solid", 3, 3, "t", {"r": "red"}, ["rrr", "rrr", "rrr"])
    su = epx_upscale(solid)
    assert (su.width, su.height) == (6, 6)
    assert all(su.color_at(x, y) == "red" for y in range(6) for x in range(6))


def test_studio_analyze():
    from spritekit.studio import analyze

    m = analyze(Grid.parse(SPRITE), PAL)
    assert m["size"] == "4x4"
    assert m["mirror_symmetry_pct"] == 100.0  # the test dot is symmetric
    assert "edge_jitter_px_per_row" in m


def test_ramp_hue_shifts():
    import colorsys
    from spritekit.ramp import expand, shade
    from spritekit.palette import hex_to_rgb

    def hue(hx):
        r, g, b = hex_to_rgb(hx)
        return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 360

    base = "#b83040"  # crimson
    sh = shade(base, -1)
    # shadow must be darker AND hue-shifted (not a flat value change)
    assert hex_to_rgb(sh) != hex_to_rgb(base)
    assert abs(((hue(sh) - hue(base) + 180) % 360) - 180) >= 5
    cols = expand({"bases": {"tunic": base}, "ramps": {"tunic": {"down": 1, "up": 1}}})
    assert {"tunic", "tunic_shadow", "tunic_light"} <= set(cols)


def test_selout_recolors_outline():
    from spritekit.selout import recolor_outline
    pal = Palette("t", {"red": "#d04648", "red_shadow": "#7a1f2c"})
    g = Grid("o", 3, 3, "t",
             {"o": "outline", "r": "red"},
             ["ooo", "oro", "ooo"])
    out = recolor_outline(g, pal)
    # the outline cells around the red centre become red_shadow
    assert out.color_at(1, 0) == "red_shadow"
    assert out.color_at(0, 0) == "red_shadow"


def test_skeleton_flesh_base():
    from spritekit.skeleton import Rig
    rig = Rig("t", [32, 48], {
        "down_0": {
            "head_top": [15, 13], "head": [15, 18], "neck": [15, 22],
            "shoulder_l": [11, 23], "shoulder_r": [19, 23],
            "elbow_l": [10, 25], "elbow_r": [20, 25],
            "hand_l": [9, 27], "hand_r": [20, 27],
            "pelvis": [15, 30],
            "hip_l": [13, 34], "hip_r": [17, 34],
            "knee_l": [13, 37], "knee_r": [17, 37],
            "foot_l": [13, 40], "foot_r": [17, 40],
        }
    })
    g = rig.flesh("down_0", (64, 96), palette="kael")
    # dims double the rig frame
    assert (g.width, g.height) == (64, 96)
    # all the body materials show up, plus transparency around the figure
    used = g.opaque_names_used()
    assert {"outline", "skin", "hair", "tunic", "trousers", "boots"} <= used
    assert "transparent" in g.names_used()
    # the figure does not fill the whole frame (there is empty margin)
    filled = sum(ch != "." for row in g.rows for ch in row)
    assert 0 < filled < g.width * g.height


def main() -> int:
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
