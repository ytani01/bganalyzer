"""TODO-072: the checkers' radius found on the rewarped board without starting from lay.pw.

The same conditions as measure.py (CONDS). After board.recognize, on its rewarped board (taken where
add_hidden_stacks is called), circles are looked for at radii from 0.6 to 1.6 times pw / 2 as
TODO-068's measure_scale.py raw does (radial symmetry peaks, a clear rim, and a neighbour about a
diameter away); the radius with the most such circles wins. Prints its share of pw / 2 ("scan"), the
count, and how many points were read wrong.

usage: uv run python archives/agents/TODO-072/scan.py [-j N] [-c cond,...] [names...] > scan.jsonl
"""
import argparse, glob, json, os, sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from measure import CONDS, ROOT, move  # noqa: E402

SUPPORT = 0.5
PAIR = (1.6, 2.4)


def scan(ground, lay, m):
    import cv2, numpy as np, radial, checkers
    radial.RADII = (1.0,)
    gray = cv2.cvtColor(ground, cv2.COLOR_BGR2GRAY)
    lab8 = cv2.cvtColor(ground, cv2.COLOR_BGR2Lab)
    chans = [cv2.GaussianBlur(checkers._stretch(ch), (0, 0), 1) for ch in (gray, lab8[:, :, 1], lab8[:, :, 2])]
    _, gx, gy = checkers.lab_gradients(ground)
    half = lay.pw / 2
    rows = []
    for k in np.arange(0.6, 1.62, 0.05):
        r = half * k
        peaks = [p for ch in chans for p in radial._peaks(ch, r)]
        kept = []
        for x, y, _ in peaks:
            # inside the playing area only (the frame's ornaments are not checkers)
            if not (m <= x <= m + lay.w and m <= y <= m + lay.h):
                continue
            if all((x - u) ** 2 + (y - v) ** 2 > (0.5 * r) ** 2 for u, v in kept) and \
                    checkers.edge_support(gx, gy, x, y, r) >= SUPPORT:
                kept.append((x, y))
        paired = sum(any(PAIR[0] * r <= ((x - u) ** 2 + (y - v) ** 2) ** 0.5 <= PAIR[1] * r for u, v in kept)
                     for x, y in kept)
        rows.append((round(float(k), 2), paired))
    return rows


def one(args):
    path, name, conds = args
    import cv2, numpy as np, board
    from evaluate import shrink_like_app
    from position import Position
    t = json.load(open(path))
    img = cv2.imread(os.path.join(os.path.dirname(path), t["image"]))
    img, truth_c = shrink_like_app(img, t["corners_TL_TR_BR_BL"])
    truth = Position(points=t["points"])
    got = {}
    orig = board.add_hidden_stacks

    def grab(ground, lay, m, pitch, circles):
        got.update(ground=ground, lay=lay, m=m)
        return orig(ground, lay, m, pitch, circles)

    board.add_hidden_stacks = grab
    out = []
    for cname in conds:
        pos, info = board.recognize(img, move(truth_c, CONDS[cname]), home=t["home"])
        wrong = min(sum(a != b for a, b in zip(truth.points, p)) for p in (pos.points, [-n for n in pos.points]))
        rows = scan(got["ground"], got["lay"], got["m"])
        k, n = max(rows, key=lambda v: (v[1], -v[0]))
        top = [v for v in rows if v[1] >= 0.8 * n] if n else []
        centre = sum(v[0] for v in top) / len(top) if top else None
        # how much wider the truth's playing area is than the read one, in the read board's own pixels
        lay = got["lay"]
        Hr = cv2.getPerspectiveTransform(np.float32(info["geometry"]["corners"]), np.float32(lay.src_pts()))
        tq = cv2.perspectiveTransform(np.float32([truth_c]), Hr)[0]
        true_scale = ((tq[1][0] - tq[0][0]) + (tq[2][0] - tq[3][0])) / 2 / lay.w
        out.append(dict(sample=name, cond=cname, wrong=wrong, scan=k, n=n, centre=centre and round(centre, 3), true_scale=round(float(true_scale), 3), pitch_ratio=round(info["pitch"] / got["lay"].pw, 3),
                        rows=rows))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-j", type=int, default=None)
    ap.add_argument("-c", default="ideal,in4,in8,b_in6,r_in6,out4")
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    conds = a.c.split(",")
    files = sorted(glob.glob(os.path.join(ROOT, "samples", "*.truth.json")))
    jobs = [(f, os.path.basename(f).removesuffix(".truth.json"), conds) for f in files if "synth-cube-" not in f]
    if a.names:
        jobs = [j for j in jobs if j[1] in a.names]
    with ProcessPoolExecutor(a.j) as ex:
        for rows in ex.map(one, jobs):
            for r in rows:
                print(json.dumps(r), flush=True)


if __name__ == "__main__":
    main()
