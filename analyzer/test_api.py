"""Run: python3 -m pytest analyzer"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from analysis import Position, analyze
from app import app

client = TestClient(app)
START_ID = "4HPwATDgc/ABMA"


def test_start_position():
    r = analyze(Position.start(), "white", plies=0)
    assert r["position_id"] == START_ID
    assert r["pips"] == {"white": 167, "black": 167, "leader": None, "difference": 0}
    p = r["probabilities"]
    assert 50 < p["white"]["win"] < 55 and abs(p["white"]["win"] + p["black"]["win"] - 100) < 0.2
    assert r["favourite"] == "white"


def test_sides_are_symmetric():
    # Same position, Black on roll: Black's numbers are what White's were.
    w = analyze(Position.start(), "white", plies=0)
    b = analyze(Position.start(), "black", plies=0)
    assert b["probabilities"]["black"] == w["probabilities"]["white"]


def test_race_leader_wins():
    pos = Position(points=[0] * 24)
    pos.points[0] = 2           # White: 2 checkers on the 1-point
    pos.points[23] = -15        # Black: all 15 on its 1-point
    pos.off_white = 13
    r = analyze(pos, "black", plies=1)
    assert r["favourite"] == "white" and r["probabilities"]["white"]["win"] > 85


def test_game_over():
    pos = Position(points=[0] * 24, off_white=15)
    pos.points[23] = -15
    assert analyze(pos, "white")["game_over"] is True


def test_api_position_id_with_dice():
    res = client.post("/analyze", json={"position_id": START_ID, "dice": [3, 1]})
    assert res.status_code == 200, res.text
    j = res.json()
    assert j["moves"][0]["move"] == "8/5 6/5"
    assert j["board"]["points"][5] == 5 and "summary" in j


def test_api_moves_bearing_off_are_whole():
    # gnubg's move tuple stops at the first checker borne off, so "3/off 1/off" and
    # "3/off 3/2" both came out as "3/off"
    res = client.post("/analyze", json={"position_id": "e24HABDZAAAAAA", "dice": [3, 1]})
    assert res.status_code == 200, res.text
    moves = [m["move"] for m in res.json()["moves"]]
    assert moves[0] == "3/off 1/off"
    assert "3/2* 3/off" in moves and len(set(moves)) == len(moves)


def test_api_board_matches_truth():
    truth = json.loads((Path(__file__).parent.parent / "samples" / "photo2.truth.json").read_text())
    res = client.post("/analyze", json={"board": {"points": truth["points"]}, "on_roll": "black"})
    assert res.status_code == 200, res.text
    j = res.json()
    pos = Position(points=truth["points"])
    assert j["position_id"] == pos.position_id("black")
    assert j["pips"]["white"] == pos.pips()[0]


def test_api_rejects_bad_input():
    assert client.post("/analyze", json={}).status_code == 422
    assert client.post("/analyze", json={"position_id": "!!"}).status_code == 422
    too_many = [0] * 24
    too_many[0] = 16
    assert client.post("/analyze", json={"board": {"points": too_many}}).status_code == 422
    assert client.post("/analyze", json={"position_id": START_ID, "dice": [0, 7]}).status_code == 422


def test_pwa_is_served():
    r = client.get("/")
    assert r.status_code == 200 and "BG Analyzer" in r.text
    assert client.get("/manifest.webmanifest").headers["content-type"].startswith("application/manifest+json")
    assert client.get("/sw.js").status_code == 200
    # the phone must not keep running an old app.js after the server is updated
    assert client.get("/app.js").headers["cache-control"] == "no-cache"
    assert client.get("/").headers["cache-control"] == "no-cache"
    assert client.get("/health").json() == {"ok": True}   # API routes still win over the static mount


def test_server_exit_stops_gnubg_helper():
    import analysis
    with TestClient(app) as c:   # runs the lifespan, like uvicorn does
        assert c.post("/analyze", json={"position_id": START_ID}).status_code == 200
        helpers = list(analysis._pool._processes.values())
    assert analysis._pool is None
    assert helpers and not any(p.is_alive() for p in helpers)


def test_steep_photo_is_flagged():
    # The top-down samples and screenshots are fine. photo1 (removed for privacy) was taken at
    # a steep angle and read badly: its tapped corners and image size are kept here.
    import cv2
    from board import OBLIQUE_WARN_DEG, view_tilt_deg

    photo1 = view_tilt_deg([[1450, 1712], [2268, 1366], [3137, 1553], [2320, 2157]], (3024, 4032, 3))
    assert photo1 > OBLIQUE_WARN_DEG
    # the oblique Commons photos added in TODO-017 are steep enough to be flagged too
    steep = {"commons-nardy-midgame.truth.json", "commons-rollup-oblique.truth.json"}
    samples = Path(__file__).resolve().parent.parent / "samples"
    for f in samples.glob("*.truth.json"):
        t = json.loads(f.read_text())
        shape = cv2.imread(str(samples / t["image"])).shape
        assert (view_tilt_deg(t["corners_TL_TR_BR_BL"], shape) > OBLIQUE_WARN_DEG) == (f.name in steep), f.name


def test_version_reports_both_parts_and_commit():
    import subprocess

    import board
    import app as app_module
    v = client.get("/version").json()
    assert v["analyzer"] == app_module.__version__
    # the PWA shows its own version when it differs from the server's (an old cached copy)
    app_js = (Path(__file__).parent / "static" / "app.js").read_text()
    assert f'const APP_VERSION = "{app_module.__version__}"' in app_js
    assert v["recognizer"] == board.__version__
    head = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], capture_output=True, text=True,
                          cwd=Path(__file__).parent).stdout.strip()
    assert v["commit"] == (head or None)


def test_git_commit_reads_packed_and_detached_refs(tmp_path):
    from app import git_commit
    sha = "0123456789abcdef0123456789abcdef01234567"
    (tmp_path / "HEAD").write_text("ref: refs/heads/main\n")
    (tmp_path / "packed-refs").write_text(f"# pack-refs with: peeled\n{sha} refs/heads/main\n")
    assert git_commit(tmp_path) == "0123456"
    (tmp_path / "refs/heads").mkdir(parents=True)
    (tmp_path / "refs/heads/main").write_text("fedcba9876543210fedcba9876543210fedcba98\n")
    assert git_commit(tmp_path) == "fedcba9"   # a loose ref wins over packed-refs
    (tmp_path / "HEAD").write_text(sha + "\n")  # detached, as in CI's checkout
    assert git_commit(tmp_path) == "0123456"
    assert git_commit(tmp_path / "missing") is None


def _corner_error(found, truth, shape):
    """Largest distance between found and true corners, as a share of the photo's long side."""
    import numpy as np
    return float(np.linalg.norm(np.subtract(found, truth), axis=1).max() / max(shape[:2]))


def test_corners_are_found_on_samples():
    # The app shows these as the starting corners; the user drags them into place.
    # Boards with printed triangles are found; carved ones (photo4) and striped app
    # screens (screen1) may not be, and the app then starts from a rectangle.
    import cv2
    from corners import find_corners

    samples = Path(__file__).resolve().parent.parent / "samples"
    for name in ("photo2", "photo3", "screen2"):
        t = json.loads((samples / f"{name}.truth.json").read_text())
        img = cv2.imread(str(samples / t["image"]))
        found = find_corners(img)
        assert found is not None, name
        assert _corner_error(found, t["corners_TL_TR_BR_BL"], img.shape) < 0.035, name


def test_corners_are_found_on_synthetic_boards():
    import numpy as np
    from corners import find_corners
    from synth import photograph, random_position, render_board

    rng = np.random.default_rng(1)
    for k in range(4):
        board_img, c = render_board(random_position(rng), rng, home="right" if k % 2 else "left")
        photo, c = photograph(board_img, c, rng)
        found = find_corners(photo)
        assert found is not None and _corner_error(found, c, photo.shape) < 0.035, k


def test_api_find_corners():
    import cv2
    import numpy as np

    samples = Path(__file__).resolve().parent.parent / "samples"
    img = cv2.imread(str(samples / "photo2.jpg"))
    f = 2048 / max(img.shape[:2])   # the app sends large photos at this size
    small = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    res = client.post("/find-corners", files={"image": ("b.jpg", cv2.imencode(".jpg", small)[1].tobytes())})
    assert res.status_code == 200, res.text
    j = res.json()
    assert (j["width"], j["height"]) == (small.shape[1], small.shape[0])
    truth = json.loads((samples / "photo2.truth.json").read_text())["corners_TL_TR_BR_BL"]
    assert _corner_error(j["corners"], np.multiply(truth, f), small.shape) < 0.035

    blank = cv2.imencode(".png", np.full((300, 400, 3), 200, np.uint8))[1].tobytes()
    assert client.post("/find-corners", files={"image": ("b.png", blank)}).json()["corners"] is None
    assert client.post("/find-corners", files={"image": ("x.jpg", b"not an image")}).status_code == 422


def test_share_target():
    # Android's share sheet posts the photo to the manifest's share_target; sw.js answers on the
    # phone. Without it the server must not keep the photo, only send the app back to ./.
    manifest = client.get("/manifest.webmanifest").json()
    st = manifest["share_target"]
    assert not st["action"].startswith("/")   # relative, so it stays under /bg/
    assert st["method"] == "POST" and st["enctype"] == "multipart/form-data"
    name = st["params"]["files"][0]["name"]
    sw = client.get("/sw.js").text
    assert f'"{st["action"]}"' in sw and f'.get("{name}")' in sw
    res = client.post("/" + st["action"], files={name: ("b.jpg", b"\xff\xd8", "image/jpeg")},
                      follow_redirects=False)
    assert res.status_code == 303 and res.headers["location"] == "./?shared=none"


def test_home_side_is_guessed_from_the_checkers():
    import home_prior

    samples = Path(__file__).resolve().parent.parent / "samples"
    for f in sorted(samples.glob("*.truth.json")) + sorted((samples / "external").glob("*.truth.json")):
        t = json.loads(f.read_text())
        right = t["points"] if t["home"] == "right" else home_prior.mirror(t["points"])
        assert home_prior.guess(right)[0] == t["home"], f.name
    # nothing to go on: keep the default
    assert home_prior.guess([0] * 24, default="left") == ("left", 0)


def test_api_guesses_home_side():
    import cv2

    samples = Path(__file__).resolve().parent.parent / "samples"
    t = json.loads((samples / "screen1.truth.json").read_text())   # home on the left
    ok, png = cv2.imencode(".png", cv2.imread(str(samples / t["image"])))
    res = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")},
                      data={"corners": ",".join(str(v) for xy in t["corners_TL_TR_BR_BL"] for v in xy),
                            "home": "auto", "bottom_colour": str(t["bottom_colour"]), "plies": "0"})
    assert res.status_code == 200, res.text
    j = res.json()
    assert j["home"] == "left" and j["home_guess"]["margin"] < -1
    assert j["recognized"]["points"] == t["points"]


def _draw_die(img, cx, cy, side, value, deg):
    import cv2
    import numpy as np

    spots = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
             4: [(-1, -1), (1, -1), (-1, 1), (1, 1)], 5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
             6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}[value]
    t = np.deg2rad(deg)
    R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    box = (np.array([(-1, -1), (1, -1), (1, 1), (-1, 1)]) * side / 2) @ R.T + (cx, cy)
    cv2.fillConvexPoly(img, box.astype(np.int32), (235, 235, 235))
    for p in np.array(spots) * side * 0.27 @ R.T + (cx, cy):
        cv2.circle(img, (int(p[0]), int(p[1])), int(side * 0.09), (20, 20, 20), -1)


def test_dice_are_read_from_a_drawn_board():
    import cv2
    import numpy as np
    import dice
    from board import Layout

    lay = Layout(a=430, bar=70)
    H = np.eye(3)
    for a, b, deg in ((6, 1, 0), (5, 3, 20), (4, 2, 35), (2, 2, 70)):
        img = np.full((int(lay.h), int(lay.w), 3), (40, 70, 30), np.uint8)
        _draw_die(img, 650, 480, 50, a, deg)
        _draw_die(img, 730, 520, 50, b, deg + 25)
        assert dice.read_dice(img, H, lay, 80.0)["values"] == sorted([a, b], reverse=True)
    # one die, or a third one, and nothing is filled in
    img = np.full((int(lay.h), int(lay.w), 3), (40, 70, 30), np.uint8)
    _draw_die(img, 650, 480, 50, 5, 10)
    assert dice.read_dice(img, H, lay, 80.0)["values"] is None
    _draw_die(img, 730, 520, 50, 3, 10)
    _draw_die(img, 200, 520, 50, 4, 10)
    assert dice.read_dice(img, H, lay, 80.0)["values"] is None


def test_api_reads_dice_from_the_photo():
    import cv2

    samples = Path(__file__).resolve().parent.parent / "samples"
    t = json.loads((samples / "screen1.truth.json").read_text())   # dice 4-2 on the board
    ok, png = cv2.imencode(".png", cv2.imread(str(samples / t["image"])))
    form = {"corners": ",".join(str(v) for xy in t["corners_TL_TR_BR_BL"] for v in xy),
            "home": t["home"], "bottom_colour": str(t["bottom_colour"]), "plies": "0"}
    j = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")}, data=form).json()
    assert j["dice_read"] == [4, 2]
    assert j["analysis"]["moves"]                 # the best moves for the dice read
    # dice the user gave come first
    j = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")},
                    data=form | {"dice": "6,5"}).json()
    want = client.post("/analyze", json={"position_id": j["analysis"]["position_id"], "dice": [6, 5], "plies": 0}).json()
    assert j["dice_read"] == [4, 2] and j["analysis"]["moves"] == want["moves"]
