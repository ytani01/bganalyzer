"""TODO-175: 数枚の写真で、検出した四隅と盤面の読みを測る。
使い方: uv run python archives/agents/TODO-175/measure.py [名前]   （worktree の top で）
corners.py をその時点の内容で使う。案の切り替えは corners.py を直接直して流す。"""
import json
import sys

import cv2
import numpy as np

sys.path.insert(0, "recognizer")
import board  # noqa: E402
import corners as C  # noqa: E402
from position import Position  # noqa: E402

TOP = "/home/ytani/work/bganalyzer"
PHOTOS = {
    "hedmzy": f"{TOP}/collected/user-1792442165190-hedmzy",
    "galaxy-1": "samples/collected-galaxy-screen-1",
    "green-far": "samples/screen-app-green-far",
    "champions": "samples/collected-champions-screen",
}


def area(q):
    x, y = q[:, 0], q[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def iou(a, b):
    a, b = np.float32(a), np.float32(b)
    inter, _ = cv2.intersectConvexConvex(a, b)
    return inter / (area(a) + area(b) - inter)


def read(img, corners, t):
    pos, _ = board.recognize(img, corners, home=t["home"], side=t.get("side"))
    truth = Position(points=t["points"], bar_white=t["bar_white"], bar_black=t["bar_black"])
    neg = [-n for n in pos.points]
    return min(
        sum(a != b for a, b in zip(truth.points, p)) for p in (pos.points, neg)
    )


for name, p in PHOTOS.items():
    if len(sys.argv) > 1 and name not in sys.argv[1:]:
        continue
    t = json.load(open(p + ".truth.json"))
    img = cv2.imread(p + ".jpg")
    truth = np.float64(t["corners_TL_TR_BR_BL"])
    det = np.float64(C.find_corners(img))
    d = np.linalg.norm(det - truth, axis=1)
    wrong = read(img, det.tolist(), t)
    wrong_truth = read(img, truth.tolist(), t)
    print(
        f"{name:10s} iou={iou(det, truth):.4f} 四隅のずれ(px)={d.round(0).astype(int).tolist()} "
        f"誤った点数(検出の四隅)={wrong} (正解の四隅)={wrong_truth}"
    )
