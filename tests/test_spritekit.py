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


def main() -> int:
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
