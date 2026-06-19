"""Skeleton / rig — the bare-bones internal structure of a figure.

A rig is named joints (head, neck, shoulders, elbows, hands, pelvis, hips, knees,
feet) positioned per *pose*, plus the bones connecting them. We lay it onto the
reference sprites to capture a style's PROPORTIONS and MOVEMENT, then reuse the
posed skeleton as the construction base for new characters:

    pose the skeleton -> flesh bones to a silhouette -> detail -> colour.

The proportions are read off with ``ratios`` (everything normalised to total
height), which is how we copy the Chrono-Trigger body plan onto an original.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

# Standard humanoid bone graph (joint-name pairs).
BONES = [
    ("head_top", "head"), ("head", "neck"),
    ("neck", "shoulder_l"), ("neck", "shoulder_r"), ("neck", "pelvis"),
    ("shoulder_l", "elbow_l"), ("elbow_l", "hand_l"),
    ("shoulder_r", "elbow_r"), ("elbow_r", "hand_r"),
    ("pelvis", "hip_l"), ("pelvis", "hip_r"),
    ("hip_l", "knee_l"), ("knee_l", "foot_l"),
    ("hip_r", "knee_r"), ("knee_r", "foot_r"),
]
BONE_COL = (90, 200, 255, 255)
JOINT_COL = (255, 210, 60, 255)
HEAD_COL = (255, 110, 110, 255)


class Rig:
    def __init__(self, name: str, frame_size: tuple[int, int],
                 poses: dict[str, dict[str, list[int]]], bones=None):
        self.name = name
        self.frame_size = tuple(frame_size)
        self.poses = poses
        self.bones = bones or BONES

    @classmethod
    def load(cls, path: str | Path) -> "Rig":
        d = json.loads(Path(path).read_text())
        bones = [tuple(b) for b in d["bones"]] if d.get("bones") else None
        return cls(d["name"], d["frame_size"], d["poses"], bones)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps({
            "name": self.name,
            "frame_size": list(self.frame_size),
            "bones": [list(b) for b in self.bones],
            "poses": self.poses,
        }, indent=2) + "\n")

    # -- drawing -----------------------------------------------------------
    def _draw(self, img: Image.Image, joints: dict, scale: int) -> Image.Image:
        d = ImageDraw.Draw(img)
        c = lambda p: (p[0] * scale + scale // 2, p[1] * scale + scale // 2)
        for a, b in self.bones:
            if a in joints and b in joints:
                d.line([c(joints[a]), c(joints[b])], fill=BONE_COL, width=max(1, scale // 4))
        r = max(2, scale // 2)
        for name, p in joints.items():
            cx, cy = c(p)
            col = HEAD_COL if name in ("head", "head_top") else JOINT_COL
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(20, 20, 20, 255))
        return img

    def overlay(self, pose: str, base: Image.Image, scale: int) -> Image.Image:
        img = base.convert("RGBA").copy()
        return self._draw(img, self.poses[pose], scale)

    def stick(self, pose: str, scale: int, bg=(24, 26, 32, 255)) -> Image.Image:
        w, h = self.frame_size
        img = Image.new("RGBA", (w * scale, h * scale), bg)
        return self._draw(img, self.poses[pose], scale)

    # -- proportions -------------------------------------------------------
    def ratios(self, pose: str) -> dict:
        j = self.poses[pose]

        def dy(a, b): return abs(j[a][1] - j[b][1])
        def dist(a, b):
            return ((j[a][0] - j[b][0]) ** 2 + (j[a][1] - j[b][1]) ** 2) ** 0.5

        top = min(p[1] for p in j.values())
        bot = max(p[1] for p in j.values())
        H = max(1, bot - top)
        head_h = dy("head_top", "neck")
        return {
            "total_height_px": H,
            "head_height_px": head_h,
            "heads_tall": round(H / max(1, head_h), 2),
            "head_pct": round(100 * head_h / H, 1),
            "torso_pct": round(100 * dy("neck", "pelvis") / H, 1),
            "leg_pct": round(100 * (dy("pelvis", "knee_l") + dy("knee_l", "foot_l")) / H, 1),
            "shoulder_w_px": abs(j["shoulder_l"][0] - j["shoulder_r"][0]),
            "hip_w_px": abs(j["hip_l"][0] - j["hip_r"][0]),
            "arm_len_px": round(dist("shoulder_l", "elbow_l") + dist("elbow_l", "hand_l"), 1),
            "leg_len_px": round(dist("hip_l", "knee_l") + dist("knee_l", "foot_l"), 1),
        }
