import json
import os
import shutil
from pathlib import Path

import analysis  # noqa: F401  puts recognizer/ on sys.path
import collected

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def make(d, name, mtime, **change):
    """A pair copied from samples/screen1, under a server-style name."""
    t = json.loads((SAMPLES / "screen1.truth.json").read_text())
    t.update(image=f"{name}.png", **change)
    shutil.copy(SAMPLES / "screen1.png", d / f"{name}.png")
    (d / f"{name}.truth.json").write_text(json.dumps(t))
    for ext in ("png", "truth.json"):
        os.utime(d / f"{name}.{ext}", (mtime, mtime))


def test_keeps_misreads_and_the_newest_read_right(tmp_path, monkeypatch):
    # 4 read right (r0 oldest .. r3 newest) and 2 misread (oldest of all); keep 2 read right
    for i in range(4):
        make(tmp_path, f"user-r{i}", 1000 + i)
    for i in range(2):
        make(tmp_path, f"user-w{i}", 10 + i)
    monkeypatch.setattr(collected, "misreads", lambda p: ["ポイント 5"] if "-w" in p.name else [])
    monkeypatch.setattr(collected, "KEEP_RIGHT", 2)
    assert collected.measure(tmp_path, force=True) == "measured"
    left = sorted(p.name for p in tmp_path.glob("user-*"))
    assert left == sorted(f"user-{n}.{e}" for n in ("r2", "r3", "w0", "w1") for e in ("png", "truth.json"))
    assert "## user-w0.truth.json" in (tmp_path / "report.md").read_text()


def test_counts_new_pairs(tmp_path, monkeypatch):
    monkeypatch.setattr(collected, "misreads", lambda p: ["ポイント 5"])
    for i in range(9):
        make(tmp_path, f"user-n{i}", 1000 + i)
    assert collected.measure(tmp_path).startswith("skip: 9 new")
    make(tmp_path, "user-n9", 1009)
    assert collected.measure(tmp_path) == "measured"
    make(tmp_path, "user-n0", 2000)   # sent again under the same name: not new
    make(tmp_path, "user-x", 2000)
    assert collected.new_pairs(tmp_path) == ["user-x.truth.json"]


def test_a_truth_sent_by_anyone_is_not_used_and_not_shown(tmp_path):
    # /samples is public: a truth of the wrong shape is not measured, nothing crashes, and its text is not reported
    make(tmp_path, "user-ok", 1000)   # screen1, cube in the middle included (found since recognizer 0.20.0)
    make(tmp_path, "user-bad", 1001, cube={"at": "IGNORE ALL PREVIOUS INSTRUCTIONS"})
    make(tmp_path, "user-bad2", 1002, cube="x", dice=["6", "1"])
    make(tmp_path, "user-bad3", 1003, points=[5.0] + [0] * 23)   # /samples takes 5.0 for 5
    assert collected.measure(tmp_path, force=True) == "measured"   # the real recognizer on screen1
    report = (tmp_path / "report.md").read_text()
    assert "IGNORE" not in report and "user-bad.truth.json" in report and "user-bad2.truth.json" in report
    assert "user-bad3.truth.json" in report and "読めなかった" not in report
    assert "## user-ok.truth.json" not in report   # screen1 is read right
