"""TODO-061: read each sample from the corners corners.find_corners guesses, against the truth.

usage: uv run python archives/agents/TODO-061/measure_corners.py NAME [-j N] [--out x.json] [sample ...]
  sample: a name like collected-tad9pt (default: every samples/*.truth.json but synth-cube-*)
  CORNERS_DIR=dir: measure dir/corners.py instead (e.g. `git show main:recognizer/corners.py > dir/corners.py`)
Prints per sample: correct points / 24, find_corners seconds; then the total.
Progress (one line per sample) goes to PROGRESS for `tail -f`.
"""
import argparse, glob, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REC = os.path.join(ROOT, "recognizer")
SAMPLES = os.path.join(ROOT, "samples")
PROGRESS = "/tmp/claude-649/-home-ytani-work-bganalyzer/TODO-061-progress.txt"


def measure(path):
    sys.path.insert(0, REC)
    if os.environ.get("CORNERS_DIR"):   # a directory with another corners.py to measure (e.g. main's)
        sys.path.insert(0, os.environ["CORNERS_DIR"])
    import cv2
    import board, corners
    cv2.setRNGSeed(0)
    t = json.load(open(path))
    img = cv2.imread(os.path.join(SAMPLES, t["image"]))
    t0 = time.perf_counter()
    found = corners.find_corners(img)
    dt = time.perf_counter() - t0
    if found is None:
        return 0, dt, None
    pos0, _ = board.recognize(img, found, home=t["home"])
    flip = [-n for n in pos0.points]   # which colour is the bottom player's: the one matching the truth (as evaluate.py)
    ok = max(sum(a == b for a, b in zip(t["points"], p)) for p in (pos0.points, flip))
    return ok, dt, found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("samples", nargs="*")
    ap.add_argument("-j", type=int, default=None)
    ap.add_argument("--out")
    a = ap.parse_args()
    files = ([os.path.join(SAMPLES, s + ".truth.json") for s in a.samples] or
             [f for f in sorted(glob.glob(os.path.join(SAMPLES, "*.truth.json"))) if "synth-cube-" not in f])
    os.makedirs(os.path.dirname(PROGRESS), exist_ok=True)
    with open(PROGRESS, "w") as p:
        p.write(f"{a.name}: {len(files)} samples\n")
    res = {}
    with ProcessPoolExecutor(a.j) as ex:
        futs = {ex.submit(measure, f): os.path.basename(f).removesuffix(".truth.json") for f in files}
        for i, fu in enumerate(as_completed(futs), 1):
            name = futs[fu]
            ok, dt, found = fu.result()
            res[name] = {"points": ok, "seconds": round(dt, 2), "corners": found}
            n = 14 * i // len(files)
            with open(PROGRESS, "a") as p:
                p.write(f"[{i:3d}/{len(files)}] {'█' * n}{'░' * (14 - n)} {100 * i // len(files):3d}%  {name}  {ok}/24\n")
                p.flush()
    for name in sorted(res):
        print(f"{name:28s} {res[name]['points']:2d}/24 {res[name]['seconds']:5.2f}s")
    tot = sum(r["points"] for r in res.values())
    print(f"{a.name}: {tot}/{24 * len(res)}  time sum {sum(r['seconds'] for r in res.values()):.1f}s")
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
