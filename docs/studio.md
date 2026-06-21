# Sprite Studio — a tighter feedback loop

The hardest part of making good sprites is **specific, quantified feedback**.
"Too blocky" is a whole-sprite verdict; quality actually lives in particular
**parts** and particular **pixels**. These tools make feedback precise so we can
iterate at small scope and measure progress.

## The three tools

```
python3 -m spritekit.cli grade   SPRITE... --palette P [--parts parts.json]
python3 -m spritekit.cli parts   SPRITE   --palette P [--parts parts.json] --out PNG --scale N
python3 -m spritekit.cli inspect SPRITE   --palette P --out PNG --scale N --step 4
```

- **grade** — a quantified scorecard: size, fill %, colours used, content
  bounding box, **edge jitter** (silhouette roughness; lower = smoother/less
  blocky), **mirror symmetry %**, and colours per part. Turns vague verdicts into
  numbers we can drive toward a target.
- **parts** — a contact sheet that **isolates each part** (hair / face / tunic /
  legs / boots …) in colour against the ghosted rest, plus the FULL sprite. Lets
  us critique and rework **one asset at a time**.
- **inspect** — a zoomed render with a **labelled coordinate grid** (columns
  A, B, … ; rows 0, 1, …) so feedback can name exact cells, e.g. "shave the hair
  tip at AC2" or "add a cheek shadow around AG37".

## Parts manifest

A part is just a named group of palette materials, e.g.
`styles/chrono-trigger/kael-parts.json`:

```json
{ "parts": { "hair": ["hair","hair_light","hair_shadow"], "face": ["skin","skin_shadow"], ... } }
```

If omitted, every material becomes its own part.

## The loop (how you direct me)

1. I send you the **parts sheet** and the **inspect** grid for the frame.
2. You give targeted feedback any of these ways:
   - by **part**: "hair: narrower and spikier; tunic: add a darker shadow under the arms";
   - by **cell**: "the chin at AG40 is too heavy — drop it";
   - by **metric target**: "get max width down to ~32 and leave headroom at the top";
   - or **mark up the image** and send it back — I read the marked PNG.
3. I rework just that part, re-`grade` to confirm the numbers moved, and re-render.
4. Repeat per part until the scorecard and your eye both pass; then lock it.

## Example insight it already surfaced

Grading Kael vs the Crono benchmark showed Kael's **max width 46 vs Crono's 32**
and **fill 40% vs 26%**, with Kael's hair filling the canvas top-to-bottom (no
headroom). Quantified target: slim the body, shrink the hair, leave headroom.
