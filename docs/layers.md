# Layer decomposition — read the construction of a finished sprite

Finished pixel art is built in layers. To *understand* (and later reproduce) a
style, we reverse-engineer that stack from an official sprite:

```
skeleton -> silhouette -> outline -> flat colour -> shading -> light -> highlights
```

`layers` classifies every palette colour into a **material** (skin, hair, tunic …)
and a **role/tier** (outline / base / shadow / light / highlight), infers the
**light direction**, and renders an exploded, labelled breakdown so each layer is
legible on its own.

```
python3 -m spritekit.cli layers styles/chrono-trigger/reference/recreation/crono_r0_c0.sprite \
  --out breakdown.png --json crono.layers.json \
  --rig styles/chrono-trigger/rig.json --pose down_0
```

The breakdown PNG has one panel per layer: **FULL**, **SKELETON** (if a rig is
passed), **SILHOUETTE** (the mass), **OUTLINE** (line work), **FLATS** (base
fills), **SHADING** (shadow tiers), **LIGHT** (light tiers), **HIGHLIGHTS**, and a
**VALUE MAP** (grayscale luminance — the value structure with hue removed).

## The place to correct

Classification is a heuristic (name suffixes like `_shadow`/`_light`, then a
per-material luminance ranking). It will sometimes guess wrong — so it is
**correctable**. `--json` writes a sidecar:

```json
"colors": {
  "skin":        { "material": "skin",  "role": "base",   "tier": 0,  "hex": "#f8c898", "px": 12 },
  "skin_shadow": { "material": "skin",  "role": "shadow", "tier": -1, "hex": "#f88068", "px": 22 },
  "tunic_light": { "material": "tunic", "role": "light",  "tier": 2,  "hex": "#50d0e8", "px": 24 }
}
```

Edit any colour's `material`, `role`, or `tier`, then feed the file back:

```
python3 -m spritekit.cli layers SPRITE --apply crono.layers.json --out breakdown.png
```

The re-render honours your edits. That corrected sidecar becomes the locked,
human-verified description of how the sprite is constructed — the basis for
writing the style's shading rules and for building new sprites the same way.
