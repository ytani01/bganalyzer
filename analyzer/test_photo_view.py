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
    # the dice read (screen1: 4 and 2) and the cube in the middle (found since recognizer 0.20.0) as squares in image pixels
    assert sorted(d["value"] for d in g["dice"]) == [2, 4]
    for d in g["dice"]:
        assert len(d["quad"]) == 4 and all(min(xs) < x < max(xs) and min(ys) < y < max(ys) for x, y in d["quad"])
    assert g["cube"]["at"] == "centre" and len(g["cube"]["quad"]) == 4


def test_analyze_photo_streams_the_stages():
    t = json.loads((SAMPLES / "screen2.truth.json").read_text())
    corners = ",".join(str(v) for xy in t["corners_TL_TR_BR_BL"] for v in xy)
    data = {"corners": corners, "home": t["home"], "bottom_colour": str(t["bottom_colour"]), "plies": "0"}
    with open(SAMPLES / t["image"], "rb") as f:
        res = client.post("/analyze-photo", files={"image": (t["image"], f)}, data=data | {"stream": "true"})
    assert res.status_code == 200 and res.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in res.text.splitlines()]
    assert [e["stage"] for e in events] == ["fit"] * 4 + ["tips", "checkers", "counts", "dice", "cube", "done"]
    fits = [e for e in events if e["stage"] == "fit"]
    assert [(f["by"], f["round"]) for f in fits] == [("edges", 1), ("edges", 2), ("triangles", 1), ("triangles", 2)]
    assert all(len(f["corners"]) == 4 and len(f["columns"]) == 12 for f in fits)
    by = {e["stage"]: e for e in events}
    assert len(by["checkers"]["columns"]) == 12
    assert sorted(d["value"] for d in by["dice"]["dice"]) == [4, 5] and by["cube"]["cube"]["at"] == "black"
    result = by["done"]["result"]
    assert result["dice_read"] == [5, 4]
    # the counts by the points add up to the board read
    counts, rec = by["counts"]["counts"], result["recognized"]
    assert sum(c["n"] for c in counts if c["side"] == "white") == sum(n for n in rec["points"] if n > 0) + rec["bar_white"]
    assert sum(c["n"] for c in counts if c["side"] == "black") == -sum(n for n in rec["points"] if n < 0) + rec["bar_black"]
    assert result["geometry"]["counts"] == counts   # the same as without streaming
    with open(SAMPLES / t["image"], "rb") as f:
        plain = client.post("/analyze-photo", files={"image": (t["image"], f)}, data=data).json()
    assert plain["recognized"] == result["recognized"] and plain["geometry"] == result["geometry"]
    assert fits[-1]["corners"] == result["geometry"]["corners"]   # the last round is where it ended up


def test_find_corners_streams_the_stages():
    with open(SAMPLES / "photo3.jpg", "rb") as f:
        body = f.read()
    res = client.post("/find-corners", files={"image": ("photo3.jpg", body)}, data={"stream": "true"})
    assert res.status_code == 200 and res.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in res.text.splitlines()]
    assert [e["stage"] for e in events] == ["edges", "uprights", "candidates", "corners", "done"]
    by = {e["stage"]: e for e in events}
    assert len(by["edges"]["lines"]) >= 2 and by["uprights"]["lines"]
    assert all(len(line) == 2 for line in by["edges"]["lines"] + by["uprights"]["lines"])
    quads = by["candidates"]["quads"]
    assert quads and all(len(q) == 4 for q in quads)
    result = by["done"]["result"]
    assert by["corners"]["corners"] == result["corners"]
    plain = client.post("/find-corners", files={"image": ("photo3.jpg", body)}).json()
    assert plain == result   # the same as without streaming
    h, w = plain["height"], plain["width"]
    assert all(-0.2 * w < x < 1.2 * w and -0.2 * h < y < 1.2 * h for q in quads for x, y in q)   # image pixels


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_stage_times_are_in_one_table():
    script = f"""
    const s = require({json.dumps(str(STATIC / "scan.js"))});
    console.log(JSON.stringify({{ ms: s.STAGE_MS, dflt: s.DEFAULT_STAGE_MS }}));
    """
    out = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)
    stages = {"edges", "uprights", "candidates", "corners", "fit", "board", "tips", "checkers", "counts", "dice", "cube"}
    assert set(out["ms"]) == stages
    assert set(out["ms"].values()) == {1000} and out["dflt"] == 1000   # one second each (2026-10-15)


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


# Runs scan.js in Node with a canvas that only records what is drawn, frame by frame (16 ms).
_SCAN_HARNESS = """
const path = process.argv[1];
let now = 0; const queue = [];
global.performance = { now: () => now };
global.requestAnimationFrame = (f) => { queue.push(f); return queue.length; };
global.cancelAnimationFrame = () => {};
const texts = new Set();
const ctx = new Proxy({}, { get: (o, k) => k === "measureText" ? () => ({ width: 10 }) : k in o ? o[k] : () => {},
                            set: (o, k, v) => { o[k] = v; return true; } });
ctx.fillText = (t) => texts.add(String(t));
global.document = { createElement: () => ({ getContext: () => ctx, width: 0, height: 0 }) };
const canvas = { width: 800, height: 400, clientWidth: 800, isConnected: true, offsetParent: {}, getContext: () => ctx };
const s = require(path);
async function run(ms) { const end = now + ms; while (now < end) { now += 16; queue.splice(0).forEach((f) => f(now)); await null; } }
const C = [[5, 5], [795, 5], [795, 395], [5, 395]];
const frame = { corners: C, columns: [0.04,0.12,0.2,0.28,0.36,0.44,0.56,0.64,0.72,0.8,0.88,0.96], bar: [0.47, 0.53] };
async function go(mode, events) {
  const sc = s.start(canvas, { mode, corners: C, reduced: false, prepare: () => (p) => p });
  const seen = [];
  await run(300);
  events.forEach((e) => sc.push(e));   // all at once: they are queued and shown in turn
  let doneAt = null; const t0 = now;
  sc.done().then(() => { doneAt = now - t0; });
  for (let k = 0; k < 2000 && doneAt === null; k++) {
    await run(16);
    const st = sc.stage();
    if (st && seen[seen.length - 1] !== st) seen.push(st);
  }
  sc.stop();
  return { seen, doneAt };
}
(async () => {
  const corners = await go("corners", [
    { stage: "edges", lines: [[[0, 5], [800, 5]], [[0, 395], [800, 395]]] },
    { stage: "uprights", lines: [[[5, 5], [5, 395]]] },
    { stage: "candidates", quads: [C] },
    { stage: "corners", corners: C }]);
  s.STAGE_MS.fit = 300;   // one stage made shorter
  const reading = await go(undefined, [
    { stage: "fit", ...frame, by: "edges", round: 1 }, { stage: "fit", ...frame, by: "triangles", round: 1 },
    { stage: "tips", tips: [[10, 10]] }, { stage: "checkers", ...frame, checkers: [[50, 50, 10, "white"]] },
    { stage: "counts", counts: [{ at: [50, -5], n: 13, side: "black" }] },
    { stage: "dice", dice: [{ quad: [[400, 180], [420, 180], [420, 200], [400, 200]], value: 5 }] },
    { stage: "cube", cube: null }]);
  console.log(JSON.stringify({ corners, reading, texts: [...texts] }));
})();
"""


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_overlays_show_stages_in_turn_with_only_numbers():
    r = subprocess.run(["node", "-e", _SCAN_HARNESS, str(STATIC / "scan.js")], capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    assert out["corners"]["seen"] == ["edges", "uprights", "candidates", "corners"]
    assert out["corners"]["doneAt"] == pytest.approx(4000, abs=50)            # 1 s each
    assert out["reading"]["seen"] == ["fit", "tips", "checkers", "counts", "dice", "cube"]
    assert out["reading"]["doneAt"] == pytest.approx(2 * 300 + 5 * 1000, abs=80)   # fit made 0.3 s
    # no words on the photo: only the numbers counted and the dice read (ai1, 2026-10-15)
    assert out["texts"] and all(t.isdigit() for t in out["texts"])
    assert set(out["texts"]) == {"13", "5"}
