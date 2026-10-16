# 一時の確認用: board.fit_columns を包み、呼び出しの reach と cols を表示してから evaluate.py を走らせる
import runpy, sys
REPO = "/home/ytani/work/bganalyzer"
sys.path.insert(0, REPO + "/recognizer")
import board
import geometry

orig = board.fit_columns
calls = []

def wrapped(ground, lay, m, reach=1.2):
    out = orig(ground, lay, m, reach)
    calls.append((reach, out))
    if len(calls) == 1:  # 1 回目の呼び出し（reach=1.2）
        print(f"[probe] call#1 reach={reach} a={out.a:.3f} bar={out.bar:.3f}", file=sys.stderr)
        print(f"[probe] cols[:6]={[round(v,1) for v in out.cols[:6]]}", file=sys.stderr)
        print(f"[probe] cols[6:]={[round(v,1) for v in out.cols[6:]]}", file=sys.stderr)
    return out

board.fit_columns = wrapped
sys.argv = ["evaluate.py", REPO + "/samples/photo6.truth.json"]
runpy.run_path(REPO + "/recognizer/evaluate.py", run_name="__main__")
print(f"[probe] fit_columns calls={len(calls)}", file=sys.stderr)
