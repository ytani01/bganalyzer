# per photo and way: score, corner error vs truth (same order), area against the normal quad, share inside the normal quad
import json, os, sys
sys.path.insert(0, "recognizer")
import cv2, numpy as np, corners as C, side
def err(q, t, shape):
    return max(np.hypot(*(np.float64(a) - b)) for a, b in zip(q, t)) / max(shape[:2])
def area(q):
    return abs(cv2.contourArea(np.float32(q)))
for f in sys.argv[1:]:
    t = json.load(open(f))
    tq = t.get("corners_TL_TR_BR_BL") or t["corners"]
    img = cv2.imread(os.path.join(os.path.dirname(f), t["image"]))
    qs = {"n": C.find_corners(img), "r": side.find_corners_side(img, "right"), "l": side.find_corners_side(img, "left")}
    out = []
    for k, q in qs.items():
        if q is None:
            out.append(f"{k}: -"); continue
        s = side._score(img, q)
        e = err(q, tq, img.shape)
        if k != "n" and qs["n"] is not None:
            a = area(q) / area(qs["n"])
            m = np.zeros(img.shape[:2], np.uint8); cv2.fillPoly(m, [np.int32(qs["n"])], 1)
            m2 = np.zeros_like(m); cv2.fillPoly(m2, [np.int32(q)], 1)
            inside = (m & m2).sum() / m2.sum()
            out.append(f"{k}: s={s:.2f} e={e:.0%} a={a:.2f} in={inside:.2f}")
        else:
            out.append(f"{k}: s={s:.2f} e={e:.0%}")
    print(f"{os.path.basename(f)[:28]:28s} " + " | ".join(out), flush=True)
