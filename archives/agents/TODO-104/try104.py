"""TODO-104: corner error with wider slopes / aspect. usage: try104.py MAXSLOPE ASPECTMAX names..."""
import json, os, sys, time
sys.path.insert(0, "recognizer")
import cv2, numpy as np, corners
m = int(float(sys.argv[1]) * 200); corners.SLOPES = np.arange(-m, m + 1, 2)
for n in sys.argv[3:]:
    t = json.load(open(f"samples/{n}.truth.json")); img = cv2.imread(os.path.join("samples", t["image"]))
    t0 = time.perf_counter(); g = corners.find_corners(img); dt = time.perf_counter() - t0
    err = "-" if g is None else "%.1f%%" % (100 * np.linalg.norm(np.subtract(g, t["corners_TL_TR_BR_BL"]), axis=1).max() / max(img.shape[:2]))
    print(f"{n:24s} {err:>6s} {dt:5.2f}s")
