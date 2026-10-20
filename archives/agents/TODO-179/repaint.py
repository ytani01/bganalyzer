"""Paint samples/collected-* again from the photos left in collected/ (TODO-179).

    uv run python archives/agents/TODO-179/repaint.py <collected/> <dir for the old photos>
"""

import json
import shutil
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "recognizer"))
import import_collected  # noqa: E402

d, old = Path(sys.argv[1]), Path(sys.argv[2])
old.mkdir(parents=True, exist_ok=True)
samples = Path(__file__).resolve().parents[3] / "samples"
by_id = {import_collected.sample_id(p.name): p.name for p in d.glob("user-*.truth.json")}
n = 0
for p in sorted(samples.glob("collected-*.truth.json")):
    t = json.loads(p.read_text())
    if not (name := by_id.get(t.get("id"))):
        continue
    src = cv2.imread(str(import_collected.photo(d, name)))
    dst = samples / t["image"]
    if src is None or src.shape != cv2.imread(str(dst)).shape:
        print("skipped (size differs or unreadable):", p.name)
        continue
    shutil.copy(dst, old / dst.name)
    img = import_collected.paint(src, t["corners_TL_TR_BR_BL"])
    cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    n += 1
    print("repainted:", dst.name)
print(n)
