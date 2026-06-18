# Crono reference sheet — frame map

Sheet is 4 cols x 4 rows of 32x48 frames, files `crono_r{row}_c{col}.sprite`
(row 0 = top). Each **row** is one facing; the **columns** are walk-cycle poses.

| Frame   | Facing | Walk role                |
|---------|--------|--------------------------|
| r0_c0   | down   | neutral (standing)       |
| r0_c1   | down   | step (mid-stride)        |
| r0_c2   | down   | neutral / standing alt   |
| r0_c3   | down   | step (opposite stride)   |
| r1_c0   | down   | neutral (standing)       |
| r1_c1   | left   | step (profile, leg out)  |
| r1_c2   | down   | neutral / standing alt   |
| r1_c3   | right  | step (profile, leg out)  |
| r2_c0   | down   | neutral (standing)       |
| r2_c1   | left   | step (profile, leg out)  |
| r2_c2   | down   | neutral / standing alt   |
| r2_c3   | right  | step (profile, leg out)  |
| r3_c0   | up     | neutral (standing, back) |
| r3_c1   | up     | step (back, leg out)     |
| r3_c2   | up     | neutral / standing alt   |
| r3_c3   | up     | step (opposite stride)   |

Notes:
- Row 0 = facing DOWN (face + headband to viewer). Row 3 = facing UP (back of
  head, no face, hair spiked away). Profiles (LEFT / RIGHT) sit in the c1/c3
  columns of rows 1 and 2.
- r1_c1 / r2_c1 are clear LEFT profiles; r1_c3 / r2_c3 are clear RIGHT profiles.
- Frames in a row vary by stride phase; pair a `c0` neutral with two opposing
  step frames for a 0,1,0,2 cycle.

## Recommended walk mapping

- **DOWN walk:** `crono_r0_c0` (neutral) + `crono_r0_c1` (step_left) +
  `crono_r0_c3` (step_right).
- **UP walk:** `crono_r3_c0` (neutral) + `crono_r3_c1` (step_left) +
  `crono_r3_c3` (step_right).
- **LEFT walk (profile):** `crono_r1_c0`-style neutral + `crono_r1_c1` and
  `crono_r2_c1` as the two step frames (left-facing strides).
- **RIGHT walk:** produce by **mirroring the LEFT frames** (per repo convention,
  do not hand-draw); the native right-profile frames `r1_c3` / `r2_c3` confirm
  the target pose.
