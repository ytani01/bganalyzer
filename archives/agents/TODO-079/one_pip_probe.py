"""TODO-079 (1 の目): what the shape way and the pip way find on one sample.

uv run python archives/agents/TODO-079/one_pip_probe.py <sample name>
Prints the dice of each way (ground pixels) and writes one_pip_<name>.png: the ground image with
the shape bodies (yellow), the pip readings (red), and the read dice labelled."""

import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "recognizer"))
import board  # noqa: E402
import dice  # noqa: E402
import exact  # noqa: E402

name = sys.argv[1]
cap = {}
orig = dice.read_dice


def spy(img, H, lay, pitch, circles=(), debug=None):
    cap.update(img=img, H=H, lay=lay, pitch=pitch, circles=circles)
    return orig(img, H, lay, pitch, circles, debug)


board.dice_reader.read_dice = spy
t = json.loads((ROOT / f"samples/{name}.truth.json").read_text())
img = cv2.imread(str(ROOT / "samples" / t["image"]))
_, info = board.recognize(
    img, t["corners_TL_TR_BR_BL"], home=t["home"], side=t.get("side")
)
print(name, "truth", t.get("dice"), "read", info["dice"]["values"])
img, H, lay, pitch, circles = (cap[k] for k in ("img", "H", "lay", "pitch", "circles"))
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
lab = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab)
print(f"  pitch*k={pitch * k:.1f} ground {ground.shape[1]}x{ground.shape[0]}")
g = ground.copy()
for way, found, hue, colour in (
    (
        "shape",
        dice._found(gray, dice._bodies(gray, pitch * k), circles, k),
        15,
        (0, 255, 255),
    ),
    ("pip", dice._pip_found(gray, pitch, k, lay, circles), 25, (0, 0, 255)),
):
    dd, values, out = dice._read(gray, lab, found, k, lay, pitch, hue=hue)
    print(f"  {way}: readings {len(found)}, values {values}")
    for d, o in zip(dd, out):
        print(
            f"    ({d['x']:.0f},{d['y']:.0f}) side={d['side']:.0f} value={d['value']} "
            f"n={len(d['seen'])} seen={sorted(set(d['seen']))} sure={d['sure']} "
            f"bar={o['on_bar']} dark={d['dark_pips']} lab={np.round(d['lab']).astype(int).tolist()}"
        )
        cv2.drawContours(g, [d["hull"]], -1, colour, 1)
        cv2.putText(
            g, f"{way[0]}{d['value']}", (int(d["x"]), int(d["y"])), 0, 0.5, colour, 1
        )
cv2.imwrite(str(Path(__file__).parent / f"one_pip_{name}.png"), g)
