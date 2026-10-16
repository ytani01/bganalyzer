"""TODO-071: pick the checker size and the tilt from measure_ruler.py's counts (ruler.json) and compare with the truth.

rule: for each stretch, the radius with the most upright triples (a stack); a radius about half of it with
at least half as many wins (every other checker of a tall stack is also evenly spaced). The stretch with the
most wins. usage: python analyse.py [ruler.json]
"""
import json, math, os, sys

RATIO = 13.7
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "ruler.json")))


def pick(rows, col):
    best = max(rows, key=lambda v: (v[col], -v[1]))
    half = [v for v in rows if abs(v[1] / (best[1] / 2) - 1) < 0.1 and 2 * v[col] >= best[col] and v[col] >= 3]
    return max(half, key=lambda v: v[col]) if half else best


bands = {0.1: 0, 0.2: 0}
tilt_err = []
for name, v in d.items():
    per = []
    for st in sorted({r[0] for r in v["rows"]}):
        per.append(pick([r for r in v["rows"] if r[0] == st], 3))
    st, r, kept, up, side = max(per, key=lambda x: (x[3], -x[0]))
    ratio = 2 * r * RATIO / v["width"]
    tilt = math.degrees(math.acos(1 / st))
    for b in bands:
        bands[b] += abs(ratio - 1) <= b
    tilt_err.append(abs(tilt - v["tilt"]))
    print(f"{name:28s} size {ratio:4.2f}  tilt {v['tilt']:4.1f} est {tilt:4.1f}  stacks {up:3d}  "
          + " ".join(f"{x[0]}:{x[1]:.0f}/{x[3]}" for x in per))
n = len(d)
print(f"size within 10 %: {bands[0.1]} / {n}, within 20 %: {bands[0.2]} / {n}; "
      f"tilt within 10 degrees: {sum(e <= 10 for e in tilt_err)} / {n}")
