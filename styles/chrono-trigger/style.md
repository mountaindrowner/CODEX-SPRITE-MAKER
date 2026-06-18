# Style: Chrono Trigger overworld hero

A taller, less-chibi RPG sprite style modelled on the SNES classic *Chrono
Trigger*. Rules distilled from the master guide's Chrono Trigger section and from
the rendered study of the official Crono walking sheet (`sprites/_crono_study.png`).

**Characters in this style:** the emulated **Crono** (`sprites/hero_*`, palette
`palette.json`) and an **original** character, **Kael, a blue-spiky swordmage**
(`sprites/kael_*`, palette `kael-palette.json`) — proof of the "generate" step:
a hand-authored cobalt-haired, crimson-tunic swordmage built on the CT skeleton,
4-direction walk, reviewed and revised against critic feedback (real leg stride,
trouser shadow value, foot shadow on every frame). Each character carries its own
≤12-colour palette; `lint` validates a sprite against its own declared palette.

## Canvas & proportions
- **32×48** pixels per frame. A standard human stands ~32px tall in the body;
  the extra canvas gives headroom for the **spiky hair** and the drop shadow.
  > *"they're all around 32 pixels tall … the 32 pixel mark, that's sort of the
  > average or the default to start from … your basic non-frog human design."*
- **Less chibi than Pokémon**: a **smaller head-to-body ratio**, closer to a
  realistically proportioned (but still stylised) figure.
  > *"the Crono sprite has a smaller head to body ratio than a lot of the other
  > sprite styles … it's more toward a realistically proportioned human … it's
  > just that it's like less chibi or less deformed."*
- Build from a **stick-figure skeleton** — circles for head, hands and feet, then
  connect them up. The same skeleton repeats across the cast in different poses,
  so keep head / torso / legs / arms readable. Smaller head = **less space for
  facial features, more space for costuming and limb posing**.
- **Spiky dramatic hair is the dominant silhouette feature.** Assemble it from a
  **mosaic of rigid triangle shapes** sitting away from the skull, giving it
  volume. Pick a character's 2-3 strong identifying features and lean into them.

## View & light
- **Top-down 3/4 (oblique)**: you read the top of the head and the front of the
  body at once; legs are slightly foreshortened.
- **Light from the top**, consistently. Lighter values on top edges (hair crown,
  shoulders), darker under the chin, overhangs and the lower legs. No uniform
  "pillow shading" wrapped around the outline.

## Colour & outline
- About **12 colours per sprite**, under the SNES 16-colour-per-sprite limit.
  The linter enforces `max_colors: 12`.
  > *"most of them here have a palette of exactly 12 colors that are used …
  > there's a limit of 16 colors per sprite on the Super Nintendo so these are
  > just under that limit."*
- **Colored line work, NOT pure black.** The outline of each form is a **darker
  shade of that material** (dark red/brown for hair, a costume-specific dark for
  cloth/metal, a darker tone around the edge of the skin). This is the core of
  the CT look.
  > *"instead of black line work you've got this subtle colored line work that's
  > going throughout the entire sprite and it just punches up the vibrancy."*
  The `outline` colour is the default border, but recolour the line work toward
  each material's dark tone where the budget allows.
- **~2-3 values per material**: a base midtone plus a shadow (and/or highlight).
  Skin is typically **base + one shade**, reused only for skin. Hair commonly
  **steps through 3-4 colours** (e.g. yellow → orange → dark red/brown line work).
- **Occasional bright white highlights** on reflective or attention-worthy areas
  — gloves, boots, metal, and the odd single skin dot at the shoulder or knee.
  > *"the white highlights in … the highly reflective or areas of interest …
  > bright highlights like this sometimes also appear on the skin as well."*
- Keep the small details — **prominent cuffs, wristbands, belts, straps** — even
  when they're only 2-3px and a single subtle shade; that density is part of the
  CT formula.
- The locked palette lives in `palette.json` (produced separately). Crono's own
  scheme is the **teal-and-orange** reference: spiky orange hair, teal tunic,
  pale skin, **gold trim**, red boots, with material-dark colored line work.

## Directions & movement
- Four facings: **down, up, left, right**.
  - `down` shows the face (smaller, fewer features) and the front of the tunic.
  - `up` shows the back of the head/hair — no face.
  - `left` is a profile (one eye, hair massed dramatically).
  - `right` is the **horizontal mirror of left** (`spritekit mirror`).
- A **soft drop-shadow ellipse** sits under the feet on every frame.

## Walk cycle
- **3 distinct frames per direction**: `neutral`, `step_left`, `step_right`.
- Played as a 4-step loop: **neutral → step_left → neutral → step_right** at
  ~6 fps (`play_order: [0, 1, 0, 2]`).
- One foot can sit forward of the other in stride frames; the upper body and hair
  stay steady so the spiky silhouette reads consistently.

## Files
- `palette.json` — the locked ~12-colour palette.
- `style.json` — machine constraints for `spritekit lint`.
- `sprites/<name>_<dir>_<0|1|2>.sprite` — the hero frames (neutral/stepL/stepR).
- `reference/` — the imported/rendered study used to lock the style
  (`sprites/_crono_study.png`).
