# Skeleton studio (p5.js)

An experiment in **p5.js**: an animated, interactive companion to the static rig
editor. Where the rig-editor is for precise offline joint placement, this is for
*watching movement and judging body shape*.

- **Play walk** — animates the walk cycle (`0,1,0,2`) for the chosen facing
  (down has all 3 frames; up/left animate once their step poses are added).
- **Flesh: on** — wraps the bones in a procedural capsule body (skin/tunic/
  trousers/boots + outline) so you can preview the silhouette the skeleton implies.
- **Drag joints** (when paused) to edit the current frame; **frame** picks 0/1/2.
- **Overlay** a reference sprite to rig directly on top of it.
- **Copy / download rig JSON** to send back.

## Open it
- **Local:** open `index.html` in a browser. It pulls p5.js from a CDN, so it
  needs internet the first time.
- **Hosted:** if the repo is public,
  `https://raw.githack.com/mountaindrowner/codex-sprite-maker/claude/pixel-art-grid-generator-3a91q5/tools/skeleton-studio/index.html`

## Rebuild
```
python3 - <<'PY'
import pathlib
rig=pathlib.Path('styles/chrono-trigger/rig.json').read_text().strip()
tpl=pathlib.Path('tools/skeleton-studio/template.html').read_text()
pathlib.Path('tools/skeleton-studio/index.html').write_text(tpl.replace('__RIG__',rig))
PY
```

Framework note: the toolkit (`spritekit`) is **Python + Pillow**; the rig-editor is
**vanilla JS + Canvas**; this studio is the one **p5.js** piece (CDN dependency).
