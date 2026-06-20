# The prompt → pixel pipeline

This is the repeatable formula for taking a **one-line text prompt** to a
**finished, professional Chrono-Trigger-style sprite** — a documented agent
workflow on top of the `spritekit` command spine. Three sub-agents supply judgment
(Designer, Detailer, Critic); everything between them is deterministic commands.

```
text prompt
   │  Designer agent
   ▼
character.json ──► ramp ──► palette        (Phase 1–2)
   │
   ▼  per pose (down/up/left ×0/1/2)
skeleton --flesh ──► stamp ──► shade ──► recolor-outline   (Phase 3–5: the spine)
   │
   ▼  Detailer agent  ⇄  Critic agent      (Phase 6: the judgment loop)
mirror ──► sheet / gif                     (Phase 7: assemble)
```

The deterministic spine is runnable as one script:
`bash styles/chrono-trigger/build/pipeline_crono.sh`.

---

## Stage by stage (the spine)

| # | Stage | Command | In → Out |
|---|-------|---------|----------|
| 1 | Spec | *Designer agent* | prompt → `specs/<name>.character.json` |
| 2 | Palette | `ramp` (generate) or reference palette (emulate) | bases → `*-palette.json` |
| 3 | Flesh | `skeleton --flesh --flesh-size 64x96 --flesh-palette N` | rig pose → capsule body `.sprite` |
| 4 | Stamps | `stamp --rig R --pose P --parts ...` | flesh → features (hair/eyes/headband/collar/belt/boots) |
| 5 | Shade | `shade --light top-left` then `recolor-outline` | flats → lit, integrated form |
| 6 | Polish | *Detailer ⇄ Critic agents* | rough → finished, gated by QA |
| 7 | Assemble | `mirror` (right=left), `sheet`, `gif` | frames → sheet + walk GIFs |

## The character spec (Designer output)

`styles/<style>/specs/<name>.character.json` — see `specs/crono.character.json`:

```json
{
  "name": "crono", "style": "chrono-trigger",
  "mode": "emulate",                 // or "generate" for an original
  "rig": "rig.json", "frame_size": [32, 48],
  "palette": "crono-gen",            // emulate: reference hexes; generate: ramp output
  "light": "top-left",
  "parts": ["hair_spikes", "headband", "eyes", "collar", "boots"]
}
```

- **emulate** — recreate a known sprite. Use the reference's exact colours (keyed to
  the flesh material names, e.g. `trousers` = Crono's `pants`) and score by `diff`.
- **generate** — an original from a prompt. Give palette `bases` for `ramp` to expand
  into hue-shifted ramps, and score by `lint` + `grade` + `layers`.

## The three agents

**Designer** — *prompt → spec.*
> You turn a one-line character prompt into a `character.json` for the
> `<style>` style. Read `styles/<style>/style.md` for the locked rules. Choose
> `mode` (emulate vs generate), the palette (reference hexes for emulate; base
> hexes per material for generate), the `light` direction, and the `parts` list
> from the stamp registry — hero parts (`hair_spikes, headband, eyes, collar,
> belt, boots`) and NPC parts (`hair_short, mustache, apron`). For a generate
> character also set a `girth` (1.0 normal, ~1.35 portly) for `--flesh-girth`.
> Map the prompt's materials onto the flesh names: hair, skin, tunic, trousers,
> boots, plus accessories. Output only the JSON.

**Detailer** — *rough → finished (the hybrid's agent half).*
> You refine a shaded, stamped sprite to finished pixel art. Render it and run
> `inspect` (coordinate grid) and `parts` (isolate materials) to target cells.
> Edit the `.sprite` grid directly: enlarge/shape the hair into the style's
> silhouette, clean the face, define hands and the costume trim, fix any stray
> pixels from the procedural passes. Re-render after every edit. Stay within the
> palette and the frame size; preserve the light direction.

**Critic** — *the QA gate.*
> Score the sprite against the locked rules and report MUST-FIX items only.
> Run `lint --style style.json` (size/colours/outline), `grade` (edge jitter,
> symmetry, fill), and `layers` (does the construction match the style recipe —
> heads-tall, light direction, values per material?). For `mode: emulate` also run
> `diff` against the reference frame and report the match %. Loop with the Detailer
> until lint passes, grade thresholds are met, and the diff plateaus.

## "Done" — the QA gates

- **Originals (generate):** `lint` passes (frame size, ≤ max_colors, outline) **and**
  `grade` thresholds (low edge jitter, sane symmetry/fill) **and** the `layers`
  decomposition matches the locked CT recipe.
- **Emulation:** all of the above **and** `diff` vs the reference is driven as high
  as it will go; the residual is the gap analysis backlog.

---

## Proof run: re-emulating Crono

Driving `specs/crono.character.json` through the spine (at the reference's native
32×48) and `diff`-ing against `reference/recreation/crono_r0_c0.sprite`:

- **Spine-only result: 76.1% pixel match**, no agent polish — the pipeline nails
  the colour story and rough silhouette (teal tunic, tan pants, red boots/headband,
  skin arms, eyes) straight from the rig.
- **Gap analysis (the Detailer's backlog):**
  1. **Hair mass** — Crono's signature wild spiky hair is far larger and frames the
     whole head; our `hair_spikes` stamp is a small central fan. This is the single
     biggest source of mismatch (transparent-vs-outline across the hair region).
  2. **Head/body proportion** — our capsule head reads slightly large and round.
  3. **Costume fine detail** — trim lines, defined boot shape, facial nuance are
     simplified versions of the hand recreation.

The same spine, run at the production 64×96 for all nine poses + mirrored right,
yields a clean, lint-passing 4-direction walk cycle
(`sprites/crono_gen_sheet.png`, `sprites/crono_gen_walk_*.gif`) — proof the
pipeline produces a complete, usable asset set end to end, with the agent loop
reserved for closing the artistic gap.
