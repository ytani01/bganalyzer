# TODO-084: 24 ポイント中いくつ合うか、四隅を合わせ直す（既定）と固定するで比べる。uv run python archives/agents/TODO-084/measure_keep.py photo6 ...
import sys, functools
sys.path.insert(0, "recognizer")
import board, evaluate
orig = board.recognize
for name in sys.argv[1:]:
    row = [name]
    for keep in (False, True):
        board.recognize = functools.partial(orig, keep_corners=keep)
        pos, truth, wrong, bar_ok, *_ = evaluate.run(f"samples/{name}.truth.json", app=True)
        row.append(f"{24 - len(wrong)}{'' if bar_ok else '(bar NG)'}")
    print(*row, sep="\t")
