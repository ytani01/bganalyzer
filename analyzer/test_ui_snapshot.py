"""tools/ui_snapshot.py: comparing two recordings of the PWA (recording itself needs a browser and is run by hand)."""

import json
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))

import ui_snapshot  # noqa: E402


def test_differences_name_the_step_and_what_changed():
    a = [
        ["manual: start", {"title": "BG Analyzer", "dice": ["", ""]}],
        ["manual: dice", {"title": "盤面・設定", "dice": ["3", "1"]}],
    ]
    b = [
        ["manual: start", {"title": "BG Analyzer", "dice": ["", ""]}],
        ["manual: dice", {"title": "盤面・設定", "dice": ["3", "2"]}],
        ["manual: more", {}],
    ]
    assert ui_snapshot.differences(a, a) == []
    assert ui_snapshot.differences(a, b) == [
        ("manual: dice", "dice", ["3", "1"], ["3", "2"]),
        ("(end)", "snapshots", 2, 3),
    ]


def test_excerpt_shows_where_the_values_part():
    a, b = ui_snapshot.excerpt(
        "x" * 300 + "リード。", "x" * 300 + "リードしています。", width=20
    )
    assert a.endswith("リード。") and b.endswith("リードしています。") and len(b) <= 20


def test_compare_exits_1_on_a_difference(tmp_path):
    same, other = tmp_path / "a.json", tmp_path / "b.json"
    same.write_text(json.dumps([["s", {"title": "結果"}]]))
    other.write_text(json.dumps([["s", {"title": "盤面"}]]))
    run = lambda *f: subprocess.run(
        [sys.executable, str(TOOLS / "ui_snapshot.py"), "compare", *map(str, f)],  # noqa: E731
        capture_output=True,
        text=True,
    )
    assert run(same, same).returncode == 0
    r = run(same, other)
    assert r.returncode == 1 and "[s] title" in r.stdout and "1 differences" in r.stdout
