"""Fail when recognition gets worse than the recorded baseline (TODO-035).

Runs evaluate.run on every samples/*.truth.json (not samples/external, which needs the
network) and compares each sample with accuracy_baseline.json:

  points  correct points out of 24. Each sample may be 1 below its baseline (see below),
          but the total must not go below the sum of the baselines
  bar     the bar checkers read right; must not go from ok to wrong
  home    the guess of the home side; must not go from ok to wrong
  dice    "ok" > "not read" > "WRONG"; must not go down
  cube    "ok" > "not found" > "WRONG"; must not go down

  uv run python recognizer/check_accuracy.py            # check (exit 1 on a regression)
  uv run python recognizer/check_accuracy.py --update   # rewrite the baseline with this run

With the SIMD capped below, every x86_64 machine tried reads the same (2026-10-14: the cloud's
Xeon, GitHub's AMD EPYC 7763 / 9V74 and Xeon 8370C). The 1-point slack per sample is a guard
against a machine not tried yet; the total stays strict, so a real loss still fails.
Raspberry Pi (aarch64) differs (recognizer/README.md), so don't update the baseline from a Pi run.
"""
import glob, json, os, sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# the same SIMD code on every machine of a kind (AVX2 on x86_64, plain NEON on aarch64); before cv2/numpy load
import cpu_caps  # noqa: E402,F401

BASELINE = os.path.join(HERE, "accuracy_baseline.json")
SAMPLES = os.path.join(HERE, "..", "samples")
SLACK = 1  # points a sample may lose against its baseline (the total may not)
RANK = {"dice": ["WRONG", "not read", "ok"], "cube": ["WRONG", "not found", "ok"]}


def measure(path):
    """One sample's result, as stored in the baseline."""
    sys.path.insert(0, HERE)
    import cv2
    import evaluate
    cv2.setRNGSeed(0)  # cv2.kmeans seeds from OpenCV's RNG; make each sample independent of the order
    pos, truth, wrong, bar_ok, (home_ok, _), (dice, want), (cube, cube_want) = evaluate.run(path)
    return {
        "points": 24 - len(wrong),
        "bar": bar_ok,
        "home": home_ok,
        "dice": "ok" if dice == want else "not read" if dice is None else "WRONG",
        "cube": "ok" if cube == cube_want else "not found" if cube is None else "WRONG",
    }


def measure_all(jobs=None):
    files = sorted(glob.glob(os.path.join(SAMPLES, "*.truth.json")))
    with ProcessPoolExecutor(jobs) as ex:
        results = ex.map(measure, files)
    return {os.path.basename(f).removesuffix(".truth.json"): r for f, r in zip(files, results)}


def compare(base, now):
    """(regressions, improvements, drops within the slack) as lists of messages."""
    worse, better, slack = [], [], []
    for name in sorted(set(base) | set(now)):
        if name not in now:
            worse.append(f"{name}: in the baseline but not in samples/ (run --update if it was removed on purpose)")
            continue
        if name not in base:
            # with this run's result, so a sample added on a Pi can be added from the CI's x86_64 run
            worse.append(f"{name}: not in the baseline (run --update to add it): {json.dumps(now[name])}")
            continue
        b, n = base[name], now[name]
        for key in ("points", "bar", "home", "dice", "cube"):
            rank = RANK.get(key)
            bv, nv = (rank.index(b[key]), rank.index(n[key])) if rank else (b[key], n[key])
            msg = f"{name}: {key} {b[key]} -> {n[key]}"
            if key == "points" and 0 < bv - nv <= SLACK:
                slack.append(msg)
            elif nv < bv:
                worse.append(msg)
            elif nv > bv:
                better.append(msg)
    got, was = total(now)[0], total(base)[0]
    if got < was:
        worse.append(f"total points {was} -> {got}")
    return worse, better, slack


def total(results):
    return sum(r["points"] for r in results.values()), 24 * len(results)


def main():
    now = measure_all()
    got, of = total(now)
    if "--update" in sys.argv:
        with open(BASELINE, "w") as f:
            # one line per sample, so a diff shows which sample changed
            f.write("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(v)}" for k, v in sorted(now.items())) + "\n}\n")
        print(f"wrote {os.path.relpath(BASELINE)}: {got}/{of} points")
        return 0
    with open(BASELINE) as f:
        base = json.load(f)
    worse, better, slack = compare(base, now)
    was, _ = total(base)
    print(f"points: {got}/{of} (baseline {was})")
    for m in slack:
        print(f"  within the {SLACK}-point slack: {m}")
    for m in better:
        print(f"  better: {m}")
    for m in worse:
        print(f"  WORSE:  {m}")
    if worse:
        print("Recognition got worse than recognizer/accuracy_baseline.json.")
        return 1
    if better:
        print("Better than the baseline: run with --update and commit accuracy_baseline.json"
              " (and update the table in recognizer/README.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
