# The `.sprite` grid format

A `.sprite` file is a plain-text description of one pixel grid. It is designed to
be authored and read directly in a monospace editor: each character is one pixel.

```
name: hero_down_0
size: 16x16
palette: pokemon-overworld
legend:
  .: transparent
  o: outline
  s: skin
  c: cap
grid: |
  ......oooo......
  ....ollcccco....
  ...(height rows, each exactly width characters)...
```

## Fields

- **name** — identifier; also used as the frame key in sheet coordinate manifests.
- **size** — `WIDTHxHEIGHT` in pixels.
- **palette** — the palette name. Tools resolve it to
  `styles/<palette>/palette.json` (or pass `--palette PATH` explicitly).
- **legend** — maps a single character to a palette **colour name**. The
  character `.` always means `transparent`, whether or not it is listed.
- **grid** — a literal block (`grid: |`). Each following line indented by two
  spaces is one pixel row. Every row must be exactly `width` characters, and there
  must be exactly `height` rows.

## Rules

- One character per pixel. Use `.` for transparent.
- Every character that appears in the grid must be defined in the legend.
- Colour names must exist in the referenced palette.
- A legend may contain entries that the grid does not use (harmless).

## Palette files

A palette is JSON: a name and a map of colour name → hex (or `null` for
transparent). `transparent` is always available.

```json
{
  "name": "pokemon-overworld",
  "colors": {
    "transparent": null,
    "outline": "#281d2b",
    "skin": "#f4c89a"
  }
}
```

## Why text grids

Because Claude works in text, the grid *is* the editable artwork: Claude can place
pixels one at a time, see the silhouette in monospace, and diff two grids
pixel-for-pixel. Rendering to PNG is just a view of the same data.
