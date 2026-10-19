"""Find checker centres with a radius known in advance (TODO-032 idea 5, TODO-051).

After rectification every checker has about the same radius (half a point's
width), so instead of the Hough transform, which also has to find the radius and
needs a clear, closed outline, use the fast radial symmetry transform (Loy and
Zelinsky 2003): every pixel with a clear gradient votes for the point one radius
away along its gradient, on both sides (a checker can be lighter or darker than
what lies around it). The votes of a checker's rim, even a faint one, pile up at
its centre. Peaks of the votes are the candidates, which checkers.detect_checkers
then scores.

Everything is counted in integers, or in floats only with operations IEEE 754
rounds the same way on every CPU (+ - * / and sqrt, element by element), so the
candidates are the same on x86_64 and arm64 (TODO-046): Sobel in 16 bits, the
strongest gradients by an order statistic, the votes as integer counts and sums,
the smoothing as two integer box filters.

The maps depend only on the image and the radius, and board.recognize calls
detect_checkers several times on the same image: they are kept for the last image.
"""

import hashlib
import os

import cv2
import numpy as np

GRAD_KEEP = 0.3  # the strongest share of the gradients vote
ORIENT_CAP = 10  # votes counted per pixel for the direction term ((O / cap)^2 in Loy and Zelinsky)
PEAK_REL = 0.25  # a peak needs this share of the strongest one's height
BOX_PASSES = 3  # box filters standing in for the Gaussian (2: 526, 3: 537, 4: 528 points on the samples)
RADII = (
    0.9,
    1.0,
    1.1,
)  # radii tried, in the expected radius (one radius: 496, two: 523)

if os.environ.get("RADIAL_TUNE"):  # experiments: RADIAL_TUNE=grad_keep,peak_rel
    GRAD_KEEP, PEAK_REL = map(float, os.environ["RADIAL_TUNE"].split(","))

_cache = {}


def _box(a, w):
    """Sum over a w x w window centred on each pixel (int64, zero outside), exactly."""
    h = w // 2
    rows, cols = a.shape
    c = np.zeros((rows + w, cols), np.int64)
    np.cumsum(a, axis=0, out=c[h + 1 : h + 1 + rows])
    c[h + 1 + rows :] = c[h + rows]
    a = c[w:] - c[:rows]
    c = np.zeros((rows, cols + w), np.int64)
    np.cumsum(a, axis=1, out=c[:, h + 1 : h + 1 + cols])
    c[:, h + 1 + cols :] = c[:, h + cols : h + cols + 1]
    return c[:, w:] - c[:, :cols]


def _maps(ch, r0):
    """The symmetry map (int64) of a channel, the best of RADII at each pixel, and that radius."""
    key = (hashlib.sha1(ch.tobytes()).hexdigest(), ch.shape, r0)
    if key in _cache:
        return _cache[key]
    if len(_cache) > 12:
        _cache.clear()
    h, w = ch.shape
    gx = cv2.Sobel(ch, cv2.CV_16S, 1, 0).astype(np.int64)
    gy = cv2.Sobel(ch, cv2.CV_16S, 0, 1).astype(np.int64)
    mag2 = gx * gx + gy * gy
    flat = mag2.ravel()
    k = int(len(flat) * (1 - GRAD_KEEP))
    thr = max(int(np.partition(flat, k)[k]), 1)
    ys, xs = np.nonzero(mag2 >= thr)
    m = np.sqrt(
        mag2[ys, xs].astype(np.float64)
    )  # sqrt and / are rounded alike on every CPU
    ux, uy = gx[ys, xs] / m, gy[ys, xs] / m
    weight = np.floor(m).astype(np.int64)
    S = R = None
    for f in RADII:
        r = f * r0
        O = np.zeros(h * w, np.int64)
        M = np.zeros(h * w, np.int64)
        for sgn in (1.0, -1.0):
            px = np.rint(xs + sgn * r * ux).astype(np.int64)
            py = np.rint(ys + sgn * r * uy).astype(np.int64)
            ok = (px >= 0) & (px < w) & (py >= 0) & (py < h)
            idx = py[ok] * w + px[ok]
            O += np.bincount(idx, minlength=h * w)
            M += np.bincount(idx, weights=weight[ok], minlength=h * w).astype(
                np.int64
            )  # sums of integers: exact
        O = np.minimum(O, ORIENT_CAP)
        F = (O * O * M).reshape(h, w)
        # a Gaussian of sigma r/4, as BOX_PASSES box filters (each adds a variance of (b^2 - 1) / 12)
        b = max(int(round((12 * (0.25 * r) ** 2 / BOX_PASSES + 1) ** 0.5)), 1) | 1
        for _ in range(BOX_PASSES):
            F = _box(F, b) // (b * b)  # a mean, so that the sums stay small
        if S is None:
            S, R = F, np.full((h, w), r)
        else:  # the first radius wins a tie, as np.argmax would
            better = F > S
            S = np.where(better, F, S)
            R = np.where(better, r, R)
    _cache[key] = (S, R)
    return S, R


def _peaks(ch, r0):
    """[(x, y, r)] of a channel's symmetry peaks, strongest first."""
    key = ("peaks", hashlib.sha1(ch.tobytes()).hexdigest(), ch.shape, r0)
    if key not in _cache:
        S, R = _maps(ch, r0)
        top = int(S.max())
        out = []
        if top > 0:
            # local maxima of a (1.3 r)-wide window; float64 holds these integers exactly
            size = int(1.3 * r0) | 1
            dil = cv2.dilate(S.astype(np.float64), np.ones((size, size), np.uint8))
            ys, xs = np.nonzero((S >= dil) & (S * 100 > int(PEAK_REL * 100) * top))
            order = np.lexsort(
                (xs, ys, -S[ys, xs])
            )  # strongest first, ties by position
            out = [
                (float(xs[i]), float(ys[i]), float(R[ys[i], xs[i]]))
                for i in order[:120]
            ]
        _cache[key] = out
    return _cache[key]


def find(channels, r0):
    """Candidates [(x, y, r)] like cv2.HoughCircles' (for each channel image, 8 bits)."""
    out = [c for ch in channels for c in _peaks(ch, r0)]
    return np.float32(out) if out else None
