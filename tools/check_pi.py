"""Check the Pi's public server from anywhere (the cloud included): version, static files, and
the reading of a few public sample photos, compared with this checkout and the truth.

    uv run python tools/check_pi.py                      # https://bg.tail5c266.ts.net/bg/
    uv run python tools/check_pi.py --all URL            # every samples/*.truth.json

Read-only: it never calls /samples (which would save a photo on the Pi). It sends only the
photos in samples/, which are public in this repository, and analyzes at 0-ply to keep the
Pi's load small.
"""

import json
import subprocess
import sys
import urllib.request
import uuid
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "recognizer"))
import board  # noqa: E402
from evaluate import shrink_like_app  # noqa: E402

DEFAULT_URL = "https://bg.tail5c266.ts.net/bg/"
DEFAULT_SAMPLES = [
    "photo-blue-red-top",
    "photo-green-felt-top",
    "photo-carved-brown-top",
    "screen-app-grey-shot",
    "screen-app-green-far",
]
STATIC = ["", "app.js", "style.css", "sw.js", "manifest.webmanifest", "sample.js"]


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.status, r.read()


def post_photo(url, fields, image):
    b = uuid.uuid4().hex
    body = b"".join(
        f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for k, v in fields.items()
    )
    body += (
        (
            f'--{b}\r\nContent-Disposition: form-data; name="image"; filename="p.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode()
        + image
        + f"\r\n--{b}--\r\n".encode()
    )
    req = urllib.request.Request(
        url, body, {"Content-Type": f"multipart/form-data; boundary={b}"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def git(*args):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True
    ).stdout.strip()


def check_version(base):
    v = json.loads(get(base + "version")[1])
    print(
        f"Pi: analyzer {v['analyzer']}, recognizer {v['recognizer']}, commit {v['commit']}, samples {v['samples']}"
    )
    print(
        f"here: analyzer {local_versions()[0]}, recognizer {board.__version__}, commit {git('rev-parse', '--short=7', 'HEAD')}"
    )
    # the docs-only commits after the Pi's don't need an update
    changed = git(
        "diff",
        "--name-only",
        v["commit"],
        "HEAD",
        "--",
        "analyzer",
        "recognizer",
        "bganalyzer.service",
        "pyproject.toml",
        "uv.lock",
    )
    print(
        "code changed since the Pi's commit:",
        changed.replace("\n", ", ") if changed else "none",
    )
    return not changed


def local_versions():
    src = (ROOT / "analyzer" / "app.py").read_text()
    return [
        line.split('"')[1]
        for line in src.splitlines()
        if line.startswith("__version__")
    ]


def check_static(base):
    ok = True
    for f in STATIC:
        status, data = get(base + f)
        same = data == (ROOT / "analyzer" / "static" / (f or "index.html")).read_bytes()
        ok &= status == 200 and same
        print(f"  /{f}: {status}, {'same as here' if same else 'DIFFERENT from here'}")
    return ok


def check_sample(base, name):
    t = json.loads((ROOT / "samples" / f"{name}.truth.json").read_text())
    img = cv2.imread(str(ROOT / "samples" / t["image"]))
    img, corners = shrink_like_app(img, t["corners_TL_TR_BR_BL"])
    jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])[1].tobytes()
    fields = {
        "corners": ",".join(f"{v:.1f}" for xy in corners for v in xy),
        "home": t["home"],
        "bottom_colour": t.get("bottom_colour", 0),
        "plies": 0,
    }
    r = post_photo(base + "analyze-photo", fields, jpg)
    # the same bytes and corners, read here
    sent = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
    c = [float(v) for v in fields["corners"].split(",")]
    pos, _ = board.recognize(
        sent,
        list(zip(c[0::2], c[1::2])),
        home=t["home"],
        bottom_colour=fields["bottom_colour"],
    )
    pi = r["recognized"]["points"]
    right = sum(a == b for a, b in zip(pi, t["points"]))
    same = pi == pos.points
    a = r["analysis"]
    res = a["summary"] if a else f"not analyzed: {r['errors']}"
    print(
        f"  {name}: {right}/24 points as the truth, {'same as here' if same else 'DIFFERENT from here'}, {res}"
    )
    return same


def main():
    args = [a for a in sys.argv[1:] if a != "--all"]
    base = (args[0] if args else DEFAULT_URL).rstrip("/") + "/"
    names = (
        sorted(
            p.name[: -len(".truth.json")]
            for p in (ROOT / "samples").glob("*.truth.json")
        )
        if "--all" in sys.argv
        else DEFAULT_SAMPLES
    )
    ok = check_version(base)
    print("static files:")
    ok &= check_static(base)
    print("photos (0-ply):")
    for n in names:
        ok &= check_sample(base, n)
    print("OK" if ok else "DIFFERENCES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
