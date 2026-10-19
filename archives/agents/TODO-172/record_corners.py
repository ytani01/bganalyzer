"""Record the guessed corners and the time for each sample (TODO-172).

usage: uv run python archives/agents/TODO-172/record_corners.py OUT.json [samples/x.truth.json ...]
       uv run python archives/agents/TODO-172/record_corners.py --compare A.json B.json

Runs as check_corners.py does with no options (whole photo, no fixed corner).
--compare prints the samples whose corners differ (bit for bit) and the times.
"""

import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "recognizer"))

import cv2  # noqa: E402

import corners  # noqa: E402


def record(out, files):
    res = {}
    for f in files:
        t = json.load(open(f))
        img = cv2.imread(os.path.join(os.path.dirname(f), t["image"]))
        t0 = time.perf_counter()
        if t.get("side"):
            import side

            found = side.find_corners_side(img, t["side"])
        else:
            found = corners.find_corners(img)
        dt = time.perf_counter() - t0
        name = os.path.basename(f).replace(".truth.json", "")
        res[name] = {"corners": found, "seconds": dt}
        print(f"{name:32s} {dt:6.2f}s", flush=True)
    json.dump(res, open(out, "w"), indent=1)
    print(f"total {sum(r['seconds'] for r in res.values()):.1f}s")


def compare(a, b):
    A, B = json.load(open(a)), json.load(open(b))
    diff = [n for n in A if A[n]["corners"] != B.get(n, {}).get("corners")]
    print(f"samples {len(A)}, differing corners: {len(diff)}")
    for n in diff:
        print(" ", n, A[n]["corners"], B.get(n, {}).get("corners"))
    ta, tb = (sum(r["seconds"] for r in X.values()) for X in (A, B))
    print(f"total {ta:.1f}s -> {tb:.1f}s")
    for n in sorted(A, key=lambda n: -A[n]["seconds"])[:10]:
        print(f"  {n:32s} {A[n]['seconds']:6.2f}s -> {B[n]['seconds']:6.2f}s")


if __name__ == "__main__":
    if sys.argv[1] == "--compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        files = sys.argv[2:] or sorted(
            glob.glob(os.path.join(ROOT, "samples", "*.truth.json"))
        )
        record(sys.argv[1], files)
