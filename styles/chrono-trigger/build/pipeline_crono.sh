#!/usr/bin/env bash
# Reproducible "prompt -> sprite" pipeline run for Crono (the emulation proof).
# This is the deterministic spine documented in docs/pipeline.md, made runnable.
# Usage:  bash styles/chrono-trigger/build/pipeline_crono.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

RIG=styles/chrono-trigger/rig.json
PAL=styles/chrono-trigger/specs/crono-gen-palette.json
OUT=styles/chrono-trigger/sprites
TMP="$(mktemp -d)"
PARTS=hair_spikes,headband,eyes,collar,boots
LIGHT=top-left
SIZE=64x96

build_pose() {  # $1 = pose name (down_0, up_1, ...)
  local pose="$1" t="$TMP/$1.sprite"
  python3 -m spritekit.cli skeleton --rig "$RIG" --pose "$pose" \
    --flesh "$t" --flesh-size "$SIZE" --flesh-palette crono-gen
  python3 -m spritekit.cli stamp "$t" --rig "$RIG" --pose "$pose" \
    --parts "$PARTS" --palette "$PAL" --out "$t"
  python3 -m spritekit.cli shade "$t" --palette "$PAL" --light "$LIGHT" --out "$t"
  python3 -m spritekit.cli recolor-outline "$t" --palette "$PAL" \
    --out "$OUT/crono_gen_${pose}.sprite"
}

for d in down up left; do
  for f in 0 1 2; do build_pose "${d}_${f}"; done
done
# right = mirror of left (never hand-built)
for f in 0 1 2; do
  python3 -m spritekit.cli mirror "$OUT/crono_gen_left_${f}.sprite" \
    --name "crono_gen_right_${f}" --out "$OUT/crono_gen_right_${f}.sprite"
done

# assemble: sheet (rows = direction) + per-direction walk GIFs (play 0,1,0,2)
python3 -m spritekit.cli sheet \
  "$OUT"/crono_gen_{down,up,left,right}_{0,1,2}.sprite \
  --cols 3 --palette "$PAL" --coords sprites/crono_gen_sheet.coords.json \
  --out sprites/crono_gen_sheet.png
for d in down up left right; do
  python3 -m spritekit.cli gif \
    "$OUT/crono_gen_${d}_0.sprite" "$OUT/crono_gen_${d}_1.sprite" \
    "$OUT/crono_gen_${d}_0.sprite" "$OUT/crono_gen_${d}_2.sprite" \
    --fps 6 --palette "$PAL" --out "sprites/crono_gen_walk_${d}.gif"
done
rm -rf "$TMP"
echo "pipeline complete -> $OUT/crono_gen_*.sprite + sprites/crono_gen_sheet.png + gifs"
