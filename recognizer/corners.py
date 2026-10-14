"""Guess the 4 corners of the playing area in a photo, as a starting point for the app.

The printed triangles are the most reliable sign of a board: long, narrow
shapes in two rows, pointing at each other. They are found as colour regions
shaped like a narrow triangle, and if that gives no board, also as pairs of
straight edges meeting at a tip. Their tips lie on two lines, and their bases
near the far and near edges of the playing area; each of those edges is the
frame's straight edge found beyond the bases (checkers and dice cups often
cut the triangles short).

The spacing of the triangles gives the point width, and the left and right
edges are a whole number of points beyond the outermost triangles found
(outer ones may be hidden under checkers). Placements of the far and the
near row are taken together, so that their columns line up with the lean of
the triangles, and the one whose sides (and bar) fall on the strongest
straight edges wins.

Boards without visible triangles (some carved ones, striped app screens) are
not found; the app then starts from a rectangle for the user to drag into place.
"""
from __future__ import annotations

import cv2
import numpy as np

WORK_SIDE = 800        # longest side the search runs at (px)
CLUSTERS = 8           # colour clusters the photo is split into
V_MIN_SIDE = 0.04      # shortest straight edge taken as a triangle's side, against the photo's long side
V_JOIN = 0.015         # how close two sides' ends must be to make a tip, the same way
V_ANGLE = (3, 30)      # angle at the tip (degrees)
MIN_PER_ROW = 3        # triangles needed in each row
MAX_SLOPE = 0.27       # steepest far / near edge (15 degrees)
EDGE_FROM = 0.9        # far / near edge searched from this much of the triangles' length ...
EDGE_TO = 1.1          # ... to this much of it,
EDGE_OTHER = 1.3       # or this much of the other row's length, if further
EDGE_TILTS = (-0.02, -0.01, 0.0, 0.01, 0.02)   # slopes tried against the line of the bases found
EDGE_CLEAR = 0.5       # an edge counts if this strong against the strongest in the range
FURTHER = 2            # how much stronger an edge further out must be
PITCH_MIN = 0.8        # point widths tried, against the base width of the triangles found
PITCH_MAX = 2.6
MAX_BAR = 2.5          # widest bar, in points
FIELD_DE = 12          # colour difference (Lab) still taken for the plain board
ALIGN = 0.3            # how far (in points) the far and near rows' columns may miss each other
BAR_WEIGHT = 0.25      # the bar's edges against the frame's in choosing a placement
OUTSIDE = 0.05         # how far beyond the photo a corner may be, against its long side


def _kmeans(x, cnt, k, attempts=2, iters=20):
    """Labels of the int32 points x (n, 3), each counted cnt times, in k clusters
    (k-means++ starts, the best of `attempts`).

    In integers throughout, so every CPU splits the colours the same way:
    cv2.kmeans in floats split them differently on x86_64 and the Raspberry Pi,
    and the corners found with them (TODO-028)."""
    cnt = cnt.astype(np.int64)
    rng = np.random.Generator(np.random.PCG64(0))

    def dists(c):
        return np.stack([((x - cj) ** 2).sum(1) for cj in c], 1)

    def pick(weights):
        cs = np.cumsum(weights)
        if cs[-1] == 0:         # every colour is already a centre (a nearly plain image)
            return x[0]
        return x[np.searchsorted(cs, rng.integers(cs[-1]), side="right")]

    best = None
    for _ in range(attempts):
        c = [pick(cnt)]
        d = ((x - c[0]) ** 2).sum(1)
        for _ in range(k - 1):
            c.append(pick(d * cnt))
            d = np.minimum(d, ((x - c[-1]) ** 2).sum(1))
        c = np.array(c)
        for _ in range(iters):
            lbl = dists(c).argmin(1)
            n = np.bincount(lbl, cnt, minlength=k).astype(np.int64)
            sums = np.stack([np.bincount(lbl, x[:, i] * cnt, minlength=k).astype(np.int64) for i in range(3)], 1)
            new = np.where(n[:, None] > 0, sums // np.maximum(n, 1)[:, None], c).astype(np.int32)
            if (new == c).all():
                break
            c = new
        d = dists(c)
        cost = int((d.min(1) * cnt).sum())
        if best is None or cost < best[0]:
            best = (cost, d.argmin(1))
    return best[1]


def find_triangles(small):
    """Narrow triangles among the colour regions: list of (tip, base_mid, base_width)."""
    h, w = small.shape[:2]
    lab = cv2.cvtColor(cv2.GaussianBlur(small, (0, 0), 1.5), cv2.COLOR_BGR2Lab)
    # a photo has far fewer colours than pixels: split each colour once, counted by its pixels.
    # Lightness weighed 0.6 against the colour; x16 keeps the cluster centres' fractions,
    # and squared distances stay within int32 (3 * (255 * 5 * 16) ** 2 < 2 ** 31)
    key = lab.reshape(-1, 3).astype(np.int32) @ np.int32([1 << 16, 1 << 8, 1])
    keys, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    colours = np.stack([keys >> 16, (keys >> 8) & 255, keys & 255], 1).astype(np.int32)
    lbl = _kmeans(colours * np.int32([3 * 16, 5 * 16, 5 * 16]), cnt, CLUSTERS)[inv].reshape(h, w)
    out = []
    for k in range(CLUSTERS):
        mask = cv2.morphologyEx((lbl == k).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cn in contours:
            area = cv2.contourArea(cn)
            if not 0.0003 * w * h < area < 0.03 * w * h:
                continue
            tri_area, tri = cv2.minEnclosingTriangle(cn)
            if tri_area <= 0 or area / tri_area < 0.7:
                continue
            tri = tri.reshape(3, 2).astype(np.float64)
            sides = [np.linalg.norm(tri[(i + 1) % 3] - tri[(i + 2) % 3]) for i in range(3)]
            i = int(np.argmin(sides))          # the short side is the base, the tip faces it
            base = sides[i]
            if not 2.5 < 2 * tri_area / base / base < 9:
                continue
            out.append((tri[i], (tri[(i + 1) % 3] + tri[(i + 2) % 3]) / 2, base))
    return out


def find_v_shapes(small):
    """Narrow triangles as pairs of straight edges meeting at a tip: list of (tip, base_mid, base_width).

    Where a triangle's colour runs into a checker, a dice cup or a shadow,
    its colour region is no triangle, but its two long sides still show as
    straight edges (and so do those of carved or outlined triangles)."""
    grey = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    side = max(grey.shape)
    segs = cv2.createLineSegmentDetector().detect(grey)[0]
    if segs is None:
        return []
    segs = segs.reshape(-1, 2, 2).astype(np.float64)
    segs = segs[np.linalg.norm(segs[:, 1] - segs[:, 0], axis=1) > V_MIN_SIDE * side]
    n = len(segs)
    if n < 2:
        return []
    # nearest pair of ends of every two segments: (n, n, 2, 2) distances
    d = np.linalg.norm(segs[:, None, :, None, :] - segs[None, :, None, :, :], axis=4)
    flat = d.reshape(n, n, 4)
    k = flat.argmin(2)
    close = np.triu(flat.min(2) < V_JOIN * side, 1)
    out = []
    for i, j in zip(*np.nonzero(close)):
        ei, ej = divmod(int(k[i, j]), 2)
        ti, fi, tj, fj = segs[i, ei], segs[i, 1 - ei], segs[j, ej], segs[j, 1 - ej]
        li, lj = np.linalg.norm(fi - ti), np.linalg.norm(fj - tj)
        ui, uj = (fi - ti) / li, (fj - tj) / lj
        angle = np.degrees(np.arccos(np.clip(ui @ uj, -1, 1)))
        if not V_ANGLE[0] < angle < V_ANGLE[1]:
            continue
        tip, length = (ti + tj) / 2, min(li, lj)
        a, b = tip + ui * length, tip + uj * length
        out.append((tip, (a + b) / 2, float(np.linalg.norm(a - b))))
    return out


def _fit_line(pts, tol):
    """(p, q) of y = p x + q through most of the points (RANSAC), and the inlier mask."""
    pts = np.asarray(pts, np.float64)
    best = None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dx = pts[j, 0] - pts[i, 0]
            if abs(dx) < 1e-6 or abs((pts[j, 1] - pts[i, 1]) / dx) > MAX_SLOPE:
                continue
            p = (pts[j, 1] - pts[i, 1]) / dx
            inl = np.abs(pts[:, 1] - (pts[i, 1] + p * (pts[:, 0] - pts[i, 0]))) < tol
            if best is None or inl.sum() > best.sum():
                best = inl
    if best is None:
        return None
    p, q = np.polyfit(pts[best, 0], pts[best, 1], 1)
    return (p, q), best


def _rows(tris):
    """The far row (pointing down) and the near row (pointing up), each sorted left to right."""
    rows = {"top": [], "bottom": []}
    for tri in tris:
        tip, mid, _ = tri
        d = tip - mid
        if abs(d[1]) < 2 * abs(d[0]):        # points sideways: not a board triangle seen this way
            continue
        rows["top" if d[1] > 0 else "bottom"].append(tri)
    out = {}
    for name, row in rows.items():
        if len(row) < MIN_PER_ROW:
            return None
        # all triangles are the same size, but checkers can hide the base end of some:
        # take the length most of the longer ones share
        lens = np.array([np.linalg.norm(t - m) for t, m, _ in row])
        support = [(np.sum(np.abs(lens - L) < 0.15 * L), L) for L in lens]
        ref = max(support)[1]
        row = [(t, t + ref * (m - t) / L, b, L > 0.85 * ref) for (t, m, b), L in zip(row, lens)
               if 0.35 * ref < L < 1.15 * ref]
        # their tips lie on one line, and so do their bases
        for k in (0, 1):
            fit = _fit_line([r[k] for r in row], 0.1 * ref) if len(row) >= MIN_PER_ROW else None
            if fit is None:
                return None
            row = [r for r, ok in zip(row, fit[1]) if ok]
            if k == 0:
                tip_line = fit[0]
        row.sort(key=lambda r: r[0][0])
        dedup = []
        for r in row:                         # one region can be found twice (two clusters)
            if dedup and r[0][0] - dedup[-1][0][0] < 0.5 * r[2]:
                continue
            dedup.append(r)
        if len(dedup) < MIN_PER_ROW:
            return None
        # where each point meets the frame: below its tip along the point's
        # centre line, whose lean changes evenly across a slanted photo
        tips = np.array([r[0] for r in dedup])
        axes = np.array([r[1] - r[0] for r in dedup])
        lean = np.polyfit(tips[:, 0], axes[:, 0] / axes[:, 1], 1)
        p, q = fit[0]
        drop = (p * tips[:, 0] + q) - tips[:, 1]
        dedup = [(t, b, w, full, t[0] + np.polyval(lean, t[0]) * dy)
                 for (t, b, w, full), dy in zip(dedup, drop)]
        out[name] = (dedup, fit[0], tip_line, lean)
    # the two rows face each other across the middle of the board
    if np.median([r[0][1] for r in out["top"][0]]) >= np.median([r[0][1] for r in out["bottom"][0]]):
        return None
    return out


def _layouts(row):
    """Ways to place the row's triangles on the 12 points.

    Each is (fit, left x, right x, bar x0, bar x1, pitch, x of the 12 points),
    all where the points meet the frame.

    Points are evenly spaced within each field (the far field a little
    narrower in a slanted photo), with the bar (up to MAX_BAR points wide)
    between the 6th and 7th. Which point the first triangle found is on is
    open, since the outer ones may be hidden under checkers."""
    xs = np.array([r[4] for r in row])
    whole = [r[2] for r in row if r[3]]        # base width of triangles not cut short
    width = float(np.median(whole or [r[2] for r in row]))
    kept = []
    for p0 in _pitches(xs, width):
        kept += [o for o in _place(xs, p0)
                 if all(max(abs(o[1] - k[1]), abs(o[2] - k[2]), abs(o[3] - k[3])) > 0.3 * p0 for k in kept)]
    return kept


def _pitches(xs, width):
    """Likely spacings of the points, from the spacing of the triangles found.

    Neighbouring triangles are one point apart, but checkers hide some and
    one colour of triangle may be missed altogether (every other point), and
    narrow triangles leave the base well short of a point: take every
    spacing that makes all steps but one (the one across the bar) whole
    numbers of points."""
    steps = np.diff(xs)
    steps = steps[steps > 0.5 * width]
    if not len(steps):
        return [width]
    out = []
    for c in sorted({s / k for s in steps for k in (1, 2)}):
        if not PITCH_MIN * width < c < PITCH_MAX * width:
            continue
        n = np.round(steps / c)
        whole = (n >= 1) & (np.abs(steps / c - n) < 0.15)
        if whole.sum() < max(1, len(steps) - 1):
            continue
        p = float(np.median(steps[whole] / n[whole]))
        if all(abs(p / q - 1) > 0.08 for q in out):
            out.append(p)
    return out or [width]


def _place(xs, p0):
    """The layouts for one spacing of the points (see _layouts)."""
    c = np.arange(12)
    grid = np.linspace(0.85, 1.15, 13) * p0
    pl, pr, bar = np.meshgrid(grid, grid, np.linspace(0, MAX_BAR, 26) * p0, indexing="ij")
    keep = np.abs(pl / pr - 1) < 0.1           # the two fields are the same size
    pl, pr, bar = pl[keep], pr[keep], bar[keep]
    # column centres from the left edge: (models, 12)
    cols = np.where(c < 6, (c + 0.5) * pl[:, None], 6 * pl[:, None] + bar[:, None] + (c - 5.5) * pr[:, None])
    left = xs[0] - cols                                          # first triangle on point j: (models, 12)
    pos = left[:, :, None, None] + cols[:, None, None, :]        # (models, j, 1, 12)
    d = np.abs(xs[None, None, :, None] - pos).min(3)             # (models, j, n)
    fit = np.exp(-(d / (0.12 * p0)) ** 2).mean(2)
    m, j = np.nonzero(fit > 0.7)
    out = sorted(zip(fit[m, j], left[m, j], left[m, j] + 6 * pl[m] + bar[m] + 6 * pr[m],
                     left[m, j] + 6 * pl[m], left[m, j] + 6 * pl[m] + bar[m], (pl[m] + pr[m]) / 2,
                     left[m, j][:, None] + cols[m]),
                 key=lambda o: -o[0])
    kept = []
    for o in out:   # one per distinct placement of the frame edges and the bar
        if o[0] < out[0][0] - 0.1:
            break
        if all(max(abs(o[1] - k[1]), abs(o[2] - k[2]), abs(o[3] - k[3])) > 0.3 * p0 for k in kept):
            kept.append(o)
    return kept


def _edge_strength(grad, p0, p1):
    """Contrast across the segment p0-p1, the same way round along all of it.

    The frame edge is one colour against another along its whole length;
    checker stacks also make long edges, but light and dark ones in turn.
    The median lets checkers hide part of the edge."""
    gx, gy = grad
    d = p1 - p0
    n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9)
    t = np.linspace(0.05, 0.95, 40)
    xs = np.clip(p0[0] + t * d[0], 0, gx.shape[1] - 1).astype(int)
    ys = np.clip(p0[1] + t * d[1], 0, gx.shape[0] - 1).astype(int)
    return float(abs(np.median(gx[ys, xs] * n[0] + gy[ys, xs] * n[1])))


def _sample(lab, x, y):
    h, w = lab.shape[:2]
    return lab[np.clip(np.int32(y), 0, h - 1), np.clip(np.int32(x), 0, w - 1)]


def _field_colour(lab, rows):
    """The plain board between the two rows of tips."""
    xs = np.concatenate([[r[0][0] for r in row] for row, *_ in rows.values()])
    x = np.linspace(xs.min(), xs.max(), 30)
    (pt, qt), (pb, qb) = rows["top"][2], rows["bottom"][2]
    y = [(pt * x + qt) * (1 - f) + (pb * x + qb) * f for f in (0.3, 0.5, 0.7)]
    return np.median(_sample(lab, np.tile(x, 3), np.concatenate(y)), 0)


def _plausible(lab, field, row_info, length, layouts):
    """Drop layouts that put a point where none can be.

    A point no triangle was found on must be covered by checkers, so along
    its middle the plain board can't show (the outer edge of the frame, or the
    tray beyond it, often looks like the plain board). Look across the
    point's base half, where even a narrow triangle is wide enough to be seen
    (the tips of a row don't all reach the same line)."""
    row, base, (pt, qt), lean = row_info
    xs = np.array([r[4] for r in row])
    depth = np.array([0.45, 0.65, 0.85])
    out = []
    for lay in layouts:
        ok = True
        for xc in lay[6]:
            if np.abs(xs - xc).min() < 0.35 * lay[5]:
                continue
            by = base[0] * xc + base[1]
            ty = by - np.sign(by - (pt * xc + qt)) * length
            y = ty + depth * (by - ty)
            x = xc - np.polyval(lean, xc) * (by - y)
            px = _sample(lab, (x[:, None] + np.linspace(-0.2, 0.2, 5) * lay[5]).ravel(), np.repeat(y, 5))
            if np.sum(np.linalg.norm(px - field, axis=1) > FIELD_DE) < 3:
                ok = False
                break
        if ok:
            out.append(lay)
    return out or layouts


def _row_length(row_info):
    """How far the row's bases lie from its tips (median over the triangles)."""
    row, (p, q), _, _ = row_info
    return float(np.median([abs(p * r[0][0] + q - r[0][1]) for r in row]))


def _frame_line(grad, row_info, length, other_length, sgn):
    """The far (sgn -1) or near (sgn 1) edge of the playing area along a row.

    The bases found from the triangles are often short of the frame: checkers
    or a dice cup at the frame cut the triangles' colour region, and some
    boards shade the base end differently. The edge is the frame's: a straight
    edge the same way round across all the triangles. Look for it from a
    little inside the bases found out to well beyond the other row's length
    (in a slanted photo the far row is the shorter one), and take the nearest
    clear edge; one further out (the outer side of the frame, the case) only
    when much stronger. Returns the new line of the bases (p, q)."""
    row, (p, q), (pt, qt), _ = row_info
    x0, x1 = min(r[0][0] for r in row), max(r[0][0] for r in row)
    ds = np.arange(EDGE_FROM * length, max(EDGE_TO * length, EDGE_OTHER * other_length), 1.0)
    prof = np.zeros(len(ds))
    tilt = np.zeros(len(ds))
    for i, d in enumerate(ds):
        y0 = pt * x0 + qt + sgn * d
        for dp in EDGE_TILTS:
            e = _edge_strength(grad, np.array([x0, y0]), np.array([x1, y0 + (p + dp) * (x1 - x0)]))
            if e > prof[i]:
                prof[i], tilt[i] = e, dp
    if not len(prof) or prof.max() <= 0:
        return p, q
    peaks = [i for i in range(len(prof))
             if prof[i] >= EDGE_CLEAR * prof.max() and prof[i] == prof[max(0, i - 3):i + 4].max()]
    best = peaks[0]
    for i in peaks[1:]:
        if prof[i] > FURTHER * prof[best]:
            best = i
    pp = p + tilt[best]
    y0 = pt * x0 + qt + sgn * ds[best]
    return pp, y0 - pp * x0


def _move_bases(row_info, line):
    """The row with its bases on `line`: where each point meets the frame."""
    row, _, tip_line, lean = row_info
    p, q = line
    out = []
    for t, b, w, full, _ in row:
        dy = p * t[0] + q - t[1]
        out.append((t, b, w, full, t[0] + np.polyval(lean, t[0]) * dy))
    return (out, line, tip_line, lean)


def guess(small):
    """Corners (TL, TR, BR, BL) in `small`'s pixels, or None.

    The colour regions are tried first; when they don't give a board, the
    triangles' straight sides are added."""
    tris = find_triangles(small)
    quad = _guess(small, _rows(tris))
    if quad is None:
        quad = _guess(small, _rows(tris + find_v_shapes(small)))
    return quad


def _guess(small, rows):
    """Corners from the two rows of triangles (see _rows), or None."""
    if rows is None:
        return None
    lab = cv2.cvtColor(cv2.GaussianBlur(small, (0, 0), 1.0), cv2.COLOR_BGR2Lab).astype(np.float32)
    grad = tuple(np.linalg.norm(g, axis=2) * np.sign(g.sum(2)) for g in
                 (cv2.Sobel(lab, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(lab, cv2.CV_32F, 0, 1, ksize=3)))
    lengths = {name: _row_length(r) for name, r in rows.items()}
    for name, other, sgn in (("top", "bottom", -1), ("bottom", "top", 1)):
        line = _frame_line(grad, rows[name], lengths[name], lengths[other], sgn)
        rows[name] = _move_bases(rows[name], line)
    lengths = {name: _row_length(r) for name, r in rows.items()}
    on = {name: (lambda x, l=r[1]: np.array([x, l[0] * x + l[1]])) for name, r in rows.items()}
    field = _field_colour(lab, rows)
    layouts = {name: _plausible(lab, field, rows[name], lengths[name], _layouts(rows[name][0])) for name in rows}
    found = {}

    def edge(xt, xb, r):
        """Strongest frame edge with its ends within r of xt (far edge) and xb (near edge)."""
        key = (round(xt), round(xb))
        if key not in found:
            found[key] = max((_edge_strength(grad, on["top"](a), on["bottom"](b)), a, b)
                             for a in xt + np.linspace(-r, r, 7) for b in xb + np.linspace(-r, r, 7))
        return found[key]

    # the columns' lean (dx/dy) across the photo, from the axes of all the
    # triangles: in a slanted photo the columns meet at a point beyond the far
    # edge, so the lean changes evenly from left to right
    mid = lambda x: (on["top"](x)[1] + on["bottom"](x)[1]) / 2
    ax = np.array([(t[0] + (b[0] - t[0]) / (b[1] - t[1]) * (mid(t[0]) - t[1]), (b[0] - t[0]) / (b[1] - t[1]))
                   for r in rows.values() for t, b, *_ in r[0]])
    lean = np.polyfit(ax[:, 0], ax[:, 1], 1)
    ok = np.abs(ax[:, 1] - np.polyval(lean, ax[:, 0])) < 0.1
    if ok.sum() >= 4:
        lean = np.polyfit(ax[ok, 0], ax[ok, 1], 1)

    def miss(xt, xb):
        """How far (px, at the near edge) the line from xt on the far edge to xb
        on the near edge is from the columns' lean there."""
        h = (on["bottom"](xb)[1] + on["bottom"](xt)[1] - on["top"](xb)[1] - on["top"](xt)[1]) / 2
        return abs(xb - xt - np.polyval(lean, (xt + xb) / 2) * h)

    # the two rows together: a layout of the far row and one of the near row
    # that put the same columns (frame edges and bar) over each other
    cands = []
    for t in layouts["top"]:
        for b in layouts["bottom"]:
            pitch = (t[5] + b[5]) / 2
            if max(miss(t[k], b[k]) for k in (1, 2, 3, 4)) > ALIGN * pitch:
                continue
            r = 0.5 * pitch    # the outer points may stop a little short of the frame
            bar = edge(t[3], b[3], 0.2 * pitch)[0] + edge(t[4], b[4], 0.2 * pitch)[0]
            cands.append((edge(t[1], b[1], r), edge(t[2], b[2], r), bar))
    if not cands:
        return None

    def weight(side, sgn):
        """Each edge found for one side, with its strength counted down when it
        is not much stronger than an edge nearer the triangles: the frame's
        inner edge is often fainter than the case or tray beyond it."""
        found = sorted({c[side] for c in cands}, key=lambda e: sgn * (e[1] + e[2]))
        out, nearer = {}, 0.0
        for e in found:
            out[e] = e[0] if e[0] > FURTHER * nearer else e[0] / FURTHER
            nearer = max(nearer, e[0])
        return out

    wl, wr = weight(0, -1), weight(1, 1)
    # the bar's sides (or the seam, on a board without a bar) run straight across too
    el, er, _ = max(cands, key=lambda c: wl[c[0]] + wr[c[1]] + BAR_WEIGHT * c[2])
    quad = np.float64([on["top"](el[1]), on["top"](er[1]), on["bottom"](er[2]), on["bottom"](el[2])])
    h, w = small.shape[:2]
    if np.any(quad < -OUTSIDE * max(h, w)) or np.any(quad - [w, h] > OUTSIDE * max(h, w)):
        return None        # a board reaching well beyond the photo is not the one photographed
    return quad


def find_corners(img):
    """TL, TR, BR, BL of the playing area in image pixels, or None if no board was found."""
    s = min(1.0, WORK_SIDE / max(img.shape[:2]))
    small = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img
    q = guess(small)
    return None if q is None else (q / s).round(1).tolist()


if __name__ == "__main__":
    import sys
    for path in sys.argv[1:]:
        print(path, find_corners(cv2.imread(path)))
