"""TODO-071: would the checkers' size (measure_ruler.py, ruler.json) pick better corners?

For each sample (shrunk as the PWA does, as check_corners.py --app), the candidates corners.guess scored last
(corners.DEBUG) are kept; then
  drop T:   candidates whose width is off the checkers' estimate by more than a factor T are dropped
            (all dropped: the best as now)
  add W:    the structure score loses W * |log(width / estimate)|
and the error of the winner (largest corner distance / long side, as check_corners.py) is counted as there.

usage: uv run python archives/agents/TODO-071/simulate.py [-j N]
"""
import argparse, glob, json, math, os, sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SAMPLES = os.path.join(ROOT, "samples")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "recognizer"))
GOOD = 0.036
RATIO = 13.7


def candidates(path):
    """(truth corners in small's pixels, small's long side, [(score, quad)])."""
    import cv2, numpy as np, corners
    from evaluate import shrink_like_app
    t = json.load(open(path))
    img = cv2.imread(os.path.join(SAMPLES, t["image"]))
    img, truth = shrink_like_app(img, t["corners_TL_TR_BR_BL"])
    small, s = corners.shrink(img)
    corners.DEBUG = []
    corners.guess(small)
    return (np.float64(truth) * s).tolist(), max(small.shape[:2]), [(sc, q.tolist()) for sc, q, _ in corners.DEBUG]


def estimate(rows):
    """The playing area's width from the checkers (no stretch, all triples; a radius about half wins
    with half as many)."""
    rows = [r for r in rows if r[0] == 1.0]
    f = lambda v: v[3] + v[4]
    best = max(rows, key=lambda v: (f(v), -v[1]))
    half = [v for v in rows if abs(v[1] / (best[1] / 2) - 1) < 0.1 and 2 * f(v) >= f(best) and f(v) >= 3]
    return 2 * (max(half, key=f) if half else best)[1] * RATIO


def main():
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("-j", type=int, default=None)
    a = ap.parse_args()
    ruler = json.load(open(os.path.join(HERE, "ruler.json")))
    files = [f for f in sorted(glob.glob(os.path.join(SAMPLES, "*.truth.json"))) if "synth-cube-" not in f]
    cache = os.path.join(HERE, "candidates.json")
    if os.path.exists(cache):
        cand = json.load(open(cache))
    else:
        with ProcessPoolExecutor(a.j) as ex:
            cand = dict(zip([os.path.basename(f).removesuffix(".truth.json") for f in files], ex.map(candidates, files)))
        json.dump(cand, open(cache, "w"))

    def width(q):
        q = np.float64(q)
        return (np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])) / 2

    def err(q, truth, side):
        return float(np.linalg.norm(np.float64(q) - truth, axis=1).max() / side)

    rules = [("now", None)] + [(f"drop {t}", ("drop", t)) for t in (1.15, 1.25, 1.4, 1.6)] + \
            [(f"add {w}", ("add", w)) for w in (0.05, 0.1, 0.2, 0.4)]
    table = {name: [0, 0, 0] for name, _ in rules}
    changed = {name: [] for name, _ in rules}
    for name, (truth, side, cs) in cand.items():
        truth = np.float64(truth)
        est = estimate(ruler[name]["rows"])
        base = None
        for rule, how in rules:
            if not cs:
                table[rule][0] += 1
                continue
            if how is None:
                pool = [(s, q) for s, q in cs]
            elif how[0] == "drop":
                pool = [(s, q) for s, q in cs if 1 / how[1] <= width(q) / est <= how[1]] or list(cs)
            else:
                pool = [(s - how[1] * abs(math.log(width(q) / est)), q) for s, q in cs]
            s, q = max(pool, key=lambda v: v[0])
            if s < 0.15 and how is None:   # corners.MIN_SCORE
                table[rule][0] += 1
                base = None
                continue
            e = err(q, truth, side)
            table[rule][1 if e <= GOOD else 2] += 1
            if how is None:
                base = e
            elif base is None or (e <= GOOD) != (base <= GOOD):
                changed[rule].append(f"{name.replace('collected-', 'c-').replace('commons-', '')} "
                                     f"{'-' if base is None else f'{100 * base:.1f}'}→{100 * e:.1f}")
    for rule, _ in rules:
        nf, good, bad = table[rule]
        print(f"{rule:10s} within {good:2d}  further {bad:2d}  not found {nf:2d}   " + ", ".join(changed[rule]))


if __name__ == "__main__":
    main()
