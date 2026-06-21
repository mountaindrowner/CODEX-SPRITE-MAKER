# Methodology: emulate → understand → rules → generate

The point of this project is not to generate sprites blindly, but to *learn* a
style the way an animator does — by copying real work exactly, understanding why
it is drawn that way, then encoding repeatable rules. Each style goes through the
same loop, and once locked, you move on to the next.

## 1. Emulate EXACTLY

Drop a reference image (a sprite or a full sheet) into the style's `reference/`
folder, then import it:

```bash
python3 -m spritekit.cli import reference/source.png --native 64x64 --grid 4x4 --name pkmn --out reference/
```

The importer downscales to native resolution (per-block median, so JPEG noise and
upscaling are undone), treats the background as transparent, quantises the colours
to a small palette, and slices the sheet into one `.sprite` per cell — recording
each cell's **coordinates on the sheet** in `frames.coords.json`.

Imported grids from a lossy source are a *draft*. Recreate each frame by hand in a
clean `.sprite`, then drive it to pixel-perfect with `diff`:

```bash
python3 -m spritekit.cli diff mine.sprite reference/pkmn_r0_c0.sprite   # aim for 100%
```

`diff` round-trips at 100% on clean input, so it is a true fidelity gate.

## 2. Understand it

While recreating, ask *why* each pixel is where it is — proportions, the dominant
silhouette feature, where the light comes from, how many values per material, what
the outline is doing. These observations are the rules.

## 3. Write the rules

Capture them twice:
- `style.md` — readable rules for a human or agent (sizing, view, light, palette,
  proportions, outline, directions, walk-cycle spec).
- `style.json` — machine constraints the linter enforces (frame size, max colours,
  required outline, directions, walk frames).

```bash
python3 -m spritekit.cli lint sprites/*.sprite --style style.json
```

## 4. Generate new sprites

Author original characters that obey the locked rules. For 4-direction movement,
draw `down`, `up`, and `left`; produce `right` by mirroring `left`:

```bash
python3 -m spritekit.cli mirror sprites/hero_left_0.sprite --out sprites/hero_right_0.sprite
```

Then assemble the walk sheet (with coordinates) and preview GIFs:

```bash
python3 -m spritekit.cli sheet FRAME... --out sheet.png --cols 3 --coords sheet.coords.json
python3 -m spritekit.cli gif   dir_0 dir_1 dir_0 dir_2 --out walk.gif --fps 6
```

The walk cycle plays `neutral → step_left → neutral → step_right`; only three
distinct frames are stored per direction (the play order is in `style.json`).

## 5. Lock and move on

Once a style produces clean, consistent, lintable sprites, freeze it and start the
loop again on the next style (Chrono Trigger, Mega Man X, …).
