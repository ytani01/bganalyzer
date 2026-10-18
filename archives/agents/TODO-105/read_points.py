# points read right from the eye's corners, today's guess and the new one
import json, os, sys
import cv2, numpy as np
sys.path.insert(0, "recognizer")
import corners as C, board
swap = C._swap
def right(t, img, corners):
    if corners is None:
        return "-"
    pos, _ = board.recognize(img, [list(map(float, p)) for p in corners], home=t["home"], side=t.get("side"))
    return max(sum(a == b for a, b in zip(t["points"], pts)) for pts in (pos.points, [-n for n in pos.points]))
for name in sys.argv[1:]:
    t = json.load(open(f"samples/{name}.truth.json"))
    img = cv2.imread(os.path.join("samples", t["image"]))
    C.W_ALONG, C._swap = 0.0, (lambda small, gx, gy, best, *a: best[1]); q0 = C.find_corners(img)
    C.W_ALONG, C._swap = 0.4, swap; q1 = C.find_corners(img)
    print(f"{name:24s} 目視 {right(t, img, t['corners_TL_TR_BR_BL'])}  今 {right(t, img, q0)}  新 {right(t, img, q1)}")
