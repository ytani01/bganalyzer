"""HoughCircles の結果を 2 回つなげて返し、同じ円が重なって出ても落ちないか見る。
使い方: python dup_hough.py <recognizer のディレクトリ> <truth.json ...>"""
import sys, numpy as np
rec = sys.argv[1]
sys.path.insert(0, rec)
import board, evaluate
orig = board.cv2.HoughCircles
def dup(*a, **k):
    c = orig(*a, **k)
    return None if c is None else np.concatenate([c, c], axis=1)
board.cv2.HoughCircles = dup
for p in sys.argv[2:]:
    evaluate.run(p)
    print("OK", p)
