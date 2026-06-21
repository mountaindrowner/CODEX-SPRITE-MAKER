# mini-rpg style

A small **16-bit RPG mini-character** style, emulated from the reference tiny-RPG
class sheets (knight, cleric, ranger, mage, goblin). Deliberately simple and
chunky — the opposite end of the size range from our 64×96 Chrono-Trigger work.

## Rules
- **Canvas:** 24×22, character ~20px tall on a base shadow (~2.5 heads tall).
- **View:** front-facing, near-symmetric. Right = same as left (no separate mirror).
- **Outline-light:** no black keyline. Form reads from **one darker shade per
  material** (`*_shadow`) under a consistent **top-left light**, plus the dark
  background/base for separation. Eyes are the only pure-dark pixels.
- **Palette:** ~12 colours — skin (+shadow), hair (+shadow), tunic (+shadow),
  pants (+shadow), boots, belt, and a dark **base** oval under the feet (present on
  every frame, the "standing on a tile" look of the references).
- **Silhouette:** big head, compact torso, short legs with a small gap, stubby
  arms at the sides (a villager carries no weapon; classes would add a raised
  sword/staff at the hands).
- **Idle:** a 2-frame breathing bob (`villager_idle_0/1`) — frame 1 lowers the
  body 1px (legs compress) over a planted base; play order `0,1` at ~3 fps.

## Build a new mini-rpg character
Author the grid by hand at 24×22 (this style is too small for the skeleton/flesh
pipeline). Reuse `palette.json`, keep the base-shadow oval, shade right/down with
`*_shadow`, and swap the tunic colour / add a held item for a class variant.
