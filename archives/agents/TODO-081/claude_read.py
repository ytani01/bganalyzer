"""TODO-081 案 C の試し: 写真を claude -p に渡して盤面を読ませ、*.truth.json と比べる。

uv run python archives/agents/TODO-081/claude_read.py samples/<名前>.truth.json [--model M]
呼び方は analyzer/claude_corners.py と同じ（stream-json、道具なし、effort high、長辺 1568px）。
四隅は渡さない。home は truth のものを使う（アプリでは利用者が選ぶ）。駒の色は evaluate.py と同じく、合う方の割り当てで比べる。
"""
import base64, json, os, shutil, subprocess, sys, tempfile, time
import cv2

PROMPT = ("This photo shows a backgammon board, seen by a player at the bottom of the photo. "
          "Read the position. The board has 24 points (triangles): 12 along the bottom edge and 12 along the top edge, "
          "6 on each side of the bar. For each point give how many checkers stand on it and their colour "
          "(\"dark\" or \"light\", the darker or lighter of the two checker colours), or 0. Also count the checkers on the bar. "
          "Checkers stacked on a point may overlap; count every one. First, for each row, describe in one line per point what you see. "
          "Then end with one line of JSON: "
          "{\"bottom\": [12 items, left to right], \"top\": [12 items, left to right], \"bar\": {\"dark\": n, \"light\": n}} "
          "where an item is [count, \"dark\"|\"light\"] or [0, null].")


def ask(img, model):
    s = min(1, 1568 / max(img.shape[:2]))
    small = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img
    b64 = base64.b64encode(cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 90])[1]).decode()
    msg = {"type": "user", "message": {"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
        {"type": "text", "text": PROMPT}]}}
    with tempfile.TemporaryDirectory() as cwd:
        out = subprocess.run([shutil.which("claude"), "-p", "--model", model, "--input-format", "stream-json",
                              "--output-format", "stream-json", "--verbose", "--tools", "", "--no-session-persistence",
                              "--setting-sources", "", "--effort", "high"],
                             input=(json.dumps(msg) + "\n").encode(), capture_output=True, cwd=cwd, timeout=300)
    lines = [json.loads(l) for l in out.stdout.decode(errors="replace").splitlines() if l.startswith("{")]
    text = [r for r in lines if r.get("type") == "result"][-1]["result"]
    start = text.rindex('{"bottom"')
    return text, json.JSONDecoder().raw_decode(text[start:])[0]


def points(board, home, light_is_white):
    """points[i] = 手前から見たポイント i+1（正が white = 手前）。home=right なら下の段の右端が 1。"""
    bottom, top = board["bottom"], board["top"]
    if home == "right":
        order = bottom[::-1] + top          # 1..12 は下の段の右から左、13..24 は上の段の左から右
    else:
        order = bottom + top[::-1]
    sign = lambda c: (1 if (c == "light") == light_is_white else -1)
    return [n * sign(c) if n else 0 for n, c in order]


if __name__ == "__main__":
    model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "claude-sonnet-5-5"
    path = sys.argv[1]
    t = json.load(open(path))
    img = cv2.imread(os.path.join(os.path.dirname(path), t["image"]))
    t0 = time.monotonic()
    text, board = ask(img, model)
    dt = time.monotonic() - t0
    best = None
    for light_is_white in (True, False):
        p = points(board, t["home"], light_is_white)
        wrong = [(i + 1, t["points"][i], p[i]) for i in range(24) if t["points"][i] != p[i]]
        if best is None or len(wrong) < len(best):
            best = wrong
    print(f"{os.path.basename(path)}: {24 - len(best)}/24 points correct ({model}, {dt:.0f} s)")
    for pt, a, b in best:
        print(f"   point {pt:2d}: truth {a:+d}  got {b:+d}")
    print("--- answer\n" + text)
