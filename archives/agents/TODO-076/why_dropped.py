"""TODO-076: why detect_checkers drops circles. Prints each candidate circle with its
measures and the test that drops it. usage: why_dropped.py <truth.json> [x0 x1 y0 y1 (canonical)]"""
import inspect, json, os, re, sys
here = os.path.join(os.path.dirname(__file__), "..", "..", "..", "recognizer")
sys.path.insert(0, here)
import cv2, numpy as np
import board, checkers

src = inspect.getsource(checkers.detect_checkers)
box = [float(v) for v in sys.argv[2:6]] or None
log = []
def note(why, **kw):
    if box is None or (box[0] <= kw["cx"] <= box[1] and box[2] <= kw["cy"] <= box[3]):
        log.append((why, {k: round(float(v), 2) for k, v in kw.items()}))
# label every `continue` in the scoring loop
lines, out = src.split("\n"), []
for i, l in enumerate(lines):
    if l.strip() == "continue" and "for x, y, r in cs[0]" in "\n".join(lines[:i]) and "scored.append" not in "\n".join(lines[:i]):
        ind = l[:len(l) - len(l.lstrip())]
        out.append(ind + f"_note('drop@{i}', **{{k: v for k, v in dict(cx=cx, cy=cy, r=r, support=locals().get('support', -1), ring_same=locals().get('ring_same', -1), distinct=locals().get('distinct', -1), score=locals().get('score', -1)).items()}})")
    out.append(l)
    if "scored.append" in l:
        ind = l[:len(l) - len(l.lstrip())]
        out.append(ind + "_note('kept', cx=cx, cy=cy, r=r, support=support, ring_same=ring_same, distinct=distinct, score=score)")
ns = vars(checkers) | {"_note": note}
exec(re.sub(r"^def detect_checkers", "def detect_checkers", "\n".join(out)), ns)
checkers.detect_checkers = ns["detect_checkers"]
board.detect_checkers = ns["detect_checkers"]

t = json.load(open(sys.argv[1]))
img = cv2.imread(os.path.join(os.path.dirname(sys.argv[1]), t["image"]))
pos, info = board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"], bottom_colour=t["bottom_colour"])
print("pitch", info["pitch"], "layout", info["layout"])
for why, kw in log:
    print(why, kw)
