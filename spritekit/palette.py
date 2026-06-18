"""Palette handling: named colours, hex<->rgb, and nearest-colour matching.

A palette is a JSON file of the form::

    {
      "name": "pokemon-overworld",
      "colors": {
        "transparent": null,
        "outline":     "#202020",
        "skin":        "#f8d8a8"
      }
    }

The name ``transparent`` (value ``null``) is always available even if absent.
"""

from __future__ import annotations

import json
from pathlib import Path

TRANSPARENT = "transparent"


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    if len(value) != 6:
        raise ValueError(f"bad hex colour: {value!r}")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{c:02x}" for c in rgb)


class Palette:
    def __init__(self, name: str, colors: dict[str, str | None]):
        self.name = name
        # Always allow transparent.
        self.colors: dict[str, str | None] = {TRANSPARENT: None}
        self.colors.update(colors)

    # -- IO ----------------------------------------------------------------
    @classmethod
    def load(cls, path: str | Path) -> "Palette":
        data = json.loads(Path(path).read_text())
        return cls(data.get("name", Path(path).stem), data.get("colors", {}))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps({"name": self.name, "colors": self.colors}, indent=2) + "\n"
        )

    # -- lookups -----------------------------------------------------------
    def rgb(self, name: str) -> tuple[int, int, int] | None:
        """RGB for a colour name, or None for transparent."""
        if name not in self.colors:
            raise KeyError(f"colour {name!r} not in palette {self.name!r}")
        value = self.colors[name]
        return None if value is None else hex_to_rgb(value)

    def opaque_names(self) -> list[str]:
        return [n for n, v in self.colors.items() if v is not None]

    def nearest_name(self, rgb: tuple[int, int, int]) -> str:
        """Name of the closest opaque colour by squared Euclidean distance."""
        best, best_d = None, None
        for name in self.opaque_names():
            cr, cg, cb = hex_to_rgb(self.colors[name])  # type: ignore[arg-type]
            d = (cr - rgb[0]) ** 2 + (cg - rgb[1]) ** 2 + (cb - rgb[2]) ** 2
            if best_d is None or d < best_d:
                best, best_d = name, d
        if best is None:
            raise ValueError(f"palette {self.name!r} has no opaque colours")
        return best


def resolve_palette(
    ref: str, root: str | Path | None = None, explicit: str | None = None
) -> Palette:
    """Resolve a palette by name or path.

    Resolution order:
      1. ``explicit`` path, if given.
      2. ``ref`` as a direct ``.json`` path that exists.
      3. ``styles/<ref>/palette.json`` under ``root``.
      4. recursive search under ``styles/`` for ``<ref>-palette.json`` then ``<ref>.json``.

    This lets a single style host several characters, each declaring its own
    palette (e.g. ``palette: kael`` -> ``styles/chrono-trigger/kael-palette.json``).
    """
    root = Path(root or Path.cwd())
    if explicit:
        return Palette.load(explicit)
    p = Path(ref)
    if p.suffix == ".json" and p.exists():
        return Palette.load(p)
    cand = root / "styles" / ref / "palette.json"
    if cand.exists():
        return Palette.load(cand)
    styles = root / "styles"
    if styles.exists():
        for pattern in (f"{ref}-palette.json", f"{ref}.json"):
            matches = sorted(styles.rglob(pattern))
            if matches:
                return Palette.load(matches[0])
    raise FileNotFoundError(f"could not resolve palette {ref!r}; pass --palette PATH")
