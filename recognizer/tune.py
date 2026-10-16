"""Try the recognizer's thresholds one at a time and say which settings read the samples better (TODO-030).

For each parameter in PARAMS (a module's constant), each step (the value times 0.8, 0.9, 1.1, 1.2 by
default) is tried on every sample, and the results compared with the settings as they are: points read,
bar, home side, dice, cube and the cube's number (the same measures as check_accuracy.py). A setting is
suggested only when it reads more points and nothing gets worse on any sample. Then all the suggested
settings are tried together. Nothing in the code is changed: the report says what to change, and that
goes in as a PR like any other change to the recognizer (CLAUDE.md: the accuracy baseline).

  uv run python recognizer/tune.py                                   # samples/ (not the synthetic copies)
  uv run python recognizer/tune.py --collected collected             # and the pairs kept with 「Pi に残す」 (on the Pi)
  uv run python recognizer/tune.py --params checkers.CIRCLE_MIN_SCORE,checkers.STACK_SKEW --steps 0.9,1.1
  uv run python recognizer/tune.py --only photo2,photo3 --out tune.md

Each try reads every sample once, so the whole run is (parameters x steps + 2) readings of all the
samples: hours on the Raspberry Pi. Run it there when the photos have piled up (docs/raspi.md).
"""
from __future__ import annotations

import argparse
import ast
import glob
import importlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "..", "samples")

# module.NAME: constants read when the recognizer runs (not baked into a default argument)
PARAMS = [
    "checkers.CIRCLE_MIN_SCORE", "checkers.LONE_MIN_SCORE", "checkers.STACK_SKEW", "checkers.GAP_MIN_SCORE",
    "checkers.OUTLINE_SUPPORT", "checkers.PATTERN_SUPPORT", "checkers.PATTERN_DISTINCT", "checkers.BAR_COLOUR_TOL",
    "checkers.LONE_COLOUR_TOL", "geometry.COL_MIN_SCORE", "checkers.TEX_MIN", "checkers.TEX_HIDDEN", "checkers.TEX_SHOWN",
    "dice.PIP_CONTRAST", "cube.MIDDLE", "cube_value.SCORE_MIN", "cube_value.GAP_MIN",
]
STEPS = (0.8, 0.9, 1.1, 1.2)
KEYS = ("points", "bar", "home", "dice", "cube", "cube_value")


def default_args(module):
    """Names of the module's constants used as a default argument somewhere: changing the constant
    afterwards does not reach those functions, so they cannot be tried this way."""
    with open(os.path.join(HERE, module + ".py")) as f:
        src = f.read()
    out = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.FunctionDef, ast.Lambda)):
            for d in node.args.defaults + node.args.kw_defaults:
                for n in ast.walk(d) if d is not None else ():
                    if isinstance(n, ast.Name):
                        out.add(n.id)
    return out


def current(param):
    module, name = param.split(".")
    sys.path.insert(0, HERE)
    return getattr(importlib.import_module(module), name)


def _setup(overrides):
    """In each worker: the recognizer with these constants changed."""
    sys.path.insert(0, HERE)
    for param, value in overrides.items():
        module, name = param.split(".")
        setattr(importlib.import_module(module), name, value)


def _measure(path):
    import check_accuracy
    try:
        return check_accuracy.measure(path)
    except Exception as e:   # a setting may break a sample: count it as read wrong everywhere
        return {"points": 0, "bar": False, "home": False, "dice": "WRONG", "cube": "WRONG", "error": str(e)[:200]}


def read_all(files, overrides, jobs):
    with ProcessPoolExecutor(jobs, initializer=_setup, initargs=(overrides,)) as ex:
        return dict(zip((name_of(f) for f in files), ex.map(_measure, files)))


def name_of(path):
    base = os.path.basename(path).removesuffix(".truth.json")
    return base if os.path.dirname(os.path.abspath(path)) == os.path.abspath(SAMPLES) else "collected/" + base


def rank(key, v):
    import check_accuracy
    r = check_accuracy.RANK.get(key)
    return r.index(v) if r else v


def compare(base, now):
    """(points gained, [what got better], [what got worse]) of now against base."""
    better, worse = [], []
    gain = 0
    for name in base:
        b, n = base[name], now[name]
        for key in KEYS:
            if key not in b or key not in n:
                continue
            bv, nv = rank(key, b[key]), rank(key, n[key])
            if key == "points":
                gain += nv - bv
            if nv > bv:
                better.append(f"{name} {key} {b[key]} → {n[key]}")
            elif nv < bv:
                worse.append(f"{name} {key} {b[key]} → {n[key]}")
    return gain, better, worse


def fmt(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--params", help="comma-separated module.NAME (default: PARAMS)")
    ap.add_argument("--steps", help="comma-separated factors (default: 0.8,0.9,1.1,1.2)")
    ap.add_argument("--collected", help="a folder of pairs kept with 「Pi に残す」 (user-*.truth.json)")
    ap.add_argument("--only", help="comma-separated sample names from samples/ (default: all real ones)")
    ap.add_argument("--jobs", type=int, default=None)
    ap.add_argument("--out", default=None, help="write the report here too (Markdown)")
    a = ap.parse_args(argv)
    sys.path.insert(0, HERE)
    import collected

    params = a.params.split(",") if a.params else PARAMS
    steps = [float(s) for s in a.steps.split(",")] if a.steps else list(STEPS)
    files = []
    for f in sorted(glob.glob(os.path.join(SAMPLES, "*.truth.json"))):
        with open(f) as fh:
            t = json.load(fh)
        name = os.path.basename(f).removesuffix(".truth.json")
        if t.get("synthetic") and not (a.only and name in a.only.split(",")):
            continue   # copies of other photos with a cube pasted in: their points count twice
        if a.only and name not in a.only.split(","):
            continue
        files.append(f)
    if a.collected:
        for n in collected.names(a.collected):
            p = os.path.join(a.collected, n)
            with open(p) as fh:
                ok = collected.valid(json.load(fh))
            if ok:
                files.append(p)
    if not files:
        sys.exit("no samples")

    lines = [f"# 認識のしきい値の試し（tune.py、{time.strftime('%Y-%m-%d %H:%M')}）", "",
             f"サンプル {len(files)} 枚。1 つずつ変えて、ポイントが増え、どのサンプルのどの項目も悪くならないものを候補にする。", ""]
    print("\n".join(lines), flush=True)
    t0 = time.time()
    base = read_all(files, {}, a.jobs)
    total = sum(r["points"] for r in base.values())
    print(f"今の設定: {total}/{24 * len(files)} ポイント（{time.time() - t0:.0f} 秒）", flush=True)
    lines += [f"今の設定: **{total}/{24 * len(files)}** ポイント", "",
              "| パラメータ | 今 | 試した値 | ポイント | 良くなった | 悪くなった |", "|---|---|---|---|---|---|"]
    found = {}
    for param in params:
        module, name = param.split(".")
        if name in default_args(module):
            lines.append(f"| {param} | {fmt(current(param))} | （関数の既定値に使われていて、この方法では変えられない） | | | |")
            continue
        now_v = current(param)
        best = None
        for f in steps:
            v = type(now_v)(round(now_v * f)) if isinstance(now_v, int) else round(now_v * f, 6)
            if v == now_v:
                continue
            res = read_all(files, {param: v}, a.jobs)
            gain, better, worse = compare(base, res)
            row = f"| {param} | {fmt(now_v)} | {fmt(v)} | {gain:+d} | {len(better)} | {len(worse)} |"
            lines.append(row)
            print(row, flush=True)
            if gain > 0 and not worse and (best is None or gain > best[1]):
                best = (v, gain, better)
        if best:
            found[param] = best
    lines += ["", "## 候補", ""]
    if not found:
        lines.append("ポイントが増えて、何も悪くならない設定は無かった。今の設定のままでよい。")
    else:
        for param, (v, gain, better) in sorted(found.items(), key=lambda kv: -kv[1][1]):
            lines.append(f"- `{param}` を {fmt(current(param))} → **{fmt(v)}**（{gain:+d} ポイント）: " + "、".join(better[:8]))
        together = {p: v for p, (v, _, _) in found.items()}
        res = read_all(files, together, a.jobs)
        gain, better, worse = compare(base, res)
        lines += ["", f"全部を一緒に変えると: {gain:+d} ポイント、良くなった {len(better)}、悪くなった {len(worse)}"
                  + ("" if not worse else "（" + "、".join(worse[:8]) + "）"), "",
                  "採るときは、コードの定数を変える PR を作り、`check_accuracy.py --update` を同じ PR に入れる（CLAUDE.md）。"]
    lines.append(f"\nかかった時間: {(time.time() - t0) / 60:.0f} 分")
    report = "\n".join(lines) + "\n"
    print("\n".join(lines[lines.index("## 候補"):]))
    if a.out:
        with open(a.out, "w") as f:
            f.write(report)
    return report


if __name__ == "__main__":
    main()
