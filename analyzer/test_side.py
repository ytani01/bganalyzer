"""Photos taken from beside the board (TODO-120): recognizer/side.py, the API's side and the PWA's switch.

samples/ has no photo taken from beside; photo5 was, and was turned to put the bar upright: turned back
(as archives/agents/TODO-120/raw.py does) it is one, taken from the near player's right."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "recognizer"))
import board  # noqa: E402
import check_corners  # noqa: E402
import collected  # noqa: E402
import evaluate  # noqa: E402
import import_collected  # noqa: E402
import side  # noqa: E402
from app import app  # noqa: E402

client = TestClient(app)
STATIC = Path(__file__).parent / "static"
SIZE = 2048   # the longest side the app sends


@pytest.fixture(scope="module")
def raw():
    """photo5 as taken (from the near player's right), at the size the app sends, and its truth."""
    t = json.loads((ROOT / "samples" / "photo5.truth.json").read_text())
    img = cv2.imread(str(ROOT / "samples" / t["image"]))
    h = img.shape[0]
    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    corners = np.float64([[h - 1 - y, x] for x, y in t["corners_TL_TR_BR_BL"]])
    f = SIZE / max(img.shape[:2])
    img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
    return img, corners * f, t


def _error(q, truth, img):
    return max(np.hypot(*(np.float64(a) - b)) for a, b in zip(q, truth)) / max(img.shape[:2])


def test_corners_from_the_right_and_the_left(raw):
    img, truth, _ = raw
    right = side.find_corners_side(img, "right")
    assert _error(right, truth, img) < 0.06   # 4.4% when measured (implementer-report.md)
    # from the left the board is turned half round: the same corners, each named as the far player would
    # (the photo's bottom-left is TL)
    left = side.find_corners_side(img, "left")
    assert left == [right[i] for i in (2, 3, 0, 1)]


def test_corners_keep_the_fixed_ones(raw):
    img, truth, _ = raw
    fixed = [None, [round(float(v), 1) for v in truth[1]], None, None]
    q = side.find_corners_side(img, "right", fixed=fixed)
    assert q[1] == fixed[1] and _error(q, truth, img) < 0.06
    q = side.find_corners_side(img, "left", fixed=[None, None, None, fixed[1]])   # TR from the right is BL from the left
    assert q[3] == fixed[1]


def test_reading_from_the_right_and_the_left(raw):
    img, truth, t = raw
    pos, info = board.recognize(img, truth.tolist(), home=t["home"], side="right")
    flip = [-n for n in pos.points]
    assert max(sum(a == b for a, b in zip(p, t["points"])) for p in (pos.points, flip)) >= 20   # 22 when measured
    assert info["side"] == "right" and info["warnings"] == []   # not told to take it again from above
    g = info["geometry"]
    for (x, y), (tx, ty) in zip(g["corners"], truth):   # the playing area drawn where the corners are
        assert abs(x - tx) < 1 and abs(y - ty) < 1
    assert len(g["columns"]) == 12 and g["checkers"] and g["counts"]
    # the same photo read as taken from the left, with its corners named so: the board turned half
    # round, so the near player's point p is the far player's p + 12
    left, linfo = board.recognize(img, truth[[2, 3, 0, 1]].tolist(), home=t["home"], side="left")
    assert left.points == [pos.points[(i + 12) % 24] for i in range(24)]
    # what the app draws over the photo is where the corners say, from the left too (side.py turns H half round)
    for (x, y), (tx, ty) in zip(linfo["geometry"]["corners"], truth[[2, 3, 0, 1]]):
        assert abs(x - tx) < 1 and abs(y - ty) < 1
    first = lambda g: np.float64([c[:2] for c in g["checkers"]])   # noqa: E731 (the same circles, in the photo)
    assert np.allclose(np.sort(first(linfo["geometry"]), 0), np.sort(first(info["geometry"]), 0), atol=1)


def test_api_find_corners_takes_the_side(raw):
    img, _, _ = raw
    jpg = cv2.imencode(".jpg", img)[1].tobytes()
    res = client.post("/find-corners", files={"image": ("b.jpg", jpg)}, data={"side": "left", "stream": "true"})
    events = [json.loads(line) for line in res.text.splitlines()]
    assert [e["stage"] for e in events] == ["uprights", "edges", "candidates", "corners", "done"]
    found = events[-1]["result"]["corners"]
    assert found == side.find_corners_side(cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR), "left")
    assert events[-2]["corners"] == found   # the stage names the corners as the result does
    assert client.post("/find-corners", files={"image": ("b.jpg", jpg)}, data={"side": "up"}).status_code == 422


def test_api_find_corners_finds_the_side(raw):
    """Not said to be taken from beside (TODO-134): the normal search scores low, so it is looked for from
    beside too, and found from the right, named so."""
    img, _, _ = raw
    jpg = cv2.imencode(".jpg", img)[1].tobytes()
    res = client.post("/find-corners", files={"image": ("b.jpg", jpg)}, data={"stream": "true"})
    events = [json.loads(line) for line in res.text.splitlines()]
    found = events[-1]["result"]
    assert found["side"] == "right"
    assert found["corners"] == side.find_corners_side(cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR), "right")
    assert events[-2] == {"stage": "corners", "corners": found["corners"]}   # the last corners shown are the answer
    # looking again (fixed) is done the normal way: not turned to beside
    fixed = [found["corners"][0], None, None, None]
    assert client.post("/find-corners", files={"image": ("b.jpg", jpg)}, data={"fixed": json.dumps(fixed)}).json()["side"] is None


@pytest.mark.parametrize("sent, passed", [({"side": "left"}, "left"), ({"side": ""}, None), ({}, None)])
def test_api_analyze_photo_passes_the_side(monkeypatch, sent, passed):
    seen = {}

    def recognize(img, corners, **kw):
        seen.update(kw)
        raise RuntimeError("stop here")
    monkeypatch.setattr(board, "recognize", recognize)
    png = cv2.imencode(".png", np.zeros((40, 40, 3), np.uint8))[1].tobytes()
    data = {"corners": "0,0,39,0,39,39,0,39"} | sent
    with pytest.raises(RuntimeError, match="stop here"):
        client.post("/analyze-photo", files={"image": ("s.png", png, "image/png")}, data=data)
    assert seen["side"] == passed
    bad = client.post("/analyze-photo", files={"image": ("s.png", png, "image/png")}, data=data | {"side": "up"})
    assert bad.status_code == 422


def test_pwa_switch():
    html = client.get("/").text
    corners = html[html.index('<section id="corners"'):html.index('<section id="board"')]
    assert '<input type="checkbox" id="side-mode"> 横から撮った' in corners
    assert 'data-name="sideFrom"' in corners and 'data-value="right">右から' in corners and 'data-value="left">左から' in corners
    js = (STATIC / "app.js").read_text()
    # kept on the phone for the next photo: the mode, and the side once chosen (asked only until then)
    assert 'const storedSide = () => ({ sideMode: stored("sideMode", ["on", "off"], "off") === "on",' in js
    assert 'sideFrom: stored("sideFrom", ["right", "left"], "") });' in js
    assert 'keep("sideMode", on ? "on" : "off");' in js and 'keep("sideFrom", v);' in js
    assert '$("side-ask").hidden = !!s.sideFrom;' in js and '$("side-from-row").hidden = !s.sideMode;' in js
    # sent with the search for the corners and with the reading, only while on and the side is chosen
    assert js.count('if (sideSent()) fd.append("side", sideSent());') == 2
    assert "const sideSent = () => (state.sideMode && state.sideFrom) || null;" in js
    assert "sideFrom: setSideFrom," in js


def test_pwa_keeps_the_way_with_each_photo():
    js = (STATIC / "app.js").read_text()
    assert "sideMode: s.sideMode, sideFrom: s.sideFrom," in js   # in the photo history's record
    # reopened: the way kept with the photo, before the phone's; a new photo: the phone's
    assert "...(kept ? { sideMode: !!kept.sideMode, sideFrom: kept.sideFrom || storedSide().sideFrom } : storedSide())," in js


def test_pwa_switching_keeps_the_corners_put_in_place():
    js = (STATIC / "app.js").read_text()
    body = js[js.index("function cornersAgain(was) {"):js.index("// The switch kept on this phone")]
    assert "was === sideSent()) return;" in body
    assert "corners: BgCornersView.renamed(state.corners, was, sideSent())," in body
    assert "cornersFixed: BgCornersView.renamed(state.cornersFixed, was, sideSent()) });\n    findAgain();" in body
    assert js.count("const was = sideSent();") == 2 and js.count("cornersAgain(was);") == 2
    # Claude's corners (the near player at the photo's bottom) named as this photo was taken
    assert "corners = BgCornersView.renamed(data.corners.map(([x, y]) => [x / scale, y / scale]), null, sideSent());" in js


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_corners_renamed_for_the_way_the_photo_was_taken():
    script = f"""
    const v = require({json.dumps(str(STATIC / "corners-view.js"))});
    const P = ["tl", "tr", "br", "bl"];   // the photo's top-left, top-right, ... as named from the photo's bottom
    console.log(JSON.stringify([v.renamed(P, null, "right"), v.renamed(P, null, "left"),
                                v.renamed(v.renamed(P, null, "right"), "right", "left"),
                                v.renamed(v.renamed(P, null, "left"), "left", null)]));
    """
    out = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    assert out[0] == ["tr", "br", "bl", "tl"]   # from the right: the photo's top-right is TL
    assert out[1] == ["bl", "tl", "tr", "br"]   # from the left: its bottom-left
    assert out[2] == out[1] and out[3] == ["tl", "tr", "br", "bl"]


# ---- the samples collected keep the way the photo was taken

@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_sample_truth_has_the_side_only_from_beside():
    base = {"image": "a.jpg", "corners": [[0, 0], [1, 0], [1, 1], [0, 1]], "home": "right", "bottomColour": 1,
            "board": {"points": [0] * 24, "bar_white": 0, "bar_black": 0}}
    script = f"""
    const S = require({json.dumps(str(STATIC / "sample.js"))});
    const b = {json.dumps(base)};
    console.log(JSON.stringify([S.truth({{ ...b, side: "left" }}), S.truth({{ ...b, side: null }})]));
    """
    left, plain = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    assert left["side"] == "left" and "side" not in plain
    js = (STATIC / "app.js").read_text()
    assert "dice: diceIn(), cube: state.cube, read: state.read, side: sideSent()," in js


def test_samples_api_checks_the_side(monkeypatch, tmp_path):
    monkeypatch.setenv("BG_SAMPLES_DIR", str(tmp_path))
    truth = {"image": "x.jpg", "corners_TL_TR_BR_BL": [[0, 0], [10, 0], [10, 10], [0, 10]], "home": "right",
             "bottom_colour": 1, "points": [0] * 24, "bar_white": 0, "bar_black": 0}
    img = {"image": ("a.jpg", b"jpg", "image/jpeg")}
    r = client.post("/samples", data={"id": "1-a", "truth": json.dumps(truth | {"side": "left"})}, files=img)
    assert r.status_code == 200 and json.loads((tmp_path / "user-1-a.truth.json").read_text())["side"] == "left"
    r = client.post("/samples", data={"id": "1-b", "truth": json.dumps(truth | {"side": "up"})}, files=img)
    assert r.status_code == 422


def test_collected_checks_and_keeps_the_side():
    t = json.loads((ROOT / "samples" / "screen1.truth.json").read_text())
    assert collected.valid(t) and collected.valid(t | {"side": "right"}) and collected.valid(t | {"side": "left"})
    assert not collected.valid(t | {"side": "up"}) and not collected.valid(t | {"side": None})
    assert import_collected.clean(t | {"side": "left"})["side"] == "left"
    assert "side" not in import_collected.clean(t)


def test_measured_from_beside_when_the_truth_says(monkeypatch, tmp_path, raw):
    img, truth, t = raw
    cv2.imwrite(str(tmp_path / "s.jpg"), img)
    (tmp_path / "s.truth.json").write_text(json.dumps(t | {"image": "s.jpg", "corners_TL_TR_BR_BL": truth.tolist(), "side": "left"}))
    seen = []
    real = board.recognize
    monkeypatch.setattr(board, "recognize", lambda *a, **kw: (seen.append(kw.get("side")), real(*a, **kw))[1])
    evaluate.run(str(tmp_path / "s.truth.json"))   # what check_accuracy.py and collected.py measure with
    looked = []
    monkeypatch.setattr(side, "find_corners_side", lambda img, s, **kw: looked.append(s))
    check_corners.measure(str(tmp_path / "s.truth.json"))
    assert seen == ["left"] and looked == ["left"]
