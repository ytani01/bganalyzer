"""Corners found in the photo cut to the board (TODO-070): crop=None vs crop = the whole cut image.

usage: uv run python archives/agents/TODO-070/measure_cropped.py
The cut is the truth corners' bounding box with margins of MARGIN (default 0.15, as check_corners.py --crop) of its sides.
Error: the largest corner distance / the cut image's longest side."""
import glob, json, os, sys
import cv2
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../recognizer"))
import corners  # noqa: E402

counts = {"none": [0, 0, 0], "whole": [0, 0, 0]}
for path in sorted(glob.glob("samples/*.truth.json")):
    t = json.load(open(path))
    img = cv2.imread(os.path.join("samples", t["image"]))
    truth = np.float64(t["corners_TL_TR_BR_BL"])
    (x0, y0), (x1, y1) = truth.min(0), truth.max(0)
    m = float(os.environ.get("MARGIN", "0.15"))
    mx, my = m * (x1 - x0), m * (y1 - y0)
    h, w = img.shape[:2]
    a, b = int(max(x0 - mx, 0)), int(max(y0 - my, 0))
    cut = img[b:int(min(y1 + my, h)), a:int(min(x1 + mx, w))]
    tr = truth - [a, b]
    row = []
    for k, crop in (("none", None), ("whole", (0, 0, cut.shape[1], cut.shape[0]))):
        f = corners.find_corners(cut, crop=crop)
        e = None if f is None else float(np.linalg.norm(np.subtract(f, tr), axis=1).max() / max(cut.shape[:2]))
        counts[k][0 if e is None else 1 if e <= 0.036 else 2] += 1
        row.append("-" if e is None else f"{100 * e:.1f}%")
    print(f"{os.path.basename(path)[:-11]:28s} {row[0]:>6s} {row[1]:>6s}", flush=True)
for k, c in counts.items():
    print(f"{k}: within 3.6%: {c[1]}, further: {c[2]}, not found: {c[0]}")
