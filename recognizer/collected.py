"""Measure the photos kept with 「Pi に残す」 again, and drop old ones that are read right (docs/raspi.md).

    python recognizer/collected.py /data/samples            # in the container (docker compose exec -T app)
    python recognizer/collected.py /data/samples --force    # measure even without 10 new pairs

Measures only when NEW or more pairs came since the last time. Writes report.md next to the pairs.
Pairs with a misread are kept (they are what to fix). Pairs read right are kept up to KEEP_RIGHT,
the newest ones: they tell whether a fix makes others worse. Prints "measured" when it measured.
"""
import json, os, sys
from datetime import datetime
from pathlib import Path

import board
import evaluate

NEW = 10           # measure again after this many new pairs
KEEP_RIGHT = 50    # pairs read right that are kept, newest first
STATE = ".measured.json"
REPORT = "report.md"


def misreads(path):
    """What the recognizer gets wrong on one pair (an empty list: read right)."""
    try:
        _, _, wrong, bar_ok, _, (dice, want), (cube, cube_want) = evaluate.run(str(path))
    except Exception as e:   # a broken pair is kept and shown, not deleted
        return [f"error: {type(e).__name__}: {e}"]
    out = [f"point {pt}: truth {a:+d}, read {b:+d}" for pt, a, b in wrong]
    if not bar_ok:
        out.append("bar")
    if dice != want:
        out.append(f"dice: truth {want}, read {dice}")
    if cube != cube_want:
        out.append(f"cube: truth {cube_want and cube_want['at']}, read {cube and cube['at']}")
    return out


def to_delete(results, keep=KEEP_RIGHT):
    """results: [(name, mtime, misreads)]. The pairs read right beyond the newest `keep`."""
    right = sorted((r for r in results if not r[2]), key=lambda r: r[1], reverse=True)
    return [name for name, _, _ in right[keep:]]


def main(d, force=False):
    d = Path(d)
    truths = sorted(d.glob("*.truth.json"))
    state = d / STATE
    seen = set(json.loads(state.read_text())) if state.exists() else set()
    new = [p.name for p in truths if p.name not in seen]
    if len(new) < NEW and not force:
        print(f"skip: {len(new)} new pairs (measure at {NEW})")
        return
    results = [(p.name, p.stat().st_mtime, misreads(p)) for p in truths]
    gone = to_delete(results, KEEP_RIGHT)
    for name in gone:   # the photo and its truth.json, the way /samples names them
        for f in d.glob(name.removesuffix(".truth.json") + ".*"):
            f.unlink()
    kept = [r for r in results if r[0] not in gone]
    wrong = [r for r in kept if r[2]]
    lines = [f"# collected/ の測り直し（{datetime.now():%Y-%m-%d %H:%M}、recognizer {board.__version__}）", "",
             f"- 組: {len(results)}（新しい組 {len(new)}）。読み違いの無い組 {len(results) - len(wrong) - len(gone)} を残し、"
             f"古い {len(gone)} を消した（上限 {KEEP_RIGHT}）",
             f"- 読み違いのある組: {len(wrong)}", ""]
    for name, _, why in wrong:
        lines.append(f"## {name}")
        lines += [f"- {w}" for w in why] + [""]
    if gone:
        lines += ["## 消した組", ""] + [f"- {n}" for n in gone] + [""]
    (d / REPORT).write_text("\n".join(lines))
    state.write_text(json.dumps(sorted(r[0] for r in kept)))
    print("measured")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(next(a for a in args if not a.startswith("--")), force="--force" in args)
