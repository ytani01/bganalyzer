"""The checkers (steps 4 and 5 of the pipeline in board.py): circles of the known radius, kept when
they look like a checker and not like the empty spot under them; stacks the circles miss; and the
count on each point and on the bar, with the two checker colours split by 2-means.

Coordinates are canonical (geometry.py); images carry a margin of m pixels.
"""
from __future__ import annotations

import cv2
import numpy as np

import exact
import radial
from colours import LAB_W
from geometry import TRI_DEPTH, Layout

HOUGH_VOTES = 18
CIRCLE_MIN_SCORE = 0.85  # circle score for a checker on its own
LONE_MIN_SCORE = 1.0     # ... and for a single checker with no stack to back it
STACK_SKEW = 0.25        # max sideways step between neighbouring checkers of a stack / pitch
GAP_MIN_SCORE = 0.6      # enough for a circle in line between two checkers of a stack
OUTLINE_SUPPORT = 0.8    # edge support of a checker that has the colour of the spot under it
PATTERN_SUPPORT = 0.68   # edge support of a checker whose face does not match its rim ...
PATTERN_DISTINCT = 30    # ... and its colour distance from every empty spot
COS_35 = 0.8191520442889918   # cos(35 degrees)
BAR_COLOUR_TOL = 0.25    # a checker on the bar: colour distance to its cluster / distance between the clusters
LONE_COLOUR_TOL = 0.3     # ... and for a single checker on a point (a triangle's base can look like one, TODO-048)


# cos and sin of 64 directions round a circle, snapped (libm's last bit differs by CPU)
_COS64 = exact.snap(np.cos(np.linspace(0, 2 * np.pi, 64, endpoint=False)), 2.0 ** -40)
_SIN64 = exact.snap(np.sin(np.linspace(0, 2 * np.pi, 64, endpoint=False)), 2.0 ** -40)


def edge_support(gx, gy, x, y, r):
    """Fraction of a circle's perimeter with a strong, radial colour edge (gx, gy: integer gradients)."""
    best = 0.0
    for rr in np.linspace(r * 0.85, r * 1.1, 6):
        px = (x + rr * _COS64).astype(int)
        py = (y + rr * _SIN64).astype(int)
        ok = (px >= 0) & (px < gx.shape[1]) & (py >= 0) & (py < gx.shape[0])
        if ok.sum() < 32:
            continue
        vx = gx[py[ok], px[ok]].astype(np.float64)
        vy = gy[py[ok], px[ok]].astype(np.float64)
        mag = np.sqrt(vx * vx + vy * vy) + 1e-6
        radial = np.abs(vx * _COS64[ok] + vy * _SIN64[ok]) / mag
        best = max(best, float(((mag > 40) & (radial > 0.7)).sum() / len(_COS64)))
    return best


TEX_MIN = 3.0       # median sideways / up-down edge ratio of a row at which the triangles' sides stand out
TEX_HIDDEN = 0.35   # a spot below this share of the median is covered
TEX_SHOWN = 0.84    # ... above this share, the sides show through it
TEX_DEPTHS = 5      # depths (in checkers from the frame) to look at


def column_texture(gx, gy, lay: Layout, m: int, pitch: float):
    """Where the triangles' sides show and where something covers them.

    Near the middle of a column, an empty spot shows the sides of its triangle:
    edges running up and down. A checker hides them. For each row and depth
    (in checkers from the frame), compare the sideways / up-down edge ratio of
    each column with the median of the row (most spots are empty).
    Returns {(c, row, k): 'shown' | 'hidden'}."""
    r = int(pitch * 0.45)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disc = xx ** 2 + yy ** 2 <= r * r
    ax, ay = np.abs(gx), np.abs(gy)
    out = {}
    for row in ("top", "bottom"):
        for k in range(TEX_DEPTHS):
            dep = pitch * (k + 0.5)
            if dep > lay.h / 2 - pitch / 2:   # big checkers: this depth is on the other row
                break
            y = int(m + (dep if row == "top" else lay.h - dep))
            ratio = []
            for c in range(12):
                x = int(m + lay.col_x(c))
                sl = np.s_[y - r:y + r + 1, x - r:x + r + 1]
                if ax[sl].shape != disc.shape:
                    ratio.append(np.nan)
                    continue
                ratio.append(ax[sl][disc].sum() / (ay[sl][disc].sum() + 1))
            ratio = np.float32(ratio)
            med = float(np.nanmedian(ratio))
            if not med >= TEX_MIN:   # the triangles' sides do not stand out here
                continue
            for c in range(12):
                if ratio[c] < TEX_HIDDEN * med:
                    out[(c, row, k)] = "hidden"
                elif ratio[c] > TEX_SHOWN * med:
                    out[(c, row, k)] = "shown"
    return out


def _slot_of(cx, cy, lay: Layout, pitch: float):
    """(column, row, depth in checkers) of the nearest spot of a stack, None when off the column."""
    c = int(np.argmin([abs(cx - lay.col_x(i)) for i in range(12)]))
    row = "top" if cy < lay.h / 2 else "bottom"
    depth = (cy if row == "top" else lay.h - cy) / pitch - 0.5
    k = int(round(depth))
    if abs(cx - lay.col_x(c)) > 0.3 * pitch or k < 0:
        return None
    return c, row, k


def _stretch(ch):
    """An 8-bit channel stretched to 0..255 (cv2.normalize NORM_MINMAX, in integers)."""
    lo, hi = int(ch.min()), int(ch.max())
    if hi == lo:
        return np.zeros_like(ch)
    return (((ch.astype(np.int32) - lo) * 510 + (hi - lo)) // (2 * (hi - lo))).astype(np.uint8)


def lab_gradients(bgr):
    """Lab blurred in 8 bits (as float32) and its Sobel gradients summed over the channels (int32).
    Before TODO-046 the blur and the gradients were in floats, which round differently by CPU."""
    lab = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab), (0, 0), 1.5)
    gx = sum(cv2.Sobel(lab[:, :, i], cv2.CV_16S, 1, 0).astype(np.int32) for i in range(3))
    gy = sum(cv2.Sobel(lab[:, :, i], cv2.CV_16S, 0, 1).astype(np.int32) for i in range(3))
    return lab.astype(np.float32), gx, gy


def _top_colour(inner):
    """A checker's colour: brightness from the median, hue from the most saturated half
    (glare makes a red checker look pink; its saturated part stays red)."""
    chroma = np.sqrt((inner[:, 1] - 128) ** 2 + (inner[:, 2] - 128) ** 2)
    sat = inner[chroma >= np.percentile(chroma, 50)]
    return np.float32([np.median(inner[:, 0]), *np.median(sat[:, 1:], 0)])




def detect_checkers(img_bgr, board, lay: Layout, m: int, pitch: float, tri_map=None, tri_len=None, drop_shown=True,
                    finder="radial"):
    """Checker tops as circles, scored by edge support and colour.

    finder: how candidates are found: "radial" (radial.py, TODO-051), or for comparison "hough" or "both".

    Returns list of (x, y, r, lab_median, score) in canonical coords (no margin).
    """
    gray = cv2.GaussianBlur(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY), (0, 0), 2)
    r0 = pitch / 2
    # brightness alone misses e.g. black checkers on dark green felt: also look
    # for circles in the colour channels
    lab8 = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2Lab)
    found = []
    chans = [cv2.GaussianBlur(_stretch(ch), (0, 0), 2) for ch in (gray, lab8[:, :, 1], lab8[:, :, 2])]
    if finder != "radial":
        for ch in chans:
            c = cv2.HoughCircles(ch, cv2.HOUGH_GRADIENT, dp=1.5, minDist=r0 * 1.3, param1=70, param2=HOUGH_VOTES,
                                 minRadius=int(r0 * 0.78), maxRadius=int(r0 * 1.2))
            if c is not None:
                found.append(c[0])
    if finder != "hough":   # radial symmetry with the known radius (TODO-032 idea 5, TODO-051)
        c = radial.find(chans, r0)
        if c is not None:
            found.append(c)
    if not found:
        return []
    cs = [np.vstack(found)]
    labf, gx, gy = lab_gradients(img_bgr)
    lab = labf * LAB_W
    Wb = board * LAB_W
    hh, ww = gray.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    tex = column_texture(gx, gy, lay, m, pitch)
    scored = []
    for x, y, r in cs[0]:
        cx, cy = x - m, y - m
        # a checker's centre lies inside the field (labels and scores on the frame do not)
        if not (-0.3 * pitch < cx < lay.w + 0.3 * pitch and -0.1 * pitch < cy < lay.h + 0.1 * pitch):
            continue
        shown = tex.get(_slot_of(cx, cy, lay, pitch)) == "shown"
        x0, x1, y0, y1 = int(max(x - r, 0)), int(min(x + r + 1, ww)), int(max(y - r, 0)), int(min(y + r + 1, hh))
        d2 = (xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2
        patch = lab[y0:y1, x0:x1]
        inner = patch[d2 < (0.55 * r) ** 2]
        ring = patch[(d2 > (0.7 * r) ** 2) & (d2 < (0.92 * r) ** 2)]
        if len(inner) < 20 or len(ring) < 20:
            continue
        med = _top_colour(inner)
        ring_same = float((np.linalg.norm(ring - med, axis=1) < 22).mean())
        # what an empty spot here would look like: field, frame, or this column's triangle.
        # The frame only matters where a circle could sit on it: a checker in
        # the field may well be the frame's colour (black on black leather)
        bar0, bar1 = lay.a, lay.a + lay.bar
        on_frame = (min(cx, lay.w - cx, cy, lay.h - cy) < 0.3 * pitch or
                    bar0 - 0.3 * pitch < cx < bar1 + 0.3 * pitch)
        expected = [Wb[0]] + (list(Wb[3:]) if on_frame else [])
        if tri_map is not None:
            c = int(np.argmin([abs(cx - lay.col_x(i)) for i in range(12)]))
            row = "top" if cy < lay.h / 2 else "bottom"
            depth = cy if row == "top" else lay.h - cy
            if depth < (tri_len or TRI_DEPTH * lay.h):
                expected.append(Wb[1 + tri_map[(c, row)]])
        else:
            expected += [Wb[1], Wb[2]]
        distinct = float(np.min(np.linalg.norm(np.float32(expected) - med, axis=1)))
        support = edge_support(gx, gy, x, y, r)
        score = support + 0.012 * min(distinct, 30) + 0.3 * ring_same
        # the colour of an empty spot is fine with a clear outline all round
        # (a white checker on a white triangle in a diagram)
        # a face with a pattern (an embossed or printed centre) differs from its rim, so the ring
        # is not the centre's colour: a clear outline all round in a colour no empty spot has is
        # a checker too (tv-vegas-open, TODO-044)
        patterned = support >= PATTERN_SUPPORT and distinct >= PATTERN_DISTINCT
        if support < 0.2 or (ring_same < 0.35 and not patterned) or (distinct < 8 and (support < OUTLINE_SUPPORT or ring_same < 0.6)):
            continue
        if score < GAP_MIN_SCORE:
            continue
        scored.append((score, cx, cy, r, med / LAB_W, shown))

    # where the triangle's sides show through there is no checker, unless the circle is
    # in line with ones that are (in an oblique photo, the sides of a stack look like them;
    # a stack: at least two such circles in the column)
    keep = {i for i, s in enumerate(scored) if not s[5] or not drop_shown}
    while True:
        more = {i for i, s in enumerate(scored) if i not in keep
                and any(abs(s[1] - scored[k][1]) < 0.25 * pitch and abs(s[2] - scored[k][2]) < 1.3 * pitch for k in keep)
                and sum(abs(s[1] - k[1]) < 0.25 * pitch and (s[2] < lay.h / 2) == (k[2] < lay.h / 2)
                        for k in scored if not k[5]) >= 2}
        if not more:
            break
        keep |= more
    scored = [s[:5] for i, s in enumerate(scored) if i in keep]

    def clear(cx, cy, out):
        # overlapping checkers of one stack are allowed closer, straight in line
        return not any((cx - o[0]) ** 2 + (cy - o[1]) ** 2 < (0.8 * pitch) ** 2 and
                       not (abs(cx - o[0]) < 0.12 * pitch and abs(cy - o[1]) > 0.6 * pitch) for o in out)

    ranked = sorted(scored, key=lambda t: -t[0])
    out = []
    for score, cx, cy, r, med in ranked:
        if score >= CIRCLE_MIN_SCORE and clear(cx, cy, out):
            out.append((cx, cy, r, med, score))
    # stacks have no holes and start at the frame: a weaker circle in line between
    # a sure checker and either another one or the frame (e.g. white on a white
    # triangle, brown on a brown one) is a checker too
    for score, cx, cy, r, med in ranked:
        if score >= CIRCLE_MIN_SCORE or not clear(cx, cy, out):
            continue
        line = [o[1] for o in out if abs(o[0] - cx) < 0.15 * pitch and abs(o[1] - cy) < 2.3 * pitch]
        top = cy < lay.h / 2
        inner = [y for y in line if (y > cy) == top]   # towards mid-board
        outer = [y for y in line if (y > cy) != top]
        stack = [o for o in out if abs(o[0] - cx) < 0.15 * pitch and (o[1] < lay.h / 2) == top]
        depth = cy if top else lay.h - cy   # a checker's centre is half a pitch in from the frame
        # between two checkers, or between a stack of at least two and the frame
        if inner and (outer or (len(stack) >= 2 and depth > 0.3 * pitch)):
            out.append((cx, cy, r, med, score))
    return out


def add_hidden_stacks(ground_bgr, lay: Layout, m: int, pitch: float, circles):
    """Checkers that make no circle (dark wood on a dark board): a column whose
    triangle is covered from the frame on, in an unbroken line, holds a stack.
    Only where at most one circle was found: next to a stack of circles, a dice
    or a cup covering the triangle would make it longer. Returns circles + the added ones."""
    labf, gx, gy = lab_gradients(ground_bgr)
    tex = column_texture(gx, gy, lay, m, pitch)
    lab = labf * LAB_W
    out = list(circles)
    r = pitch / 2
    yy, xx = np.mgrid[-int(r):int(r) + 1, -int(r):int(r) + 1]
    inner = xx ** 2 + yy ** 2 < (0.55 * r) ** 2
    for c in range(12):
        for row in ("top", "bottom"):
            n = 0   # covered at depths 1..n (at the frame the triangle's sides are hard to see)
            while tex.get((c, row, n + 1)) == "hidden":
                n += 1
            if n < 1 or tex.get((c, row, 0)) == "shown":
                continue
            x = lay.col_x(c)
            if sum(abs(o[0] - x) < 0.5 * lay.pw and (o[1] < lay.h / 2) == (row == "top") for o in circles) > 1:
                continue
            for k in range(n + 1):
                dep = pitch * (k + 0.5)
                y = dep if row == "top" else lay.h - dep
                if any((o[0] - x) ** 2 + (o[1] - y) ** 2 < (0.6 * pitch) ** 2 for o in out):
                    continue
                X, Y = int(x + m), int(y + m)
                med = _top_colour(lab[Y - int(r):Y + int(r) + 1, X - int(r):X + int(r) + 1][inner])
                out.append((x, y, r, med / LAB_W, CIRCLE_MIN_SCORE))
    return out


def count_from_circles(circles, lay: Layout, pitch: float):
    """Assign circles to points / bar, count the stacks, split colours with 2-means."""
    if len(circles) < 2:
        return {}, [0, 0], None
    # 1. where each circle is: a point (column, row, depth from the edge) or the bar
    counts = {(c, r): [] for c in range(12) for r in ("top", "bottom")}
    on_bar = []
    bar_x0, bar_x1 = lay.col_x(5) + lay.pw / 2, lay.col_x(6) - lay.pw / 2
    for i, (x, y, r, _, sc) in enumerate(circles):
        if bar_x0 - 0.15 * lay.pw < x < bar_x1 + 0.15 * lay.pw and \
                min(abs(x - lay.col_x(5)), abs(x - lay.col_x(6))) > 0.45 * lay.pw:
            on_bar.append(i)
            continue
        c = int(np.argmin([abs(x - lay.col_x(i)) for i in range(12)]))
        if abs(x - lay.col_x(c)) > 0.5 * lay.pw:
            continue
        row = "top" if y < lay.h / 2 else "bottom"
        counts[(c, row)].append((y if row == "top" else lay.h - y, x, sc, i))   # depth from the edge
    # the first checker sits a little in from the canonical edge (frame lip,
    # rough corners): measure that per row from the stacks themselves
    lip = {}
    for row in ("top", "bottom"):
        firsts = [min(d for d, *_ in v) for (c, r), v in counts.items() if r == row and v]
        firsts = [f for f in firsts if f < 1.6 * pitch]
        lip[row] = float(np.clip(np.median(firsts) - pitch / 2, -0.3 * pitch, 0.8 * pitch)) if firsts else 0.0
    # 2. count each stack
    stacks = {}
    for (c, row), v in counts.items():
        # checkers stack from the base without gaps, so walk out from the base and
        # let the farthest checker of that chain give the count (a checker missed
        # in the middle is still counted; a stray circle far away is not)
        last, last_x, chain, members = None, None, [], []
        for depth, x, sc, i in sorted((d - lip[row], x, sc, i) for d, x, sc, i in v):
            limit = 2.3 * pitch if last is None else last + 2.3 * pitch
            # a stack is straight; round things piled askew (a dice cup) are not
            if depth > limit or (last_x is not None and abs(x - last_x) > STACK_SKEW * pitch):
                break
            last, last_x = depth, x
            chain.append(depth)
            members.append(i)
        used = len(chain)
        n = 0 if last is None else max(used, int(round(last / pitch + 0.5)))
        if n == 1 and circles[members[0]][4] < LONE_MIN_SCORE:
            n = 0   # a lone checker needs a clearer circle than one in a stack
        gaps = np.diff(chain)
        if len(gaps) >= 2 and np.median(gaps) < 0.85 * pitch:
            # apps and full points overlap the checkers: count in steps of the overlap
            step = float(np.median(gaps))
            n = max(used, 1 + int(sum(round(g / step) for g in gaps)))
        stacks[(c, row)] = (min(n, 15), members if n else [])
    # 3. colours, learnt from the checkers only: circles that are in no stack
    # (a dice cup, a printed emblem) would pull a cluster to themselves; so would
    # hinges and straps on the bar
    keep = sorted({i for _, mem in stacks.values() for i in mem})
    if len(keep) < 2:
        keep = sorted(set(keep) | set(on_bar))
    if len(keep) < 2:
        keep = list(range(len(circles)))
    raw = np.float32([c[3] for c in circles])
    cols = raw * LAB_W
    # in integers (quarter units: the colours are medians of whole numbers, L halved): cv2.kmeans differs by CPU
    _, cc = exact.kmeans(np.round(cols[keep] * 4).astype(np.int32), 2, attempts=5)
    cc = (cc / 4).astype(np.float32)
    cc = cc[np.argsort(cc[:, 0], kind="stable")]          # colour 0 = darker
    dd = np.linalg.norm(cols[:, None, :] - cc[None, :, :], axis=2)
    lbl = list(np.argmin(dd, 1))
    # glare washes a coloured checker towards white (red looks pink). When one
    # colour is neutral (white, black) and the other is not, a checker with clear
    # chroma in the coloured one's hue belongs to it, however light it looks
    ca, cb = raw[:, 1].astype(np.float64) - 128, raw[:, 2].astype(np.float64) - 128
    chroma = np.sqrt(ca * ca + cb * cb)
    cent = cc / LAB_W
    cchroma = np.sqrt((cent[:, 1].astype(np.float64) - 128) ** 2 + (cent[:, 2].astype(np.float64) - 128) ** 2)
    neutral = int(np.argmin(cchroma))
    if cchroma[neutral] < 15 and cchroma[1 - neutral] > 35:
        # the hue within 35 degrees of the coloured one's (by the cosine: no libm's arctan, TODO-046)
        ka, kb = float(cent[1 - neutral, 1]) - 128, float(cent[1 - neutral, 2]) - 128
        cos_dh = (ca * ka + cb * kb) / (np.maximum(chroma, 1e-9) * float(cchroma[1 - neutral]))
        for i in range(len(lbl)):
            if lbl[i] == neutral and chroma[i] > 20 and cos_dh[i] > COS_35:
                lbl[i] = 1 - neutral
    # how sure each colour call is: glare makes some checkers sit between the two
    conf = np.abs(dd[:, 0] - dd[:, 1]) / (dd.sum(1) + 1e-6)
    bar = [0, 0]
    for i in on_bar:
        # hinges, clasps and straps on the bar make circles too: a checker there
        # needs a clear circle and one of the checker colours
        if circles[i][4] < LONE_MIN_SCORE or dd[i].min() > BAR_COLOUR_TOL * exact.norm(cc[0] - cc[1]):
            continue
        bar[lbl[i]] += 1
    sep = exact.norm(cc[0] - cc[1])
    runs = {}
    for key, (n, members) in stacks.items():
        # a lone checker needs one of the checker colours too: the base of a triangle whose
        # colour is near a checker's makes a clear circle (tv-vegas-open's red 13 point, TODO-048)
        if n == 1 and dd[members[0]].min() > LONE_COLOUR_TOL * sep:
            n = 0
        if not n:
            runs[key] = (None, 0)
            continue
        # a point holds one colour: vote
        k = 0 if sum(conf[i] for i in members if lbl[i] == 0) >= sum(conf[i] for i in members if lbl[i] == 1) else 1
        runs[key] = (k, n)
    return runs, bar, cent
