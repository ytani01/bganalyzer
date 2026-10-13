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
     show. The two checker colours are split by 2-means.
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
import home_prior
from position import Position

# The recognizer's version (board.py, position.py, corners.py and dice.py). Bump it when recognizer/ changes;
# the analyzer has its own in analyzer/app.py. How to bump: CLAUDE.md.
__version__ = "0.6.1"

H_CAN = 1000          # canonical field height (px)
TRI_DEPTH = 0.44      # triangle length / field height
HOUGH_VOTES = 18
CIRCLE_MIN_SCORE = 0.85  # circle score for a checker on its own
LONE_MIN_SCORE = 1.0     # ... and for a single checker with no stack to back it
STACK_SKEW = 0.25        # max sideways step between neighbouring checkers of a stack / pitch
GAP_MIN_SCORE = 0.6      # enough for a circle in line between two checkers of a stack
OUTLINE_SUPPORT = 0.8    # edge support of a checker that has the colour of the spot under it
BAR_COLOUR_TOL = 0.25    # a checker on the bar: colour distance to its cluster / distance between the clusters


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


# ---------------------------------------------------------------- geometry --

def _edge_gradients(lab):
    """Contrast across horizontal and across vertical edges, for _edge_points."""
    return {"h": cv2.blur(np.abs(np.diff(lab, axis=0)).sum(2), (15, 1)),
            "v": cv2.blur(np.abs(np.diff(lab, axis=1)).sum(2), (1, 15))}


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
            if col[k] > 6:
                pts.append((x, y0 + k + 0.5, col[k]))
    else:
        for y in range(int(lo), int(hi), step):
            x0, x1 = int(max(pos - win, 0)), int(min(pos + win, g.shape[1] - 1))
            if x1 <= x0 or not (0 <= y < g.shape[0]):
                continue
            row = g[y, x0:x1]
            k = int(np.argmax(row))
            if row[k] > 6:
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
    p, q = np.polyfit(t[inl], u[inl], 1)
    return p, q, inl.mean()


def refine(img, corners, lay: Layout, m: int):
    """Snap the field edges to straight lines found near their expected place.

    Returns the canonical->image homography, a quality score and the layout
    (field / bar widths re-estimated from the found edges).
    """
    H0 = cv2.getPerspectiveTransform(lay.src_pts(), np.float32(corners))
    Sh = np.array([[1, 0, m], [0, 1, m], [0, 0, 1]], np.float64)
    size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
    warp = cv2.warpPerspective(img, Sh @ np.linalg.inv(H0), size, flags=cv2.INTER_AREA)
    lab = cv2.GaussianBlur(cv2.cvtColor(warp, cv2.COLOR_BGR2Lab).astype(np.float32), (0, 0), 1.5)
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
    quality = float(np.mean([v[2] for v in lines.values() if v is not None]))

    def meet(hl, vl):
        ph, qh = hl[:2]   # y = ph*x + qh
        pv, qv = vl[:2]   # x = pv*y + qv
        y = (ph * qv + qh) / (1 - ph * pv)
        return pv * y + qv, y

    found = {v: [meet(lines["top"], lines[v]), meet(lines["bot"], lines[v])]
             for v in ("L", "BL", "BR", "R") if lines[v] is not None}
    xmid = {v: (p[0][0] + p[1][0]) / 2 - m for v, p in found.items()}
    hgt = np.mean([p[1][1] - p[0][1] for p in found.values()])
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
    xs2 = {"L": 0, "BL": new.a, "BR": new.a + new.bar, "R": new.w}
    dst = np.float64([(xs2[v], y) for v in names for y in (0, new.h)])
    src = np.float64([p for v in names for p in found[v]]) - m
    img_pts = cv2.perspectiveTransform(src[None], H0)[0]
    H, _ = cv2.findHomography(dst, img_pts)
    return H / H[2, 2], quality, new


def camera_from_h(H, shape, f_default=0.75):
    """Focal length (principal point at centre) and pose from a plane homography."""
    hh, ww = shape[:2]
    cx, cy = ww / 2, hh / 2
    T = np.array([[1, 0, -cx], [0, 1, -cy], [0, 0, 1]])
    G = T @ H
    h1, h2 = G[:, 0], G[:, 1]
    f2 = -(h1[0] * h2[0] + h1[1] * h2[1]) / (h1[2] * h2[2]) if abs(h1[2] * h2[2]) > 1e-12 else -1
    f = np.sqrt(f2) if f2 > 0 else f_default * max(ww, hh)
    if not (0.4 * max(ww, hh) < f < 2.0 * max(ww, hh)):
        f = f_default * max(ww, hh)  # near top-down: f is unobservable but also irrelevant
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]])
    B = np.linalg.inv(K) @ H
    lam = (np.linalg.norm(B[:, 0]) + np.linalg.norm(B[:, 1])) / 2
    r1 = B[:, 0] / np.linalg.norm(B[:, 0])
    r2 = B[:, 1] - r1 * (r1 @ B[:, 1])
    r2 /= np.linalg.norm(r2)
    r3 = np.cross(r1, r2)
    t = B[:, 2] / lam
    if r3 @ t > 0:
        r3 = -r3
    return K, r1, r2, r3, t


def view_tilt_deg(corners, shape) -> float:
    """How far from straight above the photo was taken, in degrees (0 = top-down).

    From the tapped corners alone. Steep views (photo1, ~70 degrees) hide and
    shift checkers behind the frame and each other, and read badly.
    """
    H = cv2.getPerspectiveTransform(np.float32([(0, 0), (1, 0), (1, 1), (0, 1)]), np.float32(corners))
    _, _, _, r3, _ = camera_from_h(H, shape)
    return float(np.degrees(np.arccos(min(1.0, abs(r3[2])))))


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
                on = np.interp(c, xs, prof)
                side = (np.interp(c - 0.5 * pw, xs, prof) + np.interp(c + 0.5 * pw, xs, prof)) / 2
                sc = (on - side).sum()
                if best is None or sc > best[0]:
                    best = (sc, c - m)
        if os.environ.get("BG_DEBUG_COLS"):
            print("fit_columns", f0, round(float(best[0]), 3), file=sys.stderr)
        if best[0] < COL_MIN_SCORE:
            # no visible triangles (e.g. engraved, same colour as the field):
            # keep the even spacing from the frame edges
            best = (best[0], f0 + lay.a / 2 + (np.arange(6) - 2.5) * lay.pw)
        cols += list(best[1])
    return Layout(a=lay.a, bar=lay.bar, h=lay.h, cols=cols)


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
            return np.exp(-(near / (0.12 * lay.pw)) ** 2).sum(), used

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
            cols[6 * f:6 * f + 6] = list(best[2])
    return Layout(a=lay.a, bar=lay.bar, h=lay.h, cols=cols)


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
    lab = cv2.cvtColor(ground_bgr, cv2.COLOR_BGR2Lab).astype(np.float32)
    lab = cv2.GaussianBlur(lab, (0, 0), 1.5)
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
                p = np.polyfit(d[:, 0], d[:, 1], 1)
                res = np.abs(np.polyval(p, d[:, 0]) - d[:, 1])
                keep = res <= max(2.5, 2 * np.median(res))
                if keep.sum() < 15:
                    break
                d = d[keep]
            exp_slope = -lay.pw / D
            if not (1.6 * exp_slope < p[0] < 0.6 * exp_slope) or np.median(res) > 2.5 or len(d) < 15:
                continue
            # where the sides would meet; triangles with blunt or rounded ends stop short of it
            tip_depth = min(-p[1] / p[0], d[:, 0].max() + 0.02 * lay.h)
            px = np.polyfit(d[:, 0], d[:, 2], 1)
            tip_x = np.polyval(px, tip_depth)
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
    pts = [lab[img_y(dd), int(round(np.polyval(px, dd)))] for dd in depths[sel]] if sel.sum() >= 5 else []
    if not len(pts):
        return None
    col = np.median(np.array(pts), 0)
    thr = max(15.0, 0.45 * float(np.linalg.norm(col - plain)))
    miss, last = 0, None
    for depth in range(int(depths.min()), -int(m), -1):
        y = img_y(depth)
        if not 0 <= y < lab.shape[0]:
            return None
        xc = np.polyval(px, depth)
        x0, x1 = int(xc - 0.7 * lay.pw), int(xc + 0.7 * lay.pw)
        if x0 < 0 or x1 > lab.shape[1]:
            return None
        own = np.linalg.norm(lab[y, x0:x1] - col, axis=1) < thr
        w, _ = _run_at(own, xc - x0, 0.15 * lay.pw)
        pred = np.polyval(p, depth)
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
    Sh = np.array([[1, 0, m], [0, 1, m], [0, 0, 1]], np.float64)
    size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
    ground = cv2.warpPerspective(img, Sh @ np.linalg.inv(H), size, flags=cv2.INTER_AREA)
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
    new = Layout(a=6 * pw * s, bar=max(bar * s, 1.0), h=lay.h)
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
    img_pts = cv2.perspectiveTransform(np.float64(obs)[None], H)[0]
    Hn, _ = cv2.findHomography(np.float64(ideal), img_pts, cv2.RANSAC, 0.006 * max(img.shape[:2]))
    if Hn is None:
        return H, lay, tips
    return Hn / Hn[2, 2], new, tips


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
    _, _, tri = cv2.kmeans(px, 2, None, (cv2.TERM_CRITERIA_EPS, 20, 0.5), 3, cv2.KMEANS_PP_CENTERS)
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


def _edge_support(gx, gy, x, y, r):
    """Fraction of a circle's perimeter with a strong, radial colour edge."""
    best = 0.0
    th = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    for rr in np.linspace(r * 0.85, r * 1.1, 6):
        px = (x + rr * np.cos(th)).astype(int)
        py = (y + rr * np.sin(th)).astype(int)
        ok = (px >= 0) & (px < gx.shape[1]) & (py >= 0) & (py < gx.shape[0])
        if ok.sum() < 32:
            continue
        vx, vy, t = gx[py[ok], px[ok]], gy[py[ok], px[ok]], th[ok]
        mag = np.hypot(vx, vy) + 1e-6
        radial = np.abs(vx * np.cos(t) + vy * np.sin(t)) / mag
        best = max(best, float(((mag > 40) & (radial > 0.7)).sum() / len(th)))
    return best


def detect_checkers(img_bgr, board, lay: Layout, m: int, pitch: float, tri_map=None, tri_len=None):
    """Checker tops as circles, scored by edge support and colour.

    Returns list of (x, y, r, lab_median, score) in canonical coords (no margin).
    """
    gray = cv2.GaussianBlur(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY), (0, 0), 2)
    r0 = pitch / 2
    # brightness alone misses e.g. black checkers on dark green felt: also look
    # for circles in the colour channels
    lab8 = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2Lab)
    found = []
    for ch in (gray, lab8[:, :, 1], lab8[:, :, 2]):
        ch = cv2.GaussianBlur(cv2.normalize(ch, None, 0, 255, cv2.NORM_MINMAX), (0, 0), 2)
        c = cv2.HoughCircles(ch, cv2.HOUGH_GRADIENT, dp=1.5, minDist=r0 * 1.3, param1=70, param2=HOUGH_VOTES,
                             minRadius=int(r0 * 0.78), maxRadius=int(r0 * 1.2))
        if c is not None:
            found.append(c[0])
    if not found:
        return []
    cs = [np.vstack(found)]
    labf = cv2.GaussianBlur(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2Lab).astype(np.float32), (0, 0), 1.5)
    gx = sum(cv2.Sobel(labf[:, :, i], cv2.CV_32F, 1, 0) for i in range(3))
    gy = sum(cv2.Sobel(labf[:, :, i], cv2.CV_32F, 0, 1) for i in range(3))
    lab = labf * LAB_W
    Wb = board * LAB_W
    hh, ww = gray.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    scored = []
    for x, y, r in cs[0]:
        cx, cy = x - m, y - m
        # a checker's centre lies inside the field (labels and scores on the frame do not)
        if not (-0.3 * pitch < cx < lay.w + 0.3 * pitch and -0.1 * pitch < cy < lay.h + 0.1 * pitch):
            continue
        x0, x1, y0, y1 = int(max(x - r, 0)), int(min(x + r + 1, ww)), int(max(y - r, 0)), int(min(y + r + 1, hh))
        d2 = (xx[y0:y1, x0:x1] - x) ** 2 + (yy[y0:y1, x0:x1] - y) ** 2
        patch = lab[y0:y1, x0:x1]
        inner = patch[d2 < (0.55 * r) ** 2]
        ring = patch[(d2 > (0.7 * r) ** 2) & (d2 < (0.92 * r) ** 2)]
        if len(inner) < 20 or len(ring) < 20:
            continue
        # colour: brightness from the median, hue from the most saturated half
        # (glare makes a red checker look pink; its saturated part stays red)
        chroma = np.hypot(inner[:, 1] - 128, inner[:, 2] - 128)
        sat = inner[chroma >= np.percentile(chroma, 50)]
        med = np.float32([np.median(inner[:, 0]), *np.median(sat[:, 1:], 0)])
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
        if support < 0.2 or ring_same < 0.35 or (distinct < 8 and (support < OUTLINE_SUPPORT or ring_same < 0.6)):
            continue
        if score < GAP_MIN_SCORE:
            continue
        scored.append((score, cx, cy, r, med / LAB_W))

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
    _, _, cc = cv2.kmeans(cols[keep], 2, None, (cv2.TERM_CRITERIA_EPS, 30, 0.1), 5, cv2.KMEANS_PP_CENTERS)
    cc = cc[np.argsort(cc[:, 0])]          # colour 0 = darker
    dd = np.linalg.norm(cols[:, None, :] - cc[None, :, :], axis=2)
    lbl = list(np.argmin(dd, 1))
    # glare washes a coloured checker towards white (red looks pink). When one
    # colour is neutral (white, black) and the other is not, a checker with clear
    # chroma in the coloured one's hue belongs to it, however light it looks
    chroma = np.hypot(raw[:, 1] - 128, raw[:, 2] - 128)
    hue = np.arctan2(raw[:, 2] - 128, raw[:, 1] - 128)
    cent = cc / LAB_W
    cchroma = np.hypot(cent[:, 1] - 128, cent[:, 2] - 128)
    neutral = int(np.argmin(cchroma))
    if cchroma[neutral] < 15 and cchroma[1 - neutral] > 35:
        chue = np.arctan2(cent[1 - neutral, 2] - 128, cent[1 - neutral, 1] - 128)
        dh = np.abs((hue - chue + np.pi) % (2 * np.pi) - np.pi)
        for i in range(len(lbl)):
            if lbl[i] == neutral and chroma[i] > 20 and dh[i] < np.radians(35):
                lbl[i] = 1 - neutral
    # how sure each colour call is: glare makes some checkers sit between the two
    conf = np.abs(dd[:, 0] - dd[:, 1]) / (dd.sum(1) + 1e-6)
    bar = [0, 0]
    for i in on_bar:
        # hinges, clasps and straps on the bar make circles too: a checker there
        # needs a clear circle and one of the checker colours
        if circles[i][4] < LONE_MIN_SCORE or dd[i].min() > BAR_COLOUR_TOL * np.linalg.norm(cc[0] - cc[1]):
            continue
        bar[lbl[i]] += 1
    runs = {}
    for key, (n, members) in stacks.items():
        if not n:
            runs[key] = (None, 0)
            continue
        # a point holds one colour: vote
        k = 0 if sum(conf[i] for i in members if lbl[i] == 0) >= sum(conf[i] for i in members if lbl[i] == 1) else 1
        runs[key] = (k, n)
    return runs, bar, cent


def recognize(img, corners, *, bottom_colour=0, home="right", bar_ratio=None,
              a_ratio=None, debug_prefix=None):
    """corners: TL, TR, BR, BL of the playing area as seen from the bottom player.
    home: 'left', 'right' or 'auto' (guessed from the checkers; info['home'] says which)."""
    cv2.setRNGSeed(0)  # k-means initialisation: make runs repeatable
    m = 60
    H0 = cv2.getPerspectiveTransform(np.float32([(0, 0), (1, 0), (1, 1), (0, 1)]), np.float32(corners))
    K, *_ = camera_from_h(H0, img.shape)
    B = np.linalg.inv(K) @ H0
    aspect = a_ratio or float(np.clip(np.linalg.norm(B[:, 0]) / np.linalg.norm(B[:, 1]), 0.9, 1.4))
    br = bar_ratio or 0.16
    a = aspect * H_CAN / (2 + br)
    lay = Layout(a=a, bar=a * br)
    # 1. geometry: frame edges, then the printed triangles
    H, quality, lay = refine(img, corners, lay, m)
    H, quality, lay = refine(img, cv2.perspectiveTransform(lay.src_pts()[None], H)[0], lay, m)
    Sh = np.array([[1, 0, m], [0, 1, m], [0, 0, 1]], np.float64)
    tips = []
    reach = 1.2
    for _ in range(2):
        size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
        ground = cv2.warpPerspective(img, Sh @ np.linalg.inv(H), size, flags=cv2.INTER_AREA)
        lay = fit_columns(ground, lay, m, reach)
        H, lay, tips = refine_tips(img, H, lay, m)
        if lay.cols is None:
            # fitted to the triangles: from here on only small corrections, as other
            # things on the board can look like triangles too
            reach = 0.4
    size = (int(lay.w + 2 * m), int(lay.h + 2 * m))
    ground = cv2.warpPerspective(img, Sh @ np.linalg.inv(H), size, flags=cv2.INTER_AREA)
    tips = find_tips(ground, lay, m)
    board = board_colours(ground, lay, m, tips)
    pitch = lay.pw * 1.05
    # 2. counting
    ground_lab = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab).astype(np.float32)
    tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
    tri_len = np.median([t[4] for t in tips]) if tips else TRI_DEPTH * lay.h
    circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len)
    if len(circles) >= 4:   # checkers may be wider than a point: measure them
        pitch = float(2 * np.median([c[2] for c in circles]))
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len)
    if len(circles) >= 4:   # learn the board colours again without the checkers on it
        mask = np.zeros(ground.shape[:2], np.uint8)
        for x, y, r, *_ in circles:
            cv2.circle(mask, (int(x + m), int(y + m)), int(r * 1.1), 1, -1)
        board = board_colours(ground, lay, m, tips, mask.astype(bool))
        tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len)
    lay2 = fit_columns_to_checkers(lay, circles)
    if lay2.cols != lay.cols:
        lay = lay2
        tri_map = triangle_colour_map(board, lay, m, tips, ground_lab)
        circles = detect_checkers(ground, board, lay, m, pitch, tri_map, tri_len)
    runs, bar, cc = count_from_circles(circles, lay, pitch)
    guessed = None
    if home == "auto":   # which way the checkers move: guess from where they stand
        home, margin = home_prior.guess(to_position(runs, bar, bottom_colour, "right").points)
        guessed = dict(margin=round(float(margin), 1))
    pos = to_position(runs, bar, bottom_colour, home)
    info = dict(home=home, home_guess=guessed, edge_quality=float(quality), tips=len(tips), circles=len(circles),
                layout=dict(a=float(lay.a), bar=float(lay.bar), h=float(lay.h)), pitch=float(pitch),
                checker_lab=None if cc is None else cc.round(1).tolist(),
                board_lab=board.round(1).tolist())
    # Where the playing area and its columns ended up, for showing the photo next to the read board:
    # corners in image pixels (TL TR BR BL), columns and bar edges as fractions of the width.
    info["geometry"] = dict(
        corners=cv2.perspectiveTransform(lay.src_pts()[None], H)[0].round(1).tolist(),
        columns=[round(float(lay.col_x(c) / lay.w), 4) for c in range(12)],
        bar=[round(float(lay.a / lay.w), 4), round(float((lay.a + lay.bar) / lay.w), 4)])
    info["dice"] = dice_reader.read_dice(img, H, lay, pitch, circles,
                                         debug=debug_prefix and debug_prefix + "_dice.jpg")
    info["cube"] = cube_reader.read_cube(img, H, lay, pitch, circles, info["dice"]["dice"],
                                         debug=debug_prefix and debug_prefix + "_cube.jpg")
    info["tilt_deg"] = round(view_tilt_deg(corners, img.shape), 1)
    info["warnings"] = ["oblique"] if info["tilt_deg"] > OBLIQUE_WARN_DEG else []
    if debug_prefix:
        save_debug(debug_prefix, ground, lay, m, runs, tips, circles)
    return pos, info


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
