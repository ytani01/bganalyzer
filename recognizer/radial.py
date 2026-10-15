"""Find checker centres with a radius known in advance (TODO-032 idea 5, experimental).

After rectification every checker has about the same radius (half a point's
width), so instead of the Hough transform, which also has to find the radius and
needs a clear, closed outline, use the fast radial symmetry transform (Loy and
Zelinsky 2003): every pixel with a clear gradient votes for the point one radius
away along its gradient, on both sides (a checker can be lighter or darker than
what lies around it). The votes of a checker's rim, even a faint one, pile up at
its centre. Peaks of the votes are the candidates, which board.detect_checkers
then scores as it does Hough's circles.

Not used by the app: `evaluate.py --radial` compares it with the Hough circles.
"""
import os

import cv2
import numpy as np

ALPHA = 2.0         # radial strictness: how much the votes must agree in direction
GRAD_PCT = 70       # only gradients above this percentile vote
PEAK_REL = 0.25     # a peak needs this share of the strongest one's height
RADII = (0.9, 1.0, 1.1)   # radii tried, in the expected radius

if os.environ.get("RADIAL_TUNE"):   # experiments: RADIAL_TUNE=alpha,grad_pct,peak_rel
    ALPHA, GRAD_PCT, PEAK_REL = map(float, os.environ["RADIAL_TUNE"].split(","))


def _frst(gx, gy, r):
    """The symmetry map for radius r (float, same shape as gx)."""
    h, w = gx.shape
    mag = np.sqrt(gx * gx + gy * gy)
    thr = np.percentile(mag, GRAD_PCT)
    ys, xs = np.nonzero(mag > max(thr, 1e-6))
    m = mag[ys, xs]
    ux, uy = gx[ys, xs] / m, gy[ys, xs] / m
    O = np.zeros((h, w))
    M = np.zeros((h, w))
    for sgn in (1, -1):
        px = np.round(xs + sgn * r * ux).astype(int)
        py = np.round(ys + sgn * r * uy).astype(int)
        ok = (px >= 0) & (px < w) & (py >= 0) & (py < h)
        idx = py[ok] * w + px[ok]
        O += np.bincount(idx, minlength=h * w).reshape(h, w)
        M += np.bincount(idx, weights=m[ok], minlength=h * w).reshape(h, w)
    k = 9.9 if r > 1 else 8
    O = np.minimum(O, k)
    F = (O / k) ** ALPHA * (M / k)
    return cv2.GaussianBlur(F, (0, 0), max(0.25 * r, 1))


def find(channels, r0):
    """Candidates [(x, y, r)] like cv2.HoughCircles' (for each channel image, 8 bits)."""
    out = []
    for ch in channels:
        f = np.float64(ch)
        gx = cv2.Sobel(f, cv2.CV_64F, 1, 0)
        gy = cv2.Sobel(f, cv2.CV_64F, 0, 1)
        maps = [(_frst(gx, gy, k * r0), k * r0) for k in RADII]
        S = np.max([m for m, _ in maps], axis=0)
        best_r = np.choose(np.argmax([m for m, _ in maps], axis=0), [rr for _, rr in maps])
        # peaks: local maxima at least 1.3 radii apart
        size = int(1.3 * r0) | 1
        dil = cv2.dilate(S, np.ones((size, size)))
        top = S.max()
        if top <= 0:
            continue
        ys, xs = np.nonzero((S >= dil) & (S > PEAK_REL * top))
        order = np.argsort(-S[ys, xs])
        for i in order[:120]:
            out.append((float(xs[i]), float(ys[i]), float(best_r[ys[i], xs[i]])))
    return np.float32(out) if out else None
