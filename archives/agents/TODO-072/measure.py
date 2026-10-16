"""TODO-072: when the corners given to board.recognize are too small / too large, does the checkers' size
(info["pitch"] against lay.pw) show it, and does the reading still match the truth?

Each sample (shrunk as the PWA does) is read from its truth corners moved in the quad's own coordinates
(fractions of the playing area's width / height; + = outward):
  ideal, in4/in8 (all sides inward), out4 (all outward), b_in6/r_in6 (bottom / right side inward),
  b_out6/r_out6 (one side outward, as when the frame's outer edge is taken).
Prints one JSON line per (sample, condition) to stdout: wrong points, pitch / pw, the read area's
corner error against the truth (largest corner distance / long side of the truth quad).

usage: uv run python archives/agents/TODO-072/measure.py [-j N] [names...] > out.jsonl
"""
import argparse, glob, json, os, sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "recognizer"))

# (left, top, right, bottom) moves, + = outward
CONDS = dict(ideal=(0, 0, 0, 0), in4=(-.04,) * 4, in8=(-.08,) * 4, out4=(.04,) * 4,
             b_in6=(0, 0, 0, -.06), r_in6=(0, 0, -.06, 0), b_out6=(0, 0, 0, .06), r_out6=(0, 0, .06, 0))


def move(corners, d):
    import cv2, numpy as np
    q = np.float32(corners)
    H = cv2.getPerspectiveTransform(np.float32([(0, 0), (1, 0), (1, 1), (0, 1)]), q)
    l, t, r, b = d
    u = np.float32([[(-l, -t), (1 + r, -t), (1 + r, 1 + b), (-l, 1 + b)]])
    return cv2.perspectiveTransform(u, H)[0].tolist()


def one(args):
    path, name = args
    import cv2, numpy as np, board
    from evaluate import shrink_like_app
    from position import Position
    t = json.load(open(path))
    img = cv2.imread(os.path.join(os.path.dirname(path), t["image"]))
    img, truth_c = shrink_like_app(img, t["corners_TL_TR_BR_BL"])
    truth = Position(points=t["points"])
    tq = np.float64(truth_c)
    side = max(np.linalg.norm(tq[i] - tq[(i + 1) % 4]) for i in range(4))
    out = []
    for cname, d in CONDS.items():
        try:
            pos, info = board.recognize(img, move(truth_c, d), home=t["home"])
        except Exception as e:  # noqa: BLE001
            out.append(dict(sample=name, cond=cname, error=repr(e)))
            continue
        wrong = min(sum(a != b for a, b in zip(truth.points, p)) for p in (pos.points, [-n for n in pos.points]))
        lay = info["layout"]
        pw = lay["a"] / 6
        got = np.float64(info["geometry"]["corners"])
        err = float(np.max(np.linalg.norm(got - tq, axis=1)) / side)
        out.append(dict(sample=name, cond=cname, wrong=wrong, circles=info["circles"], pitch=round(info["pitch"], 2),
                        pw=round(pw, 2), ratio=round(info["pitch"] / pw, 3),
                        wratio=round((2 * lay["a"] + lay["bar"]) / info["pitch"], 2), err=round(err, 4)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-j", type=int, default=None)
    ap.add_argument("names", nargs="*")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(ROOT, "samples", "*.truth.json")))
    jobs = [(f, os.path.basename(f).removesuffix(".truth.json")) for f in files if "synth-cube-" not in f]
    if a.names:
        jobs = [j for j in jobs if j[1] in a.names]
    with ProcessPoolExecutor(a.j) as ex:
        for rows in ex.map(one, jobs):
            for r in rows:
                print(json.dumps(r), flush=True)


if __name__ == "__main__":
    main()
