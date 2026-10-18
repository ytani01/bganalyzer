"""Compare two ways of using the YOLO crop (TODO-136), on all samples, as check_corners.py measures.

whole: the search in the whole photo (no YOLO); yolo: the search in locate()'s crop.
A: the better scoring of the two (side._score). B: whole, unless it scores below side.WEAK
(or finds nothing): then the better scoring of the two.

usage: uv run python archives/agents/TODO-136/compare_ways.py > out.txt
"""
import glob
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, "recognizer")
import check_corners  # noqa: E402
import corners as C  # noqa: E402
import side  # noqa: E402

locate = C.locate


def err(q, truth, img):
    return None if q is None else float(np.linalg.norm(np.subtract(q, truth), axis=1).max() / max(img.shape[:2]))


def show(e):
    return "-" if e is None else f"{100 * e:.1f}%"


counts = {k: [0, 0, 0] for k in ("whole", "yolo", "A", "B")}
for f in sorted(glob.glob("samples/*.truth.json")):
    t = json.load(open(f))
    if t.get("side"):   # the search from beside does not use YOLO
        continue
    img = cv2.imread(os.path.join("samples", t["image"]))
    C.locate = lambda img: None
    whole = C.find_corners(img)
    C.locate = locate
    box = locate(img)
    yolo = box and C.find_corners(img, crop=box)
    sw, sy = side._score(img, whole), side._score(img, yolo)
    a = whole if sw >= sy else yolo
    b = whole if sw >= side.WEAK else a
    row = {"whole": whole, "yolo": yolo, "A": a, "B": b}
    out = []
    for k, q in row.items():
        e = err(q, t["corners_TL_TR_BR_BL"], img)
        counts[k][0 if e is None else 1 if e <= check_corners.GOOD else 2] += 1
        out.append(f"{k}={show(e):>6s}")
    print(f"{os.path.basename(f)[:-11]:28s} " + " ".join(out) + f"  score whole={sw:.3f} yolo={sy:.3f}", flush=True)
for k, (none, good, far) in counts.items():
    print(f"{k:5s} within {100 * check_corners.GOOD:.1f}%: {good}, further: {far}, not found: {none}")
