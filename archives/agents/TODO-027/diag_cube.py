"""TODO-027 の一時的な調査: set-cube-dice のキューブが x86_64 で見つからなくなる理由（CI で動かす）。

    python diag_cube.py <recognizer のディレクトリ> [none|noshown|nohidden]
read_cube に渡る pitch・円・結果を出す。noshown / nohidden は column_texture の片方の判定を外す。"""
import os, sys
rec = os.path.abspath(sys.argv[1])
sys.path.insert(0, rec)
import check_accuracy  # noqa: F401  SIMD を AVX2 までに揃える（check_accuracy.py と同じ）
import cv2, numpy as np
import board, evaluate
mode = sys.argv[2] if len(sys.argv) > 2 else "none"
if mode != "none" and hasattr(board, "column_texture"):
    orig = board.column_texture
    drop = "shown" if mode == "noshown" else "hidden"
    board.column_texture = lambda *a: {k: v for k, v in orig(*a).items() if v != drop}
cap = {}
oc = board.cube_reader.read_cube
def wc(img, H, lay, pitch, circles=(), dice=(), debug=None):
    r = oc(img, H, lay, pitch, circles, dice, debug)
    cap.update(pitch=pitch, circles=list(circles), r=r); return r
board.cube_reader.read_cube = wc
cv2.setRNGSeed(0)
out = evaluate.run(os.path.join(rec, "..", "samples", "commons-set-cube-dice.truth.json"))
print(f"{rec} {mode}: points {24 - len(out[2])} pitch {cap['pitch']:.2f} circles {len(cap['circles'])} cube {cap['r']}")
for x, y, r, med, sc in cap["circles"]:
    if x < 60 or x > 900 or abs(y - 440) < 120:
        print(f"   circle {x:6.1f} {y:6.1f} r {r:5.1f} sc {sc:.2f}")
