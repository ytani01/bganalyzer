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
