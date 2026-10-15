"""Count checkers along each point's centre line (TODO-032 idea 2, experimental).

Once the board is rectified, a point's checkers lie on the column's centre line,
stacked from the frame. Walking along that line from the frame, the colour is a
checker's for as long as the stack goes on, then the empty look (the triangle,
then the field). So:

1. the colour profile: for each depth, the median colour of a narrow strip
   around the centre line;
2. the stack's length: the depth up to which the profile looks more like one of
   the two checker colours than like the empty look there (the best prefix, as
   the stack has no gaps);
3. the count: the length divided by the spacing of the checkers. The spacing is
   the checker size, unless the rims (horizontal edges along the line) repeat at a
   shorter step, as in apps and on full points where checkers overlap: then the
   autocorrelation of the edge profile gives the step.

It does not look for circles, so it can read checkers that make none (low
contrast) and it does not need the lone-checker rules. The checker colours come
from the circle reading (board.count_from_circles); the empty look from the board
colours, not from the circle reading, so that the two readings fail apart.

Not used by the app: `evaluate.py --section` compares it with the circles.
"""
import os

import numpy as np

from board import LAB_W, Layout

STRIP = 0.3         # half width of the strip around the centre line, in checker sizes
BIAS = 0.3          # evidence a depth needs before it counts as checker (in colour separations)
EMPTY_MIN_COLS = 5   # columns with one triangle colour needed to learn its empty look
ROUND = 0.2         # added to length / spacing before rounding
MIN_PERIOD = 0.45   # shortest checker step the rims may show, in checker sizes

if os.environ.get("SECTION_TUNE"):   # experiments: SECTION_TUNE=strip,bias
    STRIP, BIAS, ROUND = map(float, os.environ["SECTION_TUNE"].split(","))


def _profile(ground_lab, gy, lay: Layout, m: int, pitch: float, c: int, row: str):
    """Colours (depth x 3, weighted Lab) and rim strength (depth) along column c's centre line."""
    x = m + lay.col_x(c)
    x0, x1 = int(round(x - STRIP * pitch)), int(round(x + STRIP * pitch)) + 1
    half = int(lay.h / 2)
    if row == "top":
        ys = np.arange(m, m + half)
    else:
        ys = np.arange(m + int(lay.h) - 1, m + int(lay.h) - 1 - half, -1)
    strip = ground_lab[ys, x0:x1] * LAB_W                   # depth x width x 3
    colours = np.median(strip, axis=1)
    rims = np.abs(gy[ys, x0:x1]).astype(np.float64).mean(axis=1)
    return colours, rims


def _smooth(v, w):
    w = max(int(w), 1)
    k = np.ones(w) / w
    if v.ndim == 1:
        return np.convolve(v, k, mode="same")
    return np.stack([np.convolve(v[:, i], k, mode="same") for i in range(v.shape[1])], axis=1)


def _period(rims, pitch: float):
    """The step at which the rims repeat (in pixels), or None when no clear one shorter than a checker."""
    if len(rims) < 2 * pitch:
        return None
    v = rims - rims.mean()
    ac = np.correlate(v, v, mode="full")[len(v) - 1:]
    if ac[0] <= 0:
        return None
    ac = ac / ac[0]
    lo, hi = int(MIN_PERIOD * pitch), int(1.15 * pitch)
    if hi >= len(ac):
        return None
    k = lo + int(np.argmax(ac[lo:hi + 1]))
    return float(k) if ac[k] > 0.3 else None


def count_by_profile(ground_lab, gy, board, lay: Layout, m: int, pitch: float, tri_map, tri_len,
                     checker_lab, circles, circle_runs, lip=None):
    """runs {(column, row): (colour or None, n)} like count_from_circles.

    ground_lab: the rectified board in Lab (float, with margin m); gy its vertical colour gradient.
    checker_lab: the two checker colours (Lab, darker first) from the circle reading.
    circle_runs: the circle reading, used only where a stack is longer than half the board."""
    from slots import _lip
    lip = lip or _lip(circles, lay, pitch)
    Wb = board * LAB_W
    chk = [np.float32(checker_lab[i]) * LAB_W for i in (0, 1)]
    prof = {}
    for c in range(12):
        for row in ("top", "bottom"):
            colours, rims = _profile(ground_lab, gy, lay, m, pitch, c, row)
            prof[(c, row)] = (_smooth(colours, 0.15 * pitch), rims)
    # the empty look at each depth, per triangle colour: the median over the columns with
    # that triangle (most of them are empty at most depths). The board colours where too few
    n_d = min(len(v[0]) for v in prof.values())
    looks = {}
    for t in set(tri_map.values()):
        cols = [prof[k][0][:n_d] for k in prof if tri_map[k] == t]
        depth = np.arange(n_d)
        fallback = np.where((depth < tri_len)[:, None], Wb[1 + t], Wb[0])
        looks[t] = np.median(np.stack(cols), axis=0) if len(cols) >= EMPTY_MIN_COLS else fallback
    runs = {}
    for c in range(12):
        for row in ("top", "bottom"):
            colours, rims = prof[(c, row)]
            colours = colours[:n_d]
            empty = looks[tri_map[(c, row)]]
            d_emp = np.linalg.norm(colours - empty, axis=1)
            start = int(max(lip[row], 0))
            best = (0.0, None, 0)
            for i in (0, 1):
                sep = np.maximum(np.linalg.norm(empty - chk[i], axis=1), 10.0)
                s = (np.linalg.norm(colours - chk[i], axis=1) - d_emp) / sep + BIAS   # negative: checker
                acc = np.cumsum(s[start:])
                if not len(acc):
                    continue
                L = int(np.argmin(acc)) + 1
                if acc[L - 1] < best[0]:
                    best = (float(acc[L - 1]), i, L)
            _, col, L = best
            n = int(np.floor(L / pitch + 0.5 + ROUND)) if col is not None else 0
            if n >= 3:
                p = _period(rims[start:start + L], pitch)
                if p is not None and p < 0.85 * pitch:
                    n = int(np.floor(L / p + 0.5 + ROUND))
            ccol, cn = circle_runs.get((c, row), (None, 0))
            if L >= len(colours) - start - 2 and cn > n:
                col, n = ccol, cn   # reaches mid-board: trust the stack the circles saw
            runs[(c, row)] = (col if n else None, min(n, 15))
    return runs
