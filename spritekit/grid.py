"""The .sprite text format: parse, serialise, and query a pixel grid.

A .sprite file looks like::

    name: hero_walk_down_0
    size: 16x16
    palette: pokemon-overworld
    legend:
      .: transparent
      o: outline
      s: skin
    grid: |
      ......oooo......
      .....ohhhho.....
      ...(height rows, each exactly width chars)...

Rules:
- One character per pixel. ``.`` is transparent by convention (and is always in
  the legend implicitly).
- Every grid row must be exactly ``width`` characters; there must be ``height`` rows.
- Every character used in the grid must appear in the legend.
"""

from __future__ import annotations

from pathlib import Path

from .palette import TRANSPARENT

TRANSPARENT_CHAR = "."


class Grid:
    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        palette: str,
        legend: dict[str, str],
        rows: list[str],
    ):
        self.name = name
        self.width = width
        self.height = height
        self.palette = palette
        # ``.`` always maps to transparent.
        self.legend: dict[str, str] = {TRANSPARENT_CHAR: TRANSPARENT}
        self.legend.update(legend)
        self.rows = rows
        self.validate()

    # -- validation --------------------------------------------------------
    def validate(self) -> None:
        if len(self.rows) != self.height:
            raise ValueError(
                f"{self.name}: expected {self.height} rows, got {len(self.rows)}"
            )
        for i, row in enumerate(self.rows):
            if len(row) != self.width:
                raise ValueError(
                    f"{self.name}: row {i} has width {len(row)}, expected {self.width}"
                )
            for ch in row:
                if ch not in self.legend:
                    raise ValueError(
                        f"{self.name}: char {ch!r} in row {i} missing from legend"
                    )

    # -- queries -----------------------------------------------------------
    def color_at(self, x: int, y: int) -> str:
        """Palette colour *name* at (x, y)."""
        return self.legend[self.rows[y][x]]

    def names_used(self) -> set[str]:
        chars = {ch for row in self.rows for ch in row}
        return {self.legend[ch] for ch in chars}

    def opaque_names_used(self) -> set[str]:
        return {n for n in self.names_used() if n != TRANSPARENT}

    def flipped_h(self, new_name: str | None = None) -> "Grid":
        """Return a horizontally mirrored copy (for right = mirror of left)."""
        rows = [row[::-1] for row in self.rows]
        legend = {k: v for k, v in self.legend.items() if k != TRANSPARENT_CHAR}
        return Grid(
            new_name or self.name,
            self.width,
            self.height,
            self.palette,
            legend,
            rows,
        )

    # -- IO ----------------------------------------------------------------
    @classmethod
    def parse(cls, text: str) -> "Grid":
        name = ""
        width = height = 0
        palette = ""
        legend: dict[str, str] = {}
        rows: list[str] = []

        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue
            if stripped.startswith("name:"):
                name = stripped[len("name:") :].strip()
            elif stripped.startswith("size:"):
                w, h = stripped[len("size:") :].strip().lower().split("x")
                width, height = int(w), int(h)
            elif stripped.startswith("palette:"):
                palette = stripped[len("palette:") :].strip()
            elif stripped.startswith("legend:"):
                i += 1
                while i < len(lines) and (lines[i].startswith((" ", "\t"))):
                    entry = lines[i].strip()
                    if entry:
                        ch, _, cname = entry.partition(":")
                        # Allow the char to be quoted to make space/colon literal.
                        ch = ch.strip()
                        if len(ch) >= 2 and ch[0] == ch[-1] and ch[0] in "'\"":
                            ch = ch[1:-1]
                        legend[ch] = cname.strip()
                    i += 1
                continue
            elif stripped.startswith("grid:"):
                i += 1
                # Pixel rows are the following lines, indented by at least 2 spaces.
                # We strip exactly the common leading indentation.
                block: list[str] = []
                while i < len(lines) and lines[i].startswith("  "):
                    block.append(lines[i][2:])
                    i += 1
                rows = [r.rstrip("\n") for r in block]
                continue
            i += 1

        if not name:
            raise ValueError("sprite is missing a 'name:' field")
        return cls(name, width, height, palette, legend, rows)

    @classmethod
    def load(cls, path: str | Path) -> "Grid":
        return cls.parse(Path(path).read_text())

    def to_text(self) -> str:
        out = [
            f"name: {self.name}",
            f"size: {self.width}x{self.height}",
            f"palette: {self.palette}",
            "legend:",
        ]
        for ch, cname in self.legend.items():
            # Quote characters that would confuse the parser.
            shown = ch if ch not in (" ", ":", "") else f"'{ch}'"
            out.append(f"  {shown}: {cname}")
        out.append("grid: |")
        for row in self.rows:
            out.append(f"  {row}")
        return "\n".join(out) + "\n"

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_text())
