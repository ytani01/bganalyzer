"""rows where column_texture falls back to the upper quartile, and whether
dropping 'shown' there changes the reading (TODO-102; from TODO-077's tex.py)
usage: tex_fallback.py [--alt] truth.json ...   (--alt: also read with no 'shown' in those rows)"""
import json, os, sys
sys.path.insert(0, "recognizer")
import numpy as np, cv2, board, checkers
orig = checkers.column_texture
ALT = False
rows = []
def ct(gx, gy, lay, m, pitch):
    out = orig(gx, gy, lay, m, pitch)
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
            med = np.nanmedian(rs)
            if med >= checkers.TEX_MIN: continue
            q = np.nanpercentile(rs, 75)
            shown = [c for c in range(12) if out.get((c, row, k)) == "shown"]
            rows.append((row, k, med, q, q >= checkers.TEX_MIN_COVERED, shown))
            if ALT and q >= checkers.TEX_MIN_COVERED:
                for c in shown: del out[(c, row, k)]
    return out
checkers.column_texture = ct
args = sys.argv[1:]
if args[0] == "--alt": ALT = True; args = args[1:]
def read(p):
    t = json.load(open(p))
    img = cv2.imread(os.path.join(os.path.dirname(p), t["image"]))
    pos, _ = board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"], bottom_colour=t["bottom_colour"])
    return t, pos
for p in args:
    rows.clear(); ALT_ = ALT; ALT = False
    t, pos = read(p)
    used = sorted({(r, k, round(med, 2), round(q, 2), tuple(s)) for r, k, med, q, ok, s in rows if ok})
    low = sorted({(r, k, round(q, 2)) for r, k, med, q, ok, s in rows if not ok})
    line = "%s fallback=%s below=%s" % (os.path.basename(p), used, low)
    if ALT_ and used:
        ALT = True; rows.clear()
        _, pos2 = read(p); ALT = ALT_
        line += " alt_same=%s" % (pos2 == pos)
    else:
        ALT = ALT_
    print(line, flush=True)
