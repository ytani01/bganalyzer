"""TODO-104: for oblique samples, the truth quad's edge slopes, aspect and score vs the guess."""
import json, os, sys
sys.path.insert(0, "recognizer")
import cv2, numpy as np, corners
for n in sys.argv[1:]:
    t = json.load(open(f"samples/{n}.truth.json")); img = cv2.imread(os.path.join("samples", t["image"]))
    small, sc = corners.shrink(img)
    T = np.float64(t["corners_TL_TR_BR_BL"]) * np.float64(sc)
    sl = lambda a, b, horiz: (T[b][1]-T[a][1])/(T[b][0]-T[a][0]) if horiz else (T[b][0]-T[a][0])/(T[b][1]-T[a][1])
    slopes = dict(top=sl(0,1,1), bottom=sl(3,2,1), left=sl(0,3,0), right=sl(1,2,0))
    wid = (np.linalg.norm(T[1]-T[0]) + np.linalg.norm(T[2]-T[3])) / 2; hgt = (np.linalg.norm(T[3]-T[0]) + np.linalg.norm(T[2]-T[1])) / 2
    v, _ = corners._view(small, T, corners.RW, corners.RH, 0)
    corners.DEBUG = []
    g = corners.guess(small)
    best = max((d[0] for d in corners.DEBUG), default=None)
    print(n, "slopes", {k: round(float(v_), 2) for k, v_ in slopes.items()}, "aspect %.2f" % (wid / hgt),
          "truth score %.3f" % corners._structure(v), "best found", best and round(float(best), 3), "found" if g is not None else "none")
