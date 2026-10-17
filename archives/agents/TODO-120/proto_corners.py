"""TODO-120: a first try of the corner search for photos taken from beside the board, as taken (the bar across).
usage: uv run python archives/agents/TODO-120/proto_corners.py <x.truth.json> ...

Seen from beside, the playing area is a trapezoid: its two ends (where the bear-off trays are) run
across the photo, the near one wide at the bottom and the far one narrower above; its long edges
(where the triangles' bases are) lean in towards the top. The near player is on the left.
Tools taken from corners.py: shrink, the gradients, the across lines (_h_lines), the upright lines
over a band (_Upright), the view from above and its score (_structure), moving edges in (_move_in)."""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, "recognizer")
import corners as C
import exact

TOP_OVER_BOTTOM = (0.45, 1.05)   # the far end's width against the near end's
TALL = (0.5, 2.0)                 # the area's height (along the points) against its width at the bottom

SAME = 0.006                      # two long edges nearer than this in the middle (against the width) are one
BANDS = 5                         # where the long edges are looked for: bands from these many starts and ends

def side_guess(small):
    """The long edges first (they are long and plain in these photos), then the ends between them."""
    h, w = small.shape[:2]
    gx, gy = C._gradients(small)
    up = C._Upright(gx, gy)
    across = C._Upright(gy.T.copy(), gx.T.copy())     # lines y = c + x k / 200, over a band of columns
    found = []   # (rows covered, k, c): a line found over a taller band counts for more
    for a in range(BANDS):
        for b in range(a + 2, BANDS + 1):
            y0, y1 = a * h // BANDS, b * h // BANDS
            found += [(sh * (y1 - y0), k, c) for k, c, sh in up.lines(y0, y1)]
    longs = []   # the strongest of each group of lines near one another in the middle of the photo
    for rows, k, c in sorted(found, reverse=True):
        mid = c + h / 2 * k / 200
        if all(abs(mid - (c2 + h / 2 * k2 / 200)) > SAME * w or abs(k - k2) > 12 for k2, c2 in longs):
            longs.append((k, c))
    longs.sort(key=lambda v: v[1] + h / 2 * v[0] / 200)
    best, n = None, 0
    at = lambda k, c, v: c + v * k / 200
    for i in range(len(longs)):
        for j in range(i + 1, len(longs)):
            L, R = longs[i], longs[j]
            if R[0] - L[0] < 0:            # they must come closer towards the top (or run parallel)
                continue
            xm0, xm1 = at(*L, h / 2), at(*R, h / 2)
            if xm1 - xm0 < 0.3 * w:
                continue
            band = (int(xm0 + 0.03 * (xm1 - xm0)), int(xm1 - 0.03 * (xm1 - xm0)))
            ends = across.lines(max(0, band[0]), min(w, band[1]))
            for a in range(len(ends)):
                for b in range(a + 1, len(ends)):
                    top, bot = ends[a], ends[b]
                    q = np.float64([C._meet(top, L), C._meet(top, R), C._meet(bot, R), C._meet(bot, L)])
                    wt, wb = exact.norm(q[1] - q[0]), exact.norm(q[2] - q[3])
                    ht = (exact.norm(q[3] - q[0]) + exact.norm(q[2] - q[1])) / 2
                    if wb <= 0 or not TOP_OVER_BOTTOM[0] < wt / wb < TOP_OVER_BOTTOM[1] or not TALL[0] < ht / wb < TALL[1]:
                        continue
                    player = q[[1, 2, 3, 0]]          # TL, TR, BR, BL as the near player (on the left) sees it
                    view, _ = C._view(small, player, C.RW // 2, C.RH // 2, 0)
                    if view is None:
                        continue
                    n += 1
                    s = C._structure(view)
                    if best is None or s > best[0]:
                        best = (s, player)
    if best is None:
        return None, n
    q = best[1]
    cand = C._move_in(small, q)
    v, _ = C._view(small, cand, C.RW, C.RH, 0)
    v0, _ = C._view(small, q, C.RW, C.RH, 0)
    if v is not None and C._structure(v) > C._structure(v0):
        q = cand
    return q, n

for path in sys.argv[1:]:
    t = json.load(open(path))
    img = cv2.imread(str(Path(path).parent / t["image"]))
    small, s = C.shrink(img)
    truth = np.float64(t["corners_TL_TR_BR_BL"])
    q, n = side_guess(small)
    if q is None:
        print(Path(path).name, "not found", n); continue
    q = q / s
    err = max(exact.norm(a - b) for a, b in zip(q, truth)) / max(img.shape[:2])
    print(f"{Path(path).name}  error {100 * err:.1f}%  quads {n}  truth score {C._structure(C._view(small, truth * s, C.RW, C.RH, 0)[0]):.3f}")
