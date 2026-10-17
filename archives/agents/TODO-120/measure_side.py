"""TODO-120: side.py against the current detection and reading, on the photos taken from beside.
usage: uv run python archives/agents/TODO-120/measure_side.py [--mirror] [--no-current] <x.truth.json> ...

For each photo: the corners found by the current detection (corners.find_corners; its error is the least
over the four ways round, as it does not know the side) and by side.find_corners_side, as the largest
distance from the truth's corners against the photo's longer side, with the time taken; the points read
right (of 24, with the truth's corners, the better of the two colour assignments as in evaluate.py) by
the current reading (board.recognize) and by board.recognize(side=...), and by it with the corners side.find_corners_side found.
--mirror: the photo flipped left to right and read as taken from the left (the truth flipped to match:
the corners in the order the left side gives them, home on the other side).
--no-current: leave out the current detection and reading (they take most of the time)."""
import json, sys, time
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, "recognizer")
import board, corners, side

mirror = "--mirror" in sys.argv
current = "--no-current" not in sys.argv


def err(q, truth, shape):
    return max(np.hypot(*(np.float64(a) - b)) for a, b in zip(q, truth)) / max(shape[:2])


def right(pos, truth):
    flip = [-n for n in pos.points]
    return max(sum(a == b for a, b in zip(p, truth)) for p in (pos.points, flip))


def wrong(pos, truth):
    flip = [-n for n in pos.points]
    best = max((pos.points, flip), key=lambda p: sum(a == b for a, b in zip(p, truth)))
    return " ".join(f"{i + 1}:{truth[i]:+d}>{best[i]:+d}" for i in range(24) if best[i] != truth[i])


print("photo | current corners | side corners | current reading | side reading (truth corners) | side reading (found corners)")
for path in [a for a in sys.argv[1:] if not a.startswith("--")]:
    t = json.load(open(path))
    img = cv2.imread(str(Path(path).parent / t["image"]))
    truth = np.float64(t["corners_TL_TR_BR_BL"])
    home, s = t["home"], "right"
    if mirror:
        img = img[:, ::-1].copy()
        truth = np.stack([img.shape[1] - 1 - truth[:, 0], truth[:, 1]], 1)[[1, 0, 3, 2]]
        home, s = {"left": "right", "right": "left"}[home], "left"
    row = [Path(path).name.replace(".truth.json", "")]
    if current:
        t0 = time.time()
        q = corners.find_corners(img)
        dt = time.time() - t0
        row.append("not found" if q is None else
                   f"{100 * min(err(np.roll(q, k, 0), truth, img.shape) for k in range(4)):.1f}% {dt:.1f}s")
    t0 = time.time()
    q = side.find_corners_side(img, s)
    dt = time.time() - t0
    row.append("not found" if q is None else f"{100 * err(q, truth, img.shape):.1f}% {dt:.1f}s")
    if current:
        pos, _ = board.recognize(img, truth.tolist(), home=home)
        row.append(f"{right(pos, t['points'])}/24")
    t0 = time.time()
    pos, info = board.recognize(img, truth.tolist(), home=home, side=s)
    row.append(f"{right(pos, t['points'])}/24 {time.time() - t0:.1f}s")
    if q is not None:
        pos2, _ = board.recognize(img, q, home=home, side=s)
        row.append(f"{right(pos2, t['points'])}/24")
    else:
        row.append("-")
    print(" | ".join(row))
    print("    wrong (truth corners):", wrong(pos, t["points"]))
