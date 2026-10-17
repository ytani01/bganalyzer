"""TODO-120: read the photos taken from beside the board with the checkers' tops moved back over their points.
usage: uv run python archives/agents/TODO-120/proto_parallax.py <x.truth.json> ...

Seen from beside, a checker's top shows away from the camera from where it stands (it is as high as
it is thick): in the view from above, every stack is shifted along the points the same way, by up to
half a point. Before the circles are given to their points, the shift is measured from the circles
(the one that brings the most of them onto a column) and taken off. Run with the truth's corners,
through evaluate.py, once as it is and once with the shift taken off."""
import sys
import numpy as np
sys.path.insert(0, "recognizer")
import checkers, evaluate

orig = checkers.count_from_circles

import os
SHIFT = float(os.environ["SHIFT"]) if "SHIFT" in os.environ else None   # points; None: measured from the circles

import board, geometry
_last = {}
_to_ground = board.to_ground

def to_ground(img, H, m, size):          # keep the last homography (layout -> photo) for shifted()
    _last["H"], _last["shape"] = H, img.shape
    return _to_ground(img, H, m, size)

def camera(H, shape):
    """The camera's centre over the board, in layout units (x, y, height)."""
    K, r1, r2, r3, t = geometry.camera_from_h(H, shape)
    R = np.stack([r1, r2, r3], 1)
    c = -R.T @ t
    return c if c[2] > 0 else -c

def shifted(circles, lay, pitch):
    """Each circle (a checker's top, as high as the checker is thick) moved to where the checker
    stands: towards the point under the camera, by thickness / (camera's height - thickness)."""
    if len(circles) < 4:
        return orig(circles, lay, pitch)
    cx, cy, ch = camera(_last["H"], _last["shape"])
    cols = np.array([lay.col_x(i) for i in range(12)])
    pts = np.array([(c[0], c[1]) for c in circles])
    def moved(z):
        f = (ch - z) / ch
        return np.array([cx, cy]) + (pts - [cx, cy]) * f
    def fit(z):
        d = np.min(np.abs(moved(z)[:, 0][:, None] - cols[None, :]), 1)
        return int((d < 0.2 * lay.pw).sum()), -z
    z = SHIFT * pitch if SHIFT is not None else max(np.linspace(0, 0.6, 25) * pitch, key=fit)
    shifted.last = z / pitch
    shifted.cam = (cx / lay.w, cy / lay.h, ch / lay.w)
    mv = moved(z)
    return orig([(x, y, *rest) for (x, y), (_, _, *rest) in zip(mv, circles)], lay, pitch)

board.to_ground = to_ground
import board
for path in sys.argv[1:]:
    out = []
    for f in (orig, shifted):
        board.count_from_circles = f
        r = evaluate.run(path)
        out.append((24 - len(r[2]), sorted(p for p, *_ in r[2])))
    board.count_from_circles = orig
    print(path.rsplit("/", 1)[-1], f"thickness {shifted.last:.2f} of a checker, camera at {tuple(round(v, 2) for v in shifted.cam)}:", out[0][0], "->", out[1][0], " wrong before", out[0][1], " after", out[1][1])
