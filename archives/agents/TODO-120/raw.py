"""TODO-120: samples taken from beside the board, turned back to how they were taken (the bar across).
usage: uv run python archives/agents/TODO-120/raw.py <out dir> samples/photo5.truth.json ...
photo5 and photo6 were turned 90 degrees anticlockwise to put the bar upright; this turns them
clockwise, so the side nearest the camera is at the bottom. The truth's corners are turned with them
and keep their order (TL, TR, BR, BL as the near player sees the board): the near player is on the left."""
import json, sys
from pathlib import Path
import cv2

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for path in sys.argv[2:]:
    t = json.load(open(path))
    img = cv2.imread(str(Path(path).parent / t["image"]))
    h = img.shape[0]
    raw = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    name = Path(t["image"]).stem + "-raw"
    t["corners_TL_TR_BR_BL"] = [[h - 1 - y, x] for x, y in t["corners_TL_TR_BR_BL"]]
    t["image"] = name + ".jpg"
    cv2.imwrite(str(out / t["image"]), raw)
    (out / (name + ".truth.json")).write_text(json.dumps(t))
    print(out / (name + ".truth.json"))
