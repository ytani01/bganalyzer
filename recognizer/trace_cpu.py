"""Where do two machines part in reading the samples? (TODO-046)

Reads every samples/*.truth.json like check_accuracy.py, with recognize(trace=...), and writes each
step's hash and the final reading as JSON. Run it on two machines (GitHub Actions' x86_64 and
arm64 in .github/workflows/cpu-match.yml, or a Raspberry Pi) and compare:

  uv run python recognizer/trace_cpu.py > x86.json
  uv run python recognizer/trace_cpu.py compare x86.json pi.json   # exit 1 when a reading differs

The comparison prints, for each sample that differs, the first step whose value is not the same.
"""
import glob, json, os, sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cpu_caps  # noqa: E402,F401  same SIMD on every machine; before cv2 and numpy load

SAMPLES = os.path.join(HERE, "..", "samples")


def trace_one(path):
    sys.path.insert(0, HERE)
    import cv2
    import board
    cv2.setRNGSeed(0)
    t = json.load(open(path))
    img = cv2.imread(os.path.join(os.path.dirname(path), t["image"]))
    steps = []
    pos, info = board.recognize(img, t["corners_TL_TR_BR_BL"], home=t["home"], trace=steps)
    cube = info["cube"] and info["cube"]["at"]
    return os.path.basename(path)[:-len(".truth.json")], {
        "steps": steps,
        "reading": {"points": pos.points, "bar": [pos.bar_white, pos.bar_black],
                    "dice": info["dice"]["values"], "cube": cube},
    }


def run():
    paths = sorted(glob.glob(os.path.join(SAMPLES, "*.truth.json")))
    with ProcessPoolExecutor() as ex:
        out = dict(ex.map(trace_one, paths))
    import cv2
    import numpy
    import platform
    meta = {"machine": platform.machine(), "opencv": cv2.__version__, "numpy": numpy.__version__,
            "cpu": cpu_caps.describe()}
    json.dump({"meta": meta, "samples": out}, sys.stdout, ensure_ascii=False, indent=0)


def compare(a_path, b_path):
    a, b = json.load(open(a_path)), json.load(open(b_path))
    print("A:", a["meta"])
    print("B:", b["meta"])
    differ = 0
    first_steps = {}
    for name in sorted(set(a["samples"]) | set(b["samples"])):
        sa, sb = a["samples"].get(name), b["samples"].get(name)
        if sa is None or sb is None:
            print(f"{name}: only in {'B' if sa is None else 'A'}")
            differ += 1
            continue
        same_reading = sa["reading"] == sb["reading"]
        first = next((x[0] for x, y in zip(sa["steps"], sb["steps"]) if x != y), None)
        if first is None and len(sa["steps"]) != len(sb["steps"]):
            first = "(number of steps)"
        if first is not None:
            first_steps[first] = first_steps.get(first, 0) + 1
        if not same_reading:
            differ += 1
            wrong = [i + 1 for i, (p, q) in enumerate(zip(sa["reading"]["points"], sb["reading"]["points"])) if p != q]
            print(f"{name}: reading differs (points {wrong}, bar {sa['reading']['bar']} / {sb['reading']['bar']}, "
                  f"dice {sa['reading']['dice']} / {sb['reading']['dice']}, cube {sa['reading']['cube']} / {sb['reading']['cube']}); "
                  f"first different step: {first}")
        elif first is not None:
            print(f"{name}: same reading, first different step: {first}")
    print(f"first different steps: {first_steps}")
    print(f"{differ} of {len(a['samples'])} samples read differently")
    return differ


if __name__ == "__main__":
    if sys.argv[1:2] == ["compare"]:
        sys.exit(1 if compare(sys.argv[2], sys.argv[3]) else 0)
    run()
