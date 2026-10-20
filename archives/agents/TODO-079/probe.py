"""TODO-079: where does dice.py lose the green dice of photo-black-blue-oblique?

uv run python archives/agents/TODO-079/probe.py
Prints, per stage of dice._bodies / pips / _face_value, what happens to the blobs near the two dice
(in the warped "ground" image of read_dice, same as dbg_dice.jpg).
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "recognizer"))
import board  # noqa: E402
import dice  # noqa: E402
import exact  # noqa: E402

OUT = Path(__file__).parent
# the two dice in dbg_dice.jpg (ground pixels): the six and the two
DICE = {"six": (625, 255), "two": (655, 375)}
R = 60

cap = {}
orig = dice.read_dice


def spy(img, H, lay, pitch, circles=(), debug=None):
    cap.update(img=img, H=H, lay=lay, pitch=pitch, circles=circles)
    return orig(img, H, lay, pitch, circles, debug)


board.dice_reader.read_dice = spy
t = json.loads((ROOT / "samples/photo-black-blue-oblique.truth.json").read_text())
img = cv2.imread(str(ROOT / "samples" / t["image"]))
board.recognize(img, np.float64(t["corners_TL_TR_BR_BL"]), home=t["home"])

H, lay, pitch = cap["H"], cap["lay"], cap["pitch"]
corners = exact.apply_h(H, lay.src_pts())
k = exact.snap(
    np.clip(
        math.sqrt(exact.polygon_area(corners) / (lay.w * lay.h)),
        1,
        max(1.0, dice.WORK_PITCH / pitch),
    ),
    2.0**-20,
)
size = (int(lay.w * k), int(lay.h * k))
ground = exact.warp(img, exact.mul3(np.diag([k, k, 1.0]), exact.inv3(H)), size)
gray = cv2.cvtColor(ground, cv2.COLOR_BGR2GRAY)
P = pitch * k
smin, smax = dice.SIDE_MIN * P, dice.SIDE_MAX * P
print(f"pitch={pitch:.1f} k={k:.3f} pitch*k={P:.1f} side range {smin:.1f}..{smax:.1f}")
for name, (x, y) in DICE.items():
    g = gray[y - R : y + R, x - R : x + R]
    print(f"{name}: gray around p5/p50/p95 = {np.percentile(g, [5, 50, 95])}")
cv2.imwrite(str(OUT / "crop_gray.png"), gray[180:440, 540:720])


def which(cx, cy):
    for name, (x, y) in DICE.items():
        if abs(cx - x) < R and abs(cy - y) < R:
            return name
    return None


stats = Counter()
samples = {}
small = np.ones((3, 3), np.uint8)
for t_ in range(16, 250, 8):
    for light in (True, False):
        bw = ((gray > t_) if light else (gray < t_)).astype(np.uint8)
        bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, small)
        n, lab, st, cen = cv2.connectedComponentsWithStats(bw)
        for i in range(1, n):
            x, y, w, h, a = st[i]
            d = which(*cen[i])
            if d is None:
                continue
            key = (d, t_, "light" if light else "dark")
            big = max(w, h)
            if not (0.7 * smin <= big <= 1.45 * smax and a >= 0.4 * smin * smin):
                stats[(d, "size(bbox)")] += 1
                continue
            pts = cv2.findNonZero((lab[y : y + h, x : x + w] == i).astype(np.uint8)) + (
                x,
                y,
            )
            hull = cv2.convexHull(pts)
            (cx, cy), (rw, rh), ang = exact.min_area_rect(hull)
            side = (rw + rh) / 2
            fill = cv2.contourArea(hull) / (rw * rh)
            nc = len(cv2.approxPolyDP(hull, 0.05 * cv2.arcLength(hull, True), True))
            info = f"thr={t_} {key[2]} box {rw:.0f}x{rh:.0f} side={side:.0f} aspect={max(rw, rh) / min(rw, rh):.2f} fill={fill:.2f} corners={nc}"
            if not smin <= side <= smax:
                why = "side"
            elif max(rw, rh) > 1.3 * min(rw, rh):
                why = "aspect"
            elif fill < 0.86:
                why = "fill"
            elif nc != 4:
                why = "corners"
            else:
                why = "OK"
                b = dict(x=cx, y=cy, side=side, ang=ang, hull=hull)
                reads = []
                for dark in (True, False):
                    for find in (dice._pips, dice._pips_level):
                        for f in (0.35, 0.5, 0.65):
                            p = find(gray, b, dark, f)
                            reads.append(
                                (dark, find.__name__, f, len(p), dice._face_value(p, b))
                            )
                info += f" reads={[r for r in reads if r[3]]}"
            stats[(d, why)] += 1
            samples.setdefault((d, why), []).append(info)

for k_, v in sorted(stats.items()):
    print(k_, v)
for k_, v in sorted(samples.items()):
    print(f"--- {k_} ({len(v)})")
    for s in v[:6]:
        print("  ", s)


# stage 2-3 with hand-placed bodies (the top face, judged from crop_dice.png): would the pips
# and the face be read if _bodies had found the die?
def square(cx, cy, s, ang=0.0):
    r = cv2.boxPoints(((cx, cy), (s, s), ang))
    return dict(x=cx, y=cy, side=s, ang=ang, hull=np.int32(r).reshape(-1, 1, 2))


print("--- hand-placed bodies")
for name, (cx, cy) in {"six": (605, 240), "two": (649, 360)}.items():
    for s in (36, 42, 50, 60):
        b = square(cx, cy, s)
        reads = []
        for dark in (True, False):
            for find in (dice._pips, dice._pips_level):
                for f in (0.35, 0.5, 0.65):
                    p = find(gray, b, dark, f)
                    reads.append(
                        (dark, find.__name__[1:], f, len(p), dice._face_value(p, b))
                    )
        print(name, s, [r for r in reads if r[3]])

# the masks _bodies sees around the dice, at a few levels (light: gray > t)
strip = [gray[180:440, 540:720]] + [
    ((gray[180:440, 540:720] > t_) * 255).astype(np.uint8) for t_ in (48, 64, 80, 96)
]
cv2.imwrite(str(OUT / "masks_light_48_64_80_96.png"), np.hstack(strip))
