"""TODO-068: does a checker's size tell the playing area's width?

ideal: read each sample from its truth corners (board.recognize) and print the width of the
playing area against the checkers' diameter (canonical: (2a + bar) / pitch).

raw: look for checkers in the photo itself at several radii; print the radius with the most\ncircles with a clear rim against the true one (truth width / RATIO / 2)\n\nusage: uv run python archives/agents/TODO-068/measure_scale.py ideal|raw [-j N] [sample ...]
"""
import argparse, glob, json, os, sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REC = os.path.join(ROOT, "recognizer")
SAMPLES = os.path.join(ROOT, "samples")
sys.path.insert(0, REC)


def ideal(path):
    import cv2, board
    t = json.load(open(path))
    img = cv2.imread(os.path.join(SAMPLES, t["image"]))
    _, info = board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"])
    lay = info["layout"]
    return info["circles"], (2 * lay["a"] + lay["bar"]) / info["pitch"], lay["bar"] / (lay["a"] / 6)


RATIO = 13.7   # median of `ideal`
SUPPORT = float(os.environ.get("SUPPORT", 0.5))
PAIR = (1.6, 2.4)


def raw(path):
    """Find checkers in the photo itself (shrunk as corners.py does) at several radii.
    Returns (true radius at the board's middle row, [(r, peaks, supported)])."""
    import cv2, numpy as np, corners, radial, checkers
    radial.RADII = (1.0,)
    t = json.load(open(path))
    img = cv2.imread(os.path.join(SAMPLES, t["image"]))
    small, s = corners.shrink(img)
    q = np.float64(t["corners_TL_TR_BR_BL"]) * s
    true_r = (np.linalg.norm(q[1] - q[0]) + np.linalg.norm(q[2] - q[3])) / 2 / RATIO / 2
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    lab8 = cv2.cvtColor(small, cv2.COLOR_BGR2Lab)
    chans = [cv2.GaussianBlur(checkers._stretch(ch), (0, 0), 1) for ch in (gray, lab8[:, :, 1], lab8[:, :, 2])]
    _, gx, gy = checkers.lab_gradients(small)
    out = []
    r = 5.0
    while r < 40:
        peaks = [p for ch in chans for p in radial._peaks(ch, r)]
        kept = []   # rims clear enough, one per spot (the channels find the same circles)
        for x, y, _ in peaks:
            if all((x - u) ** 2 + (y - v) ** 2 > (0.5 * r) ** 2 for u, v in kept) and \
                    checkers.edge_support(gx, gy, x, y, r) >= SUPPORT:
                kept.append((x, y))
        # a checker stands next to another: a neighbour about a diameter away
        paired = sum(any(PAIR[0] * r <= ((x - u) ** 2 + (y - v) ** 2) ** 0.5 <= PAIR[1] * r for u, v in kept)
                     for x, y in kept)
        out.append((round(r, 1), len(kept), paired))
        r *= 1.12
    return true_r, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["ideal", "raw"])
    ap.add_argument("samples", nargs="*")
    ap.add_argument("-j", type=int, default=None)
    a = ap.parse_args()
    files = ([os.path.join(SAMPLES, s + ".truth.json") for s in a.samples] or
             [f for f in sorted(glob.glob(os.path.join(SAMPLES, "*.truth.json"))) if "synth-cube-" not in f])
    with ProcessPoolExecutor(a.j) as ex:
        for f, r in zip(files, ex.map(globals()[a.mode], files)):
            name = os.path.basename(f).removesuffix('.truth.json')
            if a.mode == "raw":
                true_r, rows = r
                best = max(rows, key=lambda v: v[2])
                print(f"{name:28s} true r {true_r:5.1f}  best r {best[0]:5.1f} ({best[0] / true_r:4.2f})  " +
                      " ".join(f"{rr}:{n}" for rr, _, n in rows), flush=True)
                continue
            n, ratio, bar = r
            print(f"{os.path.basename(f).removesuffix('.truth.json'):28s} circles {n:3d}  width/diameter {ratio:5.2f}  bar/point {bar:4.2f}", flush=True)


if __name__ == "__main__":
    main()
