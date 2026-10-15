"""TODO-062: bar width and the gap between the fields' innermost columns at each step, in points."""
import json, sys
from pathlib import Path
import cv2
sys.path.insert(0, "recognizer")
import board, geometry

def show(name, lay):
    pw = lay.a / 6
    if lay.cols:
        pw = (lay.cols[5] - lay.cols[0] + lay.cols[11] - lay.cols[6]) / 10
        gap = (lay.cols[6] - lay.cols[5]) / pw
    else:
        gap = (lay.bar + pw) / pw
    print(f"  {name:12s} bar={lay.bar / pw:.2f}pt gap={gap:.2f}pt")

for f in sys.argv[1:]:
    t = json.loads(Path(f).read_text())
    img = cv2.imread(str(Path(f).parent / t["image"]))
    print(Path(f).name)
    def wrap(fn, name, pick=lambda r: r):
        def w(*a, **k):
            r = fn(*a, **k); show(name, pick(r)); return r
        return w
    board.refine = wrap(geometry.refine, "refine", lambda r: r[2])
    board.fit_columns = wrap(geometry.fit_columns, "fit_columns")
    board.refine_tips = wrap(geometry.refine_tips, "refine_tips", lambda r: r[1])
    board.fit_columns_to_checkers = wrap(geometry.fit_columns_to_checkers, "to_checkers")
    pos, _ = board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"], bottom_colour=t["bottom_colour"])
    bad = sum(a != b for a, b in zip(pos.points, t["points"]))
    print(f"  wrong points: {bad}")
