"""Compare the corners from YOLO with corners.py and the true corners (TODO-135).

"YOLO+crop" gives corners.py only the part of the photo around YOLO's corners
(their bounding box and 15 % of its sides, as check_corners.py --crop does).

For each sample: the corner error as check_corners.py measures it (largest
distance / the photo's long side) and the points read right by board.py with
those corners.

usage: uv run python archives/agents/TODO-135/compare.py <predict.json> samples/x.truth.json ...
"""
import json
import os
import sys
import tempfile
import time

import cv2
import numpy as np

sys.path.insert(0, "recognizer")
import check_corners  # noqa: E402
import corners as cmod  # noqa: E402
import evaluate  # noqa: E402

GOOD = check_corners.GOOD


def read_with(f, corners):
    """Points read right (of 24) when board.py is given these corners."""
    if corners is None:
        return None
    t = json.load(open(f))
    t["image"] = os.path.abspath(os.path.join(os.path.dirname(f), t["image"]))
    t["corners_TL_TR_BR_BL"] = [list(map(float, p)) for p in corners]
    with tempfile.NamedTemporaryFile("w", suffix=".truth.json", delete=False) as tmp:
        json.dump(t, tmp)
    try:
        return 24 - len(evaluate.run(tmp.name)[2])
    finally:
        os.unlink(tmp.name)


def error(f, corners):
    if corners is None:
        return None
    t = json.load(open(f))
    h, w = cv2.imread(os.path.join(os.path.dirname(f), t["image"])).shape[:2]
    return float(np.linalg.norm(np.subtract(corners, t["corners_TL_TR_BR_BL"]), axis=1).max() / max(h, w))


def crop_around(q):
    (x0, y0), (x1, y1) = np.min(q, 0), np.max(q, 0)
    mx, my = 0.15 * (x1 - x0), 0.15 * (y1 - y0)
    return (x0 - mx, y0 - my, x1 + mx, y1 + my)


def show(err):
    return "-" if err is None else f"{100 * err:.1f}%"


pred = json.load(open(sys.argv[1]))
print(f"{'sample':20s} {'truth':>5s} | {'corners.py':>10s} {'read':>4s} {'sec':>5s} | {'YOLO':>6s} {'read':>4s} {'sec':>5s} {'conf':>4s} | {'YOLO+crop':>9s} {'read':>4s}")
for f in sys.argv[2:]:
    name = os.path.basename(f).replace(".truth.json", "")
    truth_read = 24 - len(evaluate.run(f)[2])
    t = json.load(open(f))
    img = cv2.imread(os.path.join(os.path.dirname(f), t["image"]))
    t0 = time.perf_counter()
    found = cmod.find_corners(img)
    dt = time.perf_counter() - t0
    y = pred[name]
    both = y["corners"] and cmod.find_corners(img, crop=crop_around(y["corners"]))
    print(f"{name:20s} {truth_read:5d} | {show(error(f, found)):>10s} {str(read_with(f, found)):>4s} {dt:5.2f} | "
          f"{show(error(f, y['corners'])):>6s} {str(read_with(f, y['corners'])):>4s} {y['seconds']:5.2f} {y['conf']:.2f} | "
          f"{show(error(f, both)):>9s} {str(read_with(f, both)):>4s}")
print(f"(corner error within {100 * GOOD:.1f}% is as good as the eye's, check_corners.GOOD)")
