# Skeleton rig editor

A self-contained, drag-and-drop tool for placing skeleton joints on a sprite and
exporting the rig — so a human can give Claude the *exact* body-part positions.

## Open it

**Hosted (raw.githack.com — needs the repo to be public):**

```
https://raw.githack.com/mountaindrowner/codex-sprite-maker/claude/pixel-art-grid-generator-3a91q5/tools/rig-editor/index.html
```

**Local (always works):** download `index.html` and open it in any browser. It's
fully self-contained — sprites and rig are embedded, no server needed.

## Use it

1. Pick a sprite/pose from the dropdown (Crono down / up / left ship in it).
2. **Drag the labelled joints** onto the body. Arrow keys nudge the selected
   joint by 1px; `snap` keeps joints on whole pixels.
3. To rig your own sprite: load an image, set its **native** W/H (e.g. 32×48),
   click *rig this*, and drag the default skeleton onto it.
4. **Copy rig JSON** (or download `rig.json`) and send it back to Claude.

Joint labels: `ht` head-top, `hd` head, `nk` neck, `sL/sR` shoulders,
`eL/eR` elbows, `hL/hR` hands, `pv` pelvis, `pL/pR` hips, `kL/kR` knees,
`fL/fR` feet.

## Rebuild (after sprites/rig change)

```
python3 tools/rig-editor/build.py
```

Regenerates `index.html` with the current `styles/chrono-trigger/rig.json` and the
reference sprites embedded.
