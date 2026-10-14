"""The PWA's static files. The browser-side logic of history.js is checked with Node when it is installed."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)
STATIC = Path(__file__).parent / "static"


def test_history_script_is_served_and_cached():
    assert client.get("/history.js").status_code == 200
    assert '<script src="history.js"></script>' in client.get("/").text
    assert '"history.js"' in (STATIC / "sw.js").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_history_helpers():
    script = f"""
    const h = require({json.dumps(str(STATIC / "history.js"))});
    const out = {{
      keep: h.KEEP,
      big: h.fitScale(4000, 3000, 2048),
      small: h.fitScale(1000, 800, 2048),
      drop: h.idsToDrop([{{id: "a", time: 1}}, {{id: "b", time: 4}}, {{id: "c", time: 3}}, {{id: "d", time: 2}}], 3),
      dropDefault: h.idsToDrop(Array.from({{length: 12}}, (_, i) => ({{id: "e" + i, time: i}}))),
      none: h.idsToDrop([{{id: "a", time: 1}}, {{id: "b", time: 2}}]),
    }};
    console.log(JSON.stringify(out));
    """
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    assert out["keep"] == 10
    assert out["big"] == pytest.approx(2048 / 4000)
    assert out["small"] == 1
    assert out["drop"] == ["a"]     # the oldest beyond the newest 3
    assert out["dropDefault"] == ["e1", "e0"]   # by default the newest 10 stay
    assert out["none"] == []


def test_on_roll_label_follows_the_dice():
    # TODO-042: the label app.js rewrites ("振った人" with dice in, "次に振る人" without) is there
    assert '<span class="opt-label" id="onroll-label">次に振る人</span>' in client.get("/").text
    js = (STATIC / "app.js").read_text()
    assert 'dice ? "振った" : "次に振る"' in js and "次に振るのは" not in js


def test_moves_script_is_served_and_cached():
    assert client.get("/moves.js").status_code == 200
    assert '<script src="moves.js"></script>' in client.get("/").text
    assert '"moves.js"' in (STATIC / "sw.js").read_text()


def run_moves(expr: str):
    script = f"""
    const m = require({json.dumps(str(STATIC / "moves.js"))});
    const START = [-2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2];
    const board = (points, bw = 0, bb = 0) => ({{points, bar_white: bw, bar_black: bb}});
    console.log(JSON.stringify({expr}));
    """
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_move_parse():
    assert run_moves('m.parse("24/18/13 6/4*(2) bar/22 3/off")') == [
        {"from": 24, "to": 18, "hit": False}, {"from": 18, "to": 13, "hit": False},
        {"from": 6, "to": 4, "hit": True}, {"from": 6, "to": 4, "hit": True},
        {"from": 25, "to": 22, "hit": False}, {"from": 3, "to": 0, "hit": False},
    ]
    assert run_moves('m.parse("13/x")') is None


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_move_hops_on_the_board():
    # white (手前) 13/8 6/5 from the start: 13 is points[12] with 5 checkers, 8 has 3
    assert run_moves('m.hops(board(START), "white", "13/8 6/5")') == [
        {"from": 12, "to": 7, "fromLevel": 4, "toLevel": 3, "hit": False},
        {"from": 5, "to": 4, "fromLevel": 4, "toLevel": 0, "hit": False},
    ]
    # black (奥) counts from its own side: its 13 is points[11], its 8 is points[16]
    assert run_moves('m.hops(board(START), "black", "13/8(2)")') == [
        {"from": 11, "to": 16, "fromLevel": 4, "toLevel": 3, "hit": False},
        {"from": 11, "to": 16, "fromLevel": 3, "toLevel": 4, "hit": False},
    ]
    # double 1s, one checker four times, hitting on the way; then from the bar and bearing off
    p = [0] * 24
    p[23], p[21] = 1, -1
    assert run_moves(f'm.hops(board({p}), "white", "24/23/22*/21/20")') == [
        {"from": 23, "to": 22, "fromLevel": 0, "toLevel": 0, "hit": False},
        {"from": 22, "to": 21, "fromLevel": 0, "toLevel": 0, "hit": True},
        {"from": 21, "to": 20, "fromLevel": 0, "toLevel": 0, "hit": False},
        {"from": 20, "to": 19, "fromLevel": 0, "toLevel": 0, "hit": False},
    ]
    p = [0] * 24
    p[2], p[21] = -1, -2      # black's 22 and 3
    assert run_moves(f'm.hops(board({p}, 0, 1), "black", "bar/22 3/off")') == [
        {"from": "bar", "to": 2, "fromLevel": 0, "toLevel": 1, "hit": False},
        {"from": 21, "to": "off", "fromLevel": 1, "toLevel": 0, "hit": False},
    ]
    assert run_moves('m.hops(board(START), "white", "5/1")') is None   # no checker there


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_move_hops_from_steps():
    # the API's steps, one per die: "22/15" with 5-2 passes 17 (no hit), drawn as two arrows
    p = [0] * 24
    p[21], p[16] = 1, 0
    assert run_moves(f'm.hops(board({p}), "white", [[22, 17], [17, 15]])') == [
        {"from": 21, "to": 16, "fromLevel": 0, "toLevel": 0, "hit": False},
        {"from": 16, "to": 14, "fromLevel": 0, "toLevel": 0, "hit": False},
    ]
    # "22/17*/15": the hit on the way is on the first hop
    p[16] = -1
    assert run_moves(f'm.hops(board({p}), "white", [[22, 17], [17, 15]])')[0]["hit"] is True
    # from the bar and bearing off, for black
    p = [0] * 24
    p[2], p[21] = -1, -2
    assert run_moves(f'm.hops(board({p}, 0, 1), "black", [[25, 22], [3, 0]])') == [
        {"from": "bar", "to": 2, "fromLevel": 0, "toLevel": 1, "hit": False},
        {"from": 21, "to": "off", "fromLevel": 1, "toLevel": 0, "hit": False},
    ]
    assert run_moves('m.hops(board(START), "white", [[24, 18, 13]])') is None   # not a pair
    assert run_moves('m.hops(board(START), "white", [[5, 1]])') is None          # no checker there


def test_cube_script_is_served_and_cached():
    assert client.get("/cube.js").status_code == 200
    assert '<script src="cube.js"></script>' in client.get("/").text
    assert '"cube.js"' in (STATIC / "sw.js").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_cube_request():
    script = f"""
    const c = require({json.dumps(str(STATIC / "cube.js"))});
    console.log(JSON.stringify([
      c.request({{at: "centre", value: 2, offered: true}}, "white", null),
      c.request({{at: "white", value: 2, offered: true}}, "white", null),
      c.request({{at: "black", value: 4, offered: true}}, "black", [3, 1]),
      c.request({{at: "black", value: 4, offered: false}}, "white", null),
      c.fromRead(null), c.fromRead({{at: "black", value: 3}}),
      c.fromRead({{at: "field"}}, "white"), c.fromRead({{at: "field"}}, "black"),
    ]));
    """
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    centre, offered, with_dice, owned, none, odd, field_w, field_b = json.loads(r.stdout)
    assert centre == {"on_roll": "white", "cube_value": 1, "cube_owner": None, "doubled": False}
    # offered to 手前: 奥 doubled, so 奥 is on roll
    assert offered == {"on_roll": "black", "cube_value": 2, "cube_owner": "white", "doubled": True}
    # with dice the cube is owned, not offered
    assert with_dice == {"on_roll": "black", "cube_value": 4, "cube_owner": "black", "doubled": False}
    assert owned["doubled"] is False and owned["on_roll"] == "white"
    assert none["at"] == "centre" and odd == {"at": "black", "value": 2, "offered": True}
    # in a playing field (TODO-045): the side on roll doubled, so it is offered to the other side
    assert field_w == {"at": "black", "value": 2, "offered": True}
    assert field_b == {"at": "white", "value": 2, "offered": True}


def test_sample_script_is_served_and_cached():
    assert client.get("/sample.js").status_code == 200
    assert '<script src="sample.js"></script>' in client.get("/").text
    assert '"sample.js"' in (STATIC / "sw.js").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_sample_truth():
    script = f"""
    const s = require({json.dumps(str(STATIC / "sample.js"))});
    const START = [-2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2];
    const fixed = START.slice(); fixed[5] = 4; fixed[23] = 0;   // 3 white checkers fewer on the board
    const read = START.slice(); read[5] = 3;
    console.log(JSON.stringify({{
      name: s.baseName(new Date(2026, 9, 4, 9, 5)),
      t: s.truth({{ image: "x.jpg", corners: [[10.4, 20.6], [100, 20], [110, 90], [0, 90]], home: "left", bottomColour: 0,
                   board: {{ points: fixed, bar_white: 1, bar_black: 0 }}, dice: [5, 2],
                   cube: {{ at: "black", value: 4, offered: true }}, read: {{ points: read, bar_white: 0, bar_black: 0 }} }}),
      plain: s.truth({{ image: "y.png", corners: [[0, 0], [1, 0], [1, 1], [0, 1]], home: "right", bottomColour: 1,
                       board: {{ points: START, bar_white: 0, bar_black: 0 }}, dice: null,
                       cube: {{ at: "centre", value: 2, offered: true }}, read: null }}),
    }}));
    """
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    assert out["name"] == "user-20261004-0905"
    t = out["t"]
    assert t["corners_TL_TR_BR_BL"] == [[10, 21], [100, 20], [110, 90], [0, 90]]
    assert (t["home"], t["bottom_colour"], t["dice"]) == ("left", 0, [5, 2])
    assert (t["bar_white"], t["off_white"], t["off_black"]) == (1, 2, 0)   # 12 on the board + 1 on the bar
    assert t["cube"] == {"at": "black"} and t["cube_value"] == 4
    assert t["fixed_points"] == [6, 24]
    assert t["read"]["points"][5] == 3
    p = out["plain"]
    assert p["cube"] == {"at": "centre"} and "cube_value" not in p
    assert "read" not in p and (p["off_white"], p["off_black"]) == (0, 0)
