"""Build a self-contained rig-editor index.html with sprites + rig embedded.

Run from anywhere:  python3 tools/rig-editor/build.py
"""
import base64
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from spritekit.grid import Grid          # noqa: E402
from spritekit.palette import Palette    # noqa: E402
from spritekit.render import render_grid  # noqa: E402

REC = ROOT / "styles/chrono-trigger/reference/recreation"
PAL = Palette.load(REC / "palette.json")
HERE = Path(__file__).parent


def data_url(grid: Grid) -> str:
    buf = io.BytesIO()
    render_grid(grid, PAL, 1).save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


SPRITES = [
    ("crono down", "crono_r0_c0", "down_0"),
    ("crono up",   "crono_r3_c0", "up_0"),
    ("crono left", "crono_r1_c1", "left_0"),
]

sprites = []
for name, fname, pose in SPRITES:
    g = Grid.load(REC / f"{fname}.sprite")
    sprites.append({"name": name, "w": g.width, "h": g.height, "pose": pose, "src": data_url(g)})

rig = json.loads((ROOT / "styles/chrono-trigger/rig.json").read_text())
data = {"rig": rig, "rig0": json.loads(json.dumps(rig)), "sprites": sprites}

html = (HERE / "template.html").read_text().replace("__RIG_EDITOR_DATA__", json.dumps(data))
(HERE / "index.html").write_text(html)
print(f"wrote {HERE/'index.html'} ({len(html)} bytes, {len(sprites)} sprites, {len(rig['poses'])} poses)")
