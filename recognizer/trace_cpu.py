"""Does this machine read every sample exactly like the others? (TODO-046)

Reads every samples/*.truth.json with recognize(trace=...), which records a hash of each step's
value, and guesses its corners (corners.find_corners), and compares the hashes, the readings and
the corners with recognizer/cpu_reference.json.
The recognizer works only in integers and in float operations that round the same everywhere
(recognizer/exact.py), so x86_64, GitHub's arm64 runners and the Raspberry Pi must all match it.

  uv run python recognizer/trace_cpu.py check            # exit 1 when a step or a reading differs
  uv run python recognizer/trace_cpu.py --update         # rewrite the reference (after changing recognizer/)
  uv run python recognizer/trace_cpu.py > mine.json      # the hashes and readings as JSON
  uv run python recognizer/trace_cpu.py compare a.json b.json

For each sample that differs, the first step whose value is not the same is printed: that is where
to look for an operation that rounds differently on this CPU.
"""
import glob, json, os, platform, sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "..", "samples")
REFERENCE = os.path.join(HERE, "cpu_reference.json")


def trace_one(path):
    sys.path.insert(0, HERE)
    import cv2
    import board
    t = json.load(open(path))
    img = cv2.imread(os.path.join(os.path.dirname(path), t["image"]))
    import corners
    steps = []
    pos, info = board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"], trace=steps)
    cube = info["cube"] and info["cube"]["at"]
    return os.path.basename(path)[:-len(".truth.json")], {
        "steps": [list(s) for s in steps],
        "reading": {"points": pos.points, "bar": [pos.bar_white, pos.bar_black],
                    "dice": info["dice"]["values"], "cube": cube,
                    "corners": corners.find_corners(img)},   # the app's first guess of the corners (TODO-028)
    }


def run():
    paths = sorted(glob.glob(os.path.join(SAMPLES, "*.truth.json")))
    with ProcessPoolExecutor() as ex:
        out = dict(ex.map(trace_one, paths))
    import cv2
    import numpy
    sys.path.insert(0, HERE)
    import board
    meta = {"machine": platform.machine(), "recognizer": board.__version__, "opencv": cv2.__version__,
            "numpy": numpy.__version__, "cpu": cv2.getCPUFeaturesLine()}
    return {"meta": meta, "samples": out}


def compare(a, b):
    """Print the differences between two runs; the number of samples read differently."""
    print("A:", a["meta"])
    print("B:", b["meta"])
    differ, first_steps = 0, {}
    for name in sorted(set(a["samples"]) | set(b["samples"])):
        sa, sb = a["samples"].get(name), b["samples"].get(name)
        if sa is None or sb is None:
            print(f"{name}: only in {'B' if sa is None else 'A'}")
            differ += 1
            continue
        first = next((x[0] for x, y in zip(sa["steps"], sb["steps"]) if x != y), None)
        if first is None and len(sa["steps"]) != len(sb["steps"]):
            first = "(number of steps)"
        if first is not None:
            first_steps[first] = first_steps.get(first, 0) + 1
        ra, rb = sa["reading"], sb["reading"]
        if ra != rb:
            differ += 1
            wrong = [i + 1 for i, (p, q) in enumerate(zip(ra["points"], rb["points"])) if p != q]
            print(f"{name}: reading differs (points {wrong}, bar {ra['bar']} / {rb['bar']}, dice {ra['dice']} / {rb['dice']}, "
                  f"cube {ra['cube']} / {rb['cube']}, corners {ra.get('corners')} / {rb.get('corners')}); first different step: {first}")
        elif first is not None:
            print(f"{name}: same reading, first different step: {first}")
    print(f"first different steps: {first_steps}")
    print(f"{differ} of {len(a['samples'])} samples read differently")
    return differ, first_steps


def main(argv):
    if argv[:1] == ["compare"]:
        differ, steps = compare(json.load(open(argv[1])), json.load(open(argv[2])))
        return 1 if differ or steps else 0
    mine = run()
    if argv[:1] == ["--update"]:
        with open(REFERENCE, "w") as f:
            json.dump(mine, f, ensure_ascii=False, indent=0)
            f.write("\n")
        print(f"wrote {REFERENCE}: {len(mine['samples'])} samples")
        return 0
    if argv[:1] == ["check"]:
        ref = json.load(open(REFERENCE))
        if ref["meta"]["recognizer"] != mine["meta"]["recognizer"]:
            print(f"the reference is for recognizer {ref['meta']['recognizer']}, this is {mine['meta']['recognizer']}: "
                  "run with --update and commit it")
        differ, steps = compare(ref, mine)
        if differ or steps:
            print("This machine does not read like the reference (A). If recognizer/ was changed on purpose, "
                  "run with --update and commit recognizer/cpu_reference.json; otherwise an operation rounds "
                  "differently on this CPU (recognizer/exact.py).")
            return 1
        print("same as the reference: every step of every sample")
        return 0
    json.dump(mine, sys.stdout, ensure_ascii=False, indent=0)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
