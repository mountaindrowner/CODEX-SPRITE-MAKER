# Auto-shade — build the lit form up from flat colour

`shade` is the inverse of `layers`. Where `layers` *decomposes* a finished sprite
into its construction stack, `shade` *composes* the top of that stack: it turns a
flat-coloured sprite (e.g. a skeleton flesh base) into a shaded one, placing the
shadow tier, light tier, and highlights from a single **light direction** and the
palette's per-material ramps.

```
python3 -m spritekit.cli shade base.sprite --out lit.sprite --light top-left
```

## The model: directional form-shading (not pillow-shading)

Each material's mass is projected onto the light axis. The third of the mass
*toward* the light becomes `<material>_light`, the third *away* becomes
`<material>_shadow`, and the middle keeps the base tone. Convex edge pixels that
directly face the light get a `<material>_highlight` (or `highlight`) dab.

This keys every value to **one consistent light vector** — the professional tell —
instead of darkening every edge equally, which is the "pillow shading" amateur tell
the master guide warns against. Run `layers` on the result and it reads the light
direction straight back out.

Two safety rules keep it composable:
- **Only base tones are shaded.** Any pixel already on a `_shadow`/`_light` tone is
  left alone, so hand-shading survives a re-run.
- **A tier is applied only if its ramp colour exists** in the palette. A material
  with no `_light` simply stays flat on its lit side — so fill out the ramps
  (`ramp`) to get the full effect.

Light directions: `top, bottom, left, right, top-left, top-right, bottom-left,
bottom-right`. Tune the band sizes with the `shadow_frac` / `light_frac` arguments
(defaults 0.34 each — i.e. roughly even thirds).

## Where it sits in the construction loop

```
skeleton --flesh   ->   shade   ->   recolor-outline   ->   (hand polish)
 bones to a body      flat to lit     sel-out the lines      taste
```

So a new character goes from a posed rig to a shaded, integrated base with three
deterministic commands, leaving only the artistic polish to do by hand.
