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
      drop: h.idsToDrop([{{id: "a", time: 1}}, {{id: "b", time: 4}}, {{id: "c", time: 3}}, {{id: "d", time: 2}}]),
      none: h.idsToDrop([{{id: "a", time: 1}}, {{id: "b", time: 2}}]),
    }};
    console.log(JSON.stringify(out));
    """
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    assert out["keep"] == 3
    assert out["big"] == pytest.approx(2048 / 4000)
    assert out["small"] == 1
    assert out["drop"] == ["a"]     # the oldest beyond the newest 3
    assert out["none"] == []


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
