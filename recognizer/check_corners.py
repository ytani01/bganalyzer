"""Measure the corner guess (corners.py) against the corners read by eye in samples/*.truth.json.

For each sample: the largest distance between a guessed corner and the
corner read by eye, as a share of the photo's long side ("-" when no board
was found), and the time taken.

usage: uv run python recognizer/check_corners.py [--app] [--crop] [--fix N] [samples/x.truth.json ...]
  --app  shrink large photos the way the PWA does before sending them
  --crop look only in the corners' bounding box and a margin of 15 % of its sides (the user's trimming)
  --fix N  the first N corners (TL, TR, BR, BL) are the true ones, put in place by the user
"""
import glob
import json
import os
import sys
import time

import cv2
import numpy as np

import corners
from evaluate import shrink_like_app

GOOD = 0.036   # within this, the reading from the guessed corners is usually as good as from the eye's


def measure(path, app=False, crop=False, fix=0):
    """(error or None, seconds) for one *.truth.json."""
    t = json.load(open(path))
    img = cv2.imread(os.path.join(os.path.dirname(path), t["image"]))
    truth = t["corners_TL_TR_BR_BL"]
    if app:
        img, truth = shrink_like_app(img, truth)
    t0 = time.perf_counter()
    crop_box = None
    if crop:
        (x0, y0), (x1, y1) = np.min(truth, 0), np.max(truth, 0)
        mx, my = 0.15 * (x1 - x0), 0.15 * (y1 - y0)
        crop_box = (x0 - mx, y0 - my, x1 + mx, y1 + my)
    fixed = [list(p) if i < fix else None for i, p in enumerate(truth)]
    found = corners.find_corners(img, fixed=fixed, crop=crop_box)
    dt = time.perf_counter() - t0
    if found is None:
        return None, dt
    return float(np.linalg.norm(np.subtract(found, truth), axis=1).max() / max(img.shape[:2])), dt


if __name__ == "__main__":
    args = sys.argv[1:]
    app, crop = "--app" in args, "--crop" in args
    fix = int(args[args.index("--fix") + 1]) if "--fix" in args else 0
    files = [a for a in args if a.endswith(".json")] or sorted(
        glob.glob(os.path.join(os.path.dirname(__file__), "..", "samples", "*.truth.json")))
    counts = [0, 0, 0]
    for f in files:
        err, dt = measure(f, app, crop, fix)
        counts[0 if err is None else 1 if err <= GOOD else 2] += 1
        shown = "-" if err is None else f"{100 * err:.1f}%"
        print(f"{os.path.basename(f).replace('.truth.json', ''):28s} {shown:>6s} {dt:5.2f}s", flush=True)
    print(f"within {100 * GOOD:.1f}%: {counts[1]}, further: {counts[2]}, not found: {counts[0]}")
