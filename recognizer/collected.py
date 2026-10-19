"""Measure the pairs kept with 「サーバーに保存する」 again, and drop old ones read right (docs/raspi.md).

    uv run python recognizer/collected.py collected            # on the Pi
    uv run python recognizer/collected.py collected --force    # even without NEW new pairs

The server starts it after saving a pair, when NEW pairs came since the last time (analyzer/app.py).
Writes report.md next to the pairs, then, with BG_IMPORT set, adds the misread ones to samples/ (import_collected.py).
Pairs with a misread are kept (they are what to fix); pairs read
right are kept up to KEEP_RIGHT, the newest: they tell whether a fix makes others worse.
Anyone can send a pair (/samples is public), so a truth is used only when its fields have the expected
types, and no text from it goes into the report: names are the server's (user-<letters, digits, ->).
"""

import json
import math
import os
import re
import sys
import time
from pathlib import Path

NEW = 10  # measure again after this many new pairs
KEEP_RIGHT = 50  # pairs read right that are kept, newest first
STATE = ".measured.json"
REPORT = "report.md"
NAME = re.compile(r"user-[A-Za-z0-9-]+\.truth\.json")


def names(d):
    return sorted(
        p.name for p in Path(d).glob("*.truth.json") if NAME.fullmatch(p.name)
    )


def new_pairs(d):
    """The pairs not measured yet (a pair sent again under the same name is not new)."""
    try:
        seen = set(json.loads((Path(d) / STATE).read_text()))
    except (OSError, ValueError):
        seen = set()
    return [n for n in names(d) if n not in seen]


def valid(t):
    """Whether a truth has what evaluate.py reads, with the expected types."""

    def num(v):
        return (
            isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        )

    try:
        cube = t.get("cube")
        return (
            len(t["points"]) == 24
            and all(
                type(n) is int for n in t["points"] + [t["bar_white"], t["bar_black"]]
            )
            and t["home"] in ("left", "right")
            and Path(t["image"]).suffix in (".jpg", ".png")
            and len(t["corners_TL_TR_BR_BL"]) == 4
            and all(len(c) == 2 and all(map(num, c)) for c in t["corners_TL_TR_BR_BL"])
            and (
                t.get("dice") is None
                or (
                    len(t["dice"]) == 2
                    and all(type(n) is int and 1 <= n <= 6 for n in t["dice"])
                )
            )
            and (
                cube is None
                or (
                    isinstance(cube, dict)
                    and cube.get("at") in ("white", "black", "centre")
                )
            )
            and t.get("side", "right") in ("right", "left")
        )  # side: taken from beside the board (TODO-120)
    except Exception:
        return False


def misreads(path):
    """What the recognizer gets wrong on one pair ([]: read right), or None when the truth is not usable."""
    import evaluate  # cv2 and the recognizer: only when measuring

    try:
        if not valid(json.loads(path.read_text())):
            return None
        _, _, wrong, bar_ok, _, (dice, want), (cube, cube_want) = evaluate.run(
            str(path)
        )
        out = [f"ポイント {pt}: 正解 {a:+d}、読み {b:+d}" for pt, a, b in wrong]
        return out + [
            what
            for what, ok in (
                ("バー", bar_ok),
                ("ダイス", dice == want),
                ("キューブ", evaluate.same_cube(cube, cube_want)),
            )
            if not ok
        ]
    except Exception:
        return ["読めなかった"]


def to_delete(results, mtimes, keep):
    """The pairs read right beyond the newest `keep`."""
    right = sorted(
        (n for n, why in results.items() if why == []),
        key=lambda n: mtimes[n],
        reverse=True,
    )
    return right[keep:]


def measure(d, force=False):
    d = Path(d)
    new = new_pairs(d)
    if len(new) < NEW and not force:
        return f"skip: {len(new)} new pairs (measure at {NEW})"
    results = {n: misreads(d / n) for n in names(d)}
    gone = to_delete(results, {n: (d / n).stat().st_mtime for n in results}, KEEP_RIGHT)
    for n in gone:  # the photo and its truth.json, the way /samples names them
        for f in d.glob(n.removesuffix(".truth.json") + ".*"):
            f.unlink()
    left = {n: why for n, why in results.items() if n not in gone}
    wrong = {n: why for n, why in left.items() if why}
    bad = [n for n, why in left.items() if why is None]
    lines = [
        f"# collected/ の測り直し（{time.strftime('%Y-%m-%d %H:%M')}）",
        "",
        f"- 組: {len(left)}（新しい組 {len(new)}）。読み違いのある組 {len(wrong)}、正解の形が違う組 {len(bad)}",
        f"- 読み違いの無い古い組を {len(gone)} 消した（新しい {KEEP_RIGHT} 組を残す）",
        "",
    ]
    for n, why in wrong.items():
        lines += [f"## {n}", ""] + [f"- {w}" for w in why] + [""]
    if bad:
        lines += (
            ["## 正解の形が違う組（測っていない）", ""] + [f"- {n}" for n in bad] + [""]
        )
    (d / REPORT).write_text("\n".join(lines))
    (d / STATE).write_text(json.dumps(sorted(left)))
    if wrong and os.environ.get("BG_IMPORT"):  # the development machine only (TODO-114)
        to_samples(
            d, [n for n, why in wrong.items() if why != ["読めなかった"]]
        )  # the recognizer stops on those
    return "measured"


def to_samples(d, names):
    """Into samples/, up to the PR's merge. What it did goes to import.log."""
    import import_collected

    import_collected.run(d, names)


if __name__ == "__main__":
    print(measure(sys.argv[1], force="--force" in sys.argv))
