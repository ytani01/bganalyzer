"""TODO-082 の試し: claude -p に写真を渡して四隅を答えさせ、samples の正解とのずれと時間を測る。
uv run python archives/agents/TODO-082/try_claude.py <model> <sample>...
"""
import base64, json, subprocess, sys, tempfile, time
from pathlib import Path
import cv2

REPO = Path(__file__).resolve().parents[3]
PROMPT = ("This photo shows a backgammon board. Give the four corners of the playing area "
          "(both fields and the bar, inside the frame), as seen by the player at the bottom of the photo: "
          "top-left, top-right, bottom-right, bottom-left. Pixel coordinates in this image "
          "({w}x{h}). First, for each corner in turn, say in one line what you see there and where it is. "
          "Then end with one line of JSON: {{\"corners\": [[x,y],[x,y],[x,y],[x,y]]}}")

def ask(model, path, long=1568):
    img = cv2.imread(str(path))
    s = min(1, long / max(img.shape[:2]))
    small = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img
    h, w = small.shape[:2]
    b64 = base64.b64encode(cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 90])[1]).decode()
    msg = {"type": "user", "message": {"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
        {"type": "text", "text": PROMPT.format(w=w, h=h)}]}}
    t = time.time()
    with tempfile.TemporaryDirectory() as cwd:
        p = subprocess.run(["claude", "-p", "--model", model, "--input-format", "stream-json",
                            "--output-format", "stream-json", "--verbose", "--tools", "",
                            "--no-session-persistence", "--setting-sources", "", "--effort", "high"],
                           input=json.dumps(msg) + "\n", capture_output=True, text=True, cwd=cwd, timeout=300)
    dt = time.time() - t
    res = [json.loads(l) for l in p.stdout.splitlines() if l.startswith("{")]
    res = [r for r in res if r.get("type") == "result"][-1]
    txt = res["result"]
    c = json.loads(txt[txt.rindex('{"corners"'):txt.rindex("}") + 1])["corners"]
    return [[x / s, y / s] for x, y in c], dt, res.get("usage", {})

model = sys.argv[1]
for name in sys.argv[2:]:
    truth = json.loads((REPO / f"samples/{name}.truth.json").read_text())
    img = REPO / "samples" / truth["image"]
    c, dt, u = ask(model, img)
    longest = max(cv2.imread(str(img)).shape[:2])
    err = max(((x - a) ** 2 + (y - b) ** 2) ** .5 for (x, y), (a, b) in zip(c, truth["corners_TL_TR_BR_BL"]))
    print(f"{model} {name}: max err {err:.0f}px ({100 * err / longest:.1f}% of long side) {dt:.0f}s "
          f"in={u.get('input_tokens')}+{u.get('cache_read_input_tokens')}+{u.get('cache_creation_input_tokens')} out={u.get('output_tokens')} "
          f"corners={[[round(x), round(y)] for x, y in c]}", flush=True)
