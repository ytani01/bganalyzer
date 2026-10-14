"""Measure the corner guess (corners.py) against the corners read by eye in samples/*.truth.json.

For each sample: the largest distance between a guessed corner and the
corner read by eye, as a share of the photo's long side ("-" when no board
was found), and the time taken.

usage: uv run python recognizer/check_corners.py [--app] [samples/x.truth.json ...]
  --app  shrink large photos the way the PWA does before sending them
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


def measure(path, app=False):
    """(error or None, seconds) for one *.truth.json."""
    t = json.load(open(path))
    img = cv2.imread(os.path.join(os.path.dirname(path), t["image"]))
    truth = t["corners_TL_TR_BR_BL"]
    if app:
        img, truth = shrink_like_app(img, truth)
    t0 = time.perf_counter()
    found = corners.find_corners(img)
    dt = time.perf_counter() - t0
    if found is None:
        return None, dt
    return float(np.linalg.norm(np.subtract(found, truth), axis=1).max() / max(img.shape[:2])), dt


if __name__ == "__main__":
    app = "--app" in sys.argv
    files = [a for a in sys.argv[1:] if a != "--app"] or sorted(
        glob.glob(os.path.join(os.path.dirname(__file__), "..", "samples", "*.truth.json")))
    counts = [0, 0, 0]
    for f in files:
        err, dt = measure(f, app)
        counts[0 if err is None else 1 if err <= GOOD else 2] += 1
        shown = "-" if err is None else f"{100 * err:.1f}%"
        print(f"{os.path.basename(f).replace('.truth.json', ''):28s} {shown:>6s} {dt:5.2f}s", flush=True)
    print(f"within {100 * GOOD:.1f}%: {counts[1]}, further: {counts[2]}, not found: {counts[0]}")
