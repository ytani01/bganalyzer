"""print column_texture ratios per row/depth for a sample (TODO-077)"""
import json, os, sys
sys.path.insert(0, "recognizer")
import numpy as np, cv2, board, checkers
orig = checkers.column_texture
def ct(gx, gy, lay, m, pitch):
    r = int(pitch * 0.45)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]; disc = xx**2 + yy**2 <= r*r
    ax, ay = np.abs(gx), np.abs(gy)
    for row in ("top", "bottom"):
        for k in range(checkers.TEX_DEPTHS):
            dep = pitch * (k + 0.5)
            if dep > lay.h / 2 - pitch / 2: break
            y = int(m + (dep if row == "top" else lay.h - dep))
            rs = []
            for c in range(12):
                x = int(m + lay.col_x(c)); sl = np.s_[y-r:y+r+1, x-r:x+r+1]
                rs.append(ax[sl][disc].sum() / (ay[sl][disc].sum() + 1) if ax[sl].shape == disc.shape else np.nan)
            print(row, k, "med %.2f" % np.nanmedian(rs), " ".join("%.1f" % v for v in rs))
    print("--")
    return orig(gx, gy, lay, m, pitch)
checkers.column_texture = ct
t = json.load(open(sys.argv[1]))
img = cv2.imread(os.path.join(os.path.dirname(sys.argv[1]), t["image"]))
pos, info = board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"], bottom_colour=t["bottom_colour"])
