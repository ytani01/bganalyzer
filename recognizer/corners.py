"""Guess the 4 corners of the playing area in a photo, as a starting point for the app (TODO-028).

The playing area is framed by four long straight edges: the far and near edges of the frame, where
the triangles' bases end, and its left and right edges. The search:

1. Candidate far / near edges: the strongest straight, nearly horizontal edges in the photo
   (a Hough transform in integers over the pixels whose contrast runs up and down).
2. For each pair of them, candidate left / right edges: nearly upright lines with an edge pixel in
   (almost) every row between them. A triangle's side is only half as long, so this keeps the
   frame's edges, the bar's and the case's.
3. Each quadrilateral from two of each is scored on how well it frames two rows of twelve
   triangles: seen from straight above, the points' columns (with a bar between the two fields)
   are compared with a triangle's shape, in how far each pixel is from the plain colour of the
   field, and the band between the rows of tips must be plain all the way across.
4. The best few are tried again with each edge moved to the innermost strong edge nearby (frames
   have lips and bevels, and the outer edge is often the stronger one); the best of all wins.

Everything is in integers or in float operations that round the same on every CPU (exact.py),
so x86_64 and the Raspberry Pi find the same corners. Boards without visible triangles may
still be found from their edges; when nothing looks like a board the app starts from a rectangle
for the user to drag into place.

The user can then look again (TODO-068): the corners they have dragged into place stay where they
are in every candidate, and only the part of the photo they have trimmed to is looked in.
"""
from __future__ import annotations

import cv2
import numpy as np

import exact

DEBUG = None           # a list to collect the scored candidates in (for tuning)
WORK_SIDE = 800        # longest side the search runs at (px)
SLOPES = np.arange(-100, 101, 2)   # line slopes tried, in 1/200: up to 0.5 (27 degrees; oblique photos: photo5 0.36, photo6 0.39), steps of 0.01
EDGE_MIN = 60          # contrast (summed over Lab's channels) of an edge pixel
H_LINES = 6            # far / near edge candidates
V_LINES = 8            # left / right edge candidates for each far / near pair
LINE_SEP = 0.015       # nearest two candidates of one kind, against the photo's side
V_COVER = 0.45         # an upright line needs an edge pixel in this share of the rows
MIN_HEIGHT = 0.25      # the playing area's height, at least, against the photo's
ASPECT = (0.8, 2.2)    # its width against its height
MIN_WIDTH = 0.3        # its width, at least, against the photo's
TRIMMED = (0.5, 0.4)   # its width and height, at least, in a photo the user has trimmed to the board
STEP = 4               # rows between stored running counts of the upright lines' coverage
# the structure score (seen from straight above, RW x RH)
RW, RH = 208, 160
DEPTH = 0.40           # a triangle's length against the playing area's height
BARS = (0.0, 0.03, 0.06, 0.09, 0.12, 0.15, 0.18)   # bar widths tried, against the playing area's width
W_PLAIN = 0.6   # weight of a plain band between the tips
PLAIN_DE = 20          # colour difference (Lab) still plain
MIN_SCORE = 0.15       # a board's structure score, at least
REFINE = 12             # candidates (the best by structure) whose edges are moved in and scored again
# moving each edge to the innermost strong edge nearby (seen from straight above, FW x FH)
FW, FH, FM = 400, 320, 40
OUT, IN = 0.06, 0.05   # how far each edge is looked for, outwards and inwards, against the side
NEAR = 0.05            # a candidate agrees with a fixed corner this near it, against the long side looked in
PEAK = 0.4             # an edge counts if this strong against the strongest in the range


def shrink(img):
    """img with its longest side at most WORK_SIDE, and the scale (x, y) it was shrunk by.

    In integers only (halving with pyrDown, then INTER_LINEAR_EXACT), so every CPU
    gets the same pixels: INTER_AREA works in floats and gave x86_64 and the
    Raspberry Pi slightly different pixels, and from them different corners (TODO-028)."""
    h, w = img.shape[:2]
    s = min(1.0, WORK_SIDE / max(h, w))
    if s == 1.0:
        return img, np.array([1.0, 1.0])
    size = (round(w * s), round(h * s))
    small = img
    while small.shape[1] >= 2 * size[0] and small.shape[0] >= 2 * size[1]:
        small = cv2.pyrDown(small)
    small = cv2.resize(small, size, interpolation=cv2.INTER_LINEAR_EXACT)
    return small, np.array([size[0] / w, size[1] / h])


def _gradients(bgr, sigma=1.0):
    """Contrast across columns (gx) and across rows (gy), summed over Lab's channels (int32)."""
    lab = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab), (0, 0), sigma)
    gx = sum(np.abs(cv2.Sobel(lab[:, :, i], cv2.CV_16S, 1, 0).astype(np.int32)) for i in range(3))
    gy = sum(np.abs(cv2.Sobel(lab[:, :, i], cv2.CV_16S, 0, 1).astype(np.int32)) for i in range(3))
    return gx, gy


def _shift(t, k):
    """round(t * k / 200) in integers."""
    return (t * k * 2 + 200) // 400


# ---------------------------------------------------------------- far / near edges --

def _h_lines(gx, gy):
    """The strongest nearly horizontal lines y = c + x k / 200: [(k, c, votes)], strongest first."""
    h, w = gy.shape
    wt = np.where((gy > 2 * gx) & (gy > EDGE_MIN), gy, 0)
    ys, xs = np.nonzero(wt)
    v = wt[ys, xs].astype(np.int64)
    pad = h
    acc = np.zeros((len(SLOPES), h + 2 * pad), np.int64)
    for i, k in enumerate(SLOPES):
        c = ys - _shift(xs, int(k)) + pad
        ok = (c >= 0) & (c < acc.shape[1])
        acc[i] = np.bincount(c[ok], v[ok], minlength=acc.shape[1]).astype(np.int64)
    sep = int(LINE_SEP * max(h, w))
    out = []
    for _ in range(H_LINES):
        i, c = np.unravel_index(int(np.argmax(acc)), acc.shape)
        if acc[i, c] <= 0:
            break
        out.append((int(SLOPES[i]), int(c) - pad, int(acc[i, c])))
        acc[:, max(0, c - sep):c + sep + 1] = 0
    return out


# ---------------------------------------------------------------- left / right edges --

class _Upright:
    """How many rows of a band have an edge pixel on each nearly upright line x = c + y k / 200
    (running counts per slope, stored every STEP rows, so any band is a subtraction)."""

    def __init__(self, gx, gy):
        h, w = gx.shape
        edge = ((gx > gy) & (gx > EDGE_MIN - 10)).astype(np.uint8)
        edge = cv2.dilate(edge, np.ones((1, 3), np.uint8))
        ys, xs = np.nonzero(edge)
        self.pad = pad = int(0.3 * h) + 2
        nb = h // STEP + 1
        width = w + 2 * pad
        self.cum = np.zeros((len(SLOPES), nb + 1, width), np.int32)
        for i, k in enumerate(SLOPES):
            c = xs - _shift(ys, int(k)) + pad          # the line through (x, y) with this slope
            ok = (c >= 0) & (c < width)
            n = np.bincount((ys[ok] // STEP) * width + c[ok], minlength=nb * width)[:nb * width]
            self.cum[i, 1:] = np.cumsum(n.reshape(nb, width), 0)
        self.w = w

    def lines(self, y0, y1):
        """Upright lines covering most rows of [y0, y1): [(k, c, share)], left to right."""
        j0, j1 = -(-y0 // STEP), y1 // STEP        # whole blocks of STEP rows within [y0, y1)
        if j1 - j0 < 4:
            return []
        share = (self.cum[:, j1] - self.cum[:, j0]) / ((j1 - j0) * STEP)
        # where each line crosses the middle of the band: two lines near there are the same edge
        ymid = (y0 + y1) // 2
        mid = (np.arange(share.shape[1])[None, :] - self.pad) + _shift(ymid, SLOPES[:, None])
        sep = int(LINE_SEP * self.w)
        out = []
        for _ in range(V_LINES):
            i, c = np.unravel_index(int(np.argmax(share)), share.shape)
            if share[i, c] < V_COVER:
                break
            out.append((int(SLOPES[i]), int(c) - self.pad, float(share[i, c])))
            share[np.abs(mid - mid[i, c]) <= sep] = 0
        return sorted(out, key=lambda v: v[1])


def _meet(hl, vl):
    """Where y = ch + x kh / 200 meets x = cv + y kv / 200."""
    kh, ch = hl[0], hl[1]
    kv, cv = vl[0], vl[1]
    x = (cv + ch * kv / 200) / (1 - kh * kv / 40000)
    return x, ch + x * kh / 200


# ---------------------------------------------------------------- structure score --

def _point_templates(RW, RH):
    """For each bar width: the 24 points' pixels (rows, columns: index arrays) and their triangle
    template (zero mean, unit length), and which field each is in."""
    out = {}
    half = RH // 2
    for bar in BARS:
        a = RW * (1 - bar) / 2
        p = a / 6
        wp = int(round(p))
        rows, cols, tmpl, field = [], [], [], []
        for f, f0 in enumerate((0.0, a + bar * RW)):
            for i in range(6):
                cx = f0 + (i + 0.5) * p
                x0 = int(round(cx - wp / 2))
                xs = np.arange(x0, x0 + wp)
                for top in (True, False):
                    ys = np.arange(0, half) if top else np.arange(RH - half, RH)
                    d = (ys + 0.5) if top else (RH - ys - 0.5)
                    m = (np.abs(xs[None, :] + 0.5 - cx) < (p / 2) * (1 - d[:, None] / (DEPTH * RH))) & (d[:, None] < DEPTH * RH)
                    t = m.astype(np.float64).ravel()
                    t = t - t.sum() / len(t)
                    t = t / np.sqrt((t * t).sum())
                    rows.append(np.repeat(ys, wp))
                    cols.append(np.tile(np.clip(xs, 0, RW - 1), half))
                    tmpl.append(t)
                    field.append(f)
        out[bar] = (a, np.array(rows), np.array(cols), np.array(tmpl), np.array(field))
    return out


_TEMPLATES = {size: _point_templates(*size) for size in ((RW, RH), (RW // 2, RH // 2))}


def _structure(rect):
    RH, RW = rect.shape[:2]
    """How much the view from straight above (RW x RH) shows two rows of twelve triangles:
    the mean correlation of each point's patch (distance from the field's plain colour) with
    a triangle's shape, for the best bar width (-1..1)."""
    lab = cv2.cvtColor(rect, cv2.COLOR_BGR2Lab).astype(np.int32)
    best = -1.0
    for bar, (a, rows, cols, tmpl, field) in _TEMPLATES[(RW, RH)].items():
        plain = np.empty((2, 3), np.float64)
        for f, f0 in enumerate((0.0, a + bar * RW)):
            mid = lab[int(0.46 * RH):int(0.54 * RH), int(f0 + 0.05 * a):int(f0 + 0.95 * a)].reshape(-1, 3)
            plain[f] = np.median(mid, 0)
        d = lab[rows, cols] - plain[field][:, None, :]          # (24, pixels of a point, 3)
        v = np.sqrt((d * d).sum(2))
        # between the rows of tips the field is plain, all the way across both fields
        band = lab[int(0.45 * RH):int(0.55 * RH)]
        plain_share = 0.0
        for f, (x0, x1) in enumerate(((0, int(a)), (int(a + bar * RW + 0.5), RW))):
            e = band[:, x0:x1] - plain[f]
            plain_share += float(((e * e).sum(2) < PLAIN_DE * PLAIN_DE).sum()) / max(1, e.shape[0] * e.shape[1]) / 2
        v = v - (v.sum(1) / v.shape[1])[:, None]
        n = np.sqrt((v * v).sum(1))
        c = (v * tmpl).sum(1) / np.where(n > 0, n, 1)
        best = max(best, float(c.sum() / len(c)) + W_PLAIN * plain_share)
    return best


def _view(small, quad, w, h, m):
    """The quad seen from straight above, w x h with a margin of m pixels, and the homography."""
    dst = np.float64([(m, m), (w + m, m), (w + m, h + m), (m, h + m)])
    H = exact.homography(np.float64(quad), dst)
    if H is None:
        return None, None
    return exact.warp(small, H, (w + 2 * m, h + 2 * m)), H


# ---------------------------------------------------------------- moving the edges in --

def _innermost(prof, edge, sign, side):
    """Inward move (pixels) to the innermost strong edge within OUT * side outwards and IN * side
    inwards of `edge` in the profile; 0 when there is none."""
    lo, hi = int(-OUT * side), int(IN * side)
    vals = np.array([prof[edge + sign * t] if 0 <= edge + sign * t < len(prof) else 0 for t in range(lo, hi + 1)], np.int64)
    v = np.convolve(vals, np.int64([1, 2, 1]), "same")
    top = int(v.max())
    if top <= 0:
        return 0
    peaks = [i for i in range(1, len(v) - 1) if v[i] >= v[i - 1] and v[i] >= v[i + 1] and 10 * v[i] >= 10 * PEAK * top]
    return lo + max(peaks) if peaks else 0


def _move_in(small, quad):
    """quad with each edge moved to the innermost strong edge nearby (frames have lips and bevels).
    The left / right edges are looked for between the triangles' tips, where only the frame
    meets the field."""
    view, H = _view(small, quad, FW, FH, FM)
    if view is None:
        return quad
    gx, gy = _gradients(view)
    across_rows = gy[:, FM + FW // 20:FM + FW - FW // 20].sum(1)
    across_cols = gx[FM + int(0.38 * FH):FM + int(0.62 * FH), :].sum(0)
    mt = _innermost(across_rows, FM, 1, FH)
    mb = _innermost(across_rows, FM + FH, -1, FH)
    ml = _innermost(across_cols, FM, 1, FW)
    mr = _innermost(across_cols, FM + FW, -1, FW)
    rect = np.float64([(FM + ml, FM + mt), (FM + FW - mr, FM + mt), (FM + FW - mr, FM + FH - mb), (FM + ml, FM + FH - mb)])
    return exact.apply_h(exact.inv3(H), rect)


# ---------------------------------------------------------------- the search --

def guess(small, emit=None, fixed=None, least=(MIN_WIDTH, MIN_HEIGHT)):
    """TL, TR, BR, BL of the playing area in small's pixels (float64 4 x 2), or None.

    fixed: TL, TR, BR, BL, each a point (small's pixels) the user has put in place, or None: those
    stay where they are, and only the others are looked for. least: the playing area's width and
    height, at least, against small's.
    emit(stage, **arrays): told of each stage of the search, in small's pixels, for showing it as it
    goes ("edges", "uprights", "candidates"; see find_corners). It does not change what is found."""
    emit = emit or (lambda stage, **arrays: None)
    fixed = fixed or [None] * 4
    keep = [i for i in range(4) if fixed[i] is not None]

    def pin(q):
        q = q.copy()
        for i in keep:
            q[i] = fixed[i]
        return q

    h, w = small.shape[:2]
    gx, gy = _gradients(small)
    hl = _h_lines(gx, gy)
    emit("edges", lines=np.float64([[(0, c), (w, c + w * k / 200)] for k, c, _ in hl]).reshape(-1, 2, 2))
    if len(hl) < 2:
        return None
    up = _Upright(gx, gy)
    uprights = {}   # each upright line found, over the tallest band it was found in
    raw, looked = [], set()
    for top in hl:
        for bot in hl:
            yt, yb = top[1] + w / 2 * top[0] / 200, bot[1] + w / 2 * bot[0] / 200
            if yb - yt < least[1] * h:
                continue
            band = (int(yt + 0.03 * (yb - yt)), int(yb - 0.03 * (yb - yt)))
            vl = up.lines(max(0, band[0]), min(h, band[1]))
            for k, c, _ in vl:
                if (k, c) not in uprights or band[1] - band[0] > uprights[k, c][1] - uprights[k, c][0]:
                    uprights[k, c] = band
            for i in range(len(vl)):
                for j in range(i + 1, len(vl)):
                    q = np.float64([_meet(top, vl[i]), _meet(top, vl[j]), _meet(bot, vl[j]), _meet(bot, vl[i])])
                    if max([exact.norm(q[i] - fixed[i]) for i in keep], default=0) > NEAR * max(h, w):
                        continue   # its corners disagree with the ones the user put in place
                    q = pin(q)
                    wid = (exact.norm(q[1] - q[0]) + exact.norm(q[2] - q[3])) / 2
                    hgt = (exact.norm(q[3] - q[0]) + exact.norm(q[2] - q[1])) / 2
                    if hgt <= 0 or not ASPECT[0] < wid / hgt < ASPECT[1] or wid < least[0] * w:
                        continue
                    key = tuple(np.round(q / (0.005 * max(h, w))).astype(np.int64).ravel())
                    if key in looked:   # the same quad with the fixed corners in place
                        continue
                    looked.add(key)
                    view, _ = _view(small, q, RW // 2, RH // 2, 0)   # a first look at half size
                    if view is not None:
                        raw.append((_structure(view), q))
    emit("uprights", lines=np.float64([[(c + y0 * k / 200, y0), (c + y1 * k / 200, y1)]
                                       for (k, c), (y0, y1) in sorted(uprights.items())]).reshape(-1, 2, 2))
    # the best few, each edge moved to the innermost strong edge nearby, scored again
    raw.sort(key=lambda r: -r[0])
    emit("candidates", quads=np.float64([q for _, q in raw[:REFINE]]).reshape(-1, 4, 2))
    seen, best = set(), None
    for s0, q0 in raw[:REFINE]:
        for q in (q0, pin(_move_in(small, q0))):      # as found, and with the edges moved in
            key = tuple(np.round(q / (0.005 * max(h, w))).astype(np.int64).ravel())
            if key in seen:
                continue
            seen.add(key)
            view, _ = _view(small, q, RW, RH, 0)
            if view is None:
                continue
            s = _structure(view)
            if DEBUG is not None:
                DEBUG.append((s, q, s0))
            if best is None or s > best[0]:
                best = (s, q)
    if best is None or best[0] < MIN_SCORE:
        return None
    return best[1]


def find_corners(img, progress=None, fixed=None, crop=None):
    """TL, TR, BR, BL of the playing area in image pixels, or None if no board was found.

    fixed: TL, TR, BR, BL, each [x, y] the user has put in place or None; those are kept and only
    the others are looked for (all four given: they are the answer). crop: (x0, y0, x1, y1), the
    part of the photo to look in (the user's trimming).

    progress(stage, data): called as each stage of the search is done, with what it found in image
    pixels: "edges" {lines: the far / near edge candidates across the photo}, "uprights" {lines: the
    left / right edge candidates, over the band between two of those}, "candidates" {quads: the
    quadrilaterals that looked most like a board at first, best first}, "corners" {corners} (only
    when a board is found). It does not change what is found."""
    h, w = img.shape[:2]
    x0, y0, x1, y1 = (0, 0, w, h) if crop is None else (
        min(max(int(crop[0]), 0), w - 1), min(max(int(crop[1]), 0), h - 1),
        min(max(int(crop[2]), 1), w), min(max(int(crop[3]), 1), h))
    if x1 - x0 < 16 or y1 - y0 < 16:
        return None
    small, s = shrink(img[y0:y1, x0:x1])
    at = np.float64([x0, y0])
    fixed = list(fixed or [None] * 4)
    if all(p is not None for p in fixed):
        q = np.float64(fixed)
    else:
        emit = None
        if progress:
            def emit(stage, **arrays):
                progress(stage, {k: (np.float64(v) / s + at).round(1).tolist() for k, v in arrays.items()})
        q = guess(small, emit, [None if p is None else (np.float64(p) - at) * s for p in fixed],
                  (MIN_WIDTH, MIN_HEIGHT) if crop is None else TRIMMED)
        if q is None:
            return None
        q = q / s + at
    corners = exact.snap(q, 0.1).round(1).tolist()
    if progress:
        progress("corners", {"corners": corners})
    return corners


if __name__ == "__main__":
    import sys
    for path in sys.argv[1:]:
        print(path, find_corners(cv2.imread(path)))
