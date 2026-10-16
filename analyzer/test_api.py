"""Run: python3 -m pytest analyzer"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from analysis import Position, analyze, summary_ja
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


def test_api_moves_have_one_step_per_die():
    # 6-5 from the start: "24/13" is played as 24/18 and 18/13, so the board can draw both
    res = client.post("/analyze", json={"position_id": START_ID, "dice": [6, 5]})
    assert res.status_code == 200, res.text
    best = res.json()["moves"][0]
    assert best["move"] == "24/13" and best["steps"] == [[24, 18], [18, 13]]
    res = client.post("/analyze", json={"position_id": START_ID, "dice": [3, 3]})
    for m in res.json()["moves"]:
        assert len(m["steps"]) == 4 and all(a - b == 3 for a, b in m["steps"])


def test_api_moves_bearing_off_are_whole():
    # gnubg's move tuple stops at the first checker borne off, so "3/off 1/off" and
    # "3/off 3/2" both came out as "3/off"
    res = client.post("/analyze", json={"position_id": "e24HABDZAAAAAA", "dice": [3, 1]})
    assert res.status_code == 200, res.text
    moves = [m["move"] for m in res.json()["moves"]]
    assert moves[0] == "3/off 1/off"
    assert "3/2* 3/off" in moves and len(set(moves)) == len(moves)
    steps = {m["move"]: m["steps"] for m in res.json()["moves"]}
    assert sorted(steps["3/off 1/off"]) == [[1, 0], [3, 0]]      # the completed tuples too
    # in a match, the plays are completed by the scores seen from the other side (TODO-066)
    res = client.post("/analyze", json={"position_id": "e24HABDZAAAAAA", "dice": [3, 1],
                                        "match_length": 7, "score_white": 5, "score_black": 3})
    assert res.status_code == 200, res.text
    assert res.json()["moves"][0]["move"] == "3/off 1/off"


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
    import engine
    with TestClient(app) as c:   # runs the lifespan, like uvicorn does
        assert c.post("/analyze", json={"position_id": START_ID}).status_code == 200
        helpers = list(engine._pool._processes.values())
    assert engine._pool is None
    assert helpers and not any(p.is_alive() for p in helpers)


def test_steep_photo_is_flagged():
    # The top-down samples and screenshots are fine. photo1 (removed for privacy) was taken at
    # a steep angle and read badly: its tapped corners and image size are kept here.
    import cv2
    from board import OBLIQUE_WARN_DEG, view_tilt_deg

    photo1 = view_tilt_deg([[1450, 1712], [2268, 1366], [3137, 1553], [2320, 2157]], (3024, 4032, 3))
    assert photo1 > OBLIQUE_WARN_DEG
    # the oblique Commons photos added in TODO-017 are steep enough to be flagged too
    # and so are three of the photos collected on the Pi (TODO-030)
    steep = {"commons-nardy-midgame.truth.json", "commons-rollup-oblique.truth.json",
             "collected-4b88u3.truth.json", "collected-5wxq9t.truth.json", "collected-ajxlol.truth.json",
             "photo5.truth.json", "photo6.truth.json"}   # taken from beside the players (TODO-076)
    samples = Path(__file__).resolve().parent.parent / "samples"
    for f in samples.glob("*.truth.json"):
        t = json.loads(f.read_text())
        shape = cv2.imread(str(samples / t["image"])).shape
        assert (view_tilt_deg(t["corners_TL_TR_BR_BL"], shape) > OBLIQUE_WARN_DEG) == (f.name in steep), f.name


def test_version_reports_both_parts_and_commit():
    import shutil
    import subprocess

    import board
    import app as app_module
    v = client.get("/version").json()
    assert v["analyzer"] == app_module.__version__
    # the PWA shows its own version when it differs from the server's (an old cached copy)
    app_js = (Path(__file__).parent / "static" / "app.js").read_text()
    assert f'const APP_VERSION = "{app_module.__version__}"' in app_js
    assert v["recognizer"] == board.__version__
    if shutil.which("git") is None:   # git_commit has its own test
        pytest.skip("git is not installed")
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
    # The far / near edges are the strongest straight edges, the left / right ones lines with an edge
    # in nearly every row between them; each edge is moved to the innermost strong edge nearby, and
    # the quad that frames two rows of twelve triangles best wins (TODO-028, recognizer 0.16.0).
    # diagram-prime: the frame with the point numbers is taken (4.7%).
    import cv2
    from corners import find_corners

    samples = Path(__file__).resolve().parent.parent / "samples"
    for name, most in (("photo2", 0.035), ("photo3", 0.035), ("screen2", 0.035), ("screen1", 0.035),
                       ("commons-tavli-black", 0.035), ("commons-tavli-burl", 0.035),
                       ("commons-dark-homeleft", 0.035), ("commons-diagram-prime", 0.05),
                       ("commons-travel-case", 0.035), ("tv-vegas-open", 0.035)):
        t = json.loads((samples / f"{name}.truth.json").read_text())
        img = cv2.imread(str(samples / t["image"]))
        found = find_corners(img)
        assert found is not None, name
        assert _corner_error(found, t["corners_TL_TR_BR_BL"], img.shape) < most, name


def test_corners_are_found_on_synthetic_boards():
    import numpy as np
    from corners import find_corners
    from synth import photograph, random_position, render_board

    rng = np.random.default_rng(1)
    for k in range(4):
        board_img, c = render_board(random_position(rng), rng, home="right" if k % 2 else "left")
        photo, c = photograph(board_img, c, rng)
        found = find_corners(photo)
        assert found is not None and _corner_error(found, c, photo.shape) < 0.02, k


def test_corners_keep_the_fixed_ones_and_look_in_the_trimmed_part():
    # Looking again after the user has moved some corners or trimmed the photo (TODO-068).
    import cv2
    from corners import find_corners

    samples = Path(__file__).resolve().parent.parent / "samples"
    t = json.loads((samples / "screen1.truth.json").read_text())
    img = cv2.imread(str(samples / t["image"]))
    truth = t["corners_TL_TR_BR_BL"]
    found = find_corners(img, fixed=[truth[0], truth[1], None, None])
    assert found[:2] == truth[:2] and _corner_error(found, truth, img.shape) < 0.036
    assert find_corners(img, fixed=truth) == truth
    # a corner no candidate agrees with: nothing found (the app keeps the corners as they are)
    assert find_corners(img, fixed=[[img.shape[1] / 2, img.shape[0] / 2], None, None, None]) is None

    # the board is small in this photo: found only in the part around it
    t = json.loads((samples / "collected-sj1vrx.truth.json").read_text())
    img = cv2.imread(str(samples / t["image"]))
    truth = t["corners_TL_TR_BR_BL"]
    assert find_corners(img) is None
    xs, ys = [p[0] for p in truth], [p[1] for p in truth]
    mx, my = 0.15 * (max(xs) - min(xs)), 0.15 * (max(ys) - min(ys))
    found = find_corners(img, crop=(min(xs) - mx, min(ys) - my, max(xs) + mx, max(ys) + my))
    assert found is not None and _corner_error(found, truth, img.shape) < 0.036

    # trimmed to the board, the playing area fills most of it: not one of the two fields (20 % off),
    # and the stages of the search come in the photo's pixels
    t = json.loads((samples / "screen2.truth.json").read_text())
    img = cv2.imread(str(samples / t["image"]))
    truth = t["corners_TL_TR_BR_BL"]
    xs, ys = [p[0] for p in truth], [p[1] for p in truth]
    mx, my = 0.15 * (max(xs) - min(xs)), 0.15 * (max(ys) - min(ys))
    stages = {}
    found = find_corners(img, lambda stage, data: stages.setdefault(stage, data),
                         crop=(min(xs) - mx, min(ys) - my, max(xs) + mx, max(ys) + my))
    assert _corner_error(found, truth, img.shape) < 0.036
    assert min(line[0][0] for line in stages["edges"]["lines"]) == int(min(xs) - mx)


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

    # looking again (TODO-068): the fixed corners come back as they are, the others are looked for
    jpg = cv2.imencode(".jpg", small)[1].tobytes()
    fixed = [j["corners"][0], None, None, None]
    xs, ys = [p[0] for p in j["corners"]], [p[1] for p in j["corners"]]
    crop = f"{min(xs) - 50},{min(ys) - 50},{max(xs) + 50},{max(ys) + 50}"
    res = client.post("/find-corners", files={"image": ("b.jpg", jpg)}, data={"fixed": json.dumps(fixed), "crop": crop})
    assert res.status_code == 200, res.text
    assert res.json()["corners"][0] == fixed[0]
    assert _corner_error(res.json()["corners"], np.multiply(truth, f), small.shape) < 0.035
    res = client.post("/find-corners", files={"image": ("b.jpg", jpg)}, data={"fixed": json.dumps(j["corners"]), "stream": "true"})
    assert json.loads(res.text.splitlines()[-1])["result"]["corners"] == j["corners"]
    for bad in ({"fixed": "[1, 2]"}, {"fixed": "[[1], null, null, null]"}, {"fixed": "nope"},
                {"crop": "1,2,3"}, {"crop": "a,b,c,d"}):
        assert client.post("/find-corners", files={"image": ("b.jpg", jpg)}, data=bad).status_code == 422, bad


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
    # photo5: the black checkers hold white's 1 and 6 points and white has two back on 24,
    # so the checkers point the wrong way (TODO-076)
    for f in sorted(samples.glob("*.truth.json")) + sorted((samples / "external").glob("*.truth.json")):
        if f.name == "photo5.truth.json":
            continue
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


def test_cube_decision_before_the_roll_with_dice():
    # with dice too, whether White should have doubled before rolling (TODO-096)
    pos = _race({1: 3, 2: 3, 3: 3, 4: 2}, {6: 3, 7: 3, 8: 3, 9: 2})
    r = analyze(pos, "white", plies=0, dice=(3, 1))
    c = r["cube"]
    assert r["moves"] and c["question"] == "double" and c["rolled"] is True
    assert c["proper"] == analyze(pos, "white", plies=0)["cube"]["proper"]
    assert analyze(pos, "white", plies=0)["cube"]["rolled"] is False
    assert summary_ja(r).endswith("振る前、白はダブルすべき、黒はパス")
    # ...but not when no double was due (TODO-096)
    r = analyze(Position.start(), "white", plies=0, dice=(3, 1))
    assert r["cube"] is None and r["moves"]


def test_no_cube_decision_without_access():
    # Black owns the cube: no cube decision for White, with or without dice
    r = analyze(Position.start(), "white", plies=0, cube_value=2, cube_owner="black", dice=(3, 1))
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


def test_match_score_changes_the_answer():
    # TODO-066: the start position, 手前 on roll. Money: no double. 7-point match, 手前 behind 3-5: double
    money = analyze(Position.start(), "white", plies=0)
    assert money["match"] is None and money["cube"]["double"] is False
    behind = analyze(Position.start(), "white", plies=0, match_length=7, score_white=3, score_black=5)
    assert behind["match"] == {"length": 7, "score": {"white": 3, "black": 5}, "crawford": False}
    assert behind["cube"]["double"] is True and behind["equity"] != money["equity"]
    # 手前 wins this game more often (52%): the favourite, though the match equity is 奥's
    assert behind["favourite"] == "white" and behind["equity"]["white"] < 0 and "白が有利" in summary_ja(behind)
    # the scores go to gnubg from the side on roll: 奥 on roll and behind 3-5 is the same answer
    b = analyze(Position.start(), "black", plies=0, match_length=7, score_white=5, score_black=3)
    assert b["cube"]["proper"] == behind["cube"]["proper"] and b["equity"]["black"] == behind["equity"]["white"]
    # ahead 5-3: no double
    ahead = analyze(Position.start(), "white", plies=0, match_length=7, score_white=5, score_black=3)
    assert ahead["cube"]["double"] is False
    # the plays are scored for the match too
    m = analyze(Position.start(), "white", plies=0, dice=(3, 1), match_length=7, score_white=3, score_black=5)
    assert m["moves"][0]["equity"] != analyze(Position.start(), "white", plies=0, dice=(3, 1))["moves"][0]["equity"]
    # and back to money after a match: the same as before (gnubg's session is put back)
    assert analyze(Position.start(), "white", plies=0) == money


def test_no_double_in_the_crawford_game():
    kw = {"match_length": 7, "score_white": 5, "score_black": 6}   # 手前 behind would double, but not now
    r = analyze(Position.start(), "white", plies=0, crawford=True, **kw)
    assert r["cube"] is None and r["moves"] is None and r["match"]["crawford"] is True
    assert "7 ポイントマッチ 白 5 対 黒 6（クロフォード）" in summary_ja(r)
    # post-Crawford, the side behind doubles
    assert analyze(Position.start(), "white", plies=0, **kw)["cube"]["double"] is True


def test_optional_double_words():
    from analysis import _cube_result, cube_summary_ja

    c = _cube_result({"proper": "Optional double, take", "equity": {}}, "white", 1, False)
    assert c["optional"] is True and c["double"] is False and c["take"] is True
    assert cube_summary_ja(c) == "白はダブルしてもしなくてもよい（ダブルされたら黒はテイク）"
    t = _cube_result({"proper": "Optional double, take", "equity": {}}, "white", 1, True)
    assert cube_summary_ja(t) == "黒はテイク（白のダブルはしてもしなくてもよい）"


def test_api_match():
    base = {"position_id": START_ID, "plies": 0}
    res = client.post("/analyze", json=base | {"match_length": 7, "score_white": 3, "score_black": 5})
    assert res.status_code == 200, res.text
    assert res.json()["cube"]["double"] is True
    assert res.json()["summary"].startswith("7 ポイントマッチ 白 3 対 黒 5。")
    assert client.post("/analyze", json=base).json()["summary"].startswith("白が有利")   # money as before
    # TODO-086: the names follow the checkers' colour; 手前 (White) with the darker ones is 黒
    dark = client.post("/analyze", json=base | {"bottom_colour": 0}).json()["summary"]
    assert dark.startswith("黒が有利") and "ピップ 黒 167 / 白 167" in dark
    assert client.post("/analyze", json=base | {"bottom_colour": 1}).json()["summary"].startswith("白が有利")
    bad = [{"match_length": -1}, {"match_length": 65}, {"score_white": 1}, {"crawford": True},
           {"match_length": 7, "score_white": 7}, {"match_length": 7, "score_black": -1},
           {"match_length": 7, "score_white": 3, "crawford": True},                       # no one 1 away
           {"match_length": 7, "score_white": 6, "score_black": 6, "crawford": True},     # both 1 away
           {"match_length": 7, "score_white": 6, "crawford": True, "cube_value": 2, "cube_owner": "white"}]
    for extra in bad:
        assert client.post("/analyze", json=base | extra).status_code == 422, extra


def test_api_photo_match(monkeypatch):
    import board
    import cv2
    import numpy as np

    monkeypatch.setattr(board, "recognize", lambda img, corners, **kw: (
        Position.start(), {"home": "right", "home_guess": None, "warnings": [], "geometry": None,
                           "dice": {"values": None, "dice": []}, "cube": None}))
    _, png = cv2.imencode(".png", np.zeros((40, 40, 3), np.uint8))
    form = {"corners": "0,0,40,0,40,40,0,40", "plies": "0", "on_roll": "white",
            "match_length": "7", "score_white": "3", "score_black": "5"}
    a = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")}, data=form).json()["analysis"]
    assert a["match"]["score"] == {"white": 3, "black": 5} and a["cube"]["double"] is True
    # the Crawford game and a cube read on one side: the board comes back to be fixed, without the analysis
    monkeypatch.setattr(board, "recognize", lambda img, corners, **kw: (
        Position.start(), {"home": "right", "home_guess": None, "warnings": [], "geometry": None,
                           "dice": {"values": None, "dice": []}, "cube": {"at": "white", "value": 2}}))
    res = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")},
                      data=form | {"score_white": "6", "crawford": "true"})
    assert res.status_code == 200, res.text
    j = res.json()
    assert j["analysis"] is None and "Crawford" in j["analysis_error"] and j["recognized"]["points"]


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
    # on the bar (x 430 to 500): where it lies up or down; in a field: just doubled (TODO-045)
    for x, y, text, at in ((465, 150, "2", "black"), (465, 500, "64", "centre"), (465, 850, "4", "white"),
                           (650, 500, "2", "field"), (200, 150, "2", "field")):
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
    assert j["cube_read"] == {"at": "black", "value": 2}   # its number is read too (TODO-025)
    assert j["analysis"]["moves"] and j["analysis"]["cube"] is None    # dice on the board: 奥 owns the cube
    # a cube set by hand comes first
    j = client.post("/analyze-photo", files={"image": ("s.jpg", jpg.tobytes(), "image/jpeg")},
                    data=form | {"cube_value": "1"}).json()
    # centred, a double was due before the 5-4 (TODO-096)
    assert j["cube_read"] == {"at": "black", "value": 2} and j["analysis"]["moves"]
    assert j["analysis"]["cube"]["double"] and j["analysis"]["cube"]["rolled"]


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
    assert j["cube_read"] == {"at": "white", "value": None} and a["on_roll"] == "black"
    assert a["cube"]["question"] == "take" and a["cube"]["taker"] == "white" and a["cube"]["take"] is True
    assert a["cube"]["value"] == 1   # not read: taken as 2, so 1 before the double
    # the number read is used (TODO-025): offered at 8, so 4 before the double
    monkeypatch.setattr(board, "recognize", lambda img, corners, **kw: (
        Position.start(), {"home": "right", "home_guess": None, "warnings": [], "geometry": None,
                           "dice": {"values": None, "dice": []}, "cube": {"at": "white", "value": 8}}))
    j = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")}, data=form).json()
    assert j["cube_read"] == {"at": "white", "value": 8} and j["analysis"]["cube"]["value"] == 4


def test_api_cube_in_a_field_is_a_double_even_with_dice(monkeypatch):
    # TODO-045: the cube in a playing field: the side on roll (手前) has just doubled to 2, 奥 takes or
    # passes, and the dice on the board are left out
    import cv2
    import numpy as np
    import board

    def fake(img, corners, **kw):
        return Position.start(), {"home": "right", "home_guess": None, "warnings": [], "geometry": None,
                                  "dice": {"values": [3, 1], "dice": []}, "cube": {"at": "field"}}

    monkeypatch.setattr(board, "recognize", fake)
    ok, png = cv2.imencode(".png", np.zeros((40, 40, 3), np.uint8))
    form = {"corners": "0,0,40,0,40,40,0,40", "plies": "0", "on_roll": "white"}
    for extra in ({}, {"dice": "6,5"}):
        r = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")}, data=form | extra)
        assert r.status_code == 200
        j = r.json()
        a = j["analysis"]
        assert j["cube_read"] == {"at": "field", "value": None} and j["dice_read"] is None
        assert a["on_roll"] == "white" and a["cube"]["question"] == "take" and a["cube"]["taker"] == "black"
    # a cube set by hand comes first: then the dice are used
    j = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")},
                    data=form | {"cube_value": "1"}).json()
    assert j["analysis"]["cube"] is None and j["analysis"]["moves"]


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
    # dice set by hand are kept as sent, and a double with dice is still refused: the board comes back
    # without the analysis (TODO-066)
    r = client.post("/analyze-photo", files={"image": ("s.png", png.tobytes(), "image/png")},
                    data=form | {"dice": "6,5"})
    assert r.status_code == 200 and r.json()["analysis"] is None and "dice" in r.json()["analysis_error"]


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
    import samples
    started, done = [], []

    class Running:
        def __init__(self, args, **kw):
            started.append(args)

        def poll(self):
            return 0 if done else None   # None: still running

    monkeypatch.setenv("BG_SAMPLES_DIR", str(tmp_path))
    monkeypatch.setattr(samples.subprocess, "Popen", Running)
    monkeypatch.setattr(samples, "_measuring", None)
    for i in range(11):
        r = client.post("/samples", data={"id": f"n{i}", **_sample_form()}, files={"image": ("a.jpg", b"jpg", "image/jpeg")})
        assert r.status_code == 200
        assert len(started) == (0 if i < 9 else 1), i
    assert started[0][-1] == str(tmp_path) and started[0][-2].endswith("recognizer/collected.py")
    done.append(1)   # it finished without writing .measured.json: the next save starts it again
    client.post("/samples", data={"id": "n11", **_sample_form()}, files={"image": ("a.jpg", b"jpg", "image/jpeg")})
    assert len(started) == 2


# A stand-in for claude -p (TODO-082): FAKE_CLAUDE says what it does. The real one is never called here.
FAKE_CLAUDE = '''#!{python}
import json, os, re, subprocess, sys
mode = os.environ["FAKE_CLAUDE"]
if mode == "slow":   # ends at once, leaving a child that holds stdout and never ends
    child = subprocess.Popen(["sleep", "60"])
    open(os.environ["FAKE_PIDS"], "w").write(f"{{os.getpid()}} {{child.pid}}")
    sys.exit(0)
msg = json.loads(sys.stdin.readline())["message"]["content"]
assert msg[0]["type"] == "image" and "--tools" in sys.argv
w, h = map(int, re.search(r"\\((\\d+)x(\\d+)\\)", msg[1]["text"]).groups())
text = "top-left: ...\\n" + json.dumps({{"corners": [[-5, 10], [w - 10, 10], [w + 5, h - 10], [10, h - 10]]}})
print(json.dumps({{"type": "system"}}))
print(json.dumps({{"type": "result", "result": text if mode == "ok" else "I can't see a board"}}))
'''


def _fake_claude(monkeypatch, tmp_path, mode):
    import sys
    p = tmp_path / "claude"
    p.write_text(FAKE_CLAUDE.format(python=sys.executable))
    p.chmod(0o755)
    monkeypatch.setenv("BG_CLAUDE", str(p))
    monkeypatch.setenv("FAKE_CLAUDE", mode)
    monkeypatch.setenv("FAKE_PIDS", str(tmp_path / "pids"))


def _wide_png():
    import cv2
    import numpy as np
    return cv2.imencode(".png", np.zeros((1000, 3136, 3), np.uint8))[1].tobytes()   # sent at half the size


def test_claude_corners_off_or_busy(monkeypatch):
    import claude_corners
    monkeypatch.delenv("BG_CLAUDE", raising=False)
    assert client.get("/version").json()["claude"] is False
    img = {"image": ("a.png", _wide_png())}
    assert client.post("/claude-corners", files=img).status_code == 404
    monkeypatch.setenv("BG_CLAUDE", "/nonexistent/claude")
    assert client.get("/version").json()["claude"] is True
    monkeypatch.setattr(claude_corners, "_running", True)   # one is running: the next is not kept waiting
    assert client.post("/claude-corners", files=img).status_code == 429


def test_claude_corners_answer(monkeypatch, tmp_path):
    img = {"image": ("a.png", _wide_png())}
    _fake_claude(monkeypatch, tmp_path, "ok")
    r = client.post("/claude-corners", files=img)
    assert r.status_code == 200, r.text
    # scaled back to the sent image (it went at 1568 px wide), and kept inside it
    assert r.json() == {"corners": [[0, 20], [3116, 20], [3136, 980], [20, 980]], "width": 3136, "height": 1000}
    _fake_claude(monkeypatch, tmp_path, "garbled")
    assert client.post("/claude-corners", files=img).status_code == 502


def test_claude_corners_timeout_kills_it(monkeypatch, tmp_path):
    import os
    import time

    import claude_corners
    _fake_claude(monkeypatch, tmp_path, "slow")
    monkeypatch.setattr(claude_corners, "TIMEOUT", 1)
    t = time.monotonic()
    assert client.post("/claude-corners", files={"image": ("a.png", _wide_png())}).status_code == 504
    assert time.monotonic() - t < 10   # not waiting for the child (it holds stdout) to end by itself
    for pid in map(int, (tmp_path / "pids").read_text().split()):   # claude and its child are gone
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    assert claude_corners._running is False
