"""The photo shown next to the read board: the geometry the API returns, and photo.js (with Node when installed)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)
STATIC = Path(__file__).parent / "static"
SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def test_photo_script_is_served_and_cached():
    assert client.get("/photo.js").status_code == 200
    assert '<script src="photo.js"></script>' in client.get("/").text
    assert '"photo.js"' in (STATIC / "sw.js").read_text()


def test_analyze_photo_returns_geometry():
    t = json.loads((SAMPLES / "screen1.truth.json").read_text())
    corners = [v for xy in t["corners_TL_TR_BR_BL"] for v in xy]
    with open(SAMPLES / t["image"], "rb") as f:
        res = client.post("/analyze-photo", files={"image": (t["image"], f)},
                          data={"corners": ",".join(map(str, corners)), "home": t["home"],
                                "bottom_colour": str(t["bottom_colour"]), "plies": "0"})
    assert res.status_code == 200, res.text
    g = res.json()["geometry"]
    assert len(g["corners"]) == 4
    for (x, y), (tx, ty) in zip(g["corners"], t["corners_TL_TR_BR_BL"]):
        assert abs(x - tx) < 40 and abs(y - ty) < 40   # refined, but near the tapped corners
    cols = g["columns"]
    assert len(cols) == 12 and cols == sorted(cols) and 0 < cols[0] and cols[-1] < 1
    assert cols[5] < g["bar"][0] < g["bar"][1] < cols[6]
    # for the reading overlay (scan.js): triangle tips and checker circles in image pixels
    xs, ys = [x for x, _ in t["corners_TL_TR_BR_BL"]], [y for _, y in t["corners_TL_TR_BR_BL"]]
    assert isinstance(g["tips"], list) and all(min(xs) - 40 < x < max(xs) + 40 and min(ys) - 40 < y < max(ys) + 40 for x, y in g["tips"])
    ck = g["checkers"]
    assert ck and all(r > 0 and side in ("white", "black") for _, _, r, side in ck)
    assert {side for *_, side in ck} == {"white", "black"}
    # the dice read (screen1: 4 and 2) as squares in image pixels; no cube found in this one
    assert sorted(d["value"] for d in g["dice"]) == [2, 4]
    for d in g["dice"]:
        assert len(d["quad"]) == 4 and all(min(xs) < x < max(xs) and min(ys) < y < max(ys) for x, y in d["quad"])
    assert g["cube"] is None


def test_analyze_photo_returns_cube_square():
    t = json.loads((SAMPLES / "screen2.truth.json").read_text())
    corners = [v for xy in t["corners_TL_TR_BR_BL"] for v in xy]
    with open(SAMPLES / t["image"], "rb") as f:
        res = client.post("/analyze-photo", files={"image": (t["image"], f)},
                          data={"corners": ",".join(map(str, corners)), "home": t["home"],
                                "bottom_colour": str(t["bottom_colour"]), "plies": "0"})
    assert res.status_code == 200, res.text
    cube = res.json()["geometry"]["cube"]
    assert cube["at"] == "black" and len(cube["quad"]) == 4
    (x0, y0), _, (x2, y2), _ = cube["quad"]
    assert x2 > x0 and y2 > y0   # TL to BR, a square of some size


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_photo_helpers():
    script = f"""
    const p = require({json.dumps(str(STATIC / "photo.js"))});
    const quad = [[10, 20], [110, 30], [120, 90], [5, 80]];
    const h = p.homography([[0, 0], [1, 0], [1, 1], [0, 1]], quad);
    // a 4x3 image whose red channel is x * 10 + y: an identity warp gives it back
    const src = new Uint8ClampedArray(4 * 3 * 4);
    for (let y = 0; y < 3; y++) for (let x = 0; x < 4; x++) src[(y * 4 + x) * 4] = x * 10 + y;
    const id = p.homography([[0, 0], [4, 0], [4, 3], [0, 3]], [[0, 0], [4, 0], [4, 3], [0, 3]]);
    const same = Array.from(p.warp(src, 4, 3, id, 4, 3)).filter((_, i) => i % 4 === 0);
    // mapX moves the output: output column u samples source column u + 1
    const shifted = Array.from(p.warp(src, 4, 3, id, 3, 1, (x) => x + 1)).filter((_, i) => i % 4 === 0);
    const a = [[0, 0], [10, 0.5], [20, 1]];
    console.log(JSON.stringify({{
      corners: [[0, 0], [1, 0], [1, 1], [0, 1], [0.5, 0.5]].map(([x, y]) => p.apply(h, x, y)),
      same, shifted,
      interp: [p.interp(a, 0), p.interp(a, 5), p.interp(a, 15), p.interp(a, 30)],
    }}));
    """
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    for (x, y), (qx, qy) in zip(out["corners"], [[10, 20], [110, 30], [120, 90], [5, 80]]):
        assert x == pytest.approx(qx) and y == pytest.approx(qy)
    cx, cy = out["corners"][4]   # the centre lands where the diagonals cross, not at the corners' mean
    assert 10 < cx < 120 and 20 < cy < 90
    assert out["same"] == [x * 10 + y for y in range(3) for x in range(4)]
    assert out["shifted"] == [10, 20, 30]
    assert out["interp"] == pytest.approx([0, 0.25, 0.75, 1.5])


def test_scan_script_is_served_and_cached():
    assert client.get("/scan.js").status_code == 200
    assert '<script src="scan.js"></script>' in client.get("/").text
    assert '"scan.js"' in (STATIC / "sw.js").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_scan_lines():
    script = f"""
    const s = require({json.dumps(str(STATIC / "scan.js"))});
    const plain = s.layout(null);
    const fitted = s.layout({{columns: [0.04, 0.12, 0.2, 0.28, 0.36, 0.44, 0.56, 0.64, 0.72, 0.8, 0.88, 0.96], bar: [0.47, 0.53]}});
    const L = s.lines([[0, 0], [216, 0], [216, 100], [0, 100]], plain);
    console.log(JSON.stringify({{ plain, fitted, quad: L.quad, mid: L.mid, bar: L.bar, tris: L.tris, sweep: L.sweep(0.5) }}));
    """
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    p = out["plain"]
    assert len(p["cols"]) == 12 and p["cols"] == sorted(p["cols"])
    assert p["cols"][5] < p["bar"][0] < p["bar"][1] < p["cols"][6]
    assert p["bar"][1] - p["bar"][0] == pytest.approx(0.16 * p["bar"][0])   # the bar is 0.16 of a field
    assert out["fitted"]["cols"][0] == 0.04 and out["fitted"]["pw"] == pytest.approx(0.08)
    # a rectangle maps straight onto the image: 216 px wide, the board is 2 fields and a bar
    for (x, y), (qx, qy) in zip(out["quad"], [[0, 0], [216, 0], [216, 100], [0, 100]]):
        assert x == pytest.approx(qx) and y == pytest.approx(qy)
    assert [pt[1] for pt in out["mid"]] == pytest.approx([50, 50])
    assert out["bar"][0][0][0] == pytest.approx(100) and out["bar"][1][0][0] == pytest.approx(116)
    assert len(out["tris"]) == 24
    top, bottom = out["tris"][0], out["tris"][1]
    assert top[0][1] == pytest.approx(0) and top[1][1] == pytest.approx(44)       # tip at 0.44 of the height
    assert bottom[0][1] == pytest.approx(100) and bottom[1][1] == pytest.approx(56)
    assert top[1][0] == pytest.approx(100 / 12)                                    # under the first column
    assert sum(out["sweep"], []) == pytest.approx([108, 0, 108, 100])
