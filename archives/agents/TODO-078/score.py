"""TODO-078: structure score of the truth quad and of the found one, and the edge lines near the truth's.
usage: uv run python archives/agents/TODO-078/score.py <original.jpg>"""
import json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, "recognizer")
import corners as C
root = Path(__file__).resolve().parents[3]
p5 = cv2.imread(str(root / "samples/photo5.jpg"))
orig = cv2.rotate(cv2.imread(sys.argv[1]), cv2.ROTATE_90_COUNTERCLOCKWISE)
truth = np.float64(json.load(open(root / "samples/photo5.truth.json"))["corners_TL_TR_BR_BL"])
for name, img in (("photo5", p5), ("orig", orig)):
    small, s = C.shrink(img)
    t = truth * s
    found = C.find_corners(img)
    sc = lambda q: round(C._structure(C._view(small, q, C.RW, C.RH, 0)[0]), 3)
    print(name, "truth", sc(t), "found", None if found is None else sc(np.float64(found) * s))
    gx, gy = C._gradients(small)
    hl = C._h_lines(gx, gy)
    tk = [(round(200 * (t[1, 1] - t[0, 1]) / (t[1, 0] - t[0, 0])), t[0, 1] - t[0, 0] * (t[1, 1] - t[0, 1]) / (t[1, 0] - t[0, 0])),
          (round(200 * (t[2, 1] - t[3, 1]) / (t[2, 0] - t[3, 0])), t[3, 1] - t[3, 0] * (t[2, 1] - t[3, 1]) / (t[2, 0] - t[3, 0]))]
    print("  truth far/near (k, c):", [(k, round(c)) for k, c in tk])
    print("  h lines:", hl)
