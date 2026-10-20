"""TODO-079: the readings _pip_found makes on one sample (how many, how long) and the dice from them."""

import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "recognizer"))
import board  # noqa: E402
import dice  # noqa: E402

name = sys.argv[1] if len(sys.argv) > 1 else "photo-black-blue-oblique"
cap = {}
dice.read_dice = lambda img, H, lay, pitch, circles=(), debug=None: (
    cap.update(img=img, H=H, lay=lay, pitch=pitch, circles=circles)
    or dict(values=None, dice=[])
)
board.dice_reader.read_dice = dice.read_dice
t = json.loads((ROOT / f"samples/{name}.truth.json").read_text())
img = cv2.imread(str(ROOT / "samples" / t["image"]))
board.recognize(img, np.float64(t["corners_TL_TR_BR_BL"]), home=t["home"])
import math  # noqa: E402

import exact  # noqa: E402

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
ground = exact.warp(
    img,
    exact.mul3(np.diag([k, k, 1.0]), exact.inv3(H)),
    (int(lay.w * k), int(lay.h * k)),
)
gray = cv2.cvtColor(ground, cv2.COLOR_BGR2GRAY)
t0 = time.time()
b = dice._pip_found(gray, pitch, k, lay, cap["circles"])
print(name, "pip readings", len(b), f"{time.time() - t0:.2f}s")
lab = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab)
dd, values, out = dice._read(gray, lab, b, k, lay, pitch, hue=25)
print("values", values)
for d, o in zip(dd, out):
    print(
        f"  ({d['x']:.0f},{d['y']:.0f}) side={d['side']:.0f} value={d['value']} seen={d['seen']} "
        f"sure={d['sure']} bar={o['on_bar']} dark={d['dark_pips']} lab={d['lab']}"
    )
# the readings drawn on the ground image (pip_readings.png, around the dice)
g = ground.copy()
for r in b:
    cv2.drawContours(
        g, [r["hull"]], -1, (0, 0, 255) if r["dark_pips"] else (0, 255, 255), 1
    )
    cv2.putText(
        g, str(r["value"]), (int(r["x"]), int(r["y"])), 0, 0.5, (255, 0, 255), 1
    )
cv2.imwrite(str(Path(__file__).parent / f"pip_readings_{name}.png"), g)
