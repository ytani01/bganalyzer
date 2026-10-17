"""Corners with the gradients zeroed inside hand-drawn boxes (fractions of the photo): does it change?"""
import json, sys, glob, cv2, numpy as np
sys.path.insert(0, "recognizer")
import corners
BOXES = {   # x0, y0, x1, y1
    "y6z4dd": [(0.2, 0, 0.75, 0.1)],
    "50ygdg": [(0.15, 0.43, 1, 0.62), (0, 0.92, 0.6, 1), (0, 0.05, 0.1, 0.22), (0.3, 0, 0.6, 0.05)],
    "oktnr4": [(0.1, 0.87, 0.5, 1), (0.84, 0.6, 1, 0.95), (0.3, 0, 0.7, 0.12), (0.65, 0, 0.9, 0.3)],
    "5vutmr": [(0.62, 0, 0.95, 0.2), (0.88, 0.4, 1, 0.7), (0.1, 0.9, 0.5, 1)],
}
orig = corners._gradients
mask = None
def masked(bgr, sigma=1.0):
    gx, gy = orig(bgr, sigma)
    if mask is not None:
        h, w = gx.shape
        for x0, y0, x1, y1 in mask:
            gx[int(y0*h):int(y1*h)+1, int(x0*w):int(x1*w)+1] = 0
            gy[int(y0*h):int(y1*h)+1, int(x0*w):int(x1*w)+1] = 0
    return gx, gy
corners._gradients = masked
def err(img, truth):
    f = corners.find_corners(img)
    return "-" if f is None else f"{np.linalg.norm(np.subtract(f, truth), axis=1).max() / max(img.shape[:2]):.1%}"
for n, boxes in BOXES.items():
    t = json.load(open(glob.glob(f"collected/*-{n}.truth.json")[0]))
    img = cv2.imread("collected/" + t["image"]); truth = t["corners_TL_TR_BR_BL"]
    # only the search on the whole shrunk photo is masked (the views in _move_in have other shapes)
    mask = None; a = err(img, truth)
    small, _ = corners.shrink(img); shape = small.shape[:2]
    def only_full(bgr, sigma=1.0, boxes=boxes):
        global mask
        keep = mask; mask = boxes if bgr.shape[:2] == shape else None
        r = masked(bgr, sigma); mask = keep; return r
    corners._gradients = only_full; b = err(img, truth); corners._gradients = masked
    print(f"{n}  now {a}  masked {b}")
