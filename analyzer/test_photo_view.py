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
