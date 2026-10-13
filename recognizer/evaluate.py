"""Compare recognition against *.truth.json samples."""
import glob, json, os, sys, urllib.request
import cv2
import board
from position import Position

def shrink_like_app(img, corners, max_side=2048, send_as_is=2560):
    """What the PWA does before upload: a canvas resize (bilinear) and JPEG 0.92."""
    if max(img.shape[:2]) <= send_as_is:
        return img, corners
    f = max_side / max(img.shape[:2])
    img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_LINEAR)
    img = cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])[1], cv2.IMREAD_COLOR)
    return img, [[x * f, y * f] for x, y in corners]

def run(path, debug=None, app=False):
    t = json.load(open(path))
    img_path = os.path.join(os.path.dirname(path), t["image"])
    if not os.path.exists(img_path) and "url" in t:
        # samples/external: images we may not redistribute, fetched on demand (git-ignored)
        req = urllib.request.Request(t["url"], headers={"User-Agent": "bganalyzer-evaluate"})
        with urllib.request.urlopen(req) as r, open(img_path, "wb") as f:
            f.write(r.read())
    img = cv2.imread(img_path)
    corners = t["corners_TL_TR_BR_BL"]
    if app:
        img, corners = shrink_like_app(img, corners)
    truth = Position(points=t["points"], bar_white=t["bar_white"], bar_black=t["bar_black"])
    # which checker colour belongs to the bottom player is the user's choice in the
    # app; here take the assignment that matches the truth
    best = None
    pos0, info = board.recognize(img, corners, home=t["home"], debug_prefix=debug)
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
    # --app: shrink large photos the way the PWA does before sending them
    app = "--app" in sys.argv
    files = [a for a in sys.argv[1:] if a != "--app"] or sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "samples", "*.truth.json")))
    for f in files:
        pos, truth, wrong, bar_ok = run(f, app=app)
        print(f"{os.path.basename(f)}: {24 - len(wrong)}/24 points correct, bar {'ok' if bar_ok else 'wrong'}")
        for pt, a, b in wrong:
            print(f"   point {pt:2d}: truth {a:+d}  got {b:+d}")
