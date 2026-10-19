"""Time the corner search of two corners.py side by side, in one process, taking turns (TODO-172).

usage: uv run python archives/agents/TODO-172/ab_time.py OLD_corners.py ROUNDS samples/x.truth.json ...

On a busy machine one run's time says little; this alternates the two and keeps each one's
fastest time per sample (OLD_corners.py: e.g. `git show origin/main:recognizer/corners.py`,
saved next to a copy of corners_model.onnx).
"""

import importlib.util
import json
import os
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "recognizer"))

import cv2  # noqa: E402

import corners as new  # noqa: E402

spec = importlib.util.spec_from_file_location("corners_old", sys.argv[1])
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
rounds = int(sys.argv[2])
best = {}
for f in sys.argv[3:]:
    img = cv2.imread(os.path.join(os.path.dirname(f), json.load(open(f))["image"]))
    name = os.path.basename(f).replace(".truth.json", "")
    found = {}
    for _ in range(rounds):
        for label, m in (("old", old), ("new", new)):
            t0 = time.perf_counter()
            found[label] = m.find_corners(img)
            dt = time.perf_counter() - t0
            best[name, label] = min(best.get((name, label), dt), dt)
    same = found["old"] == found["new"]
    print(
        f"{name:32s} {best[name, 'old']:6.2f}s -> {best[name, 'new']:6.2f}s  same={same}"
    )
for label in ("old", "new"):
    print(label, f"{sum(v for (n, lb), v in best.items() if lb == label):.2f}s")
