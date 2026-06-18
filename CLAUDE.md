# CLAUDE.md — driving the sprite maker

This repo lets you (Claude) be the pixel artist. Sprites are plain-text grids you
edit directly; `spritekit` renders/imports/validates/assembles them.

## Core idea
- A `.sprite` is a grid of one character per pixel; a legend maps characters to
  palette colour names. See `docs/grid-format.md`.
- You author and read grids in monospace, then **render to PNG and look at the
  result** (read the PNG back) to verify and iterate. Always render after editing.

## The loop (see `docs/methodology.md`)
1. **Emulate exactly** — `import` a reference, recreate by hand, `diff` to 100%.
2. **Understand** — note proportions, light, values-per-material, outline, silhouette.
3. **Write rules** — `style.md` (readable) + `style.json` (linted constraints).
4. **Generate** — author originals that pass `lint`; `mirror` left→right; build
   `sheet` (+ coords) and `gif`.
5. **Lock** the style and move to the next.

## CLI
```
python3 -m spritekit.cli render SPRITE... --scale N --out PNG
python3 -m spritekit.cli import IMAGE --native WxH --grid COLSxROWS --name N --out DIR
python3 -m spritekit.cli diff   A.sprite B.sprite
python3 -m spritekit.cli lint   SPRITE... --style style.json
python3 -m spritekit.cli mirror SPRITE --out OUT.sprite
python3 -m spritekit.cli sheet  FRAME... --out PNG --cols N --coords COORDS.json
python3 -m spritekit.cli gif    FRAME... --out GIF --fps F
```

## Conventions
- 16×16 frames for the `pokemon-overworld` style; keep colours within its palette.
- Walk frames per direction: `_0` neutral, `_1` step_left, `_2` step_right. Play
  order is `0,1,0,2`.
- Generated/preview output goes in `sprites/`; throwaway previews should be named
  with a leading `_` and not committed.
- Produce `right` by mirroring `left`; do not hand-draw it.

## Working tips
- Grid rows must all be exactly the declared width — the parser will tell you which
  row is wrong. Count columns carefully or render often.
- Imports from lossy images (JPEG) are drafts; the clean recreation is the source
  of truth, verified with `diff`.
