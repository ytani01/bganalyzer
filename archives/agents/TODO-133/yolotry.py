"""Corners with the gradients zeroed where YOLOv8n-seg finds people and things (TODO-133 trial).

usage (from the repo top): <yolo venv python> yolotry.py OUT_DIR id...
Prints, per photo: the error now, the error with the things removed, and what was removed.
Writes OUT_DIR/<id>.png: removed area in blue, truth green, before red, after yellow.
"""
import glob
import json
import os
import sys

import cv2
import numpy as np
from ultralytics import YOLO

sys.path.insert(0, "recognizer")
import corners  # noqa: E402

KEEP = {"dining table"}          # the table under the board is not in the way
BIG = 0.15                       # a thing larger than this share of the photo may be the board itself
GROW = 0.01                      # widen each mask by this share of the long side (its outline is an edge too)

here = os.path.dirname(os.path.abspath(__file__))
model = YOLO(os.path.join(here, "yolov8n-seg.pt"))
orig = corners._gradients


def err(found, truth, img):
    return None if found is None else float(np.linalg.norm(np.subtract(found, truth), axis=1).max() / max(img.shape[:2]))


def fmt(e):
    return "-" if e is None else f"{e:.1%}"


out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for n in sys.argv[2:]:
    t = json.load(open(glob.glob(f"collected/*-{n}.truth.json")[0]))
    img = cv2.imread("collected/" + t["image"])
    truth = t["corners_TL_TR_BR_BL"]
    H, W = img.shape[:2]
    r = model(img, verbose=False, retina_masks=True)[0]
    mask = np.zeros((H, W), np.uint8)
    removed, kept = [], []
    if r.masks is not None:
        for cls, m in zip(r.boxes.cls.tolist(), r.masks.data.cpu().numpy()):
            name = model.names[int(cls)]
            share = float(m.mean())
            if name in KEEP or share > BIG:
                kept.append(f"{name}({share:.0%})")
                continue
            removed.append(name)
            mask |= (m > 0.5).astype(np.uint8)
    g = max(1, int(GROW * max(H, W)))
    mask = cv2.dilate(mask, np.ones((2 * g + 1, 2 * g + 1), np.uint8))
    before = corners.find_corners(img)
    small, _ = corners.shrink(img)
    small_mask = cv2.resize(mask, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)

    def masked(bgr, sigma=1.0):
        gx, gy = orig(bgr, sigma)
        if bgr.shape[:2] == small_mask.shape:   # only the search over the whole photo
            gx[small_mask] = 0
            gy[small_mask] = 0
        return gx, gy

    corners._gradients = masked
    after = corners.find_corners(img)
    corners._gradients = orig
    print(f"{n}  now {fmt(err(before, truth, img))}  removed {fmt(err(after, truth, img))}"
          f"  removed: {', '.join(removed) or '-'}  kept: {', '.join(kept) or '-'}", flush=True)

    s = 600 / max(H, W)
    view = cv2.resize(img, None, fx=s, fy=s)
    m = cv2.resize(mask, (view.shape[1], view.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
    view[m] = (0.5 * view[m] + 0.5 * np.array([255, 128, 0])).astype(np.uint8)
    for q, c in ((truth, (0, 255, 0)), (before, (0, 0, 255)), (after, (0, 255, 255))):
        if q is not None:
            cv2.polylines(view, [np.int32(np.array(q) * s)], True, c, 2)
    cv2.putText(view, n, (5, view.shape[0] - 8), 0, 0.7, (255, 0, 255), 2)
    cv2.imwrite(os.path.join(out, n + ".png"), view)
