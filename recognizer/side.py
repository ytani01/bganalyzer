"""TODO-120 (a first try): photos taken from beside the board, as taken (the bar runs across the photo).

side: where the camera was, as the near player sees it ("right" or "left"). Taken from the right,
the near player is on the photo's left and the board's right end is nearest the camera (at the
photo's bottom); from the left, the near player is on the photo's right and the left end is nearest.
Either way the photo looks the same (the camera's end at the bottom, the long edges leaning in
towards the top); only which corner is which differs: from the left it is the board turned half
round. So everything here works as if taken from the right (the camera beyond the right end) and
`side` only says which corner is which.

Seen from beside, raised things (the frame, the bar, the checkers' tops) are shifted away from the
camera, that is across the points (towards the far end) and hardly along them. The reading:
- the view from above is made from the corners; its width against its height from the camera's
  pose, and when a stack's checkers follow one another closer or farther apart than they are wide,
  made again with that corrected (the pose's focal length is often only guessed),
- each field's six columns are fitted to the printed triangles anywhere across the area (bear-off
  trays may be inside the corners), then to the triangles' tips found,
- the checkers' tops are found as circles (checkers.py) and moved back over their points by each
  field's own shift towards the camera (at most half a point),
- the stacks are counted from the circles as in the normal reading (checkers.count_from_circles).
"""
from __future__ import annotations

import cv2
import numpy as np

import corners as C
import exact
from board import to_position
from checkers import add_hidden_stacks, count_from_circles, detect_checkers
from colours import board_colours, triangle_colour_map
from geometry import Layout, camera_from_h, find_tips

# ---------------------------------------------------------------- corners --
SLOPES = np.arange(-200, 201, 4)  # line slopes tried, in 1/200: the long edges lean up to 45 degrees
TOP_OVER_BOTTOM = (0.45, 1.05)    # the far end's width against the near end's
TALL = (0.5, 2.0)                 # the area's height (along the points) against its width at the bottom
SAME = 0.006                      # two long edges nearer than this in the middle (against the width) are one
BANDS = 5                         # where the long edges are looked for: bands from these many starts and ends

# ---------------------------------------------------------------- reading --
GH = 400                # the ground view's height (along the points, both rows), px
GM = 30                 # its margin
TRI = 0.42              # a triangle's length against the playing area's height
FIELD_CANDIDATES = 300  # the best fields of six columns paired into the two fields
SHIFT = (0.0, 0.5)       # how far the checkers' tops may show away from the camera, in points
ASPECT_TOL = 1.1        # checkers of a stack this much closer or farther apart than wide: the view is squeezed
ASPECT_ROUNDS = 1       # ... looked at again at most this many times
ASPECT_STEPS = 3        # ... seen in at least this many steps
COL_MIN = 0.3           # the triangles' score for each column, at least (else the columns are spaced evenly)


def _order(quad, side):
    """Corners found as if from the right (photo top-right, bottom-right, bottom-left, top-left)
    as TL, TR, BR, BL for the near player: from the left the board is turned half round."""
    q = np.float64(quad)
    return q if side == "right" else q[[2, 3, 0, 1]]


def _guess(small):
    """The long edges first (they are long and plain in these photos), then the ends between them.
    Returns TL, TR, BR, BL as if taken from the right (photo top-right, bottom-right, bottom-left,
    top-left), or None. The score is the normal search's (corners._structure)."""
    h, w = small.shape[:2]
    gx, gy = C._gradients(small)
    up = C._Upright(gx, gy, SLOPES, 1.0)
    across = C._Upright(gy.T.copy(), gx.T.copy(), SLOPES, 1.0)   # lines y = c + x k / 200, over a band of columns
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
    best = None

    def at(k, c, v):
        return c + v * k / 200
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
                    s = C._structure(view)
                    if best is None or s > best[0]:
                        best = (s, player)
    if best is None:
        return None
    q = best[1]
    cand = C._move_in(small, q)
    v, _ = C._view(small, cand, C.RW, C.RH, 0)
    v0, _ = C._view(small, q, C.RW, C.RH, 0)
    if v is not None and C._structure(v) > C._structure(v0):
        q = cand
    return q


def find_corners_side(img, side="right"):
    """TL, TR, BR, BL of the playing area (as the near player sees it) in image pixels, or None."""
    small, s = C.shrink(img)
    q = _guess(small)
    if q is None:
        return None
    return exact.snap(_order(q / s, side), 0.1).round(1).tolist()


# ---------------------------------------------------------------- reading --

def _ground(img, corners, aspect=None):
    """The playing area seen from straight above (as if taken from the right: the camera beyond
    the right end), GW x GH with a margin of GM, and the homography from it to the photo."""
    q = np.float64(corners)
    H0 = exact.homography(np.float64([(0, 0), (1, 0), (1, 1), (0, 1)]), q)
    if aspect is None:
        K, *_ = camera_from_h(H0, img.shape)
        B = exact.mul3(exact.inv3(K), H0)
        aspect = float(np.clip(exact.norm(B[:, 0]) / exact.norm(B[:, 1]), 0.9, 1.8))
    gw = int(round(GH * aspect))
    src = np.float64([(GM, GM), (gw + GM, GM), (gw + GM, GH + GM), (GM, GH + GM)])
    Hg = exact.homography(src, q)
    return exact.warp(img, exact.inv3(Hg), (gw + 2 * GM, GH + 2 * GM)), Hg, gw


def _columns(lab, gw):
    """The 12 columns' centres (x in the ground view, without the margin) and the point's width,
    fitted to the triangles near their tips (rarely covered): two fields of six evenly spaced
    columns with a bar between, anywhere across the area (bear-off trays may be inside the corners)."""
    plain = np.median(lab[GM + int(0.46 * GH):GM + int(0.54 * GH), GM:GM + gw].reshape(-1, 3), 0)
    tri = (np.linalg.norm(lab - plain, axis=2) > 30).astype(np.float64)
    d0, d1 = int(0.6 * TRI * GH), int(0.92 * TRI * GH)
    band = np.vstack([tri[GM + d0:GM + d1], tri[GM + GH - d1:GM + GH - d0]])
    mid = tri[GM + int(0.46 * GH):GM + int(0.54 * GH)]
    prof = np.clip(band.mean(0) - mid.mean(0), 0, None)[GM:GM + gw]
    # every field of six evenly spaced columns: its score, pitch and first column's start
    xs = np.arange(gw)
    k = np.arange(6) + 0.5
    combs = []
    for pw in np.arange(gw / 17, gw / 11, 0.25):
        x0 = np.arange(-0.3 * pw, gw - 5.7 * pw, 1.0)
        cols = x0[:, None] + k[None, :] * pw
        on = np.interp(cols, xs, prof)
        side = (np.interp(cols - pw / 2, xs, prof) + np.interp(cols + pw / 2, xs, prof)) / 2
        combs.append(np.stack([(on - side).sum(1), np.full(len(x0), pw), x0], 1))
    combs = np.concatenate(combs)
    top = combs[np.argsort(-combs[:, 0], kind="stable")[:FIELD_CANDIDATES]]
    best = None
    # two fields side by side, of about one pitch (the far one may look narrower in the ground view
    # when the corners are not quite on the playing surface), the bar between them at most two points wide
    for sl, pl, xl in top:
        for sr, pr, xr in top:
            gap = xr - (xl + 6 * pl)
            if not (0 <= gap <= 2 * max(pl, pr) and 0.8 < pr / pl < 1.25):
                continue
            if best is None or sl + sr > best[0]:
                best = (float(sl + sr), np.concatenate([xl + k * pl, xr + k * pr]), float((pl + pr) / 2))
    if best is None:
        best = (0.0, None, None)
    if best[0] >= COL_MIN * 12:
        return best[1], best[2]
    # no clear triangles (engraved ones, the field's colour): two fields of even columns, from the
    # frame's ends to the bar, the least plain stretch across the middle of the area
    mid = np.linalg.norm(lab[GM + int(0.4 * GH):GM + int(0.6 * GH), GM:GM + gw] - plain, axis=2).mean(0)
    mid = np.convolve(mid, np.ones(5) / 5, "same")
    lo, hi = int(0.35 * gw), int(0.65 * gw)
    b = lo + int(np.argmax(mid[lo:hi]))
    half = (mid[b] + np.median(mid)) / 2
    b0, b1 = b, b
    while b0 > 0 and mid[b0 - 1] > half:
        b0 -= 1
    while b1 < gw - 1 and mid[b1 + 1] > half:
        b1 += 1
    k = np.arange(6) + 0.5
    pw = (b0 + gw - b1 - 1) / 12
    return np.concatenate([k * b0 / 6, b1 + 1 + k * (gw - b1 - 1) / 6]), pw


def _to_tips(cols, tips):
    """Each field's columns refitted to the triangles' tips found (a straight line through the tips'
    x against the column's number, when at least three columns of the field have a tip)."""
    cols = np.float64(cols).copy()
    for f in (0, 6):
        pts = [(c, x) for c, _, x, *_ in tips if f <= c < f + 6]
        if len({c for c, _ in pts}) < 3:
            continue
        p = exact.polyfit1(np.float64([c for c, _ in pts]), np.float64([x for _, x in pts]))
        cols[f:f + 6] = exact.polyval1(p, np.arange(f, f + 6, dtype=np.float64))
    return cols


def _shift(circles, cols, pw):
    """The checkers' tops (circles) moved back over their points. Seen from beside, every top shows
    away from the camera (towards the far end), the more the farther from the camera: so each field
    has its own shift, the one (up to SHIFT points) that brings most of its circles onto a column."""
    if len(circles) < 4:
        return circles, [0.0, 0.0]
    xs = np.float64([c[0] for c in circles])
    cols = np.float64(cols)
    split = (cols[5] + cols[6]) / 2
    shifts = []
    for field in (xs < split, xs >= split):
        def fit(s):
            d = np.min(np.abs((xs[field] + s)[:, None] - cols[None, :]), 1)
            return int((d < 0.2 * pw).sum()), -abs(s)
        shifts.append(float(max(np.arange(SHIFT[0], SHIFT[1] + 0.01, 0.05) * pw, key=fit)))
    moved = [(x + shifts[int(x >= split)], *rest) for x, *rest in circles]
    return moved, [round(s / pw, 2) for s in shifts]


def _stack_step(circles, pw):
    """The median step between neighbouring checkers of a stack (px along the points), and how
    many steps were seen."""
    cs = sorted(circles, key=lambda c: c[1])
    steps = []
    for i, a in enumerate(cs):
        nb = [b[1] - a[1] for b in cs[i + 1:] if abs(b[0] - a[0]) < 0.2 * pw and 0 < b[1] - a[1] < 1.6 * pw]
        if nb:
            steps.append(min(nb))
    return (float(np.median(steps)) if steps else 0.0), len(steps)


def _read(img, q, aspect=None):
    """The checkers' circles in the ground view: (ground, gw, aspect, cols, pw, lay, tips, pitch, circles)."""
    ground, Hg, gw = _ground(img, q, aspect)
    lab = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab).astype(np.float64)
    cols, pw = _columns(lab, gw)
    bar = max(0.0, float(cols[6] - cols[5] - pw))
    lay = Layout(a=(gw - bar) / 2, bar=bar, h=GH, cols=[float(c) for c in cols])
    tips = find_tips(ground, lay, GM)
    cols = _to_tips(cols, tips)
    pw = float((cols[5] - cols[0] + cols[11] - cols[6]) / 10)
    bar = max(0.0, float(cols[6] - cols[5] - pw))
    lay = Layout(a=(gw - bar) / 2, bar=bar, h=GH, cols=[float(c) for c in cols])
    board = board_colours(ground, lay, GM, tips)
    ground_lab = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab).astype(np.float32)
    tri_map = triangle_colour_map(board, lay, GM, tips, ground_lab)
    tri_len = np.median([t[4] for t in tips]) if tips else TRI * GH
    pitch = pw * 1.05
    circles = detect_checkers(ground, board, lay, GM, pitch, tri_map, tri_len, drop_shown=False)
    if len(circles) >= 4:
        pitch = float(2 * np.median([c[2] for c in circles]))
        circles = detect_checkers(ground, board, lay, GM, pitch, tri_map, tri_len)
    return ground, gw, gw / GH, cols, pw, lay, tips, pitch, circles


def read_side(img, corners, side="right", *, bottom_colour=0, home="right", debug=None):
    """The position read from a photo taken from beside the board (see the module's doc): the
    checkers on the points only (no bar, dice or cube yet). corners: TL, TR, BR, BL as the near
    player sees them. Returns (Position, info) like board.recognize."""
    cv2.setRNGSeed(0)
    q = _order(corners, side)              # as if from the right
    ground, gw, aspect, cols, pw, lay, tips, pitch, circles = _read(img, q)
    # the checkers are round: when a stack's checkers follow one another closer or farther apart
    # than they are wide, the view from above is squeezed (the camera's focal length was guessed)
    for _ in range(ASPECT_ROUNDS):
        step, n = _stack_step(circles, pw)
        if n < ASPECT_STEPS or 1 / ASPECT_TOL < step / pitch < ASPECT_TOL:
            break
        ground, gw, aspect, cols, pw, lay, tips, pitch, circles = _read(img, q, aspect * step / pitch)
    moved, shift = _shift(circles, cols, pw)
    moved = add_hidden_stacks(ground, lay, GM, pitch, moved)
    runs, _, cc = count_from_circles(moved, lay, pitch)
    if debug is not None:
        if isinstance(debug, dict):        # the steps' results, for measuring
            debug.update(cols=cols, pw=pw, circles=circles, gw=gw)
        else:
            _draw(debug, ground, cols, circles, moved, runs, tips)
    if side == "left":                     # turned half round: the far player's view
        runs = {(11 - c, "top" if row == "bottom" else "bottom"): v for (c, row), v in runs.items()}
    pos = to_position(runs, [0, 0], bottom_colour, home)
    info = dict(side=side, columns=[round(float(c) / gw, 4) for c in cols], pitch=float(pitch), aspect=round(aspect, 3),
                shift=shift, circles=len(circles), checker_lab=None if cc is None else cc.round(1).tolist())
    return pos, info


def _draw(path, ground, cols, circles, moved, runs, tips=()):
    """The ground view with the columns, the circles found (red) and moved (green), and the counts."""
    g = ground.copy()
    for x in cols:
        cv2.line(g, (int(GM + x), 0), (int(GM + x), g.shape[0]), (255, 255, 0), 1)
    for c, row, x, y, *_ in tips:
        cv2.drawMarker(g, (int(GM + x), int(GM + y)), (0, 255, 255), cv2.MARKER_CROSS, 10, 2)
    for (x, y, r, *_), (x2, *_) in zip(circles, moved):
        cv2.circle(g, (int(GM + x), int(GM + y)), int(r), (0, 0, 255), 1)
        cv2.circle(g, (int(GM + x2), int(GM + y)), 2, (0, 255, 0), -1)
    for x, y, r, *_ in moved[len(circles):]:
        cv2.circle(g, (int(GM + x), int(GM + y)), int(r), (255, 0, 255), 1)
    for (c, row), (k, n) in runs.items():
        y = 14 if row == "top" else g.shape[0] - 4
        cv2.putText(g, str(n), (int(GM + cols[c]) - 5, y), 0, 0.5, (0, 0, 255) if k else (255, 0, 0), 2)
    cv2.imwrite(path, g)

