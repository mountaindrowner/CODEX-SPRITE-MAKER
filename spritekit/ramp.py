"""Hue-shifted colour ramps — the single biggest "amateur vs pro" lever.

Instead of shading a material by only darkening/lightening its value (which reads
"muddy"), rotate the HUE along the ramp: shadows shift COOLER (toward blue ~240°)
and a touch more saturated; highlights shift WARMER (toward yellow ~55°) and a
touch desaturated; value steps each way. This is what separates flat ramps from
the rich Chrono-Trigger look.

A ramp config (JSON) declares base colours, which materials get ramps, and which
stay flat; `expand` produces a full palette ready to write as ``palette.json``::

    {
      "name": "kael",
      "flat":  {"outline": "#1a1426", "trim": "#c8cdd8", "boots": "#6b4a2e"},
      "bases": {"hair": "#3a5bd0", "skin": "#f0c49a", "tunic": "#b83040"},
      "ramps": {"hair": {"down": 1, "up": 1}, "skin": {"down": 1}}
    }

Generated names are ``<base>``, ``<base>_shadow``[``2``..], ``<base>_light``[..].
"""

from __future__ import annotations

import colorsys
import math

from .palette import hex_to_rgb, rgb_to_hex

COOL = 240.0   # shadows rotate toward blue
WARM = 55.0    # highlights rotate toward yellow


def _toward(h: float, anchor: float, amount: float) -> float:
    """Rotate hue ``h`` toward ``anchor`` by ``amount`` degrees (short arc)."""
    d = ((anchor - h + 180) % 360) - 180
    if d == 0:
        return h % 360
    return (h + math.copysign(min(amount, abs(d)), d)) % 360


def shade(base_hex: str, step: int, *, hue_shift: float = 16.0,
          val_step: float = 0.16, sat_step: float = 0.12) -> str:
    """One ramp entry. step<0 = shadow (darker/cooler), step>0 = highlight."""
    r, g, b = hex_to_rgb(base_hex)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    k = abs(step)
    if step < 0:
        v = max(0.0, v - k * val_step)
        h = _toward(h, COOL, k * hue_shift)
        s = min(1.0, s + k * sat_step)          # shadows a bit richer
    elif step > 0:
        v = min(1.0, v + k * val_step)
        h = _toward(h, WARM, k * hue_shift)
        s = max(0.0, s - k * sat_step * 0.7)     # highlights a bit softer
    rr, gg, bb = colorsys.hsv_to_rgb((h % 360) / 360, s, v)
    return rgb_to_hex((round(rr * 255), round(gg * 255), round(bb * 255)))


def expand(config: dict, **kw) -> dict:
    """Turn a ramp config into a full {name: hex} palette colours dict."""
    colors: dict[str, str | None] = {"transparent": None}
    colors.update(config.get("flat", {}))
    bases = config.get("bases", {})
    ramps = config.get("ramps", {})
    for name, base in bases.items():
        colors[name] = base
        spec = ramps.get(name, {})
        for k in range(1, spec.get("down", 0) + 1):
            colors[f"{name}_shadow" if k == 1 else f"{name}_shadow{k}"] = shade(base, -k, **kw)
        for k in range(1, spec.get("up", 0) + 1):
            colors[f"{name}_light" if k == 1 else f"{name}_light{k}"] = shade(base, k, **kw)
    return colors
