# Comparative anatomical study: official "Red" vs. the homage hero

This is the *understand* step of the loop. We emulated the official Pokémon "Red"
overworld trainer (recreations in `reference/recreation/red_*_0.sprite`), then
read it part-by-part to learn the design choices, then improved the hero
(`sprites/hero_*`) to match. The lossy JPEG import (`reference/snapped/`) is only a
study aid — the clean recreations are the real reference.

## Pixels per body part (improved hero, down-neutral, 142 opaque px of 256)

| Region                         | Pixels | Share | Note |
|--------------------------------|-------:|------:|------|
| Cap (red + light + shadow + bill) | 38 | 26.8% | the single largest feature |
| Head / face (skin + shadow + hair) | 30 | 21.1% | |
| Outline                        | 36 | 25.4% | a full quarter of the sprite is line work |
| Torso / vest (+ highlight)     | 20 | 14.1% | |
| Legs + shorts + shoes          | 14 |  9.9% | |
| Bag (gold + shadow)            |  4 |  2.8% | tiny but identity-defining |

**Average ≈ 9.5 px per material** across 15 materials. The headline number: the
**cap + head together are ~48% of the body mass** — this is what "big-head chibi"
means in pixels. Everything below the chin shares the other half. Design rule
confirmed: spend pixels on the head and its silhouette (the cap), keep the body
economical.

## The eyes

- The official uses **two small dark marks, wide-set, low on the face**, sitting
  just under the cap's bill with a 2-pixel gap between them. They are essentially
  1×1–1×2 dabs — there is no white, no iris detail; at 16px the *position* is the
  expression, per the guide ("if you've got four places to put your one pixel you
  might be able to pick the right one").
- Hero: matched as **single outline pixels at x6 and x9 on the eye row**, 2-px gap,
  framed by skin, sitting directly below the white bill. Kept deliberately minimal —
  enlarging them would read as "bug-eyed" and break the style.

## Roundness

- **Cap crown:** the official rounds the dome — the top is narrow and the sides
  bow out smoothly. The hero originally jumped 4→8 px between the top two rows
  (boxy); it now steps **2 → 6 → 8 → 10 → 12** down the crown, giving a smooth
  curve. Roundness here is faked entirely by stepping the outline inward one pixel
  at a time (the guide's anti-"doubles", smooth-curve advice).
- **Body:** the official tapers — rounded shoulders, a slightly narrower waist,
  arms tucked close. The hero keeps a near-constant-width torso (a touch boxier);
  the rounded cap + arm bulge at the shoulder row do most of the silhouette work.

## Part-by-part: official choice → hero

| Part | Official design choice | Hero |
|------|------------------------|------|
| Cap crown | Rounded red dome, lit on the top-left (top light) | `cap_red` + `cap_light` highlight, rounded crown |
| Cap bill | Pale band worn forward across the brow; sticks out front in profile | `bill` (off-white) full-width down view, pokes left/right in profile |
| Cap underside | Dark shadow band where the brim meets the head | `cap_shadow` right/lower edge |
| Hair / sideburns | Auburn, frames the face down to the jaw; full mass in back view | `hair`, sideburns now run down all three face rows; full hair block in `up` |
| Face | Short, mostly skin; one shadow plane for the cheek/jaw | `skin` + `skin_shadow` for nose/mouth/cheek |
| Eyes | Two wide-set dark dabs under the bill | matched (see above) |
| Neck | Almost none — head sits on shoulders | 2-px skin notch at the collar |
| Vest / torso | Dark jacket, a lighter plane catching top light | `vest` + `vest_light` chest plane |
| Arms / hands | Skin hands at the sides; subtle swing while walking | hands at sides; **left arm swings down/up** across the step frames |
| Hip bag | Bright yellow satchel on one hip — the loudest accessory and a silhouette cue | `bag_gold` + `bag_shadow` on the right hip; visible from behind in `up` |
| Shorts | Dark, short | `shorts` band |
| Legs | Bare skin, short | `skin` |
| Shoes | Red with a darker sole | `shoe` + `shoe_shadow` |
| Sole | 1-px darker line under each shoe | `shoe_shadow` row |
| Outline | Dark, slightly warm — **not pure black** | `outline` #1b1220 (near-black plum) |
| Light | From the top: lit crown/shoulders, shadow under brim/chin/bag | top-light shading throughout |

## Walk mechanics learned from the sheet

The official stores **3 distinct frames per direction** and plays
`neutral → stepA → neutral → stepB` (its columns are literally `c0 == c2`). Each
step **alternates the feet** (one shoe lifts, the other plants) and adds a small
**arm swing**; the head/cap is held steady. The hero reproduces this exactly:
foot alternation in every direction, plus a left-arm swing in the down/up step
frames and a fore/aft foot stride in the profiles.

## What was improved, and what was intentionally left

Improved: rounded cap crown, fuller sideburns, added the yellow hip bag, colored
(non-black) outline, top-light cool/warm shading, arm swing in the walk. Left as
a known gap: the torso could taper one pixel more at the waist for extra
roundness — a candidate for the next pass.
