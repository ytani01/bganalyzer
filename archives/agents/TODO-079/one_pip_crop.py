import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, "recognizer")
import board  # noqa: E402
import dice  # noqa: E402
import exact  # noqa: E402

name, pts, out = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
cap = {}
o = dice.read_dice
board.dice_reader.read_dice = lambda img, H, lay, pitch, circles=(), debug=None: (
    cap.update(H=H, lay=lay, pitch=pitch),
    o(img, H, lay, pitch, circles),
)[1]
t = json.loads(Path(f"samples/{name}.truth.json").read_text())
img = cv2.imread(f"samples/{t['image']}")
board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"], side=t.get("side"))
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
crops = []
for x, y in pts:
    px, py = exact.apply_h(H, np.float64([[x / k, y / k]]))[0]
    r = int(0.6 * pitch * math.sqrt(exact.polygon_area(corners) / (lay.w * lay.h)))
    c = img[max(int(py) - r, 0) : int(py) + r, max(int(px) - r, 0) : int(px) + r]
    crops.append(cv2.resize(c, (300, 300), interpolation=cv2.INTER_CUBIC))
    print(name, (x, y), "-> photo", (round(px), round(py)))
cv2.imwrite(out, np.hstack(crops))
