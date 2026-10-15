"""Count checkers by slots instead of by found circles (TODO-032, experimental).

Once the board is rectified, the n-th checker of a point can only sit at one
place: n - 0.5 pitches in from the frame, on the column's centre line. So
instead of looking for circles anywhere and then grouping them, look at each of
those places ("slots") and ask whether it holds a checker of colour 0, of
colour 1, or nothing. A point holds one colour and its checkers are stacked
from the frame without gaps, so a point's reading is (colour, n): the first n
slots hold that colour and the rest are empty. Pick the (colour, n) that
explains all of the point's slots best.

What an empty slot and a checker look like on this photo is learnt from the
circle reading (checkers.count_from_circles); the board colours stand in where it
has nothing. A slot's evidence is its colour (nearer a checker than the empty
look) and, a little, the outline of a circle of the known size there.

Not used by the app: `evaluate.py --slots` compares it with the circles.
On the samples it reads fewer points than the circles (recognizer/README.md).
"""
import os

import numpy as np

from checkers import edge_support
from colours import LAB_W
from geometry import Layout

EDGE_GAIN = 0.1     # weight of the circle outline against the colour evidence
EDGE_BASE = 0.4     # outline support of an empty slot when the photo cannot tell
SLOT_BIAS = 0.3     # evidence a slot needs before it counts as a checker

if os.environ.get("SLOTS_TUNE"):   # experiments: SLOTS_TUNE=edge_gain,bias
    EDGE_GAIN, SLOT_BIAS = map(float, os.environ["SLOTS_TUNE"].split(","))


def _lip(circles, lay: Layout, pitch: float):
    """How far in from the canonical edge the first checker sits, per row (as in count_from_circles)."""
    firsts = {"top": {}, "bottom": {}}
    for x, y, *_ in circles:
        c = int(np.argmin([abs(x - lay.col_x(i)) for i in range(12)]))
        if abs(x - lay.col_x(c)) > 0.5 * lay.pw:
            continue
        row = "top" if y < lay.h / 2 else "bottom"
        d = y if row == "top" else lay.h - y
        firsts[row][c] = min(d, firsts[row].get(c, 1e9))
    lip = {}
    for row, v in firsts.items():
        f = [d for d in v.values() if d < 1.6 * pitch]
        lip[row] = float(np.clip(np.median(f) - pitch / 2, -0.3 * pitch, 0.8 * pitch)) if f else 0.0
    return lip


def count_by_slots(ground_lab, gx, gy, board, lay: Layout, m: int, pitch: float, tri_map, tri_len,
                   checker_lab, circles, circle_runs):
    """runs {(column, row): (colour or None, n)} like count_from_circles.

    ground_lab: the rectified board in Lab (float, with margin m); gx, gy its colour gradients.
    checker_lab: the two checker colours (Lab, darker first) learnt from the circles.
    circle_runs: the circle reading. It also teaches what an empty slot and a checker
    look like on this photo: the slots it calls empty, per triangle colour and slot,
    give the empty look (shading near the frame, printed patterns), and the outline
    strength of its empty and full slots sets how much an outline means here."""
    lip = _lip(circles, lay, pitch)
    Wb = board * LAB_W
    r = pitch / 2
    hh, ww = ground_lab.shape[:2]
    yy, xx = np.mgrid[-int(r):int(r) + 1, -int(r):int(r) + 1]
    disk = (xx ** 2 + yy ** 2) < (0.55 * r) ** 2
    # 1. look at every slot
    feats = {}   # (c, row, k) -> (median colour, outline support, background key)
    k_max = {row: int((lay.h / 2 - lip[row]) / pitch) for row in ("top", "bottom")}
    for c in range(12):
        for row in ("top", "bottom"):
            for k in range(k_max[row]):
                depth = lip[row] + (k + 0.5) * pitch
                cy = depth if row == "top" else lay.h - depth
                X, Y = int(round(m + lay.col_x(c))), int(round(m + cy))
                y0, x0 = Y - int(r), X - int(r)
                if y0 < 0 or x0 < 0 or y0 + disk.shape[0] > hh or x0 + disk.shape[1] > ww:
                    continue
                inner = ground_lab[y0:y0 + disk.shape[0], x0:x0 + disk.shape[1]][disk] * LAB_W
                bg = (tri_map[(c, row)], k) if depth < tri_len else (None, k)
                feats[(c, row, k)] = (np.median(inner, 0), edge_support(gx, gy, X, Y, r), bg)
    # 2. learn from the circle reading
    empty, full, sup_e, sup_f = {}, {0: [], 1: []}, [], []
    for (c, row, k), (med, sup, bg) in feats.items():
        col, n = circle_runs.get((c, row), (None, 0))
        if k < n:
            full[col].append(med)
            sup_f.append(sup)
        elif k > n or n == 0:   # not right next to a stack (its shadow, a slightly long count)
            empty.setdefault(bg, []).append(med)
            sup_e.append(sup)
    chk = [np.median(full[i], 0) if len(full[i]) >= 3 else np.float32(checker_lab[i]) * LAB_W for i in (0, 1)]
    def empty_look(bg):
        if len(empty.get(bg, [])) >= 2:
            return [np.median(empty[bg], 0)]
        return [Wb[0]] if bg[0] is None else [Wb[1 + bg[0]], Wb[0]]
    se = float(np.median(sup_e)) if sup_e else EDGE_BASE
    sf = float(np.median(sup_f)) if sup_f else 0.8
    mid, spread = (se + sf) / 2, max(sf - se, 0.2)
    # 3. score the slots and pick each point's (colour, n)
    runs = {}
    for c in range(12):
        for row in ("top", "bottom"):
            K = k_max[row]
            score = np.ones((K, 2))
            for k in range(K):
                if (c, row, k) not in feats:
                    continue
                med, sup, bg = feats[(c, row, k)]
                looks = np.float32(empty_look(bg))
                e = looks[int(np.argmin(np.linalg.norm(looks - med, axis=1)))]
                d_empty = float(np.linalg.norm(e - med))
                for i in (0, 1):
                    sep = max(float(np.linalg.norm(chk[i] - e)), 10.0)
                    score[k, i] = (float(np.linalg.norm(chk[i] - med)) - d_empty) / sep \
                        - EDGE_GAIN * (sup - mid) / spread + SLOT_BIAS
            best = (0.0, None, 0)
            for col in (0, 1):
                acc = np.cumsum(score[:, col])
                n = int(np.argmin(acc)) + 1
                if acc[n - 1] < best[0]:
                    best = (float(acc[n - 1]), col, n)
            _, col, n = best
            ccol, cn = circle_runs.get((c, row), (None, 0))
            if n == K and cn > n:
                col, n = ccol, cn   # more than the slots hold: trust the stack the circles saw
            runs[(c, row)] = (col, n)
    return runs
