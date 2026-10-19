"""Record everything the reading returns, with the corners fixed to the truth's, and its time (TODO-173).

usage: uv run python archives/agents/TODO-173/record_reading.py OUT.json [samples/x.truth.json ...]
       uv run python archives/agents/TODO-173/record_reading.py --compare A.json B.json

Calls board.recognize as evaluate.py does (truth's corners, home and side; bottom_colour 0) and keeps
pos.to_dict() and the whole info (geometry, dice, cube, ...). --compare prints the samples whose
output differs (exactly, as JSON) and the times.
"""

import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..")
# ab_time.py points RECOGNIZER at another version
sys.path.insert(0, os.environ.get("RECOGNIZER") or os.path.join(ROOT, "recognizer"))

import cv2  # noqa: E402

import board  # noqa: E402


def read(f):
    t = json.load(open(f))
    img = cv2.imread(os.path.join(os.path.dirname(f), t["image"]))
    t0 = time.perf_counter()
    pos, info = board.recognize(
        img, t["corners_TL_TR_BR_BL"], home=t["home"], side=t.get("side")
    )
    dt = time.perf_counter() - t0
    # through JSON as the API does, so numpy values compare as plain numbers
    out = json.loads(json.dumps({**pos.to_dict(), "info": info}, default=repr))
    return out, dt


def record(out, files):
    res = {}
    for f in files:
        name = os.path.basename(f).replace(".truth.json", "")
        if not os.path.exists(
            os.path.join(os.path.dirname(f), json.load(open(f))["image"])
        ):
            print(f"{name:32s} (no image, skipped)")
            continue
        r, dt = read(f)
        res[name] = {"reading": r, "seconds": dt}
        print(f"{name:32s} {dt:6.2f}s", flush=True)
    json.dump(res, open(out, "w"), indent=1)
    print(f"total {sum(r['seconds'] for r in res.values()):.1f}s")


def compare(a, b):
    A, B = json.load(open(a)), json.load(open(b))
    diff = [n for n in A if A[n]["reading"] != B.get(n, {}).get("reading")]
    print(f"samples {len(A)} / {len(B)}, differing readings: {len(diff)}")
    for n in diff:
        print(" ", n)
    common = [n for n in A if n in B]
    ta, tb = (sum(X[n]["seconds"] for n in common) for X in (A, B))
    print(f"total {ta:.1f}s -> {tb:.1f}s")
    for n in sorted(common, key=lambda n: -A[n]["seconds"])[:10]:
        print(f"  {n:32s} {A[n]['seconds']:6.2f}s -> {B[n]['seconds']:6.2f}s")


if __name__ == "__main__":
    if sys.argv[1] == "--compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        files = sys.argv[2:] or sorted(
            glob.glob(os.path.join(ROOT, "samples", "*.truth.json"))
        )
        record(sys.argv[1], files)
