"""Guess the corners with the trained model (TODO-135).

usage: <venv with ultralytics>/bin/python predict.py <best.pt> <out.json> samples/x.truth.json ...
Writes {sample: {"corners": [[x, y] x 4] or null, "conf": c, "seconds": s}}.
"""
import json
import os
import sys
import time

import cv2
from ultralytics import YOLO

model = YOLO(sys.argv[1])
out = {}
for f in sys.argv[3:]:
    t = json.load(open(f))
    img = cv2.imread(os.path.join(os.path.dirname(f), t["image"]))
    model.predict(img, imgsz=640, device="cpu", verbose=False)   # warm-up, so the time below is one guess
    t0 = time.perf_counter()
    r = model.predict(img, imgsz=640, device="cpu", verbose=False)[0]
    dt = time.perf_counter() - t0
    name = os.path.basename(f).replace(".truth.json", "")
    if len(r.boxes):
        i = int(r.boxes.conf.argmax())
        out[name] = {"corners": r.keypoints.xy[i].tolist(), "conf": float(r.boxes.conf[i]), "seconds": dt}
    else:
        out[name] = {"corners": None, "conf": 0.0, "seconds": dt}
json.dump(out, open(sys.argv[2], "w"), indent=1)
