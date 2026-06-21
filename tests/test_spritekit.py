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


def test_layers_classify_roles_and_override():
    from spritekit import layers as L
    pal = Palette("t", {
        "outline": "#1a1426", "skin": "#f0c49a", "skin_shadow": "#c77d68",
        "tunic": "#b83040", "tunic_light": "#e06080", "highlight": "#ffffff",
    })
    g = Grid("c", 4, 4, "t",
             {"o": "outline", "s": "skin", "d": "skin_shadow",
              "t": "tunic", "l": "tunic_light", "h": "highlight"},
             ["oooo", "sdtl", "sdtl", "ohho"])
    info = L.classify(g, pal)
    assert info["outline"]["role"] == "outline"
    assert info["skin"]["role"] == "base"
    assert info["skin_shadow"]["role"] == "shadow"
    assert info["tunic_light"]["role"] == "light"
    assert info["highlight"]["role"] == "highlight"
    # shadow tier is negative, light tier positive
    assert info["skin_shadow"]["tier"] < 0 < info["tunic_light"]["tier"]
    # an edited sidecar overrides the auto-guess
    info2 = L.classify(g, pal, overrides={"skin_shadow": {"role": "light", "tier": 1}})
    assert info2["skin_shadow"]["role"] == "light"
    # the model carries materials + per-colour roles for editing
    m = L.model(g, pal, info)
    assert m["colors"]["tunic"]["material"] == "tunic"
    assert "skin" in m["materials"]


def test_auto_shade_is_directional():
    from spritekit.shade import auto_shade
    pal = Palette("t", {"m": "#808080", "m_shadow": "#404040", "m_light": "#c0c0c0"})
    # a 7-wide bar of one material; light from the left
    g = Grid("bar", 7, 1, "t", {"a": "m"}, ["aaaaaaa"])
    out = auto_shade(g, pal, light="left", highlights=False)
    names = [out.color_at(x, 0) for x in range(7)]
    # toward the light (left) is lit, away (right) is shadow, middle keeps base
    assert names[0] == "m_light"
    assert names[6] == "m_shadow"
    assert names[3] == "m"
    # a material with no ramp colours in the palette stays flat
    flat = auto_shade(Grid("b", 7, 1, "t", {"a": "m"}, ["aaaaaaa"]),
                      Palette("t", {"m": "#808080"}), light="left")
    assert all(flat.color_at(x, 0) == "m" for x in range(7))
    # existing hand-shading (a non-base tone) is preserved, not overwritten
    g2 = Grid("h", 5, 1, "t", {"a": "m", "d": "m_shadow"}, ["daaad"])
    out2 = auto_shade(g2, pal, light="left")
    assert out2.color_at(0, 0) == "m_shadow"
    assert out2.color_at(4, 0) == "m_shadow"


def test_feature_stamps_place_parts():
    from spritekit.skeleton import Rig
    from spritekit.stamps import apply_stamps
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
    pal = Palette("t", {
        "outline": "#1a1426", "skin": "#f0c49a", "hair": "#3a5bd0",
        "hair_light": "#5aa7f9", "tunic": "#b83040", "trousers": "#555a66",
        "boots": "#6b4a2e", "trim": "#c8cdd8", "eye": "#101018",
    })
    base = rig.flesh("down_0", (64, 96), palette="t")
    before = base.opaque_names_used()
    out = apply_stamps(base, rig, "down_0", pal,
                       parts=["hair_spikes", "eyes", "collar", "belt", "boots"])
    assert (out.width, out.height) == (64, 96)
    after = out.opaque_names_used()
    # stamps introduce features the flat flesh never had
    assert "eye" in after and "trim" in after
    assert "eye" not in before
    # eyes sit on the face: an eye pixel exists within a few cells of the head joint
    hx, hy = 15 * 2, 18 * 2
    found = any(out.color_at(x, y) == "eye"
                for y in range(hy - 3, hy + 3) for x in range(hx - 4, hx + 4))
    assert found
    # back view suppresses eyes
    back = apply_stamps(base, rig, "down_0", pal, parts=["eyes"], view="up")
    assert "eye" not in back.opaque_names_used()


def test_npc_stamps_and_girth():
    from spritekit.skeleton import Rig
    from spritekit.stamps import apply_stamps
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
    pal = Palette("t", {
        "outline": "#241c20", "skin": "#e0a878", "hair": "#6b5a48",
        "tunic": "#5a6e8c", "trousers": "#6b5436", "boots": "#3a2a1a",
        "apron": "#d8c8a8", "belt": "#3a2a1a", "eye": "#101018",
    })
    base = rig.flesh("down_0", (64, 96), palette="t")
    out = apply_stamps(base, rig, "down_0", pal,
                       parts=["hair_short", "mustache", "eyes", "apron", "belt", "boots"])
    after = out.opaque_names_used()
    assert "apron" in after          # apron panel got placed over the torso
    assert "hair" in after           # a side/back hair fringe remains after balding
    # the central crown is balded back to skin
    hx, hcy = 15 * 2, 18 * 2
    crown = [out.color_at(x, y) for y in range(13 * 2 + 1, hcy + 1)
             for x in range(hx - 2, hx + 3)]
    assert "skin" in crown

    # girth fattens the torso: a wider flesh than the normal build
    def torso_px(g):
        return sum(g.color_at(x, y) in ("tunic",)
                   for y in range(g.height) for x in range(g.width))
    normal = rig.flesh("down_0", (64, 96), palette="t", girth=1.0)
    stout = rig.flesh("down_0", (64, 96), palette="t", girth=1.5)
    assert torso_px(stout) > torso_px(normal)


def test_observe_trace_roundtrip():
    from spritekit.render import render_grid
    from spritekit import observe as O
    g = Grid.parse(SPRITE)                       # 4x4 dot, red/blue on transparent
    with tempfile.TemporaryDirectory() as td:
        png = Path(td) / "d.png"
        render_grid(g, PAL, 12).save(png)        # render big, then trace back
        ref = O.trace_image(png, 4, 4, PAL)
        mism, total = O.cell_diff(ref, g)
        assert total == 16
        assert len(mism) == 0                    # a clean render traces back exactly
    # and an introduced error is reported at the right cell
    bad = Grid("b", 4, 4, "t", {"r": "red", "b": "blue"},
               ["....", ".rb.", ".bb.", "...."])  # changed one cell vs SPRITE
    mism2, _ = O.cell_diff(Grid.parse(SPRITE), bad)
    assert any(m[:2] == (1, 1) for m in mism2)


def test_proportions_measure():
    from spritekit import proportions as P
    # head 2 rows (hair), torso 3 (tunic), legs 3 (pants); 6 wide
    g = Grid("p", 6, 8, "t",
             {"h": "hair", "t": "tunic", "p": "pants", "w": "sword"},
             [".hhhh.",
              ".hhhh.",
              "tttttt",
              "tttttt",
              "tttttt",
              ".pppp.",
              ".pppp.",
              ".pppp."])
    m = P.measure(g)
    assert m["head"] == 2 and m["torso"] == 3 and m["legs"] == 3
    assert m["total"] == 8 and m["heads_tall"] == 4.0
    # a weapon column sharing no body colour is excluded via region, not counted
    g2 = Grid("p2", 6, 8, "t",
              {"h": "hair", "t": "tunic", "p": "pants", "w": "sword"},
              ["whhhh.", "w.....", "wttttt", "w.....", "wttttt",
               "w.....", "wpppp.", "w....."])
    m2 = P.measure(g2)            # the sword column is dropped (weapon region)
    assert m2["head"] == 2        # band above the first torso row (rows 0-1)
    assert m2["torso"] == 4 and m2["legs"] == 1


def main() -> int:
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
