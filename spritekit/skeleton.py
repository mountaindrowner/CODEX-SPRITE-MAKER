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

JOINT_ORDER = [
    "head_top", "head", "neck", "shoulder_l", "shoulder_r",
    "elbow_l", "elbow_r", "hand_l", "hand_r", "pelvis",
    "hip_l", "hip_r", "knee_l", "knee_r", "foot_l", "foot_r",
]
_ABBR = {
    "head_top": "ht", "head": "hd", "neck": "nk", "shoulder_l": "sL",
    "shoulder_r": "sR", "elbow_l": "eL", "elbow_r": "eR", "hand_l": "hL",
    "hand_r": "hR", "pelvis": "pv", "hip_l": "pL", "hip_r": "pR",
    "knee_l": "kL", "knee_r": "kR", "foot_l": "fL", "foot_r": "fR",
}


def _abbr(name: str) -> str:
    return _ABBR.get(name, name[:2])


def _col_label(n: int) -> str:
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


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

    def worksheet(self, pose: str, base: Image.Image, scale: int,
                  step: int = 4, margin: int = 22) -> Image.Image:
        """A rigging worksheet: sprite + labelled coordinate grid + the skeleton
        with each joint named, so a human can read/correct joint positions."""
        w, h = self.frame_size
        body = Image.new("RGBA", base.size, (26, 28, 34, 255))
        body.alpha_composite(base.convert("RGBA"))
        canvas = Image.new("RGBA", (body.width + margin, body.height + margin),
                           (14, 14, 18, 255))
        canvas.paste(body, (margin, margin))
        d = ImageDraw.Draw(canvas)
        for cx in range(0, w + 1, step):
            x = margin + cx * scale
            d.line([(x, margin), (x, canvas.height)], fill=(255, 255, 255, 45))
            if cx < w:
                d.text((x + 2, 5), _col_label(cx), fill=(200, 200, 200, 255))
        for cy in range(0, h + 1, step):
            y = margin + cy * scale
            d.line([(margin, y), (canvas.width, y)], fill=(255, 255, 255, 45))
            if cy < h:
                d.text((3, y + 1), str(cy), fill=(200, 200, 200, 255))
        joints = self.poses[pose]
        c = lambda p: (margin + p[0] * scale + scale // 2, margin + p[1] * scale + scale // 2)
        for a, b in self.bones:
            if a in joints and b in joints:
                d.line([c(joints[a]), c(joints[b])], fill=BONE_COL, width=max(1, scale // 4))
        r = max(2, scale // 2)
        for name, p in joints.items():
            cx, cy = c(p)
            col = HEAD_COL if name in ("head", "head_top") else JOINT_COL
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(10, 10, 10, 255))
            d.text((cx + r + 1, cy - r - 1), _abbr(name), fill=(255, 255, 255, 255))
        return canvas

    def joint_table(self, pose: str) -> str:
        lines = [f"{pose}:"]
        for name in JOINT_ORDER:
            if name in self.poses[pose]:
                x, y = self.poses[pose][name]
                lines.append(f"  {name}: {x},{y}    # {_col_label(x)}{y}")
        return "\n".join(lines)

    def stick(self, pose: str, scale: int, bg=(24, 26, 32, 255)) -> Image.Image:
        w, h = self.frame_size
        img = Image.new("RGBA", (w * scale, h * scale), bg)
        return self._draw(img, self.poses[pose], scale)

    # -- flesh (skeleton -> base silhouette sprite) ------------------------
    def flesh(self, pose: str, frame_size: tuple[int, int] | None = None,
              colors: dict[str, str] | None = None,
              chars: dict[str, str] | None = None,
              palette: str = "kael") -> "Grid":
        """Rasterise a posed skeleton into a colour-named capsule body.

        Returns a :class:`~spritekit.grid.Grid` at ``frame_size`` (defaults to a
        2x the rig frame). Limbs become rounded capsules, the torso fills the
        shoulder span, and the head is an ellipse with a hair cap. This is the
        "flesh the bones" step of the construction loop — a clean base to refine
        by hand, not finished art.
        """
        from .grid import Grid  # local import to avoid a cycle

        rw, rh = self.frame_size
        tw, th = frame_size or (rw * 2, rh * 2)
        mul = tw / rw  # rig cell -> target pixels (assumes matched aspect)
        j = self.poses[pose]

        col = {"outline": "outline", "skin": "skin", "hair": "hair",
               "tunic": "tunic", "trousers": "trousers", "boots": "boots"}
        if colors:
            col.update(colors)
        ch = {"outline": "o", "skin": "s", "hair": "h",
              "tunic": "t", "trousers": "r", "boots": "b"}
        if chars:
            ch.update(chars)

        # Distinct RGBA sentinels per material so we can read pixels back exactly.
        SENT = {"outline": (1, 0, 0, 255), "skin": (2, 0, 0, 255),
                "hair": (3, 0, 0, 255), "tunic": (4, 0, 0, 255),
                "trousers": (5, 0, 0, 255), "boots": (6, 0, 0, 255)}
        sent_to_mat = {v: k for k, v in SENT.items()}

        img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        def pt(name):
            return (j[name][0] * mul + mul / 2, j[name][1] * mul + mul / 2)

        def seg(a, b, width, fill):
            pa, pb = pt(a), pt(b)
            d.line([pa, pb], fill=fill, width=max(1, int(round(width))))
            r = width / 2
            for (x, y) in (pa, pb):
                d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

        # thicknesses in RIG cells (scaled to target by *mul)
        shoulder_w = abs(j["shoulder_l"][0] - j["shoulder_r"][0]) or 6
        T_TORSO = max(shoulder_w, 5)
        limbs = [
            ("neck", "pelvis", T_TORSO, "tunic"),
            ("neck", "shoulder_l", 2.2, "tunic"), ("neck", "shoulder_r", 2.2, "tunic"),
            ("shoulder_l", "elbow_l", 2.2, "tunic"), ("elbow_l", "hand_l", 1.7, "skin"),
            ("shoulder_r", "elbow_r", 2.2, "tunic"), ("elbow_r", "hand_r", 1.7, "skin"),
            ("pelvis", "hip_l", 2.6, "trousers"), ("pelvis", "hip_r", 2.6, "trousers"),
            ("hip_l", "knee_l", 2.8, "trousers"), ("knee_l", "foot_l", 2.4, "boots"),
            ("hip_r", "knee_r", 2.8, "trousers"), ("knee_r", "foot_r", 2.4, "boots"),
        ]

        head_h = max(4, abs(j["head_top"][1] - j["neck"][1]))
        hw = head_h * 0.82 * mul          # head width (px)
        hh = head_h * 1.0 * mul           # head height (px)
        hcx, hcy = pt("head")

        # 1) outline pass: every limb + head fattened, in the outline sentinel
        for a, b, t, _m in limbs:
            seg(a, b, t * mul + 2 * mul, SENT["outline"])
        d.ellipse([hcx - hw / 2 - mul, hcy - hh / 2 - mul,
                   hcx + hw / 2 + mul, hcy + hh / 2 + mul], fill=SENT["outline"])

        # 2) fill pass: limbs at their true width
        for a, b, t, m in limbs:
            seg(a, b, t * mul, SENT[m])

        # 3) head: skin ellipse, then a hair cap over the top ~55%
        d.ellipse([hcx - hw / 2, hcy - hh / 2, hcx + hw / 2, hcy + hh / 2],
                  fill=SENT["skin"])
        htx, hty = pt("head_top")
        cap_cy = (hty + hcy) / 2
        d.ellipse([hcx - hw / 2, cap_cy - hh * 0.55, hcx + hw / 2, cap_cy + hh * 0.18],
                  fill=SENT["hair"])

        # rasterise -> grid of legend chars
        px = img.load()
        legend = {ch[m]: col[m] for m in ("outline", "skin", "hair", "tunic", "trousers", "boots")}
        rows = []
        for y in range(th):
            line = []
            for x in range(tw):
                r, g, b, a = px[x, y]
                if a == 0:
                    line.append(".")
                else:
                    mat = sent_to_mat.get((r, g, b, 255), "outline")
                    line.append(ch[mat])
            rows.append("".join(line))
        return Grid(f"{self.name}_{pose}_flesh", tw, th, palette, legend, rows)

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
