# The craft layer — what makes pixel art look "pro" not "muddy"

Three research passes (cutting-edge AI pixel-art, community-cited limits, and a
head-to-head vs our toolkit) reached the same conclusion:

> Our deterministic model — **one palette index per grid cell, fixed palette,
> nearest-neighbour render** — already *structurally avoids* the failures that
> plague AI pixel art (grid drift, blur, auto-AA bleed, palette bloat, animation
> jitter). Those are the very problems diffusion tools spend huge effort faking
> and cleanup tools (PixelRefiner, Pixel Snapper) exist to fix. We don't have
> them by construction.

What we *were* missing is the **artistic-intent layer** — and it's encodable:

## 1. Hue-shifted colour ramps (`spritekit ramp`)
The #1 amateur-vs-pro difference. Don't shade by value alone; rotate hue along the
ramp: **shadows toward blue (cooler) + a touch more saturated; highlights toward
yellow (warmer) + a touch desaturated.** Measured gap that prompted this: Kael's
old ramps shifted hue ~1–3°; the Chrono-Trigger reference shifts 16–33° per step.

A ramp config declares bases + which materials ramp; `ramp` emits a full palette:
```
python3 -m spritekit.cli ramp styles/chrono-trigger/kael-base.json --out styles/chrono-trigger/kael-palette.json
```
The sprite grids don't change — only the `_shadow`/`_light` hexes get re-tinted,
so every material improves at once.

## 2. Selective outline / sel-out (`spritekit recolor-outline`)
Pure-black outlines on lit interior edges read as cheap. Sel-out retints each
outline cell toward the **shadow shade of the material it borders**, giving the
rich "coloured line work" look. Outlines bordering materials without a shadow
ramp (and the ground/foot shadow) stay dark for readability.
```
python3 -m spritekit.cli recolor-outline FRAME.sprite --out FRAME.sprite
```

## Recommended finishing pipeline for an original character
1. Author / build the frames (small palette, silhouette-first).
2. `upscale` (EPX) if working at a higher tier.
3. `ramp` to generate the hue-shifted palette.
4. `recolor-outline` each frame (sel-out).
5. `grade` / `parts` / `inspect` to verify, then `sheet` + `gif`.

## Deliberately NOT adopted (would fight the grid moat)
- Heavy automatic anti-aliasing everywhere (adds blur/edge-jitter — the exact tell
  we avoid). Sel-out first; corner AA only ever sparing and intentional.
- ML "aesthetic/semantic" scorers (need a model, undercut determinism). Our `diff`
  already is the exact-fidelity metric; `grade` proxies aesthetics cheaply.
- Bayer dithering is available-in-spirit but low-leverage at character scale.
