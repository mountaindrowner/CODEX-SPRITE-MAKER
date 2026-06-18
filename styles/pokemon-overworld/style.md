# Style: Pokémon overworld trainer

The simplest starting style — small, readable, four-direction movement. Rules
distilled from the master guide (Game Boy / overworld sections) and from the
provided reference sheet of a red-capped trainer.

## Canvas & proportions
- **16×16** pixels per frame.
- **Chibi** proportions: oversized head, short body, tiny feet. Realistic
  anatomy does not fit at this size, and the head carries identity/emotion.
- The **cap is the dominant silhouette feature** — give it the most pixels. Pick
  only 2–3 identifying features (cap, shirt, footwear); drop the rest as noise.

## View & light
- **Top-down 3/4 (oblique)**: you see the top of the cap and the front of the
  body at once; the body is slightly foreshortened (short legs).
- **Light from the top**, consistently. Lighter values on top edges (cap crown,
  shoulders), darker under the brim, chin, and overhangs. Never wrap shadow
  uniformly around the outline (no "pillow shading").

## Colour & outline
- About **3 values per material** (base + shadow, plus an occasional highlight).
- **Dark coloured outline**, not pure black (`#281d2b`) — a darker version of the
  forms it borders, which keeps the sprite vivid and integrated.
- Keep within the palette (`palette.json`); the linter enforces `max_colors: 16`.

## Directions & movement
- Four facings: **down, up, left, right**.
  - `down` shows the full face (two eyes, nose/mouth shadow).
  - `up` shows the back of the cap and hair — no face.
  - `left` is a profile (one eye, nose toward the front, hair massed at the back).
  - `right` is the **horizontal mirror of left** (`spritekit mirror`).

## Walk cycle
- **3 distinct frames per direction**: `neutral`, `step_left`, `step_right`.
- Played as a 4-step loop: **neutral → step_left → neutral → step_right** at ~6 fps.
- For down/up, the two feet alternate lifting (a march). For the profile, the feet
  stride forward and back. The upper body is held steady between frames.

## Files
- `palette.json` — the locked palette.
- `style.json` — machine constraints for `spritekit lint`.
- `sprites/hero_<dir>_<0|1|2>.sprite` — the original trainer (neutral/stepL/stepR).
- `reference/` — the imported reference sheet used to study the style.
