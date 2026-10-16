"""TODO-071 (second round): the checkers seen through each candidate quad, from straight above.

Through the right quad the checkers are round and as big as the board says: the playing area's width is
about 13.7 checkers' spacing across, its height a fixed number of spacings up and down. For each
candidate (candidates.json, from simulate.py) and the true corners, the quad is seen from straight above
(VW x VH, as corners.py's views), checkers are looked for at radii round the expected one, and the
spacing of the centres measured: up and down between checkers of a stack (triples in a column), across
between checkers on neighbouring points (triples in a row).

Then candidates are scored again with how far those are from their median over the true corners
(size), or with how round the stacked checkers look (round: a checker's width across against the spacing
up and down, which needs no size known in advance).

usage: uv run python archives/agents/TODO-071/measure_views.py [-j N]   (writes views.json, prints the table)
"""
import argparse, glob, json, math, os, sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SAMPLES = os.path.join(ROOT, "samples")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "recognizer"))
VW, VH = 416, 320
R0 = VW / 13.7 / 2
SUPPORT = 0.35
GOOD = 0.036


def spacings(pts, r):
    """Median spacing up and down and across of evenly spaced triples (centres 1.6r-2.6r apart), with counts."""
    import numpy as np
    if len(pts) < 3:
        return None, 0, None, 0, []
    p = np.float64(pts)
    stacks = []
    out = {}
    for axis in (1, 0):   # 1: up and down (a stack), 0: across (neighbouring points)
        other = 1 - axis
        found = []
        for b in range(len(p)):
            d = p - p[b]
            nb = np.nonzero((np.abs(d[:, axis]) >= 1.6 * r) & (np.abs(d[:, axis]) <= 2.6 * r) &
                            (np.abs(d[:, other]) <= 0.35 * r))[0]
            for a in nb:
                want = 2 * p[b] - p[a]
                c = np.nonzero(np.linalg.norm(p[nb] - want, axis=1) < 0.25 * r)[0]
                if len(c):
                    found.append(abs(p[a][axis] - p[nb[c[0]]][axis]) / 2)
                    if axis == 1:
                        stacks.append((p[b][0], p[b][1], found[-1]))
                    break
        out[axis] = (float(np.median(found)) if found else None, len(found))
    return out[1][0], out[1][1], out[0][0], out[0][1], stacks


def roundness(gx, stacks):
    """Median of a stacked checker's width across (its strongest edges left and right, along its row)
    against its spacing up and down: 1 when the checkers look round (the quad is right)."""
    import numpy as np
    out = []
    for x, y, s in stacks:
        y, h = int(round(y)), s / 2
        prof = np.abs(gx[max(0, y - 2):y + 3]).sum(0)
        lo, hi = int(round(x - 1.4 * h)), int(round(x - 0.6 * h))
        lo2, hi2 = int(round(x + 0.6 * h)), int(round(x + 1.4 * h))
        if lo < 0 or hi2 >= len(prof):
            continue
        left = lo + int(np.argmax(prof[lo:hi + 1]))
        right = lo2 + int(np.argmax(prof[lo2:hi2 + 1]))
        out.append((right - left) / s)
    return float(np.median(out)) if out else None


def look(small, q):
    """[(r, n kept, up-down spacing, n, across spacing, n, roundness)] for the quad seen from straight above."""
    import cv2, numpy as np, exact, radial, checkers
    H = exact.homography(np.float64(q), np.float64([(0, 0), (VW, 0), (VW, VH), (0, VH)]))
    if H is None:
        return []
    view = exact.warp(small, H, (VW, VH))
    gray = cv2.cvtColor(view, cv2.COLOR_BGR2GRAY)
    lab8 = cv2.cvtColor(view, cv2.COLOR_BGR2Lab)
    chans = [cv2.GaussianBlur(checkers._stretch(ch), (0, 0), 1) for ch in (gray, lab8[:, :, 1], lab8[:, :, 2])]
    _, gx, gy = checkers.lab_gradients(view)
    rows = []
    for k in range(-5, 6):
        r = R0 * 1.1 ** k
        kept = []
        for ch in chans:
            for x, y, _ in radial._peaks(ch, r):
                if all((x - u) ** 2 + (y - v) ** 2 > (0.5 * r) ** 2 for u, v in kept) and \
                        checkers.edge_support(gx, gy, x, y, r) >= SUPPORT:
                    kept.append((x, y))
        *sp, stacks = spacings(kept, r)
        rows.append((r, len(kept), *sp, roundness(gx, stacks)))
    return rows


def one(name):
    import cv2, numpy as np, corners, radial
    from evaluate import shrink_like_app
    radial.RADII = (1.0,)
    truth, side, cs = json.load(open(os.path.join(HERE, "candidates.json")))[name]
    t = json.load(open(os.path.join(SAMPLES, name + ".truth.json")))
    img, _ = shrink_like_app(cv2.imread(os.path.join(SAMPLES, t["image"])), t["corners_TL_TR_BR_BL"])
    small, _ = corners.shrink(img)
    return dict(truth=look(small, truth), cands=[(s, q, look(small, q)) for s, q in cs])


def metrics(rows):
    """(width in spacings across, height in spacings up and down, stacks found) at the radius whose
    triples are the most (both ways); None when too few."""
    rows = [r for r in rows if r[3] + r[5] >= 3]
    if not rows:
        return None
    best = max(rows, key=lambda v: v[3] + v[5])
    up, across = best[2], best[4]
    return (VW / (2 * across) if across else None, VH / (2 * up) if up else None, best[3] + best[5], best[6])


def main():
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("-j", type=int, default=None)
    a = ap.parse_args()
    cache = os.path.join(HERE, "views.json")
    if os.path.exists(cache):
        views = json.load(open(cache))
    else:
        names = sorted(json.load(open(os.path.join(HERE, "candidates.json"))))
        with ProcessPoolExecutor(a.j) as ex:
            views = dict(zip(names, ex.map(one, names)))
        json.dump(views, open(cache, "w"))
    cand = json.load(open(os.path.join(HERE, "candidates.json")))

    tm = {n: metrics(v["truth"]) for n, v in views.items()}
    ws = [m[0] for m in tm.values() if m and m[0]]
    hs = [m[1] for m in tm.values() if m and m[1]]
    W0, H0 = float(np.median(ws)), float(np.median(hs))
    print(f"through the true corners: width {W0:.2f} spacings across (from {len(ws)}; "
          f"{min(ws):.1f}-{max(ws):.1f}), height {H0:.2f} up and down ({len(hs)}; {min(hs):.1f}-{max(hs):.1f})")
    for n, m in tm.items():
        print(f"  {n:28s} " + ("-" if m is None else f"width {m[0] and round(m[0], 2)}  height {m[1] and round(m[1], 2)}  triples {m[2]}"))

    def err(q, truth, side):
        return float(np.linalg.norm(np.float64(q) - np.float64(truth), axis=1).max() / side)

    rs = [m[3] for m in tm.values() if m and m[3]]
    R1 = float(np.median(rs))
    print(f"roundness through the true corners: median {R1:.3f} ({len(rs)}; " +
          " ".join(f"{x:.2f}" for x in sorted(rs)) + ")")

    def off(m):
        if m is None:
            return 0.0
        if ROUND:
            return abs(math.log(m[3] / R1)) if m[3] else 0.0
        return sum(abs(math.log(v / v0)) for v, v0 in ((m[0], W0), (m[1], H0)) if v)

    for ROUND, w in [(False, w) for w in (0, 0.1, 0.2, 0.4, 0.8)] + [(True, w) for w in (0.1, 0.2, 0.4, 0.8, 1.6)]:
        good = bad = nf = 0
        changed = []
        for n, v in views.items():
            truth, side, _ = cand[n]
            if not v["cands"]:
                nf += 1
                continue
            base = max(v["cands"], key=lambda c: c[0])
            s, q, _ = max(v["cands"], key=lambda c: c[0] - w * off(metrics(c[2])))
            if base[0] < 0.15:
                nf += 1
                continue
            e, e0 = err(q, truth, side), err(base[1], truth, side)
            good += e <= GOOD
            bad += e > GOOD
            if (e <= GOOD) != (e0 <= GOOD):
                changed.append(f"{n.replace('collected-', 'c-').replace('commons-', '')} {100 * e0:.1f}→{100 * e:.1f}")
        print(f"{'round' if ROUND else 'size '} add {w:<4}  within {good:2d}  further {bad:2d}  not found {nf:2d}   " + ", ".join(changed))


if __name__ == "__main__":
    main()
