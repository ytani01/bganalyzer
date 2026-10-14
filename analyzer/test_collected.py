import os

import analysis  # noqa: F401  puts recognizer/ on sys.path
import collected


def make(d, name, mtime):
    for ext in ("jpg", "truth.json"):
        p = d / f"{name}.{ext}"
        p.write_text("{}")
        os.utime(p, (mtime, mtime))


def test_keeps_misreads_and_the_newest_read_right(tmp_path, monkeypatch):
    # 4 read right (r0 oldest .. r3 newest) and 2 misread (oldest of all); keep 2 read right
    for i in range(4):
        make(tmp_path, f"user-r{i}", 1000 + i)
    for i in range(2):
        make(tmp_path, f"user-w{i}", 10 + i)
    monkeypatch.setattr(collected, "misreads", lambda p: ["point 5"] if "-w" in p.name else [])
    monkeypatch.setattr(collected, "KEEP_RIGHT", 2)
    monkeypatch.setattr(collected, "NEW", 6)
    collected.main(tmp_path)
    left = sorted(p.name for p in tmp_path.glob("user-*"))
    assert left == sorted(f"user-{n}.{e}" for n in ("r2", "r3", "w0", "w1") for e in ("jpg", "truth.json"))
    report = (tmp_path / "report.md").read_text()
    assert "## user-w0.truth.json" in report and "user-r0.truth.json" in report   # misread shown, deleted listed


def test_waits_for_new_pairs(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(collected, "misreads", lambda p: [])
    monkeypatch.setattr(collected, "KEEP_RIGHT", 0)
    for i in range(9):
        make(tmp_path, f"user-r{i}", 1000 + i)
    collected.main(tmp_path)   # 9 new: not yet
    assert len(list(tmp_path.glob("*.jpg"))) == 9 and "skip" in capsys.readouterr().out
    make(tmp_path, "user-r9", 1009)
    collected.main(tmp_path)   # 10 new: measured, and all read right beyond 0 are gone
    assert not list(tmp_path.glob("*.jpg")) and "measured" in capsys.readouterr().out
    make(tmp_path, "user-x", 2000)
    collected.main(tmp_path)   # the ones measured before don't count as new
    assert "skip: 1 new" in capsys.readouterr().out
