"""TODO-078: draw each stage of find_corners on photo5 and on the photo before painting (rotated).
usage: uv run python archives/agents/TODO-078/stages.py <original.jpg> <outdir>"""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, "recognizer")
import corners

root = Path(__file__).resolve().parents[3]
p5 = cv2.imread(str(root / "samples/photo5.jpg"))
orig = cv2.imread(sys.argv[1])
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
# turn the original the way photo5 is turned (pick the rotation that matches photo5 best)
small5 = cv2.resize(p5, (462, 347)).astype(np.int32)
rot = min((cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE),
          key=lambda r: np.abs(cv2.resize(cv2.rotate(orig, r), (462, 347)).astype(np.int32) - small5).sum())
orig = cv2.rotate(orig, rot)
truth = json.load(open(root / "samples/photo5.truth.json"))["corners_TL_TR_BR_BL"]
for name, img in (("photo5", p5), ("orig", orig)):
    got = []
    corners.DEBUG = dbg = []
    res = corners.find_corners(img, lambda st, d: got.append((st, d)))
    print(name, "corners", res, "truth", truth)
    dbg.sort(key=lambda r: -r[0])
    print(" best scored:", [(round(s, 3), round(s0, 3)) for s, q, s0 in dbg[:5]])
    for st, d in got:
        v = img.copy()
        cv2.polylines(v, [np.int32(truth)], True, (0, 255, 0), 8)
        for key, arr in d.items():
            arr = np.array(arr)
            if key == "corners":
                cv2.polylines(v, [np.int32(arr)], True, (0, 0, 255), 10)
            else:
                for i, a in enumerate(arr):
                    cv2.polylines(v, [np.int32(a)], key == "quads", (0, 0, 255) if i == 0 else (255, 0, 255), 10 if i == 0 else 4)
        cv2.imwrite(str(out / f"{name}-{st}.jpg"), cv2.resize(v, None, fx=0.25, fy=0.25))
        print(" ", st, {k: len(a) for k, a in d.items()})
