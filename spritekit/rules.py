"""Load a style rule-pack and lint a Grid against it.

A style.json captures the *locked* constraints of a style, e.g.::

    {
      "name": "pokemon-overworld",
      "palette": "palette.json",
      "frame_size": [16, 16],
      "max_colors": 16,
      "directions": ["down", "up", "left", "right"],
      "mirror": {"right": "left"},
      "walk": {"frames_per_direction": 4},
      "require_outline": true,
      "outline_color": "outline"
    }
"""

from __future__ import annotations

import json
from pathlib import Path

from .grid import Grid
from .palette import TRANSPARENT, Palette


class Style:
    def __init__(self, data: dict, base_dir: Path):
        self.data = data
        self.base_dir = base_dir
        self.name = data.get("name", base_dir.name)

    @classmethod
    def load(cls, path: str | Path) -> "Style":
        path = Path(path)
        return cls(json.loads(path.read_text()), path.parent)

    @property
    def palette_path(self) -> Path:
        return self.base_dir / self.data.get("palette", "palette.json")

    def palette(self) -> Palette:
        return Palette.load(self.palette_path)

    def lint(self, grid: Grid) -> list[str]:
        """Return a list of human-readable issues; empty means the grid passes."""
        issues: list[str] = []
        palette = self.palette()

        fs = self.data.get("frame_size")
        if fs and (grid.width, grid.height) != tuple(fs):
            issues.append(
                f"size {grid.width}x{grid.height} != required {fs[0]}x{fs[1]}"
            )

        opaque_used = grid.opaque_names_used()
        not_in_palette = sorted(opaque_used - set(palette.colors))
        if not_in_palette:
            issues.append(f"colours not in palette: {', '.join(not_in_palette)}")

        max_colors = self.data.get("max_colors")
        if max_colors is not None and len(opaque_used) > max_colors:
            issues.append(
                f"uses {len(opaque_used)} colours, max allowed is {max_colors}"
            )

        if self.data.get("require_outline"):
            outline = self.data.get("outline_color", "outline")
            if outline not in opaque_used:
                issues.append(f"outline colour {outline!r} not used (require_outline)")

        return issues
