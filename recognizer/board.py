"""Read a backgammon position from a phone photo of a real board.

Pipeline
  1. Geometry: 4 rough corners of the playing area (both fields + bar, inner
     edge of the frame, as seen by the bottom player) -> homography to a
     canonical top-down board.
  2. Refinement: snap the frame edges to straight lines, then re-fit the
     homography to the printed triangles (tips and sides). The triangles lie
     on the board surface, so unlike the raised frame they are not shifted
     in oblique photos.
  3. Colours: plain field and the two triangle colours are sampled inside
     detected triangles; frame colours just outside the field.
  4. Checkers: Hough circles, kept when the circle has strong radial edges,
     a solid interior and a colour unlike what an empty spot there would
     show; dropped where the triangle's sides show through. Where the sides
     are hidden from the frame on and at most one circle was found, a stack
     is added (dark checkers on a dark board make no circle). The two checker
     colours are split by 2-means.
  5. Counting: circles are assigned to the nearest point column; the
     farthest checker from the point base gives the stack height (so a
     checker missed in the middle of a stack is still counted).
     Borne-off = 15 - (on board + bar).

Canonical frame (ground plane, pixels): x 0..W left->right, y 0..H top->bottom.
"Bottom" is the side of the player whose perspective `corners` uses.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass

import cv2
import numpy as np

import cube as cube_reader
import dice as dice_reader
import exact
import home_prior
from position import Position

# The recognizer's version (board.py, position.py, corners.py and dice.py). Bump it when recognizer/ changes;
# the analyzer has its own in analyzer/app.py. How to bump: CLAUDE.md.
__version__ = "0.19.1"

H_CAN = 1000          # canonical field height (px)
TRI_DEPTH = 0.44      # triangle length / field height
HOUGH_VOTES = 18
CIRCLE_MIN_SCORE = 0.85  # circle score for a checker on its own
LONE_MIN_SCORE = 1.0     # ... and for a single checker with no stack to back it
STACK_SKEW = 0.25        # max sideways step between neighbouring checkers of a stack / pitch
GAP_MIN_SCORE = 0.6      # enough for a circle in line between two checkers of a stack
OUTLINE_SUPPORT = 0.8    # edge support of a checker that has the colour of the spot under it
PATTERN_SUPPORT = 0.85   # edge support of a checker whose face does not match its rim ...
PATTERN_DISTINCT = 30    # ... and its colour distance from every empty spot
COS_35 = 0.8191520442889918   # cos(35 degrees)
BAR_COLOUR_TOL = 0.25    # a checker on the bar: colour distance to its cluster / distance between the clusters
LONE_COLOUR_TOL = 0.3     # ... and for a single checker on a point (a triangle's base can look like one, TODO-048)


@dataclass
class Layout:
    a: float      # one field width
    bar: float    # bar width
    h: float = H_CAN
    cols: list | None = None  # fitted column centres (overrides the regular grid)

    @property
    def w(self) -> float:
        return 2 * self.a + self.bar

    @property
    def pw(self) -> float:
        return self.a / 6

    def col_x(self, c: int) -> float:
        """Centre x of canonical column c (0..11 left->right)."""
        if self.cols is not None:
            return self.cols[c]
        if c < 6:
            return (c + 0.5) * self.pw
        return self.a + self.bar + (c - 6 + 0.5) * self.pw

    def src_pts(self):
        return np.float32([(0, 0), (self.w, 0), (self.w, self.h), (0, self.h)])


def _snap_layout(lay: Layout) -> Layout:
    """lay with its widths and columns on a 1/256-pixel grid (a step's result handed on, TODO-046)."""
    q = 1 / 256
    return Layout(a=exact.snap(lay.a, q), bar=exact.snap(lay.bar, q), h=lay.h,
                  cols=None if lay.cols is None else [exact.snap(c, q) for c in lay.cols])


def _warp(img, H, m, size):
    """The photo seen from straight above: canonical (with margin m) <- image through H.
    The matrix is worked out in Python floats, the pixels in integers (exact.warp)."""
    M = exact.mul3([[1, 0, m], [0, 1, m], [0, 0, 1]], exact.inv3(H))
    return exact.warp(img, M, size)


# ---------------------------------------------------------------- geometry --

def _edge_gradients(lab):
    """Contrast across horizontal and across vertical edges, for _edge_points.
    lab: 8-bit; in integers (the sum over 15 pixels, 15 times the mean that was used before)."""
    lab = lab.astype(np.int32)
    return {"h": exact.box_sum(np.abs(np.diff(lab, axis=0)).sum(2), 15, 1),
            "v": exact.box_sum(np.abs(np.diff(lab, axis=1)).sum(2), 1, 15)}


def _edge_points(grads, axis, pos, lo, hi, win, step=4):
    """Points of the strongest straight edge near canonical line `pos`.

    axis='h': horizontal edge y≈pos spanning x in [lo, hi]; axis='v': vertical.
    grads: from _edge_gradients.
    """
    pts = []
    g = grads[axis]
    if axis == "h":
        for x in range(int(lo), int(hi), step):
            y0, y1 = int(max(pos - win, 0)), int(min(pos + win, g.shape[0] - 1))
            if y1 <= y0 or not (0 <= x < g.shape[1]):
                continue
            col = g[y0:y1, x]
            k = int(np.argmax(col))
            if col[k] > 6 * 15:
                pts.append((x, y0 + k + 0.5, col[k]))
    else:
        for y in range(int(lo), int(hi), step):
            x0, x1 = int(max(pos - win, 0)), int(min(pos + win, g.shape[1] - 1))
            if x1 <= x0 or not (0 <= y < g.shape[0]):
                continue
            row = g[y, x0:x1]
            k = int(np.argmax(row))
            if row[k] > 6 * 15:
                pts.append((x0 + k + 0.5, y, row[k]))
    return np.array(pts, np.float64)


def _ransac_line(pts, axis, tol=3.0, iters=300, max_slope=0.035):
    """Fit u = p*t + q where t is the coordinate along the edge."""
    if len(pts) < 8:
        return None
    rng = np.random.default_rng(0)
    t = pts[:, 0] if axis == "h" else pts[:, 1]
    u = pts[:, 1] if axis == "h" else pts[:, 0]
    best = None
    for _ in range(iters):
        i, j = rng.choice(len(t), 2, replace=False)
        if abs(t[i] - t[j]) < 20:
            continue
        p = (u[j] - u[i]) / (t[j] - t[i])
        if abs(p) > max_slope:   # the corners are roughly right: edges stay near axis-aligned
            continue              # (triangle sides are straight too, but slanted)
        q = u[i] - p * t[i]
        inl = np.abs(u - (p * t + q)) < tol
        sc = pts[inl, 2].sum()
        if best is None or sc > best[0]:
            best = (sc, inl)
    if best is None:
        return None
    inl = best[1]
    p, q = exact.polyfit1(t[inl], u[inl])
    return float(p), float(q), float(inl.mean())


def refine(img, corners, lay: Layout, m: int):
    """Snap the field edges to straight lines found near their expected place.

    Returns the canonical->image homography, a quality score and the layout
    (field / bar widths re-estimated from the found edges).
    """
    H0 = exact.homography(lay.src_pts(), np.float64(corners))
    size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
    warp = _warp(img, H0, m, size)
    lab = cv2.GaussianBlur(cv2.cvtColor(warp, cv2.COLOR_BGR2Lab), (0, 0), 1.5)   # 8-bit: the same on every CPU
    grads = _edge_gradients(lab)
    win = 0.06 * lay.h
    xs = [m, m + lay.a, m + lay.a + lay.bar, m + lay.w]
    lines, quality = {}, []
    for name, pos in (("top", m), ("bot", m + lay.h)):
        pts = []
        for x0, x1 in ((xs[0], xs[1]), (xs[2], xs[3])):
            pts.append(_edge_points(grads, "h", pos, x0 + 0.05 * lay.a, x1 - 0.05 * lay.a, win))
        pts = [p for p in pts if len(p)]
        r = _ransac_line(np.vstack(pts), "h") if pts else None
        lines[name] = r
    ys = (m + 0.03 * lay.h, m + 0.97 * lay.h)
    for name, pos in zip(("L", "BL", "BR", "R"), xs):
        lines[name] = _ransac_line(_edge_points(grads, "v", pos, *ys, win if name in ("L", "R") else lay.bar * 0.45), "v")
    if any(lines[k] is None for k in ("top", "bot", "L", "R")):
        return H0, 0.0, lay
    quality = exact.snap(np.mean([v[2] for v in lines.values() if v is not None]), 1e-6)

    def meet(hl, vl):
        ph, qh = hl[:2]   # y = ph*x + qh
        pv, qv = vl[:2]   # x = pv*y + qv
        y = (ph * qv + qh) / (1 - ph * pv)
        return pv * y + qv, y

    found = {v: [meet(lines["top"], lines[v]), meet(lines["bot"], lines[v])]
             for v in ("L", "BL", "BR", "R") if lines[v] is not None}
    xmid = {v: (p[0][0] + p[1][0]) / 2 - m for v, p in found.items()}
    hgt = float(np.mean([p[1][1] - p[0][1] for p in found.values()]))
    s = lay.h / hgt
    names = ["L", "R"]
    new = None
    if "BL" in xmid and "BR" in xmid:
        al, ar = xmid["BL"] - xmid["L"], xmid["R"] - xmid["BR"]
        bar = xmid["BR"] - xmid["BL"]
        # the bar edges are easy to confuse with checker or triangle edges: keep
        # them only when both fields come out the same width
        if al > 0 and ar > 0 and abs(al - ar) < 0.06 * (al + ar) / 2 and 0.03 < bar / al < 0.35:
            new = Layout(a=(al + ar) / 2 * s, bar=bar * s, h=lay.h)
            names = ["L", "BL", "BR", "R"]
    if new is None:
        width = (xmid["R"] - xmid["L"]) * s
        ratio = lay.bar / lay.a
        a = width / (2 + ratio)
        new = Layout(a=a, bar=a * ratio, h=lay.h)
    new = _snap_layout(new)
    xs2 = {"L": 0, "BL": new.a, "BR": new.a + new.bar, "R": new.w}
    dst = np.float64([(xs2[v], y) for v in names for y in (0, new.h)])
    src = np.float64([p for v in names for p in found[v]]) - m
    img_pts = exact.apply_h(H0, src)
    H = exact.homography(dst, img_pts)
    if H is None:
        return H0, 0.0, lay
    return exact.snap_h(H, new.w, new.h), quality, new


def camera_from_h(H, shape, f_default=0.75):
    """Focal length (principal point at centre) and pose from a plane homography.
    In Python floats (the same on every CPU, TODO-046)."""
    import math
    hh, ww = shape[:2]
    cx, cy = ww / 2, hh / 2
    G = exact.mul3([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]], H)
    h1, h2 = [float(v) for v in G[:, 0]], [float(v) for v in G[:, 1]]
    f2 = -(h1[0] * h2[0] + h1[1] * h2[1]) / (h1[2] * h2[2]) if abs(h1[2] * h2[2]) > 1e-12 else -1
    f = math.sqrt(f2) if f2 > 0 else f_default * max(ww, hh)
    if not (0.4 * max(ww, hh) < f < 2.0 * max(ww, hh)):
        f = f_default * max(ww, hh)  # near top-down: f is unobservable but also irrelevant
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]])
    B = exact.mul3(exact.inv3(K), H)
    b1, b2, b3 = ([float(v) for v in B[:, i]] for i in range(3))

    def dot(u, v):
        return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]

    n1, n2 = math.sqrt(dot(b1, b1)), math.sqrt(dot(b2, b2))
    lam = (n1 + n2) / 2
    r1 = [v / n1 for v in b1]
    k = dot(r1, b2)
    r2 = [b - a * k for a, b in zip(r1, b2)]
    n = math.sqrt(dot(r2, r2))
    r2 = [v / n for v in r2]
    r3 = [r1[1] * r2[2] - r1[2] * r2[1], r1[2] * r2[0] - r1[0] * r2[2], r1[0] * r2[1] - r1[1] * r2[0]]
    t = [v / lam for v in b3]
    if dot(r3, t) > 0:
        r3 = [-v for v in r3]
    return K, np.array(r1), np.array(r2), np.array(r3), np.array(t)


def view_tilt_deg(corners, shape) -> float:
    """How far from straight above the photo was taken, in degrees (0 = top-down).

    From the tapped corners alone. Steep views (photo1, ~70 degrees) hide and
    shift checkers behind the frame and each other, and read badly.
    """
    import math
    H = exact.homography(np.float64([(0, 0), (1, 0), (1, 1), (0, 1)]), np.float64(corners))
    _, _, _, r3, _ = camera_from_h(H, shape)
    return math.degrees(math.acos(min(1.0, abs(float(r3[2])))))


OBLIQUE_WARN_DEG = 40   # samples: top-down shots 0-23 degrees, photo1 69


COL_MIN_SCORE = 1.0


def fit_columns(ground_bgr, lay: Layout, m: int, reach: float = 1.2) -> Layout:
    """Fit column centres to the triangles (near their tips, rarely covered).

    reach: how far (in pitches) the columns may move from the even spacing.
    """
    lab = cv2.cvtColor(ground_bgr, cv2.COLOR_BGR2Lab).astype(np.float32)
    plain = _plain_colour(lab, lay, m)
    dist = np.linalg.norm(lab - plain, axis=2)
    tri = (dist > 30).astype(np.float32)
    d0, d1 = 0.7 * TRI_DEPTH, 0.92 * TRI_DEPTH
    band = np.vstack([tri[int(m + lay.h * d0):int(m + lay.h * d1)],
                      tri[int(m + lay.h * (1 - d1)):int(m + lay.h * (1 - d0))]])
    mid = tri[int(m + lay.h * 0.46):int(m + lay.h * 0.54)]
    # triangles end before mid-board; frame walls, trays and the bar do not
    prof = np.clip(band.mean(0) - mid.mean(0), 0, None)
    xs = np.arange(len(prof))
    cols = []
    for f0 in (0.0, lay.a + lay.bar):
        best = None
        for scale in np.linspace(1 - 0.125 * reach, 1 + 0.125 * reach, 31):
            pw = lay.pw * scale
            for off in np.linspace(-reach, reach, 97) * lay.pw:
                c = m + f0 + off + lay.a / 2 + (np.arange(6) - 2.5) * pw
                # near their tips the triangles are narrow peaks; the bar, the frame
                # and a stack of checkers (about one pitch wide) are plateaus, so
                # score peaks, not just colour
                on = exact.interp(c, xs, prof)
                side = (exact.interp(c - 0.5 * pw, xs, prof) + exact.interp(c + 0.5 * pw, xs, prof)) / 2
                sc = (on - side).sum()
                if best is None or sc > best[0]:
                    best = (sc, c - m)
        if os.environ.get("BG_DEBUG_COLS"):
            print("fit_columns", f0, round(float(best[0]), 3), file=sys.stderr)
        if best[0] < COL_MIN_SCORE:
            # no visible triangles (e.g. engraved, same colour as the field):
            # keep the even spacing from the frame edges
            best = (best[0], f0 + lay.a / 2 + (np.arange(6) - 2.5) * lay.pw)
        cols += [float(v) for v in best[1]]
    return _snap_layout(Layout(a=lay.a, bar=lay.bar, h=lay.h, cols=cols))


def fit_columns_to_checkers(lay: Layout, circles) -> Layout:
    """Re-fit each field's columns to the detected checkers.

    Checkers sit on column centres, so they pin the columns down even when the
    triangles are faint or carved. Candidates start from both the triangle fit
    and even spacing between the frame edges; a field keeps its columns unless
    at least two columns' worth of checkers support a better fit.
    """
    if lay.cols is None or not len(circles):
        return lay
    xs_all = np.array([c[0] for c in circles], np.float64)
    cols = list(lay.cols)
    for f, f0 in ((0, 0.0), (1, lay.a + lay.bar)):
        cur = np.array(lay.cols[6 * f:6 * f + 6])
        even = f0 + (np.arange(6) + 0.5) * lay.pw
        xs = xs_all[(xs_all > f0 - 0.3 * lay.pw) & (xs_all < f0 + lay.a + 0.3 * lay.pw)]
        if len(xs) < 3:
            continue

        def score(c):
            d = np.abs(xs[:, None] - c[None, :])
            near = d.min(1)
            used = len(set(d.argmin(1)[near < 0.25 * lay.pw]))
            z2 = (near / (0.12 * lay.pw)) ** 2
            # exp(-z2) without libm's exp (its last bit differs by CPU): 1 / its Taylor series
            return (1 / (1 + z2 * (1 + z2 * (1 / 2 + z2 * (1 / 6 + z2 / 24))))).sum(), used

        best = None
        for base in (cur, even):
            mid = base.mean()
            for scale in np.linspace(0.9, 1.1, 21):
                for off in np.linspace(-0.6, 0.6, 49) * lay.pw:
                    c = mid + off + (base - mid) * scale
                    sc, used = score(c)
                    if best is None or sc > best[0] + 1e-6:
                        best = (sc, used, c)
        if best[1] >= 2 and best[0] > score(cur)[0] + 0.5:
            cols[6 * f:6 * f + 6] = [float(v) for v in best[2]]
    return _snap_layout(Layout(a=lay.a, bar=lay.bar, h=lay.h, cols=cols))


def _run_at(line, k0, max_off):
    """(width, centre) of the run of True pixels nearest index k0, or (0, None)."""
    idx = np.flatnonzero(line)
    if not len(idx):
        return 0, None
    k = idx[np.argmin(np.abs(idx - k0))]
    if abs(k - k0) > max_off:
        return 0, None
    lo = k
    while lo > 0 and line[lo - 1]:
        lo -= 1
    hi = k
    while hi < len(line) - 1 and line[hi + 1]:
        hi += 1
    return hi - lo + 1, (lo + hi) / 2


def find_tips(ground_bgr, lay: Layout, m: int):
    """Sub-pixel triangle tips in a (roughly) rectified ground image.

    The tips are printed on the board surface, sit mid-board and are rarely
    covered, so unlike the frame edges they are not shifted by the frame's
    height in oblique photos. Returns a list of
    (column, row, tip x, tip y, length, lean, base) canonical: length is where
    the sides are one pitch apart, lean the centre line's sideways step per
    pixel of depth, base the distance from the tip to where the triangle ends
    (None when not found; short when a checker stands on the point).
    """
    # blurred in 8 bits (OpenCV's fixed point: the same on every CPU), then as floats
    lab = cv2.GaussianBlur(cv2.cvtColor(ground_bgr, cv2.COLOR_BGR2Lab), (0, 0), 1.5).astype(np.float32)
    plain = _plain_colour(lab, lay, m)
    tri = np.linalg.norm(lab - plain, axis=2) > 28
    tips = []
    D = TRI_DEPTH * lay.h
    for c in range(12):
        cx = m + lay.col_x(c)
        x0, x1 = int(cx - 0.6 * lay.pw), int(cx + 0.6 * lay.pw)
        if x0 < 0 or x1 > tri.shape[1]:
            continue
        for row in ("top", "bottom"):
            def img_y(depth):
                return int(m + depth) if row == "top" else int(m + lay.h - depth)
            data, miss = [], 0
            for depth in range(int(D * 0.45), int(D * 1.35)):
                y = img_y(depth)
                if not 0 <= y < tri.shape[0]:
                    break
                w, mid = _run_at(tri[y, x0:x1], cx - x0, 0.25 * lay.pw)
                if 0.08 * lay.pw < w < 0.75 * lay.pw:
                    data.append((depth, w, x0 + mid))
                    miss = 0
                elif data:
                    miss += 1
                    if miss > 6:   # walked past the tip
                        break
            if len(data) < 15:
                continue
            d = np.array(data, np.float64)
            for _ in range(4):                       # trimmed fit of width vs depth
                p = exact.polyfit1(d[:, 0], d[:, 1])
                res = np.abs(exact.polyval1(p, d[:, 0]) - d[:, 1])
                keep = res <= max(2.5, 2 * np.median(res))
                if keep.sum() < 15:
                    break
                d = d[keep]
            exp_slope = -lay.pw / D
            if not (1.6 * exp_slope < p[0] < 0.6 * exp_slope) or np.median(res) > 2.5 or len(d) < 15:
                continue
            # where the sides would meet; triangles with blunt or rounded ends stop short of it
            tip_depth = min(-p[1] / p[0], d[:, 0].max() + 0.02 * lay.h)
            px = exact.polyfit1(d[:, 0], d[:, 2])
            tip_x = float(exact.polyval1(px, tip_depth))
            tip_y = m + tip_depth if row == "top" else m + lay.h - tip_depth
            # triangle length in this image = depth at which width reaches one pitch
            length = -lay.pw / p[0]
            base = _triangle_base(lab, plain, lay, m, img_y, p, px, d, tip_depth)
            tips.append((c, row, tip_x - m, tip_y - m, length, px[0], base))
    if tips:  # all triangles are the same shape: drop odd ones
        med = np.median([t[4] for t in tips])
        tips = [t for t in tips if abs(t[4] - med) < 0.15 * med and abs(t[5]) < 0.08]
    return tips


def _triangle_base(lab, plain, lay, m, img_y, p, px, d, tip_depth):
    """Distance from the tip to the triangle's base, or None if it runs off the image.

    Walks from the measured part of the triangle towards the frame along its centre
    line, in pixels of the triangle's own colour (a neighbour has the other colour),
    while the width keeps to the straight sides. The base is where that stops: the
    frame, or a checker standing on the point (then the triangle looks shorter).
    """
    depths = d[:, 0]
    sel = (depths > tip_depth - 0.6 * (tip_depth - depths.min())) & (depths < tip_depth - 0.1 * (tip_depth - depths.min()))
    pts = [lab[img_y(dd), int(round(float(exact.polyval1(px, dd))))] for dd in depths[sel]] if sel.sum() >= 5 else []
    if not len(pts):
        return None
    col = np.median(np.array(pts), 0)
    thr = max(15.0, 0.45 * exact.norm(col - plain))
    miss, last = 0, None
    for depth in range(int(depths.min()), -int(m), -1):
        y = img_y(depth)
        if not 0 <= y < lab.shape[0]:
            return None
        xc = float(exact.polyval1(px, depth))
        x0, x1 = int(xc - 0.7 * lay.pw), int(xc + 0.7 * lay.pw)
        if x0 < 0 or x1 > lab.shape[1]:
            return None
        own = np.linalg.norm(lab[y, x0:x1] - col, axis=1) < thr
        w, _ = _run_at(own, xc - x0, 0.15 * lay.pw)
        pred = float(exact.polyval1(p, depth))
        if 0.6 * pred - 3 < w < 1.35 * pred + 3:
            last, miss = depth, 0
        else:
            miss += 1
            if miss > max(4, 0.01 * lay.h):
                break
    else:
        return None
    return None if last is None else tip_depth - last


def refine_tips(img, H, lay: Layout, m: int):
    """Re-fit the ground homography to the detected triangles (tips + sides)."""
    size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
    ground = _warp(img, H, m, size)
    tips = find_tips(ground, lay, m)
    rows = {r for _, r, *_ in tips}
    if len(tips) < 6 or rows != {"top", "bottom"}:
        return H, lay, tips
    # field height in this image: from top-row bases to bottom-row bases
    tb, bb = _row_bases(tips, "top"), _row_bases(tips, "bottom")
    if (tb is None) != (bb is None):
        # one row's bases hidden (dice cups on the points): the triangles are all the
        # same length, so take it from the other row
        top_tip = np.median([y for _, r, _, y, *_ in tips if r == "top"])
        bot_tip = np.median([y for _, r, _, y, *_ in tips if r == "bottom"])
        if tb is None:
            tb = top_tip - (bb - bot_tip)
        else:
            bb = bot_tip + (top_tip - tb)
    if tb is None or bb is None:
        # no bases seen: assume the sides reach one pitch apart at the frame
        tb = np.median([y - L for _, r, _, y, L, *_ in tips if r == "top"])
        bb = np.median([y + L for _, r, _, y, L, *_ in tips if r == "bottom"])
    field_h = bb - tb
    pw = (lay.col_x(5) - lay.col_x(0) + lay.col_x(11) - lay.col_x(6)) / 10
    bar = lay.col_x(6) - lay.col_x(5) - pw
    s = lay.h / field_h
    new = _snap_layout(Layout(a=6 * pw * s, bar=max(bar * s, 1.0), h=lay.h))
    # tips lie on two straight lines across the board
    D = s * np.median([y - tb for _, r, _, y, *_ in tips if r == "top"] +
                      [bb - y for _, r, _, y, *_ in tips if r == "bottom"])
    obs, ideal = [], []
    for c, r, x, y, L, dx, _ in tips:
        sgn = 1 if r == "top" else -1
        for f in (0.0, 0.35, 0.6):           # fraction of the way back towards the base
            oy = y - sgn * L * f
            ox = x - dx * L * f * sgn
            half_o = lay.pw / 2 * f
            iy = (D - L * s * f) if r == "top" else new.h - D + L * s * f
            half_i = new.pw / 2 * f
            for k in ((0,) if f == 0 else (-1, 1)):
                obs.append((ox + k * half_o, oy))
                ideal.append((new.col_x(c) + k * half_i, iy))
    img_pts = exact.apply_h(H, np.float64(obs))
    # (was cv2.findHomography with RANSAC: least squares that drops the far points, the same on every CPU)
    Hn = exact.homography_robust(np.float64(ideal), img_pts, 0.006 * max(img.shape[:2]))
    if Hn is None:
        return H, lay, tips
    return exact.snap_h(Hn, new.w, new.h), new, tips


def _row_bases(tips, row):
    """Where one row's triangles meet the frame (canonical y), or None.

    A checker standing on a point makes its triangle look shorter, and most
    positions leave some points of each row empty: take the outer bases.
    """
    sgn = 1 if row == "top" else -1
    ys = sorted((y - sgn * b for _, r, _, y, _, _, b in tips if r == row and b is not None), key=lambda v: sgn * v)
    if len(ys) < 3:
        return None
    return float(np.median(ys[:max(2, (len(ys) + 1) // 2)]))


def _plain_colour(lab, lay: Layout, m: int, mask=None):
    y0, y1 = int(m + lay.h * 0.47), int(m + lay.h * 0.53)
    parts = []
    for x0, x1 in ((int(m + lay.a * 0.1), int(m + lay.a * 0.9)),
                   (int(m + lay.a + lay.bar + lay.a * 0.1), int(m + lay.w - lay.a * 0.1))):
        part = lab[y0:y1, x0:x1].reshape(-1, 3)
        if mask is not None:
            part = part[~mask[y0:y1, x0:x1].ravel()]
        parts.append(part)
    samples = np.concatenate(parts)
    return np.median(samples, 0) if len(samples) > 50 else np.median(lab[y0:y1].reshape(-1, 3), 0)


# ---------------------------------------------------------------- colours --

LAB_W = np.float32([0.5, 1.0, 1.0])  # lighting mostly changes L


def board_colours(ground_bgr, lay: Layout, m: int, tips, mask=None):
    """Lab colours of the plain field, the two triangle colours and the frame.

    mask: pixels to ignore (e.g. under checkers already found)."""
    lab = cv2.cvtColor(ground_bgr, cv2.COLOR_BGR2Lab).astype(np.float32)
    plain = _plain_colour(lab, lay, m, mask)
    if mask is not None:
        lab = lab.copy()
        lab[mask] = np.nan
    px = []
    for c, r, x, y, L, dx, _ in tips:     # inside detected triangles, along the centre line
        sgn = 1 if r == "top" else -1
        for f in np.linspace(0.15, 0.5, 8):
            yy, xx = int(m + y - sgn * L * f), int(m + x - dx * L * f * sgn)
            px.append(lab[yy - 1:yy + 2, xx - 1:xx + 2].reshape(-1, 3))
    if not px:   # no triangle found: fall back to the band near where tips should be
        for c in range(12):
            x = int(m + lay.col_x(c))
            for y0 in (m + lay.h * TRI_DEPTH * 0.3, m + lay.h * (1 - TRI_DEPTH * 0.6)):
                px.append(lab[int(y0):int(y0 + lay.h * TRI_DEPTH * 0.3), x - 2:x + 3].reshape(-1, 3))
    px = np.vstack(px)
    px = px[~np.isnan(px).any(1)]
    px = px[np.linalg.norm(px - plain, axis=1) > 25] if (np.linalg.norm(px - plain, axis=1) > 25).sum() > 10 else px
    # in integers (Lab of 8-bit pixels are whole numbers): cv2.kmeans differs by CPU
    _, tri = exact.kmeans(px.astype(np.int32), 2)
    # frame: the strip just outside the near (bottom) edge of the field
    frames = [np.nanmedian(lab[int(m + lay.h + m * 0.3):int(m + lay.h + m * 0.8),
                            int(m):int(m + lay.w)].reshape(-1, 3), 0)]
    bx0, bx1 = int(m + lay.col_x(5) + lay.pw * 0.6), int(m + lay.col_x(6) - lay.pw * 0.6)
    if bx1 - bx0 >= 4:   # the bar, where visible
        frames.append(np.nanmedian(lab[int(m + lay.h * 0.3):int(m + lay.h * 0.7), bx0:bx1].reshape(-1, 3), 0))
    for x0 in (int(m * 0.2), int(m + lay.w + m * 0.3)):   # left / right frame
        frames.append(np.nanmedian(lab[int(m + lay.h * 0.3):int(m + lay.h * 0.7), x0:x0 + int(m * 0.5)].reshape(-1, 3), 0))
    frames = [f for f in frames if not np.isnan(f).any()]
    return np.vstack([plain, tri, *frames]).astype(np.float32)


def to_position(runs, bar, bottom_colour: int, home: str) -> Position:
    """Map canonical columns to White's point numbers.

    White = bottom player (colour index `bottom_colour`), home board on
    `home` side ('left' or 'right') of the bottom row.
    """
    p = Position()
    for (c, row), (col, n) in runs.items():
        if n == 0 or col is None:
            continue
        cc = c if home == "right" else 11 - c  # mirror so home is on the right
        # bottom row right->left = 1..12, top row left->right = 13..24
        pt = (12 - cc) if row == "bottom" else (13 + cc)
        p.points[pt - 1] = n if col == bottom_colour else -n
    p.bar_white = bar[bottom_colour]
    p.bar_black = bar[1 - bottom_colour]
    w = sum(n for n in p.points if n > 0) + p.bar_white
    b = -sum(n for n in p.points if n < 0) + p.bar_black
    p.off_white, p.off_black = max(15 - w, 0), max(15 - b, 0)
    return p


# ---------------------------------------------------------------- main API --

def triangle_colour_map(board, lay, m, tips, ground_lab):
    """Triangle colour index for each (column, row), using alternation."""
    tri = board[1:3] * LAB_W
    votes = []
    for c, r, x, y, L, dx, _ in tips:
        sgn = 1 if r == "top" else -1
        yy, xx = int(m + y - sgn * L * 0.3), int(m + x)
        col = np.median(ground_lab[yy - 2:yy + 3, xx - 2:xx + 3].reshape(-1, 3), 0) * LAB_W
        idx = int(np.argmin(np.linalg.norm(tri - col, axis=1)))
        votes.append((idx - c - (r == "bottom")) % 2)
    off = int(round(np.mean(votes))) if votes else 0
    return {(c, r): (c + (r == "bottom") + off) % 2 for c in range(12) for r in ("top", "bottom")}


# cos and sin of 64 directions round a circle, snapped (libm's last bit differs by CPU)
_COS64 = exact.snap(np.cos(np.linspace(0, 2 * np.pi, 64, endpoint=False)), 2.0 ** -40)
_SIN64 = exact.snap(np.sin(np.linspace(0, 2 * np.pi, 64, endpoint=False)), 2.0 ** -40)


def _edge_support(gx, gy, x, y, r):
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
TEX_SHOWN = 0.7     # ... above this share, the sides show through it
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


def _lab_gradients(bgr):
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


_FINDER = "hough"   # how detect_checkers finds candidates: "hough", or experimentally "radial" or "both"


def detect_checkers(img_bgr, board, lay: Layout, m: int, pitch: float, tri_map=None, tri_len=None, drop_shown=True):
    """Checker tops as circles, scored by edge support and colour.

    Returns list of (x, y, r, lab_median, score) in canonical coords (no margin).
    """
    gray = cv2.GaussianBlur(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY), (0, 0), 2)
    r0 = pitch / 2
    # brightness alone misses e.g. black checkers on dark green felt: also look
    # for circles in the colour channels
    lab8 = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2Lab)
    found = []
    chans = [cv2.GaussianBlur(_stretch(ch), (0, 0), 2) for ch in (gray, lab8[:, :, 1], lab8[:, :, 2])]
    if _FINDER != "radial":
        for ch in chans:
            c = cv2.HoughCircles(ch, cv2.HOUGH_GRADIENT, dp=1.5, minDist=r0 * 1.3, param1=70, param2=HOUGH_VOTES,
                                 minRadius=int(r0 * 0.78), maxRadius=int(r0 * 1.2))
            if c is not None:
                found.append(c[0])
    if _FINDER != "hough":   # experimental (TODO-032 idea 5): radial.py
        import radial
        c = radial.find(chans, r0)
        if c is not None:
            found.append(c)
    if not found:
        return []
    cs = [np.vstack(found)]
    labf, gx, gy = _lab_gradients(img_bgr)
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
        support = _edge_support(gx, gy, x, y, r)
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
    labf, gx, gy = _lab_gradients(ground_bgr)
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


def _digest(v) -> str:
    """A short hash of v's exact value (arrays: dtype, shape and bytes; else its JSON with exact floats)."""
    import hashlib
    def plain(o):
        if isinstance(o, dict):
            return sorted((repr(k), plain(x)) for k, x in o.items())
        if isinstance(o, (list, tuple)):
            return [plain(x) for x in o]
        if isinstance(o, np.ndarray):
            return [o.dtype.str, o.shape, o.tobytes().hex()]
        if isinstance(o, (np.floating, float)):
            return float(o).hex()
        if isinstance(o, np.generic):
            return o.item()
        return o

    if isinstance(v, np.ndarray):
        b = str((v.dtype.str, v.shape)).encode() + np.ascontiguousarray(v).tobytes()
    else:
        b = json.dumps(plain(v), default=repr).encode()
    return hashlib.sha1(b).hexdigest()[:12]


def _trace(trace, name, v):
    """Record a step's value for comparing two machines (TODO-046, recognizer/trace_cpu.py)."""
    if trace is not None:
        trace.append((name, _digest(v)))


def recognize(img, corners, *, bottom_colour=0, home="right", bar_ratio=None,
              a_ratio=None, debug_prefix=None, method="circles", trace=None, progress=None):
    """corners: TL, TR, BR, BL of the playing area as seen from the bottom player.
    home: 'left', 'right' or 'auto' (guessed from the checkers; info['home'] says which).
    trace: a list to append (step, hash of its value) to, for finding where two machines part.
    progress: called as progress(stage, data) when each stage is done ("fit" four times: the frame
    fitted to the frame's edges twice, then to the triangles twice; then "tips", "checkers", "counts",
    "dice", "cube"), with the parts of info["geometry"] it found (image pixels), for showing the
    reading as it goes. It does not change what is read."""
    global _FINDER
    _FINDER = {"radial": "radial", "radial+hough": "both"}.get(method, "hough")
    emit = progress or (lambda stage, data: None)
    cv2.setRNGSeed(0)  # k-means initialisation: make runs repeatable
    _trace(trace, "image", img)
    m = 60
    corners = exact.snap(np.float64(corners).reshape(4, 2), 1 / 64)
    H0 = exact.homography(np.float64([(0, 0), (1, 0), (1, 1), (0, 1)]), corners)
    K, *_ = camera_from_h(H0, img.shape)
    B = exact.mul3(exact.inv3(K), H0)
    aspect = a_ratio or exact.snap(np.clip(exact.norm(B[:, 0]) / exact.norm(B[:, 1]), 0.9, 1.4), 1e-6)
    br = bar_ratio or 0.16
    a = aspect * H_CAN / (2 + br)
    lay = _snap_layout(Layout(a=a, bar=a * br))
    _trace(trace, "start", [H0, K, aspect, a])
    # 1. geometry: frame edges, then the printed triangles
    H, quality, lay = refine(img, corners, lay, m)
    _trace(trace, "refine1", [H, quality, lay.a, lay.bar])
    emit("fit", geometry_frame(H, lay) | dict(by="edges", round=1))
    H, quality, lay = refine(img, exact.apply_h(H, lay.src_pts()), lay, m)
    _trace(trace, "refine2", [H, quality, lay.a, lay.bar])
    emit("fit", geometry_frame(H, lay) | dict(by="edges", round=2))
    tips = []
    reach = 1.2
    for round_ in range(2):
        size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
        ground = _warp(img, H, m, size)
        _trace(trace, "ground_loop", ground)
        lay = fit_columns(ground, lay, m, reach)
        _trace(trace, "fit_columns", [lay.a, lay.bar, lay.cols])
        H, lay, tips = refine_tips(img, H, lay, m)
        _trace(trace, "refine_tips", [H, lay.a, lay.bar, lay.cols, tips])
        emit("fit", geometry_frame(H, lay) | dict(by="triangles", round=round_ + 1))
        if lay.cols is None:
            # fitted to the triangles: from here on only small corrections, as other
            # things on the board can look like triangles too
            reach = 0.4
    size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
    ground = _warp(img, H, m, size)
    _trace(trace, "ground", ground)
    tips = find_tips(ground, lay, m)
    _trace(trace, "tips", tips)
    emit("tips", dict(tips=geometry_tips(tips, H)))
    board = board_colours(ground, lay, m, tips)
    _trace(trace, "board_colours", board)
    pitch = lay.pw * 1.05
    # 2. counting
    ground_lab = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab).astype(np.float32)
    tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
    tri_len = np.median([t[4] for t in tips]) if tips else TRI_DEPTH * lay.h
    # measured with all the circles: which ones show the triangle's sides must not change the size
    _trace(trace, "tri_map", [tri_map, tri_len])
    circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len, drop_shown=False)
    _trace(trace, "circles1", circles)
    if len(circles) >= 4:   # checkers may be wider than a point: measure them
        pitch = float(2 * np.median([c[2] for c in circles]))
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len)
    _trace(trace, "circles2", [pitch, circles])
    if len(circles) >= 4:   # learn the board colours again without the checkers on it
        mask = np.zeros(ground.shape[:2], np.uint8)
        for x, y, r, *_ in circles:
            cv2.circle(mask, (int(x + m), int(y + m)), int(r * 1.1), 1, -1)
        board = board_colours(ground, lay, m, tips, mask.astype(bool))
        tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len)
    _trace(trace, "circles3", [board, circles])
    lay2 = fit_columns_to_checkers(lay, circles)
    if lay2.cols != lay.cols:
        lay = lay2
        tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len)
    # last, so that the added checkers do not change the measured pitch or the board colours
    circles = add_hidden_stacks(ground, lay, m, pitch, circles)
    _trace(trace, "circles4", [lay.cols, circles])
    runs, bar, cc = count_from_circles(circles, lay, pitch)
    _trace(trace, "count", [sorted(runs.items()), bar, cc])
    if method == "slots" and cc is not None:   # experimental (TODO-032): slots.py
        import slots
        labf = cv2.GaussianBlur(ground_lab, (0, 0), 1.5)
        gx = sum(cv2.Sobel(labf[:, :, i], cv2.CV_32F, 1, 0) for i in range(3))
        gy = sum(cv2.Sobel(labf[:, :, i], cv2.CV_32F, 0, 1) for i in range(3))
        runs = slots.count_by_slots(ground_lab, gx, gy, board, lay, m, pitch, tri_map, tri_len,
                                    cc, circles, runs)
    if method == "section" and cc is not None:   # experimental (TODO-032 idea 2): section.py
        import section
        _, _, gy8 = _lab_gradients(ground)
        runs = section.count_by_profile(ground_lab, gy8, board, lay, m, pitch, tri_map, tri_len,
                                        cc, circles, runs)
    guessed = None
    if home == "auto":   # which way the checkers move: guess from where they stand
        home, margin = home_prior.guess(to_position(runs, bar, bottom_colour, "right").points)
        guessed = dict(margin=round(float(margin), 1))
    pos = to_position(runs, bar, bottom_colour, home)
    checkers = geometry_checkers(circles, cc, bottom_colour, H)
    counts = geometry_counts(runs, bar, bottom_colour, lay, H)
    emit("checkers", geometry_frame(H, lay) | dict(checkers=checkers))
    emit("counts", dict(counts=counts, home=home, home_guess=guessed))
    info = dict(home=home, home_guess=guessed, edge_quality=float(quality), tips=len(tips), circles=len(circles),
                layout=dict(a=float(lay.a), bar=float(lay.bar), h=float(lay.h)), pitch=float(pitch),
                checker_lab=None if cc is None else cc.round(1).tolist(),
                board_lab=board.round(1).tolist())
    # Where the playing area and its columns ended up, for showing the photo next to the read board:
    # corners in image pixels (TL TR BR BL), columns and bar edges as fractions of the width.
    info["geometry"] = geometry_frame(H, lay) | dict(tips=geometry_tips(tips, H), checkers=checkers, counts=counts)
    info["dice"] = dice_reader.read_dice(img, H, lay, pitch, circles,
                                         debug=debug_prefix and debug_prefix + "_dice.jpg", trace=trace)
    _trace(trace, "dice", info["dice"])
    # the dice and the cube found, for the reading overlay too (the dice read with confidence in the
    # fields: the ones dice_read can come from)
    info["geometry"]["dice"] = [dict(quad=geometry_square(d, H), value=d["value"])
                                for d in info["dice"]["dice"] if d["sure"] and not d["on_bar"]]
    emit("dice", dict(dice=info["geometry"]["dice"]))
    info["cube"] = cube_reader.read_cube(img, H, lay, pitch, circles, info["dice"]["dice"],
                                         debug=debug_prefix and debug_prefix + "_cube.jpg")
    _trace(trace, "cube", info["cube"])
    cube = info["cube"]
    info["geometry"]["cube"] = cube and dict(quad=geometry_square(cube, H), at=cube["at"])
    emit("cube", dict(cube=info["geometry"]["cube"]))
    info["tilt_deg"] = round(view_tilt_deg(corners, img.shape), 1)
    info["warnings"] = ["oblique"] if info["tilt_deg"] > OBLIQUE_WARN_DEG else []
    if debug_prefix:
        save_debug(debug_prefix, ground, lay, m, runs, tips, circles)
    return pos, info


def geometry_frame(H, lay):
    """Where the playing area and its columns are: corners in image pixels (TL TR BR BL), columns and
    bar edges as fractions of the width."""
    return dict(corners=exact.apply_h(H, lay.src_pts()).round(1).tolist(),
                columns=[round(float(lay.col_x(c) / lay.w), 4) for c in range(12)],
                bar=[round(float(lay.a / lay.w), 4), round(float((lay.a + lay.bar) / lay.w), 4)])


def geometry_counts(runs, bar, bottom_colour, lay, H):
    """The checkers counted on each point and on the bar, [{"at": [x, y], "n": n, "side": "white" | "black"}, ...],
    "at" in image pixels just outside the playing area by the point (on the bar for the bar), for the
    app's reading overlay."""
    off = 0.35 * lay.pw
    marks = [(lay.col_x(c), -off if row == "top" else lay.h + off, n, k)
             for (c, row), (k, n) in sorted(runs.items()) if n and k is not None]
    mid = lay.a + lay.bar / 2
    marks += [(mid, lay.h * (0.62 if k == bottom_colour else 0.38), n, k) for k, n in enumerate(bar) if n]
    if not marks:
        return []
    pts = cv2.perspectiveTransform(np.float32([[x, y] for x, y, *_ in marks])[None], H)[0]
    return [dict(at=[round(float(x), 1), round(float(y), 1)], n=int(n),
                 side="white" if k == bottom_colour else "black") for (x, y), (_, _, n, k) in zip(pts, marks)]


def geometry_tips(tips, H):
    """The triangle tips found, in image pixels [[x, y], ...] (for the app's reading overlay)."""
    if not tips:
        return []
    pts = np.float32([[t[2], t[3]] for t in tips])
    return cv2.perspectiveTransform(pts[None], H)[0].astype(np.float64).round(1).tolist()


def geometry_square(d, H):
    """A die or the cube (x, y, side in canonical coordinates) as its square in image pixels,
    [[x, y] TL TR BR BL] (for the app's reading overlay)."""
    x, y, h = d["x"], d["y"], d["side"] / 2
    pts = np.float32([[x - h, y - h], [x + h, y - h], [x + h, y + h], [x - h, y + h]])
    return cv2.perspectiveTransform(pts[None], H)[0].astype(np.float64).round(1).tolist()


def geometry_checkers(circles, cc, bottom_colour, H):
    """The checker circles found, in image pixels [[x, y, r, side], ...], side "white" (手前) or "black"
    by the nearer checker colour (for the app's reading overlay; the counts do not come from this)."""
    if not len(circles):
        return []
    pts = np.float32([[x, y] for x, y, *_ in circles] + [[x + r, y] for x, y, r, *_ in circles])
    img = cv2.perspectiveTransform(pts[None], H)[0]
    n = len(circles)
    out = []
    for i, (_, _, _, lab, _) in enumerate(circles):
        k = bottom_colour if cc is None else int(np.argmin(np.linalg.norm(
            (np.float32(cc) - np.float32(lab)) * LAB_W, axis=1)))
        r = float(np.linalg.norm(img[n + i] - img[i]))
        out.append([round(float(img[i][0]), 1), round(float(img[i][1]), 1), round(r, 1),
                    "white" if k == bottom_colour else "black"])
    return out


def save_debug(prefix, ground, lay, m, runs, tips, circles=()):
    g = ground.copy()
    for c, r, x, y, *_ in tips:
        cv2.circle(g, (int(x + m), int(y + m)), 6, (0, 255, 0), 2)
    for c in range(12):
        cv2.line(g, (int(m + lay.col_x(c)), 0), (int(m + lay.col_x(c)), g.shape[0]), (255, 0, 0), 1)
    cv2.imwrite(prefix + "_geometry.jpg", g)
    over = ground.copy()
    for x, y, r, *_ in circles:
        cv2.circle(over, (int(x + m), int(y + m)), int(r), (0, 255, 0), 3)
    for (c, row), (col, n) in runs.items():
        cx = int(m + lay.col_x(c))
        cv2.line(over, (cx, m), (cx, int(m + lay.h)), (0, 255, 0), 1)
        y = m + 25 if row == "top" else int(m + lay.h - 10)
        if n:
            cv2.putText(over, f"{n}{'AB'[col]}", (cx - 22, y), 0, 0.9, (0, 0, 0), 4)
            cv2.putText(over, f"{n}{'AB'[col]}", (cx - 22, y), 0, 0.9, (255, 255, 255), 2)
    cv2.imwrite(prefix + "_checkers.jpg", over)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--corners", required=True, help="x1,y1,x2,y2,x3,y3,x4,y4 (TL,TR,BR,BL)")
    ap.add_argument("--home", default="right", choices=["left", "right", "auto"])
    ap.add_argument("--bottom-colour", type=int, default=0)
    ap.add_argument("--debug")
    args = ap.parse_args()
    img = cv2.imread(args.image)
    c = list(map(float, args.corners.split(",")))
    pos, info = recognize(img, list(zip(c[0::2], c[1::2])), home=args.home,
                          bottom_colour=args.bottom_colour, debug_prefix=args.debug)
    print(pos.ascii())
    print(json.dumps({**pos.to_dict(), "info": info}, ensure_ascii=False))
