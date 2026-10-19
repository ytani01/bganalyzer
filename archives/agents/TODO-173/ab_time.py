"""Time the reading (corners fixed to the truth's) of two recognizer/ versions, taking turns (TODO-173).

usage: uv run python archives/agents/TODO-173/ab_time.py OLD_DIR ROUNDS samples/x.truth.json ...

OLD_DIR: the old recognizer/, e.g. `mkdir old && git archive origin/main recognizer | tar -x -C old`
then OLD_DIR=old/recognizer. The two versions cannot share one process (their modules have the same
names), so each runs in its own worker process that stays up; the samples go to them in turn, and each
one's fastest time per sample is kept. same= says whether the two readings were the same.
"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NEW_DIR = os.path.join(HERE, "..", "..", "..", "recognizer")


def worker(src):
    sys.path.insert(0, HERE)
    os.environ["RECOGNIZER"] = src
    import record_reading
    import board

    assert os.path.dirname(os.path.abspath(board.__file__)) == src, board.__file__

    for line in sys.stdin:
        out, dt = record_reading.read(line.strip())
        h = hashlib.sha1(json.dumps(out, sort_keys=True).encode()).hexdigest()
        print(json.dumps({"seconds": dt, "hash": h}), flush=True)


def main(old_dir, rounds, files):
    procs = {
        label: subprocess.Popen(
            [sys.executable, __file__, "--worker", os.path.abspath(d)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        for label, d in (("old", old_dir), ("new", NEW_DIR))
    }

    def ask(label, f):
        p = procs[label]
        p.stdin.write(os.path.abspath(f) + "\n")
        p.stdin.flush()
        return json.loads(p.stdout.readline())

    total = {"old": 0.0, "new": 0.0}
    for f in files:
        name = os.path.basename(f).replace(".truth.json", "")
        best, hashes = {}, {}
        for _ in range(rounds):
            for label in ("old", "new"):
                r = ask(label, f)
                best[label] = min(best.get(label, r["seconds"]), r["seconds"])
                hashes[label] = r["hash"]
        for label in total:
            total[label] += best[label]
        same = hashes["old"] == hashes["new"]
        print(f"{name:32s} {best['old']:6.2f}s -> {best['new']:6.2f}s  same={same}")
    print(f"total {total['old']:.2f}s -> {total['new']:.2f}s")
    for p in procs.values():
        p.stdin.close()
        p.wait()


if __name__ == "__main__":
    if sys.argv[1] == "--worker":
        worker(sys.argv[2])
    else:
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3:])
