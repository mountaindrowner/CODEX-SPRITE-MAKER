# CODEX-SPRITE-MAKER

A grid-based pixel-art sprite maker built so that **Claude Code can be the artist**.
A sprite is a plain-text grid — one character per pixel — that maps, through a
legend, to named colours in a palette. Claude authors and reads those grids
directly in monospace, then a small Python toolkit (`spritekit`) renders them to
PNGs, imports existing art back into the text format, lints sprites against a
locked style, and assembles directional walk-cycle sprite sheets and GIFs.

The working method is a repeatable loop:

> **emulate an existing sprite EXACTLY → understand it → write the style's rules →
> generate new sprites → lock the style and move to the next.**

## Quickstart

```bash
pip install -r requirements.txt

# Render a sprite to a scaled PNG
python3 -m spritekit.cli render styles/pokemon-overworld/sprites/hero_down_0.sprite --scale 16 --out out.png

# Import an existing sheet into editable .sprite grids + a palette
python3 -m spritekit.cli import REFERENCE.png --native 64x64 --grid 4x4 --name pkmn --out imported/

# Check a recreation is pixel-perfect against the import
python3 -m spritekit.cli diff mine.sprite imported/pkmn_r0_c0.sprite

# Validate sprites against a locked style
python3 -m spritekit.cli lint styles/pokemon-overworld/sprites/*.sprite --style styles/pokemon-overworld/style.json

# Assemble a sprite sheet (+ coordinate manifest) and animated GIFs
python3 -m spritekit.cli sheet FRAME...  --out sheet.png --cols 3 --coords sheet.coords.json
python3 -m spritekit.cli gif   FRAME...  --out walk.gif --fps 6
```

## What's here

- `spritekit/` — the toolkit (`render`, `import`, `diff`, `lint`, `mirror`, `sheet`, `gif`).
- `styles/pokemon-overworld/` — the first locked style: palette, machine rules
  (`style.json`), readable rules (`style.md`), the imported reference, and a
  complete original character with a 4-direction walk cycle.
- `sprites/` — generated output: `hero_walk_sheet.png` (+ `.coords.json`) and a
  walk GIF per direction.
- `docs/` — the `.sprite` [grid format](docs/grid-format.md) and the
  [methodology](docs/methodology.md).
- `CLAUDE.md` — how Claude should drive this repo.
- `PIXEL ART MASTER GUIDE.pdf` — the tutorial source the style rules are distilled from.

## First milestone (done)

An original green-capped trainer rendered idle + walking in all four directions,
assembled into a sprite sheet with recorded frame coordinates and four animated
GIFs. See `sprites/hero_walk_sheet.png` and `sprites/hero_walk_*.gif`.
