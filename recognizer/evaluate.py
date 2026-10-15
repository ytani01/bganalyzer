"""Compare recognition against *.truth.json samples."""
import glob, json, os, sys, urllib.request
import cv2
import board
import home_prior
from position import Position

def shrink_like_app(img, corners, max_side=2048, send_as_is=2560):
    """What the PWA does before upload: a canvas resize (bilinear) and JPEG 0.92."""
    if max(img.shape[:2]) <= send_as_is:
        return img, corners
    f = max_side / max(img.shape[:2])
    img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_LINEAR)
    img = cv2.imdecode(cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])[1], cv2.IMREAD_COLOR)
    return img, [[x * f, y * f] for x, y in corners]

def run(path, debug=None, app=False, method="circles"):
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
    pos0, info = board.recognize(img, corners, home=t["home"], debug_prefix=debug, method=method)
    pos1 = Position(points=[-n for n in pos0.points], bar_white=pos0.bar_black, bar_black=pos0.bar_white,
                    off_white=pos0.off_black, off_black=pos0.off_white)
    for pos in (pos0, pos1):
        wrong = [(i + 1, truth.points[i], pos.points[i]) for i in range(24) if truth.points[i] != pos.points[i]]
        if best is None or len(wrong) < len(best[1]):
            best = (pos, wrong)
    pos, wrong = best
    bar_ok = (pos.bar_white, pos.bar_black) == (truth.bar_white, truth.bar_black)
    # the app's guess of the home side, from this reading with the truth's checker colour
    read = (pos1 if t.get("bottom_colour", 1) else pos0).points
    home, margin = home_prior.guess(read if t["home"] == "right" else home_prior.mirror(read))
    # dice: the pair read with confidence (None when not sure) against the truth's (None when no pair can be read)
    want = t.get("dice") and sorted(t["dice"], reverse=True)
    # cube: where it lies and its number ({"at": ..., "value": ...}) against the truth's (None when
    # there is no cube); same_cube compares where, same_value the number (TODO-025)
    cube = info["cube"] and {"at": info["cube"]["at"], "value": info["cube"].get("value")}
    cube_want = t.get("cube") and {"at": t["cube"]["at"], "value": t["cube"].get("value")}
    if cube and cube["at"] == "field":
        # in a playing field: just doubled by the side on roll (the truth's on_roll, else 手前),
        # so it was offered to the other side (TODO-045)
        cube = {"at": "black" if t.get("on_roll", "white") == "white" else "white", "value": cube["value"]}
    return pos, truth, wrong, bar_ok, (home == t["home"], margin), (info["dice"]["values"], want), (cube, cube_want)

def same_cube(cube, cube_want):
    # where the cube lies. No cube in the photo is analysed as a cube in the centre, so count them
    # the same (TODO-053); a cube read in the centre is still WRONG when the truth has it on one side
    at = cube and cube["at"]
    at_want = cube_want and cube_want["at"]
    return at == at_want or (at in (None, "centre") and at_want in (None, "centre"))


def same_value(cube, cube_want):
    """The cube's number against the truth's: "ok", "not read" or "WRONG"; None when it does not
    count (no number in the truth, the cube in the centre, where its number means 1, or the cube
    not found where the truth has it)."""
    if not cube_want or cube_want.get("value") is None or cube_want["at"] == "centre":
        return None
    if not cube or cube["at"] != cube_want["at"]:
        return None
    return "ok" if cube["value"] == cube_want["value"] else "not read" if cube["value"] is None else "WRONG"

if __name__ == "__main__":
    # --app: shrink large photos the way the PWA does before sending them
    # --slots: count by slots (slots.py, experimental) instead of by circles
    app = "--app" in sys.argv
    # --section: count along each point's centre line (section.py, experimental)
    # --hough / --radial+hough: find the circles with Hough (before TODO-051) instead of / as well as radial symmetry
    method = next((a[2:] for a in sys.argv if a in ("--slots", "--section", "--hough", "--radial+hough")), "circles")
    files = [a for a in sys.argv[1:] if not a.startswith("--")] or sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "samples", "*.truth.json")))
    for f in files:
        pos, truth, wrong, bar_ok, (home_ok, margin), (dice, want), (cube, cube_want) = run(f, app=app, method=method)
        dice_ok = "ok" if dice == want else "not read" if dice is None else "WRONG"
        cube_ok = "ok" if same_cube(cube, cube_want) else "not found" if cube is None else "WRONG"
        value_ok = same_value(cube, cube_want)
        value = f", number {value_ok} (read {cube['value']}, truth {cube_want['value']})" if value_ok else ""
        print(f"{os.path.basename(f)}: {24 - len(wrong)}/24 points correct, bar {'ok' if bar_ok else 'wrong'}, "
              f"home guess {'ok' if home_ok else 'wrong'} ({margin:+.1f}), dice {dice_ok} (read {dice}, truth {want}), "
              f"cube {cube_ok} (read {cube and cube['at']}, truth {cube_want and cube_want['at']}{value})")
        for pt, a, b in wrong:
            print(f"   point {pt:2d}: truth {a:+d}  got {b:+d}")
