# Skeleton-first construction

Work from the bare-bones internal structure outward, the way the master guide
teaches ("build from a stick-figure skeleton; the same skeleton repeats across the
cast"). Fixing the figure at the *structure* level fixes body shape and movement
at the root, instead of patching pixels.

## What a rig is

A **rig** (`styles/<style>/rig.json`) is named joints — `head_top, head, neck,
shoulder_l/r, elbow_l/r, hand_l/r, pelvis, hip_l/r, knee_l/r, foot_l/r` — given a
position per **pose** (e.g. `down_0`, `down_1`, `down_2`), plus the **bones** that
connect them. One rig holds many poses (the walk cycle, each direction).

## How we derived the Chrono Trigger rig

1. Lay the skeleton onto the official Crono frame and adjust joints until the
   bones sit on the real anatomy:
   ```
   spritekit skeleton --rig rig.json --pose down_0 \
     --sprite reference/recreation/crono_r0_c0.sprite --out overlay.png
   ```
2. Read off the **proportions** (normalised to height):
   ```
   spritekit skeleton --rig rig.json --pose down_0 --ratios
   ```
   Chrono-Trigger body plan (down_0): **~3 heads tall**, head ≈ 34% of height,
   torso ≈ 41%, legs ≈ 24%, **shoulders wider than hips** — less chibi than the
   Pokémon plan, more room for limbs/costume.
3. Capture **movement** by posing the walk frames (`down_1`, `down_2`): the legs
   alternate and the arms swing. Render the skeleton alone as a construction
   guide / animation check:
   ```
   spritekit skeleton --rig rig.json --pose down_1 --out stick.png
   ```

The CT rig is **hand-tuned by the human in the loop**: joints exported from the
rig editor and pasted back, so the poses (`down_0`, `up_0`, `left_0`) sit exactly
where the artist wants them. `left_0` is a wide, low stance — the most the 32×48
grid affords for a profile — and reads as an action pose more than a clean walk
neutral; flesh it and refine, or re-place its legs/arms for a tighter profile.

## The construction workflow (how new sprites get built on the rig)

1. **Pose** the skeleton (reuse the CT ratios; move joints for the pose/direction).
2. **Flesh** the bones to a silhouette — now automated:
   ```
   spritekit skeleton --rig rig.json --pose down_0 \
     --flesh base.sprite --flesh-size 64x96 --flesh-palette kael
   ```
   Limbs become rounded capsules, the torso fills the shoulder span, and the head
   is an ellipse with a hair cap, all in the named materials (`outline, skin, hair,
   tunic, trousers, boots`). The result is a clean, on-model **base to refine** —
   not finished art.
3. **Detail** the silhouette into line-work + features.
4. **Colour** with hue-shifted ramps (`ramp`) and sel-out (`recolor-outline`).
5. **Verify** with `grade` / `parts` / `diff`, assemble `sheet` + `gif`.

Because every character reuses the same rig + ratios, the cast stays on-model and
new poses/directions are a matter of moving joints — exactly the "chess-piece"
consistency the guide describes.

## Next

- Refine each fleshed base into final line-work + shading; re-`mirror` right from left.
- Tighten `left_0` (or add a dedicated profile-walk pose) so the side view reads
  as cleanly as down/up.
