#!/usr/bin/env bash
# Generate the "normal NPC shopkeeper" (portly apron merchant) through the
# deterministic pipeline spine. Mirrors pipeline_crono.sh but generate-mode:
# a stout build (--flesh-girth) and the NPC parts (normal hair, mustache, apron).
# Usage:  bash styles/chrono-trigger/build/pipeline_shopkeeper.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

RIG=styles/chrono-trigger/rig.json
PAL=styles/chrono-trigger/shopkeeper-palette.json
OUT=styles/chrono-trigger/sprites
TMP="$(mktemp -d)"
PARTS=hair_short,mustache,eyes,apron,belt,boots
LIGHT=top-left
SIZE=64x96
GIRTH=1.35

build_pose() {  # $1 = pose name (down_0, up_1, ...)
  local pose="$1" t="$TMP/$1.sprite"
  python3 -m spritekit.cli skeleton --rig "$RIG" --pose "$pose" \
    --flesh "$t" --flesh-size "$SIZE" --flesh-palette shopkeeper --flesh-girth "$GIRTH"
  python3 -m spritekit.cli stamp "$t" --rig "$RIG" --pose "$pose" \
    --parts "$PARTS" --palette "$PAL" --out "$t"
  python3 -m spritekit.cli shade "$t" --palette "$PAL" --light "$LIGHT" --no-highlights --out "$t"
  python3 -m spritekit.cli recolor-outline "$t" --palette "$PAL" \
    --out "$OUT/shopkeeper_${pose}.sprite"
}

for d in down up left; do
  for f in 0 1 2; do build_pose "${d}_${f}"; done
done
for f in 0 1 2; do
  python3 -m spritekit.cli mirror "$OUT/shopkeeper_left_${f}.sprite" \
    --name "shopkeeper_right_${f}" --out "$OUT/shopkeeper_right_${f}.sprite"
done

python3 -m spritekit.cli sheet \
  "$OUT"/shopkeeper_{down,up,left,right}_{0,1,2}.sprite \
  --cols 3 --palette "$PAL" --coords sprites/shopkeeper_sheet.coords.json \
  --out sprites/shopkeeper_sheet.png
for d in down up left right; do
  python3 -m spritekit.cli gif \
    "$OUT/shopkeeper_${d}_0.sprite" "$OUT/shopkeeper_${d}_1.sprite" \
    "$OUT/shopkeeper_${d}_0.sprite" "$OUT/shopkeeper_${d}_2.sprite" \
    --fps 6 --palette "$PAL" --out "sprites/shopkeeper_walk_${d}.gif"
done
rm -rf "$TMP"
echo "shopkeeper pipeline complete -> $OUT/shopkeeper_*.sprite + sprites/shopkeeper_sheet.png + gifs"
