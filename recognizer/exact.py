"""Arithmetic that comes out the same, bit for bit, on every CPU (TODO-046).

x86_64 and the Raspberry Pi (aarch64) read some samples differently. The reasons are small:
compiled code may fuse a*b+c into one FMA on aarch64 and not on x86_64, BLAS and LAPACK
(numpy's @, inv, polyfit, a 1-D norm) add up in a different order on each CPU, and libm's
sin/cos/arctan can differ in the last bit. A last-bit difference is harmless until it meets a
threshold, a rounding or an argmax, and from then on the two machines read different boards.

What stays the same everywhere, and what the recognizer is built from:
- integers (numpy int arrays; OpenCV's 8-bit cvtColor, GaussianBlur, Sobel to 16 bits, morphology,
  connected components, Canny), and
- numpy's elementwise + - * / and sqrt on floats (one ufunc at a time, never fused), its sums
  (the order of adding is fixed by numpy, not by the CPU), sort, median and Python's own floats.

So: images stay 8-bit or integer, geometry is worked out with the functions below, and values
handed from one step to the next are snapped to a grid (snap), so a last-bit difference that
slipped in cannot reach the next step.
"""
from __future__ import annotations

import math

import cv2
import numpy as np


def snap(v, q):
    """v rounded to a multiple of q (an array or a float)."""
    if isinstance(v, np.ndarray):
        return np.round(np.asarray(v, np.float64) / q) * q
    return round(float(v) / q) * q


# ---------------------------------------------------------------- 3x3 matrices, in Python floats --

def mat(M):
    return [[float(x) for x in row] for row in np.asarray(M, np.float64)]


def mul3(A, B):
    """A @ B for 3x3 matrices (lists or arrays), as a float64 array."""
    A, B = mat(A), mat(B)
    return np.array([[A[i][0] * B[0][j] + A[i][1] * B[1][j] + A[i][2] * B[2][j] for j in range(3)]
                     for i in range(3)], np.float64)


def inv3(M):
    """The inverse of a 3x3 matrix (adjugate / determinant)."""
    (a, b, c), (d, e, f), (g, h, i) = mat(M)
    A, B, C = e * i - f * h, -(d * i - f * g), d * h - e * g
    det = a * A + b * B + c * C
    inv = [[A, -(b * i - c * h), b * f - c * e],
           [B, a * i - c * g, -(a * f - c * d)],
           [C, -(a * h - b * g), a * e - b * d]]
    return np.array([[x / det for x in row] for row in inv], np.float64)


def apply_h(H, pts):
    """Points (n, 2) through the homography H, as a float64 array (n, 2)."""
    H = mat(H)
    p = np.asarray(pts, np.float64).reshape(-1, 2)
    x, y = p[:, 0], p[:, 1]
    w = H[2][0] * x + H[2][1] * y + H[2][2]
    return np.stack([(H[0][0] * x + H[0][1] * y + H[0][2]) / w,
                     (H[1][0] * x + H[1][1] * y + H[1][2]) / w], 1)


def solve(A, b):
    """x with A x = b (small, square), by Gaussian elimination with partial pivoting in Python floats."""
    n = len(b)
    M = [[float(v) for v in row] + [float(bv)] for row, bv in zip(np.asarray(A, np.float64), np.asarray(b, np.float64))]
    for k in range(n):
        p = max(range(k, n), key=lambda r: abs(M[r][k]))
        M[k], M[p] = M[p], M[k]
        if M[k][k] == 0:
            raise np.linalg.LinAlgError("singular")
        for r in range(k + 1, n):
            f = M[r][k] / M[k][k]
            if f:
                M[r] = [a - f * c for a, c in zip(M[r], M[k])]
    x = [0.0] * n
    for k in range(n - 1, -1, -1):
        x[k] = (M[k][n] - sum(M[k][j] * x[j] for j in range(k + 1, n))) / M[k][k]
    return np.array(x, np.float64)


def _normaliser(p):
    """T moving points p to mean 0 and mean distance sqrt(2) (Hartley), as a 3x3 array."""
    c = p.sum(0) / len(p)
    d = np.sqrt(((p - c) ** 2).sum(1)).sum() / len(p)
    s = math.sqrt(2.0) / float(d) if d > 0 else 1.0
    return np.array([[s, 0, -s * float(c[0])], [0, s, -s * float(c[1])], [0, 0, 1]], np.float64)


def homography(src, dst, weights=None):
    """H with dst ~ H src (least squares over all points, 4 or more; H[2, 2] = 1), or None.

    Like cv2.getPerspectiveTransform / cv2.findHomography(method 0) but the same on every CPU:
    normalised DLT with h22 = 1, the normal equations added up with numpy sums and solved in Python."""
    src, dst = np.asarray(src, np.float64).reshape(-1, 2), np.asarray(dst, np.float64).reshape(-1, 2)
    if len(src) < 4:
        return None
    Ts, Td = _normaliser(src), _normaliser(dst)
    s, d = apply_h(Ts, src), apply_h(Td, dst)
    x, y, u, v = s[:, 0], s[:, 1], d[:, 0], d[:, 1]
    one, zero = np.ones_like(x), np.zeros_like(x)
    rows = np.concatenate([np.stack([x, y, one, zero, zero, zero, -u * x, -u * y], 1),
                           np.stack([zero, zero, zero, x, y, one, -v * x, -v * y], 1)])
    rhs = np.concatenate([u, v])
    w = np.ones(len(rows)) if weights is None else np.concatenate([weights, weights]).astype(np.float64)
    AtA = np.array([[(rows[:, i] * rows[:, j] * w).sum() for j in range(8)] for i in range(8)])
    Atb = np.array([(rows[:, i] * rhs * w).sum() for i in range(8)])
    try:
        h = solve(AtA, Atb)
    except np.linalg.LinAlgError:
        return None
    Hn = np.array([[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1.0]], np.float64)
    H = mul3(inv3(Td), mul3(Hn, Ts))
    if H[2, 2] == 0:
        return None
    return H / H[2, 2]


def homography_robust(src, dst, tol, rounds=8):
    """homography() refitted without the points farther than tol from it (instead of RANSAC)."""
    src, dst = np.asarray(src, np.float64).reshape(-1, 2), np.asarray(dst, np.float64).reshape(-1, 2)
    keep = np.ones(len(src), bool)
    H = None
    for k in range(rounds):
        if keep.sum() < 4:
            break
        H = homography(src[keep], dst[keep])
        if H is None:
            return None
        err = np.sqrt(((apply_h(H, src) - dst) ** 2).sum(1))
        # the first rounds also drop the worst 30%: a far outlier pulls every point off by more than tol
        thr = max(tol, float(np.sort(err)[int(0.7 * (len(err) - 1))])) if k < rounds // 2 else tol
        new = err <= thr
        if (new == keep).all() or new.sum() < 4:
            if k >= rounds // 2:
                break
            continue
        keep = new
    return H


def snap_h(H, w, h, q=1 / 64):
    """H (canonical w x h -> image) through its four corners snapped to q pixels.

    The corners decide a homography, so this loses at most q / 2 of a pixel; what it buys is that
    a last-bit difference in H cannot reach the next step."""
    src = np.float64([(0, 0), (w, 0), (w, h), (0, h)])
    return homography(src, snap(apply_h(H, src), q))


# ---------------------------------------------------------------- fitting --

def polyfit1(x, y):
    """(slope, intercept) of the least-squares line y = p x + q (np.polyfit(x, y, 1) without LAPACK)."""
    x, y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    n = len(x)
    mx, my = x.sum() / n, y.sum() / n
    dx = x - mx
    sxx = (dx * dx).sum()
    p = (dx * (y - my)).sum() / sxx if sxx else 0.0
    return np.array([p, my - p * mx], np.float64)


def polyval1(p, x):
    return p[0] * np.asarray(x, np.float64) + p[1]


def interp(x, xp, fp):
    """np.interp(x, xp, fp) for increasing integer-spaced xp = 0, 1, 2, ... (a profile along pixels),
    in separate numpy operations (np.interp's own loop may be fused differently on each CPU)."""
    fp = np.asarray(fp, np.float64)
    x = np.clip(np.asarray(x, np.float64), 0, len(fp) - 1)
    i = np.minimum(np.floor(x).astype(np.int64), len(fp) - 2)
    t = x - i
    return fp[i] + (fp[i + 1] - fp[i]) * t


def hypot(a, b):
    """sqrt(a^2 + b^2) in separate numpy operations (np.hypot is libm's, and differs by CPU)."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    r = np.sqrt(a * a + b * b)
    return float(r) if r.ndim == 0 else r


def polygon_area(pts):
    """Area of a polygon (n, 2), by the shoelace formula (cv2.contourArea on float points)."""
    p = np.asarray(pts, np.float64).reshape(-1, 2)
    x, y, x2, y2 = p[:, 0], p[:, 1], np.roll(p[:, 0], -1), np.roll(p[:, 1], -1)
    return abs(float((x * y2 - x2 * y).sum())) / 2


def norm(v):
    """Length of a 1-D vector (np.linalg.norm would use BLAS)."""
    v = np.asarray(v, np.float64)
    return float(np.sqrt((v * v).sum()))


def kmeans(x, k, attempts=3, iters=30, cnt=None):
    """Labels and centres of the int32 points x (n, d) in k clusters, in integers throughout
    (k-means++ starts from a fixed seed, the best of `attempts`). Centres are int32."""
    x = np.asarray(x, np.int64)
    cnt = np.ones(len(x), np.int64) if cnt is None else np.asarray(cnt, np.int64)
    rng = np.random.Generator(np.random.PCG64(0))

    def dists(c):
        return np.stack([((x - cj) ** 2).sum(1) for cj in c], 1)

    def pick(weights):
        cs = np.cumsum(weights)
        if cs[-1] == 0:
            return x[0]
        return x[np.searchsorted(cs, rng.integers(cs[-1]), side="right")]

    best = None
    for _ in range(attempts):
        c = [pick(cnt)]
        d = ((x - c[0]) ** 2).sum(1)
        for _ in range(k - 1):
            c.append(pick(d * cnt))
            d = np.minimum(d, ((x - c[-1]) ** 2).sum(1))
        c = np.array(c, np.int64)
        for _ in range(iters):
            lbl = dists(c).argmin(1)
            n = np.array([cnt[lbl == j].sum() for j in range(k)], np.int64)
            sums = np.array([(x[lbl == j] * cnt[lbl == j, None]).sum(0) for j in range(k)], np.int64)
            new = np.where(n[:, None] > 0, (2 * sums + n[:, None]) // (2 * np.maximum(n, 1)[:, None]), c)
            if (new == c).all():
                break
            c = new
        d = dists(c)
        cost = int((d.min(1) * cnt).sum())
        if best is None or cost < best[0]:
            best = (cost, d.argmin(1), c)
    return best[1], best[2]


# ---------------------------------------------------------------- images --

def box_sum(a, kx, ky):
    """Sum over a kx x ky box centred on each pixel (border: reflect, like cv2.blur), in int64."""
    a = np.asarray(a, np.int64)
    out = a
    if kx > 1:
        r = kx // 2
        p = np.pad(out, ((0, 0), (r + 1, kx - r - 1)), mode="reflect")
        c = np.cumsum(p, 1)
        out = c[:, kx:] - c[:, :-kx]
    if ky > 1:
        r = ky // 2
        p = np.pad(out, ((r + 1, ky - r - 1), (0, 0)), mode="reflect")
        c = np.cumsum(p, 0)
        out = c[ky:] - c[:-ky]
    return out


def warp(img, M, size, nearest=False):
    """cv2.warpPerspective(img, M, size) with bilinear (or nearest) sampling and a black border,
    the same on every CPU: OpenCV 5's own warp gives some pixels 1 off depending on the SIMD it uses.

    M maps the source to the output, as in OpenCV. The source point of each output pixel is worked
    out in float64 (separate numpy operations) and cut to 1/32 of a pixel; cv2.remap then mixes the
    four neighbours with integer weights (fixed-point maps: checked to give the same pixels as doing
    it in numpy integers, with and without AVX2)."""
    w, h = size
    (a, b, c), (d, e, f), (g, k, l) = mat(inv3(M))
    u = np.arange(w, dtype=np.float64)[None, :]
    v = np.arange(h, dtype=np.float64)[:, None]
    W = g * u + k * v + l
    lim = 30000.0   # int16 maps; far outside (or behind the camera): just black
    X = np.clip(np.where(W > 0, (a * u + b * v + c) / W, -lim), -lim, lim)
    Y = np.clip(np.where(W > 0, (d * u + e * v + f) / W, -lim), -lim, lim)
    if nearest:
        xy = np.stack([np.floor(X + 0.5), np.floor(Y + 0.5)], 2).astype(np.int16)
        return cv2.remap(img, xy, None, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    fx, fy = np.floor(X * 32 + 0.5).astype(np.int32), np.floor(Y * 32 + 0.5).astype(np.int32)   # nearest 1/32, as OpenCV rounds
    xy = np.stack([fx >> 5, fy >> 5], 2).astype(np.int16)
    frac = ((fy & 31) * 32 + (fx & 31)).astype(np.uint16)
    return cv2.remap(img, xy, frac, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def min_area_rect(hull):
    """((cx, cy), (w, h), angle) of the smallest rectangle around the convex hull's points (integers),
    like cv2.minAreaRect (which works in floats and differs by CPU, TODO-046): one side of it lies on
    a hull edge. angle: of the side w, in degrees within [0, 90)."""
    p = np.asarray(hull, np.float64).reshape(-1, 2)
    if len(p) == 1:
        return (float(p[0, 0]), float(p[0, 1])), (0.0, 0.0), 0.0
    x, y = p[:, 0], p[:, 1]
    best = None
    for i in range(len(p)):
        dx, dy = float(p[(i + 1) % len(p), 0] - p[i, 0]), float(p[(i + 1) % len(p), 1] - p[i, 1])
        n = math.sqrt(dx * dx + dy * dy)
        if n == 0:
            continue
        ux, uy = dx / n, dy / n
        a = x * ux + y * uy            # along the edge
        b = y * ux - x * uy            # across it
        a0, a1, b0, b1 = float(a.min()), float(a.max()), float(b.min()), float(b.max())
        area = (a1 - a0) * (b1 - b0)
        if best is None or area < best[0]:
            best = (area, ux, uy, a0, a1, b0, b1)
    if best is None:
        return (float(x[0]), float(y[0])), (0.0, 0.0), 0.0
    _, ux, uy, a0, a1, b0, b1 = best
    am, bm = (a0 + a1) / 2, (b0 + b1) / 2
    cx, cy = am * ux - bm * uy, am * uy + bm * ux
    w, h = a1 - a0, b1 - b0
    ang = snap(math.degrees(math.atan2(uy, ux)), 1e-9) % 180.0
    if ang >= 90.0:
        ang, w, h = ang - 90.0, h, w
    return (cx, cy), (w, h), ang
