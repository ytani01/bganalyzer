# side._part of each way from beside against the normal search's corners
import json, os, sys
sys.path.insert(0, "recognizer")
import cv2, corners as C, side
for f in sys.argv[1:]:
    t = json.load(open(f)); img = cv2.imread(os.path.join(os.path.dirname(f), t["image"]))
    n = C.find_corners(img)
    print(f"{os.path.basename(f)[:28]:28s}", " ".join(f"{s} {side._part(n, side.find_corners_side(img, s)):.2f}" for s in ("right", "left")), flush=True)
