"""Guess the 4 corners of the playing area in a photo, as a starting point for the app.

The printed triangles are the most reliable sign of a board: long, narrow,
solid-coloured shapes in two rows, pointing at each other. They are found as
colour regions shaped like a narrow triangle; their bases lie on the far and
near edges of the playing area, and their spacing gives the point width. The
left and right edges are a whole number of points beyond the outermost
triangles found (outer ones may be hidden under checkers); the number is the
one that puts the edge on the strongest straight edge (the frame).

Boards without visible triangles (carved ones, striped app screens) are not
found; the app then starts from a rectangle for the user to drag into place.
"""
from __future__ import annotations

import cv2
import numpy as np

WORK_SIDE = 800        # longest side the search runs at (px)
CLUSTERS = 8           # colour clusters the photo is split into
MIN_PER_ROW = 3        # triangles needed in each row
MAX_BAR = 2.5          # widest bar, in points
MAX_SLOPE = 0.27       # steepest far / near edge (15 degrees)
MAX_LEAN = 0.27        # most a side edge may lean, per field height
FIELD_DE = 12          # colour difference (Lab) still taken for the plain board
FURTHER = 2            # how much stronger an edge further out must be


def find_triangles(small):
    """Narrow triangles among the colour regions: list of (tip, base_mid, base_width)."""
    h, w = small.shape[:2]
    lab = cv2.cvtColor(cv2.GaussianBlur(small, (0, 0), 1.5), cv2.COLOR_BGR2Lab).astype(np.float32)
    cv2.setRNGSeed(0)
    _, lbl, _ = cv2.kmeans((lab * np.float32([0.6, 1, 1])).reshape(-1, 3), CLUSTERS, None,
                           (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 2,
                           cv2.KMEANS_PP_CENTERS)
    lbl = lbl.reshape(h, w)
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
    steps = np.diff(xs)
    steps = steps[(steps > 0.8 * width) & (steps < 1.6 * width)]
    p0 = float(np.median(steps)) if len(steps) else width
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


def _plausible(lab, field, row_info, layouts):
    """Drop layouts that put a point where none can be.

    A point no triangle was found on must be covered by checkers, so near
    its tip the plain board can't show (the outer edge of the frame, or the
    tray beyond it, often looks like the plain board)."""
    row, base, (pt, qt), lean = row_info
    xs = np.array([r[4] for r in row])
    out = []
    for lay in layouts:
        ok = True
        for xc in lay[6]:
            if np.abs(xs - xc).min() < 0.35 * lay[5]:
                continue
            ty = pt * xc + qt
            tx = xc - np.polyval(lean, xc) * (base[0] * xc + base[1] - ty)
            dy = np.sign(base[0] * xc + base[1] - ty) * lay[5] * np.array([0.5, 1.0, 1.5])
            px = _sample(lab, np.repeat(tx + np.array([-0.1, 0, 0.1]) * lay[5], 3), np.tile(ty + dy, 3))
            if np.sum(np.linalg.norm(px - field, axis=1) > FIELD_DE) < 2:
                ok = False
                break
        if ok:
            out.append(lay)
    return out or layouts


def guess(small):
    """Corners (TL, TR, BR, BL) in `small`'s pixels, or None."""
    rows = _rows(find_triangles(small))
    if rows is None:
        return None
    lab = cv2.cvtColor(cv2.GaussianBlur(small, (0, 0), 1.0), cv2.COLOR_BGR2Lab).astype(np.float32)
    grad = tuple(np.linalg.norm(g, axis=2) * np.sign(g.sum(2)) for g in
                 (cv2.Sobel(lab, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(lab, cv2.CV_32F, 0, 1, ksize=3)))
    on = {name: (lambda x, l=r[1]: np.array([x, l[0] * x + l[1]])) for name, r in rows.items()}
    height = np.mean([on["bottom"](x)[1] - on["top"](x)[1] for x in (0, small.shape[1])])
    field = _field_colour(lab, rows)
    layouts = {name: _plausible(lab, field, rows[name], _layouts(rows[name][0])) for name in rows}
    found = {}

    def edge(xt, xb, r):
        """Strongest frame edge with its ends within r of xt (far edge) and xb (near edge)."""
        key = (round(xt), round(xb))
        if key not in found:
            found[key] = max((_edge_strength(grad, on["top"](a), on["bottom"](b)), a, b)
                             for a in xt + np.linspace(-r, r, 7) for b in xb + np.linspace(-r, r, 7))
        return found[key]

    # each side on its own: the edges the layouts lead to, nearest the triangles first
    sides = {"left": [], "right": []}
    for t in layouts["top"]:
        for b in layouts["bottom"]:
            if max(abs(t[k] - b[k]) for k in (1, 2)) > MAX_LEAN * height:   # the frame is straight
                continue
            # the outer points may stop a little short of the frame
            r = 0.5 * (t[5] + b[5]) / 2
            sides["left"].append(edge(t[1], b[1], r))
            sides["right"].append(edge(t[2], b[2], r))
    if not sides["left"]:
        return None
    pick = {}
    for side, sgn in (("left", -1), ("right", 1)):
        cands = sorted(set(sides[side]), key=lambda e: sgn * (e[1] + e[2]))
        # the frame's inner edge is often fainter than the case or tray beyond it:
        # go further out only for a much stronger edge
        best = cands[0]
        for e in cands[1:]:
            if e[0] > FURTHER * best[0]:
                best = e
        pick[side] = best
    el, er = pick["left"], pick["right"]
    return np.float64([on["top"](el[1]), on["top"](er[1]), on["bottom"](er[2]), on["bottom"](el[2])])


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
