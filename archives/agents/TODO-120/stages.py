"""TODO-120: where the corner guess goes wrong on the photos taken from beside the board.
usage: uv run python archives/agents/TODO-120/stages.py samples/x.truth.json ...
For each photo, against the truth's corners (in the shrunk photo): the slopes of the four edges,
whether a far / near candidate and a left / right candidate lie near each truth edge, the shape
checks (aspect, width), and the structure score of the truth quad and of the one found."""
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
    q = np.float64(t["corners_TL_TR_BR_BL"]) * s
    TL, TR, BR, BL = q
    hk = lambda a, b: 200 * (b[1] - a[1]) / (b[0] - a[0])          # y = c + x k / 200
    vk = lambda a, b: 200 * (b[0] - a[0]) / (b[1] - a[1])          # x = c + y k / 200
    far, near = (hk(TL, TR), TL[1] - TL[0] * hk(TL, TR) / 200), (hk(BL, BR), BL[1] - BL[0] * hk(BL, BR) / 200)
    left, right = (vk(TL, BL), TL[0] - TL[1] * vk(TL, BL) / 200), (vk(TR, BR), TR[0] - TR[1] * vk(TR, BR) / 200)
    gx, gy = C._gradients(small)
    hl = C._h_lines(gx, gy)
    at = lambda k, c, x: c + x * k / 200
    tol = 0.02 * max(h, w)
    def near_h(e):
        return [(k, c) for k, c, _ in hl if abs(at(k, c, w / 2) - at(e[0], e[1], w / 2)) < tol and abs(k - e[0]) < 8]
    up = C._Upright(gx, gy)
    yt, yb = at(*far, w / 2), at(*near, w / 2)
    band = (int(yt + 0.03 * (yb - yt)), int(yb - 0.03 * (yb - yt)))
    vl = up.lines(max(0, band[0]), min(h, band[1]))
    def near_v(e):
        ym = (band[0] + band[1]) / 2
        return [(k, c, round(sh, 2)) for k, c, sh in vl if abs(at(k, c, ym) - at(e[0], e[1], ym)) < tol and abs(k - e[0]) < 8]
    # how much of the band each truth upright edge covers, with the coverage of the best line near it
    wid = (np.linalg.norm(TR - TL) + np.linalg.norm(BR - BL)) / 2
    hgt = (np.linalg.norm(BL - TL) + np.linalg.norm(BR - TR)) / 2
    sc = lambda qq: round(C._structure(C._view(small, qq, C.RW, C.RH, 0)[0]), 3)
    found = C.guess(small)
    print(f"{Path(path).name.removesuffix('.truth.json')}  size {w}x{h}")
    print(f"  slopes: far {far[0]:.0f} near {near[0]:.0f} left {left[0]:.0f} right {right[0]:.0f}  (/200; tried up to ±100)")
    print(f"  far cand: {near_h(far) or 'NONE'}  near cand: {near_h(near) or 'NONE'}")
    print(f"  h lines: {[(k, c) for k, c, _ in hl]}")
    print(f"  uprights in the truth band: {[(k, c, round(sh, 2)) for k, c, sh in vl]}")
    print(f"  left cand: {near_v(left) or 'NONE'}  right cand: {near_v(right) or 'NONE'}")
    print(f"  aspect {wid / hgt:.2f} (ok {C.ASPECT})  width {wid / w:.2f} (>= {C.MIN_WIDTH})  near/far width {np.linalg.norm(BR - BL) / np.linalg.norm(TR - TL):.2f}")
    print(f"  structure: truth {sc(q)}  found {None if found is None else sc(found)}  (min {C.MIN_SCORE})")
