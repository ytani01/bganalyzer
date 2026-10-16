import runpy, sys
REPO = "/home/ytani/work/bganalyzer"
sys.path.insert(0, REPO + "/recognizer")
import geometry, numpy as np
orig = geometry.find_tips
n = [0]
def wrapped(ground, lay, m):
    tips = orig(ground, lay, m)
    n[0] += 1
    print(f"[probe] find_tips#{n[0]} lay.a={lay.a:.1f} bar={lay.bar:.1f} h={lay.h:.1f} pw={lay.pw:.1f}", file=sys.stderr)
    for row in ("top", "bottom"):
        r = sorted((c, round(L,1), None if b is None else round(b,1), round(x,1)) for c, rr, x, y, L, dx, b in tips if rr == row)
        print(f"  {row}: (col, L, base, x) {r}", file=sys.stderr)
    tb, bb = geometry._row_bases(tips, "top"), geometry._row_bases(tips, "bottom")
    tt = np.median([y for _, r, _, y, *_ in tips if r == "top"]) if tips else None
    bt = np.median([y for _, r, _, y, *_ in tips if r == "bottom"]) if tips else None
    if tb is not None and bb is not None:
        print(f"  lt={tt-tb:.1f} lb={bb-bt:.1f}", file=sys.stderr)
    return tips
geometry.find_tips = wrapped
sys.argv = ["evaluate.py", REPO + "/samples/photo6.truth.json"]
runpy.run_path(REPO + "/recognizer/evaluate.py", run_name="__main__")
