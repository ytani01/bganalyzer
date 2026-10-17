"""TODO-104: for the samples that got worse, the truth's score and the chosen quad, at slopes 0.3 and 0.5."""
import json, os, sys
sys.path.insert(0, "recognizer")
import cv2, numpy as np, corners
for n in sys.argv[1:]:
    t = json.load(open(f"samples/{n}.truth.json")); img = cv2.imread(os.path.join("samples", t["image"]))
    small, sc = corners.shrink(img); T = np.float64(t["corners_TL_TR_BR_BL"]) * np.float64(sc)
    v, _ = corners._view(small, T, corners.RW, corners.RH, 0)
    print(n, "small", small.shape[:2], "truth", T.round().tolist(), "truth score %.3f" % corners._structure(v))
    for m in (60, 100):
        corners.SLOPES = np.arange(-m, m + 1, 2); corners.DEBUG = []
        g = corners.guess(small)
        top = sorted(corners.DEBUG, key=lambda d: -d[0])[:3]
        print(f"  slopes {m/200}: found", None if g is None else g.round().tolist())
        for s, q, s0 in top: print("    cand %.3f (first %.3f)" % (s, s0), q.round().tolist())
