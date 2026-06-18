"""spritekit — a grid-based pixel-art sprite maker driven from plain text.

The core idea: a sprite is a plain-text grid of single characters, one per pixel,
where each character maps (via a legend) to a named colour in a palette. This lets
an agent author and read sprites directly in monospace, then render them to PNGs,
import existing art back into the text format, lint against a locked style, and
assemble walk-cycle sprite sheets.
"""

from .palette import Palette
from .grid import Grid

__all__ = ["Palette", "Grid"]
__version__ = "0.1.0"
