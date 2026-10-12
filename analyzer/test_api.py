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
    samples = Path(__file__).resolve().parent.parent / "samples"
    for f in samples.glob("*.truth.json"):
        t = json.loads(f.read_text())
        shape = cv2.imread(str(samples / t["image"])).shape
        assert view_tilt_deg(t["corners_TL_TR_BR_BL"], shape) < OBLIQUE_WARN_DEG, f.name


def test_version_reports_both_parts_and_commit():
    import subprocess

    import board
    import app as app_module
    v = client.get("/version").json()
    assert v["analyzer"] == app_module.__version__
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
