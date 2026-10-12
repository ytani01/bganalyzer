"""Compare recognition against *.truth.json samples."""
import glob, json, os, sys
import cv2
import board
from position import Position

def run(path, debug=None):
    t = json.load(open(path))
    img = cv2.imread(os.path.join(os.path.dirname(path), t["image"]))
    truth = Position(points=t["points"], bar_white=t["bar_white"], bar_black=t["bar_black"])
    # which checker colour belongs to the bottom player is the user's choice in the
    # app; here take the assignment that matches the truth
    best = None
    pos0, info = board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"], debug_prefix=debug)
    pos1 = Position(points=[-n for n in pos0.points], bar_white=pos0.bar_black, bar_black=pos0.bar_white,
                    off_white=pos0.off_black, off_black=pos0.off_white)
    for pos in (pos0, pos1):
        wrong = [(i + 1, truth.points[i], pos.points[i]) for i in range(24) if truth.points[i] != pos.points[i]]
        if best is None or len(wrong) < len(best[1]):
            best = (pos, wrong)
    pos, wrong = best
    bar_ok = (pos.bar_white, pos.bar_black) == (truth.bar_white, truth.bar_black)
    return pos, truth, wrong, bar_ok

if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "samples", "*.truth.json")))
    for f in files:
        pos, truth, wrong, bar_ok = run(f)
        print(f"{os.path.basename(f)}: {24 - len(wrong)}/24 points correct, bar {'ok' if bar_ok else 'wrong'}")
        for pt, a, b in wrong:
            print(f"   point {pt:2d}: truth {a:+d}  got {b:+d}")
