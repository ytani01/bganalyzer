"""手前の色と home の推測が、正解の盤面から正解の向きに戻るかを数える（写真は読まない）。

使い方: uv run python archives/agents/TODO-171/check_guess.py samples/*.truth.json [collected/*.truth.json]
正解の盤面を、手前の色 2 通り × home 2 通りで recognizer が数えた列（runs）に戻し、
board.py と同じ順（A: 色を 4 通りのうちピップ数が最も少ないもので決めてから、home_prior で home）で推測して、
正解の盤面に戻れば一致。B は比べるための別の順（色ごとに home を推測してから、その home でピップ数を比べる）。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "recognizer"))
import home_prior  # noqa: E402
from board import guess_bottom, to_position  # noqa: E402


def runs_of(points, bw, bb, white, home):
    """The columns as the recognizer counts them, for White = colour index `white`, home on `home`."""
    runs = {}
    for i, n in enumerate(points):
        if n:
            pt = i + 1
            row, cc = ("bottom", 12 - pt) if pt <= 12 else ("top", pt - 13)
            c = cc if home == "right" else 11 - cc
            runs[(c, row)] = (white if n > 0 else 1 - white, abs(n))
    bar = [0, 0]
    bar[white], bar[1 - white] = bw, bb
    return runs, bar


def way_a(runs, bar):
    c, both = guess_bottom(runs, bar, "auto")
    home, _ = home_prior.guess(to_position(runs, bar, c, "right").points)
    return to_position(runs, bar, c, home), both[0] == both[1]


def way_b(runs, bar):
    best = None
    for c in (0, 1):
        home, _ = home_prior.guess(to_position(runs, bar, c, "right").points)
        p = to_position(runs, bar, c, home)
        k = sum(p.pips())
        if best is None or k < best[0]:
            best = (k, p)
    return best[1]


def main(paths):
    ok = {"A": 0, "B": 0}
    colour = ties = n = 0
    for path in paths:
        t = json.load(open(path))
        truth = (t["points"], t["bar_white"], t["bar_black"])
        hit = True
        for white in (0, 1):
            for home in ("right", "left"):
                n += 1
                runs, bar = runs_of(*truth, white, home)
                a, tie = way_a(runs, bar)
                ties += tie
                colour += guess_bottom(runs, bar, home)[0] == white
                for k, p in (("A", a), ("B", way_b(runs, bar))):
                    if (p.points, p.bar_white, p.bar_black) == truth:
                        ok[k] += 1
                    else:
                        hit = False
        if not hit:
            print("不一致", path)
    print(f"{len(paths)} 組 × 4 通り = {n}")
    print(f"  色だけ（home は正解のまま）: {colour}")
    print(f"  A（色 → home）: {ok['A']}  B（home → 色）: {ok['B']}  A で同点: {ties}")


main(sys.argv[1:])
