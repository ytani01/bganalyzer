"""Where the playing area is in the photo: the homography to the canonical board seen from straight above.

Steps 1 and 2 of the pipeline in board.py: from 4 rough corners, snap the frame edges to straight
lines (refine), then re-fit to the printed triangles' tips and sides (fit_columns, refine_tips), which
lie on the board surface and so are not shifted in oblique photos like the raised frame.

Canonical frame (ground plane, pixels): x 0..W left->right, y 0..H top->bottom, "bottom" being the
side of the player whose perspective the corners use. Images of it carry a margin of m pixels.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass

import cv2
import numpy as np

import exact

H_CAN = 1000          # canonical field height (px)
TRI_DEPTH = 0.44      # triangle length / field height


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


def snap_layout(lay: Layout) -> Layout:
    """lay with its widths and columns on a 1/256-pixel grid (a step's result handed on, TODO-046)."""
    q = 1 / 256
    return Layout(a=exact.snap(lay.a, q), bar=exact.snap(lay.bar, q), h=lay.h,
                  cols=None if lay.cols is None else [exact.snap(c, q) for c in lay.cols])


def to_ground(img, H, m, size):
    """The photo seen from straight above: canonical (with margin m) <- image through H.
    The matrix is worked out in Python floats, the pixels in integers (exact.warp)."""
    M = exact.mul3([[1, 0, m], [0, 1, m], [0, 0, 1]], exact.inv3(H))
    return exact.warp(img, M, size)


def plain_colour(lab, lay: Layout, m: int, mask=None):
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


# ---------------------------------------------------------------- frame edges --

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
    warp = to_ground(img, H0, m, size)
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
    new = snap_layout(new)
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
    H = exact.homography(np.float64([(0, 0), (1, 0), (1, 1), (0, 1)]), np.float64(corners))
    _, _, _, r3, _ = camera_from_h(H, shape)
    return math.degrees(math.acos(min(1.0, abs(float(r3[2])))))


OBLIQUE_WARN_DEG = 40   # samples: top-down shots 0-23 degrees, photo1 69


# ---------------------------------------------------------------- triangles --

COL_MIN_SCORE = 1.0
MAX_GAP = 2.5          # fit_columns: the most points between the fields' innermost columns (bar + 1)
MIN_GAP = 1.4          # ... and the least (TODO-062)
SHIFT_TIE = 0.6        # ... beyond it a field moved one point in may score this much less
BAR_GAIN = 0.1         # ... if what it leaves between the fields looks this much more like a bar


def fit_columns(ground_bgr, lay: Layout, m: int, reach: float = 1.2) -> Layout:
    """Fit column centres to the triangles (near their tips, rarely covered).

    reach: how far (in pitches) the columns may move from the even spacing.
    """
    lab = cv2.cvtColor(ground_bgr, cv2.COLOR_BGR2Lab).astype(np.float32)
    plain = plain_colour(lab, lay, m)
    dist = np.linalg.norm(lab - plain, axis=2)
    tri = (dist > 30).astype(np.float32)
    d0, d1 = 0.7 * TRI_DEPTH, 0.92 * TRI_DEPTH
    band = np.vstack([tri[int(m + lay.h * d0):int(m + lay.h * d1)],
                      tri[int(m + lay.h * (1 - d1)):int(m + lay.h * (1 - d0))]])
    mid = tri[int(m + lay.h * 0.46):int(m + lay.h * 0.54)]
    # triangles end before mid-board; frame walls, trays and the bar do not
    prof = np.clip(band.mean(0) - mid.mean(0), 0, None)
    xs = np.arange(len(prof))
    fits = []
    for f0 in (0.0, lay.a + lay.bar):
        centre = m + f0 + lay.a / 2
        by_shift = {}   # the best fit for each whole number of points the columns moved by
        best = None
        for scale in np.linspace(1 - 0.125 * reach, 1 + 0.125 * reach, 31):
            pw = lay.pw * scale
            for off in np.linspace(-reach, reach, 97) * lay.pw:
                c = centre + off + (np.arange(6) - 2.5) * pw
                # near their tips the triangles are narrow peaks; the bar, the frame
                # and a stack of checkers (about one pitch wide) are plateaus, so
                # score peaks, not just colour
                on = exact.interp(c, xs, prof)
                side = (exact.interp(c - 0.5 * pw, xs, prof) + exact.interp(c + 0.5 * pw, xs, prof)) / 2
                sc = (on - side).sum()
                k = int(np.floor(off / lay.pw + 0.5))
                if k not in by_shift or sc > by_shift[k][0]:
                    by_shift[k] = (sc, c - m)
                if best is None or sc > best[0]:
                    best = by_shift[k]
        fits.append([best, by_shift, [k for k, v in by_shift.items() if v is best][0]])
    # The bar is at most about one and a half points wide. When the fields' columns leave a wider gap,
    # a field may have slipped one point outwards: with its innermost triangle hidden under checkers,
    # five triangles still match, and the hidden one is taken into the bar (TODO-060). Then move the
    # field one point in if that matches nearly as well, the one that leaves between the fields most
    # like a bar (not the field's plain colour at mid-board).
    bar_like = mid.mean(0)

    def bar_score(left, right, pw):
        lo, hi = int(m + left[5] + 0.5 * pw), int(m + right[0] - 0.5 * pw)
        return float(bar_like[max(lo, 0):max(hi, lo + 1)].mean()) if hi > lo else 0.0
    for _ in range(2):
        (bl, _, _), (br_, _, _) = fits[0], fits[1]
        pw = ((bl[1][5] - bl[1][0]) + (br_[1][5] - br_[1][0])) / 10
        if bl[0] < COL_MIN_SCORE or br_[0] < COL_MIN_SCORE or br_[1][0] - bl[1][5] <= MAX_GAP * pw:
            break
        moves = []
        for f, step in ((0, 1), (1, -1)):
            cur, by_shift, k = fits[f]
            alt = by_shift.get(k + step)
            if alt is not None and alt[0] >= cur[0] - SHIFT_TIE:
                left, right = (alt[1], br_[1]) if f == 0 else (bl[1], alt[1])
                moves.append((-bar_score(left, right, pw), cur[0] - alt[0], f, alt, k + step))
        moves = [mv for mv in moves if -mv[0] >= bar_score(bl[1], br_[1], pw) + BAR_GAIN]
        if not moves:
            break
        *_, f, alt, k = min(moves, key=lambda mv: mv[:2])
        fits[f] = [alt, fits[f][1], k]
    # The other way (TODO-062): in photos of a screen a field may slip one point inwards, leaving less
    # between the fields than any bar. Then move a field one point out, the one that loses least.
    def placed(f):
        best = fits[f][0]
        return best[1] if best[0] >= COL_MIN_SCORE else (0.0, lay.a + lay.bar)[f] + lay.a / 2 + (np.arange(6) - 2.5) * lay.pw
    for _ in range(2):
        left, right = placed(0), placed(1)
        pw = ((left[5] - left[0]) + (right[5] - right[0])) / 10   # the fitted pitch, as for MAX_GAP
        if right[0] - left[5] >= MIN_GAP * pw:
            break
        moves = []
        for f, step in ((0, -1), (1, 1)):
            cur, by_shift, k = fits[f]
            alt = by_shift.get(k + step)
            if cur[0] >= COL_MIN_SCORE and alt is not None:
                moves.append((cur[0] - alt[0], f, alt, k + step))
        if not moves:
            break
        _, f, alt, k = min(moves, key=lambda mv: mv[:2])
        fits[f] = [alt, fits[f][1], k]
    cols = []
    for (best, _, _), f0 in zip(fits, (0.0, lay.a + lay.bar)):
        if os.environ.get("BG_DEBUG_COLS"):
            print("fit_columns", f0, round(float(best[0]), 3), file=sys.stderr)
        if best[0] < COL_MIN_SCORE:
            # no visible triangles (e.g. engraved, same colour as the field):
            # keep the even spacing from the frame edges
            best = (best[0], f0 + lay.a / 2 + (np.arange(6) - 2.5) * lay.pw)
        cols += [float(v) for v in best[1]]
    return snap_layout(Layout(a=lay.a, bar=lay.bar, h=lay.h, cols=cols))


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
    return snap_layout(Layout(a=lay.a, bar=lay.bar, h=lay.h, cols=cols))


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
    plain = plain_colour(lab, lay, m)
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
    ground = to_ground(img, H, m, size)
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
    new = snap_layout(Layout(a=6 * pw * s, bar=max(bar * s, 1.0), h=lay.h))
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

    A checker standing on a point makes its triangle look shorter, and checkers wider
    than a point hide the bases next to them too: most of a row can look short
    (TODO-076). Take the two outer bases.
    """
    sgn = 1 if row == "top" else -1
    ys = sorted((y - sgn * b for _, r, _, y, _, _, b in tips if r == row and b is not None), key=lambda v: sgn * v)
    if len(ys) < 3:
        return None
    return float(np.median(ys[:2]))
