"""TODO-071: find checkers in the photo itself (before rectifying) and tell the board's size and tilt from them.

Checkers in a stack touch: their centres are a diameter apart in a line. Inner rings and rims share the
centre, so the spacing does not depend on which ring the radius picked (TODO-068's trouble). For each
vertical stretch s (an oblique view squashes the circles up and down) and radius r, the peaks of radial
symmetry (radial.py) are found, and triples of them in a line, evenly spaced about 2r apart, counted.
analyse.py picks (s, r) from them: the checker's diameter across (2r) and the tilt (acos 1/s).

usage: uv run python archives/agents/TODO-071/measure_ruler.py [-j N] [sample ...]
"""
import argparse, glob, json, math, os, sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SAMPLES = os.path.join(ROOT, "samples")
sys.path.insert(0, os.path.join(ROOT, "recognizer"))

RATIO = 13.7                     # the playing area's width against a checker's diameter (TODO-068)
STRETCH = (1.0, 1.15, 1.33, 1.6, 2.0)  # vertical stretches tried (tilt 0, 30, 41, 51, 60 degrees)
SUPPORT = float(os.environ.get("SUPPORT", 0.35))
SPACING = (1.8, 2.3)             # neighbours in a stack, in r
LINE_TOL = 0.2                   # the third centre this near where an even spacing puts it, in r


def truth(t, small_shape, s):
    import numpy as np, geometry
    q = np.float64(t["corners_TL_TR_BR_BL"]) * s
    width = (np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])) / 2
    return width, geometry.view_tilt_deg(q, small_shape)


def triples(pts, r):
    """How many centres have two neighbours 1.8r-2.3r away on either side, in a line, evenly spaced:
    (in a line within 35 degrees of upright: a stack, other)."""
    import numpy as np
    if len(pts) < 3:
        return 0, 0
    p = np.float64(pts)
    d = np.linalg.norm(p[:, None] - p[None], axis=2)
    near = (d >= SPACING[0] * r) & (d <= SPACING[1] * r)
    up = side = 0
    for b in range(len(p)):
        nb = np.nonzero(near[b])[0]
        found = set()
        for a in nb:
            want = 2 * p[b] - p[a]
            if (np.linalg.norm(p[nb] - want, axis=1) < LINE_TOL * r).any():
                dx, dy = abs(p[a] - p[b])
                found.add(dy > 1.43 * dx)   # within 35 degrees of upright
        up += True in found
        side += False in found
    return up, side


def one(path):
    import cv2, numpy as np, corners, radial, checkers
    radial.RADII = (1.0,)
    t = json.load(open(path))
    img = cv2.imread(os.path.join(SAMPLES, t["image"]))
    small, s = corners.shrink(img)
    width, tilt = truth(t, small.shape, s[0])
    rows = []
    for st in STRETCH:
        im = small if st == 1.0 else cv2.resize(small, (small.shape[1], round(small.shape[0] * st)))
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        lab8 = cv2.cvtColor(im, cv2.COLOR_BGR2Lab)
        chans = [cv2.GaussianBlur(checkers._stretch(ch), (0, 0), 1) for ch in (gray, lab8[:, :, 1], lab8[:, :, 2])]
        _, gx, gy = checkers.lab_gradients(im)
        r = 5.0
        while r < 45:
            kept = []
            for ch in chans:
                for x, y, _ in radial._peaks(ch, r):
                    if all((x - u) ** 2 + (y - v) ** 2 > (0.5 * r) ** 2 for u, v in kept) and \
                            checkers.edge_support(gx, gy, x, y, r) >= SUPPORT:
                        kept.append((x, y))
            rows.append((st, r, len(kept), *triples(kept, r)))
            r *= 1.1
    return width, tilt, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("samples", nargs="*")
    ap.add_argument("-j", type=int, default=None)
    a = ap.parse_args()
    files = ([os.path.join(SAMPLES, s + ".truth.json") for s in a.samples] or
             [f for f in sorted(glob.glob(os.path.join(SAMPLES, "*.truth.json"))) if "synth-cube-" not in f])
    out = {}
    with ProcessPoolExecutor(a.j) as ex:
        for f, (width, tilt, rows) in zip(files, ex.map(one, files)):
            name = os.path.basename(f).removesuffix(".truth.json")
            out[name] = dict(width=width, tilt=tilt, rows=rows)
            print(name, flush=True)
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "ruler.json"), "w"))


if __name__ == "__main__":
    main()
