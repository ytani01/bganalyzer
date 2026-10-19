"""正解ファイルの向きが、両者のピップ数の合計が最も少ない向きと一致するかを数える。

使い方: uv run python archives/agents/TODO-170/check_pips.py samples/*.truth.json [collected/*.truth.json]
4 通りの向き（色 × home）のうち合計が最小のものが、正解の向き（そのまま）と一致すれば一致。
"""

import json
import sys


def pips(points, bar_white, bar_black):
    w = sum((i + 1) * n for i, n in enumerate(points) if n > 0) + 25 * bar_white
    b = sum((24 - i) * -n for i, n in enumerate(points) if n < 0) + 25 * bar_black
    return w + b


def mirror(points):  # home の左右を入れ替える（行の中で左右を反転）
    return [
        points[12 - 1 - i] if i < 12 else points[36 - 1 - i] for i in range(24)
    ]


def main(paths):
    ok = col = 0
    for p in paths:
        t = json.load(open(p))
        pts, bw, bb = t["points"], t["bar_white"], t["bar_black"]
        neg = [-n for n in pts]
        cand = {  # (色を入れ替え, home を入れ替え)
            (0, 0): pips(pts, bw, bb),
            (1, 0): pips(neg, bb, bw),
            (0, 1): pips(mirror(pts), bw, bb),
            (1, 1): pips(mirror(neg), bb, bw),
        }
        col += cand[(0, 0)] <= cand[(1, 0)]
        best = min(cand, key=cand.get)
        ties = [k for k in cand if cand[k] == cand[best]]
        if best == (0, 0) and len(ties) == 1:
            ok += 1
        else:
            print("不一致", p, best, cand)
    print(f"色だけ 2 通り（同じなら一致）: {col} / {len(paths)}")
    print(f"色 × home の 4 通り（同じ最小が複数あれば不一致）: {ok} / {len(paths)}")


main(sys.argv[1:])
