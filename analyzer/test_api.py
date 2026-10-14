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


def test_depth_choice():
    # the PWA offers 2- and 3-ply; deeper is refused (it would take tens of seconds on the Pi)
    html = client.get("/").text
    assert 'data-name="plies"' in html and 'data-value="3"' in html
    r = client.post("/analyze", json={"position_id": START_ID, "plies": 3})
    assert r.status_code == 200 and r.json()["plies"] == 3
    assert client.post("/analyze", json={"position_id": START_ID, "plies": 4}).status_code == 422


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


def _race(me_pips, opp_pips):
    """A race: White's checkers on its points (dict point -> count), Black's on its own."""
    pos = Position(points=[0] * 24)
    for p, n in me_pips.items():
        pos.points[p - 1] = n
    for p, n in opp_pips.items():
        pos.points[24 - p] = -n
    w, b = pos.counts()
    pos.off_white, pos.off_black = 15 - w, 15 - b
    return pos


def test_cube_decision_without_dice():
    # Start: nobody doubles; a double would be taken
    c = analyze(Position.start(), "white", plies=0)["cube"]
    assert c["question"] == "double" and c["doubler"] == "white" and c["taker"] == "black"
    assert c["double"] is False and c["take"] is True
    assert set(c["equity"]) == {"no_double", "double_take", "double_pass"}
    assert c["equity"]["double_pass"] == 1.0
    # A race 8 pips ahead with 11 checkers each: double, take
    pos = _race({6: 4, 7: 4, 8: 3}, {6: 4, 7: 4, 8: 4})
    c = analyze(pos, "white", plies=2)["cube"]
    assert c["double"] is True and c["take"] is True
    # ...and Black, on roll and behind, doesn't double
    assert analyze(pos, "black", plies=2)["cube"]["double"] is False
    # Far ahead: double, pass
    pos = _race({1: 3, 2: 3, 3: 3, 4: 2}, {6: 3, 7: 3, 8: 3, 9: 2})
    c = analyze(pos, "white", plies=0)["cube"]
    assert c["double"] is True and c["take"] is False


def test_no_cube_decision_with_dice_or_without_access():
    r = analyze(Position.start(), "white", plies=0, dice=(3, 1))
    assert r["cube"] is None and r["moves"]
    # Black owns the cube: White on roll can't double
    r = analyze(Position.start(), "white", plies=0, cube_value=2, cube_owner="black")
    assert r["cube"] is None and r["moves"] is None


def test_take_or_pass_after_a_double():
    pos = _race({6: 4, 7: 4, 8: 3}, {6: 4, 7: 4, 8: 4})
    c = analyze(pos, "white", plies=2, cube_value=2, cube_owner="black", doubled=True)["cube"]
    assert c["question"] == "take" and c["value"] == 1 and c["take"] is True and c["double"] is True
    # A redouble to 4: White owned the cube at 2
    c = analyze(pos, "white", plies=2, cube_value=4, cube_owner="black", doubled=True)["cube"]
    assert c["value"] == 2 and "redouble" in c["proper"].lower()


def test_api_cube():
    res = client.post("/analyze", json={"position_id": START_ID, "plies": 0})
    assert res.status_code == 200, res.text
    assert res.json()["cube"]["question"] == "double" and "ダブル" in res.json()["summary"]
    res = client.post("/analyze", json={"position_id": START_ID, "plies": 0, "cube_value": 2,
                                        "cube_owner": "black", "doubled": True})
    assert res.status_code == 200, res.text
    assert res.json()["cube"]["question"] == "take" and "テイク" in res.json()["summary"]
    bad = [{"cube_value": 3}, {"cube_value": 2}, {"cube_owner": "white"},
           {"cube_value": 2, "cube_owner": "white", "doubled": True},
           {"cube_value": 2, "doubled": True, "dice": [3, 1]}]
    for extra in bad:
        assert client.post("/analyze", json={"position_id": START_ID} | extra).status_code == 422, extra


def _draw_cube(img, x, y, side, text):
    import cv2

    cv2.rectangle(img, (x - side // 2, y - side // 2), (x + side // 2, y + side // 2), (235, 235, 235), -1)
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
    cv2.putText(img, text, (x - tw // 2, y + th // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (20, 20, 20), 3)


def test_cube_is_found_on_a_drawn_board():
    import numpy as np
    import cube
    from board import Layout

    lay = Layout(a=430, bar=70)
    H = np.eye(3)
    for x, y, text, at in ((650, 150, "2", "black"), (650, 500, "64", "centre"), (650, 850, "4", "white")):
        img = np.full((int(lay.h), int(lay.w), 3), (40, 70, 30), np.uint8)
        _draw_cube(img, x, y, 60, text)
        assert cube.read_cube(img, H, lay, 80.0)["at"] == at, text
    # a die is not a cube, and an empty board has none
    img = np.full((int(lay.h), int(lay.w), 3), (40, 70, 30), np.uint8)
    _draw_die(img, 650, 480, 50, 5, 10)
    assert cube.read_cube(img, H, lay, 80.0) is None


def test_api_reads_the_cube_from_the_photo():
    import cv2

    samples = Path(__file__).resolve().parent.parent / "samples"
    t = json.loads((samples / "screen2.truth.json").read_text())   # cube 2 on 奥's side, dice 5-4
    ok, jpg = cv2.imencode(".jpg", cv2.imread(str(samples / t["image"])))
    form = {"corners": ",".join(str(v) for xy in t["corners_TL_TR_BR_BL"] for v in xy),
            "home": t["home"], "bottom_colour": str(t["bottom_colour"]), "plies": "0"}
    j = client.post("/analyze-photo", files={"image": ("s.jpg", jpg.tobytes(), "image/jpeg")}, data=form).json()
    assert j["cube_read"] == {"at": "black"}
    assert j["analysis"]["moves"] and j["analysis"]["cube"] is None    # dice on the board: 奥 owns the cube
    # a cube set by hand comes first
    j = client.post("/analyze-photo", files={"image": ("s.jpg", jpg.tobytes(), "image/jpeg")},
                    data=form | {"cube_value": "1"}).json()
    assert j["cube_read"] == {"at": "black"} and j["analysis"]["cube"] is None and j["analysis"]["moves"]


def test_api_cube_read_without_dice_is_a_double(monkeypatch):
    # the cube on 手前's side and no dice: 奥 has just doubled, and 手前 takes or passes
    import cv2
    import numpy as np
    import board

    def fake(img, corners, **kw):
        return Position.start(), {"home": "right", "home_guess": None, "warnings": [], "geometry": None,
                                  "dice": {"values": None, "dice": []}, "cube": {"at": "white"}}

    monkeypatch.setattr(board, "recognize", fake)
    ok, png = cv2.imencode(".png", np.zeros((40, 40, 3), np.uint8))
    form = {"corners": "0,0,40,0,40,40,0,40", "plies": "0", "on_roll": "white"}
    j = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")}, data=form).json()
    a = j["analysis"]
    assert j["cube_read"] == {"at": "white"} and a["on_roll"] == "black"
    assert a["cube"]["question"] == "take" and a["cube"]["taker"] == "white" and a["cube"]["take"] is True


def test_api_photo_dice_cancel_a_double_set_by_hand(monkeypatch):
    # TODO-033: 「ダブルされた」set by hand (doubled=true, no dice) and dice read from the photo:
    # the photo's dice win, so it is no longer take or pass but the doubler's move (was 422)
    import cv2
    import numpy as np
    import board

    def fake(img, corners, **kw):
        return Position.start(), {"home": "right", "home_guess": None, "warnings": [], "geometry": None,
                                  "dice": {"values": [3, 1], "dice": []}, "cube": {"at": "white"}}

    monkeypatch.setattr(board, "recognize", fake)
    ok, png = cv2.imencode(".png", np.zeros((40, 40, 3), np.uint8))
    form = {"corners": "0,0,40,0,40,40,0,40", "plies": "0", "on_roll": "black",
            "cube_value": "2", "cube_owner": "white", "doubled": "true"}
    r = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")}, data=form)
    assert r.status_code == 200
    j = r.json()
    a = j["analysis"]
    assert j["dice_read"] == [3, 1] and a["on_roll"] == "black" and a["cube"] is None and a["moves"]
    # dice set by hand are kept as sent, and a double with dice is still refused
    r = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")},
                    data=form | {"dice": "6,5"})
    assert r.status_code == 422


def _sample_form(points=None, home="right"):
    truth = {"image": "x.jpg", "corners_TL_TR_BR_BL": [[0, 0], [10, 0], [10, 10], [0, 10]], "home": home,
             "bottom_colour": 1, "points": points or [0] * 24, "bar_white": 0, "bar_black": 0}
    return {"truth": json.dumps(truth)}


def test_samples_off_unless_configured(monkeypatch):
    monkeypatch.delenv("BG_SAMPLES_DIR", raising=False)
    assert client.get("/version").json()["samples"] is False
    r = client.post("/samples", data={"id": "1-a", **_sample_form()}, files={"image": ("a.jpg", b"jpg", "image/jpeg")})
    assert r.status_code == 404


def test_samples_saved_and_replaced(monkeypatch, tmp_path):
    monkeypatch.setenv("BG_SAMPLES_DIR", str(tmp_path))
    assert client.get("/version").json()["samples"] is True
    r = client.post("/samples", data={"id": "17-ab", **_sample_form()}, files={"image": ("a.png", b"png1", "image/png")})
    assert r.status_code == 200 and r.json() == {"saved": "user-17-ab"}
    # the same photo again (fixed once more, now a JPEG): the earlier pair is replaced
    pts = [0] * 24
    pts[5] = 2
    r = client.post("/samples", data={"id": "17-ab", **_sample_form(pts)}, files={"image": ("a.jpg", b"jpg2", "image/jpeg")})
    assert r.status_code == 200
    assert sorted(p.name for p in tmp_path.iterdir()) == ["user-17-ab.jpg", "user-17-ab.truth.json"]
    t = json.loads((tmp_path / "user-17-ab.truth.json").read_text())
    assert t["image"] == "user-17-ab.jpg" and t["points"][5] == 2
    assert (tmp_path / "user-17-ab.jpg").read_bytes() == b"jpg2"


def test_samples_rejects_bad_input(monkeypatch, tmp_path):
    monkeypatch.setenv("BG_SAMPLES_DIR", str(tmp_path))
    img = {"image": ("a.jpg", b"jpg", "image/jpeg")}
    assert client.post("/samples", data={"id": "../x", **_sample_form()}, files=img).status_code == 422
    assert client.post("/samples", data={"id": "1", **_sample_form([0] * 23)}, files=img).status_code == 422
    assert client.post("/samples", data={"id": "1", **_sample_form(home="up")}, files=img).status_code == 422
    assert client.post("/samples", data={"id": "1", **_sample_form()},
                       files={"image": ("a.gif", b"gif", "image/gif")}).status_code == 422
    assert list(tmp_path.iterdir()) == []


def test_4xx_reason_is_logged(caplog):
    # the access log only has the status; the reason goes to the log too, without the input
    with caplog.at_level("WARNING", logger="uvicorn.error"):
        assert client.post("/analyze-photo", files={"image": ("s.png", b"not an image", "image/png")},
                           data={"corners": "1,2,3,4,5,6,7,8"}).status_code == 422
        assert client.post("/analyze-photo", data={"plies": "secret-value"}).status_code == 422
        assert client.post("/analyze", json={"position_id": "bad\nFAKE LINE"}).status_code == 422
    assert "POST /analyze-photo -> 422: 'could not decode image'" in caplog.text
    assert "body.image: Field required" in caplog.text and "body.plies:" in caplog.text
    assert "secret-value" not in caplog.text
    assert "\nFAKE LINE" not in caplog.text and "bad\\nFAKE LINE" in caplog.text


def test_samples_measured_again_after_ten_new(monkeypatch, tmp_path):
    # recognizer/collected.py is started once the 10th new pair is saved, not before, and not twice at a time
    import app as app_module
    started = []

    class Running:
        def __init__(self, args, **kw):
            started.append(args)

        def poll(self):
            return None   # still running

    monkeypatch.setenv("BG_SAMPLES_DIR", str(tmp_path))
    monkeypatch.setattr(app_module.subprocess, "Popen", Running)
    monkeypatch.setattr(app_module, "_measuring", None)
    for i in range(11):
        r = client.post("/samples", data={"id": f"n{i}", **_sample_form()}, files={"image": ("a.jpg", b"jpg", "image/jpeg")})
        assert r.status_code == 200
        assert len(started) == (0 if i < 9 else 1), i
    assert started[0][-1] == str(tmp_path) and started[0][-2].endswith("recognizer/collected.py")
