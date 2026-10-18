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
from checkers import add_hidden_stacks, count_from_circles, detect_checkers
from colours import board_colours, triangle_colour_map
from geometry import Layout, camera_from_h, find_tips
from overlay import geometry_frame, geometry_tips

# ---------------------------------------------------------------- corners --
SLOPES = np.arange(-200, 201, 4)  # line slopes tried, in 1/200: the long edges lean up to 45 degrees
TOP_OVER_BOTTOM = (0.45, 1.05)    # the far end's width against the near end's
TALL = (0.5, 2.0)                 # the area's height (along the points) against its width at the bottom
SAME = 0.006                      # two long edges nearer than this in the middle (against the width) are one
BANDS = 5                         # where the long edges are looked for: bands from these many starts and ends
WEAK = 0.7                        # the normal search's corners scoring below this: tried from beside too (TODO-134;
                                  # photo-black-blue-oblique from beside 0.46 normally, 1.1 from beside; photos from the front about 1.0)
PART = 0.6                        # corners from beside lying this much (IoU) over a quarter of the normal search's or
                                  # its half on one side of the bar: a part of the board it found, not taken (TODO-137;
                                  # photo-carved-brown-top 0.80, photos from beside 0.50 at most)

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


def _guess(small, emit=None, fixed=None, least=None):
    """The long edges first (they are long and plain in these photos), then the ends between them.
    Returns TL, TR, BR, BL as if taken from the right (photo top-right, bottom-right, bottom-left,
    top-left), or None. The score is the normal search's (corners._structure).
    Called as corners.guess is (by corners.find_corners): emit tells of the stages ("uprights": the
    long edges, "edges": the ends, "candidates"); fixed: corners the user has put in place (as if
    taken from the right), kept where they are; least is not used (the long edges' distance is)."""
    emit = emit or (lambda stage, **arrays: None)
    fixed = fixed or [None] * 4
    keep = [i for i in range(4) if fixed[i] is not None]
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
    emit("uprights", lines=np.float64([[(c, 0), (c + h * k / 200, h)] for k, c in longs]).reshape(-1, 2, 2))
    scored, ends_seen = [], set()

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
            ends_seen |= {(k, c) for k, c, _ in ends}
            for a in range(len(ends)):
                for b in range(a + 1, len(ends)):
                    top, bot = ends[a], ends[b]
                    q = np.float64([C._meet(top, L), C._meet(top, R), C._meet(bot, R), C._meet(bot, L)])
                    wt, wb = exact.norm(q[1] - q[0]), exact.norm(q[2] - q[3])
                    ht = (exact.norm(q[3] - q[0]) + exact.norm(q[2] - q[1])) / 2
                    if wb <= 0 or not TOP_OVER_BOTTOM[0] < wt / wb < TOP_OVER_BOTTOM[1] or not TALL[0] < ht / wb < TALL[1]:
                        continue
                    player = q[[1, 2, 3, 0]]          # TL, TR, BR, BL as the near player (on the left) sees it
                    if max([exact.norm(player[n] - fixed[n]) for n in keep], default=0) > C.NEAR * max(h, w):
                        continue   # its corners disagree with the ones the user put in place
                    for n in keep:
                        player[n] = fixed[n]
                    view, _ = C._view(small, player, C.RW // 2, C.RH // 2, 0)
                    if view is None:
                        continue
                    scored.append((C._structure(view), player))
    emit("edges", lines=np.float64([[(0, c), (w, c + w * k / 200)] for k, c in sorted(ends_seen)]).reshape(-1, 2, 2))
    if not scored:
        return None
    scored.sort(key=lambda r: -r[0])
    emit("candidates", quads=np.float64([q for _, q in scored[:C.REFINE]]).reshape(-1, 4, 2))
    q = scored[0][1]
    cand = C._move_in(small, q)
    for n in keep:
        cand[n] = fixed[n]
    v, _ = C._view(small, cand, C.RW, C.RH, 0)
    v0, _ = C._view(small, q, C.RW, C.RH, 0)
    if v is not None and C._structure(v) > C._structure(v0):
        q = cand
    return q


def find_corners_side(img, side="right", progress=None, fixed=None, crop=None):
    """TL, TR, BR, BL of the playing area (as the near player sees it) in image pixels, or None, from a
    photo taken from beside the board; side: "right" or "left" (see the module's doc). As
    corners.find_corners, with its progress stages, fixed corners and crop (corners.find_corners runs
    this search in place of its own)."""
    def order(q):
        return q if side == "right" else [q[i] for i in (2, 3, 0, 1)]

    def told(stage, data):
        progress(stage, {"corners": order(data["corners"])} if stage == "corners" else data)
    q = C.find_corners(img, progress and told, fixed and order(list(fixed)), crop, search=_guess)
    return q and order(q)


def _score(img, q):
    """How much the area inside q looks like a board (corners._structure); -1 for nothing found."""
    if q is None:
        return -1
    small, s = C.shrink(img)
    v, _ = C._view(small, np.float64(q) * s, C.RW, C.RH, 0)
    return -1 if v is None else C._structure(v)


def _part(n, q):
    """IoU of q with the part of n it lies most over (a quarter, or the half on one side of the bar),
    in n's own view (a square of 2 x 2 quarters); 0 for a q not wholly before n's horizon."""
    H = exact.homography(np.float64(n), np.float64([(0, 0), (2, 0), (2, 2), (0, 2)]))
    w = np.float64(exact.mat(H))[2] @ np.c_[np.float64(q), np.ones(4)].T
    if not (w > 0).all() and not (w < 0).all():
        return 0.0
    p = np.float32(exact.apply_h(H, q))
    area = exact.polygon_area(p)
    best = 0.0
    for x0, y0, h in [(x, y, 1) for x in (0, 1) for y in (0, 1)] + [(x, 0, 2) for x in (0, 1)]:
        both = cv2.intersectConvexConvex(p, np.float32([(x0, y0), (x0 + 1, y0), (x0 + 1, y0 + h), (x0, y0 + h)]))[0]
        best = max(best, both / (area + h - both))
    return best


def find_corners_any(img, progress=None):
    """(corners, side) for a photo the user has not said is taken from beside (TODO-134): the normal
    search, and when what it finds scores below WEAK (or nothing), also from the right and the left
    (unless over a part of the normal search's corners: PART); the best scoring is taken (side
    None: the normal one). corners None: nothing found any way.
    progress as find_corners's; the searches tried again tell of their stages but their corners only
    as the answer (a "corners" stage at the end, when another way won)."""
    q = C.find_corners(img, progress)
    best = (_score(img, q), q, None)
    if best[0] >= WEAK:
        return q, None
    normal = q
    told = progress and (lambda stage, data: stage != "corners" and progress(stage, data))
    for side in ("right", "left"):
        q = find_corners_side(img, side, told)
        if q is not None and normal is not None and _part(normal, q) >= PART:
            continue
        best = max(best, (_score(img, q), q, side), key=lambda b: b[0])
    if progress and best[2] and best[1]:
        progress("corners", {"corners": best[1]})
    return best[1], best[2]


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
    """The checkers' circles in the ground view: (ground, Hg, gw, aspect, cols, pw, lay, tips, board, pitch,
    circles); board: the board's colours (colours.board_colours)."""
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
    return ground, Hg, gw, gw / GH, cols, pw, lay, tips, board, pitch, circles


def read_side(img, corners, side="right", emit=None, debug=None):
    """The checkers read from a photo taken from beside the board (see the module's doc), for
    board.recognize(side=...), which reads the dice and the cube and makes the position from them.
    corners: TL, TR, BR, BL as the near player sees them. emit(stage, data) is told of "fit" and "tips"
    as board.recognize's progress is. Returns (H, lay, tips, circles, pitch, runs, bar, cc, board), all in
    the near player's canonical frame (H: from it to the photo), as board.recognize has them."""
    emit = emit or (lambda stage, data: None)
    q = _order(corners, side)              # as if from the right
    ground, Hg, gw, aspect, cols, pw, lay, tips, board, pitch, circles = _read(img, q)
    # the checkers are round: when a stack's checkers follow one another closer or farther apart
    # than they are wide, the view from above is squeezed (the camera's focal length was guessed)
    for _ in range(ASPECT_ROUNDS):
        step, n = _stack_step(circles, pw)
        if n < ASPECT_STEPS or 1 / ASPECT_TOL < step / pitch < ASPECT_TOL:
            break
        ground, Hg, gw, aspect, cols, pw, lay, tips, board, pitch, circles = _read(img, q, aspect * step / pitch)
    moved, shift = _shift(circles, cols, pw)
    moved = add_hidden_stacks(ground, lay, GM, pitch, moved)
    H = exact.mul3(Hg, [[1, 0, GM], [0, 1, GM], [0, 0, 1]])   # canonical (no margin) -> photo
    if side == "left":
        # turned half round: the near player's frame is the ground view's turned about its centre
        w, h = lay.w, lay.h
        H = exact.mul3(H, [[-1, 0, w], [0, -1, h], [0, 0, 1]])
        lay = Layout(a=lay.a, bar=lay.bar, h=h, cols=[float(w - x) for x in reversed(lay.cols)])
        moved = [(w - x, h - y, *rest) for x, y, *rest in moved]
        tips = [(11 - c, "top" if row == "bottom" else "bottom", w - x, h - y, *rest) for c, row, x, y, *rest in tips]
    emit("fit", geometry_frame(H, lay) | dict(by="side", round=1))
    emit("tips", dict(tips=geometry_tips(tips, H)))
    runs, bar, cc = count_from_circles(moved, lay, pitch)
    if debug and side == "right":          # the ground view as it is (from the left it is turned)
        _draw(debug, ground, cols, circles, moved, runs, tips)
    return H, lay, tips, moved, pitch, runs, bar, cc, board


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

