"""TODO-120: whether the truth's edges are among the candidates of proto_corners.py (photos as taken).
usage: uv run python archives/agents/TODO-120/proto_stages.py <x.truth.json> ..."""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, "recognizer")
import corners as C

for path in sys.argv[1:]:
    t = json.load(open(path))
    img = cv2.imread(str(Path(path).parent / t["image"]))
    small, s = C.shrink(img)
    h, w = small.shape[:2]
    TL, TR, BR, BL = np.float64(t["corners_TL_TR_BR_BL"]) * s
    p0, p1, p2, p3 = BL, TL, TR, BR                     # top-left, top-right, bottom-right, bottom-left in the photo
    hk = lambda a, b: 200 * (b[1] - a[1]) / (b[0] - a[0])
    vk = lambda a, b: 200 * (b[0] - a[0]) / (b[1] - a[1])
    top = (hk(p0, p1), p0[1] - p0[0] * hk(p0, p1) / 200)
    bot = (hk(p3, p2), p3[1] - p3[0] * hk(p3, p2) / 200)
    left = (vk(p0, p3), p0[0] - p0[1] * vk(p0, p3) / 200)
    right = (vk(p1, p2), p1[0] - p1[1] * vk(p1, p2) / 200)
    gx, gy = C._gradients(small)
    ends = C._h_lines(gx, gy)
    at = lambda k, c, v: c + v * k / 200
    up = C._Upright(gx, gy)
    yt, yb = at(*top, w / 2), at(*bot, w / 2)
    band = (int(yt + 0.03 * (yb - yt)), int(yb - 0.03 * (yb - yt)))
    vl = up.lines(max(0, band[0]), min(h, band[1]))
    print(Path(path).name, f"{w}x{h}")
    print(f"  truth: top {top[0]:.0f},{at(*top, w/2):.0f}  bottom {bot[0]:.0f},{at(*bot, w/2):.0f}  left {left[0]:.0f},{at(*left, (yt+yb)/2):.0f}  right {right[0]:.0f},{at(*right, (yt+yb)/2):.0f}  (slope /200, where it crosses the middle)")
    print("  ends:", [(k, round(at(k, c, w / 2))) for k, c, _ in ends])
    print("  uprights in the truth band:", [(k, round(at(k, c, (yt + yb) / 2)), round(sh, 2)) for k, c, sh in vl])
