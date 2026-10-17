"""TODO-120: read with the camera's end of the playing area moved out (it is hidden under the frame's top edge).
usage: uv run python archives/agents/TODO-120/proto_extend.py <x.truth.json> ...
Taken from the near player's right, the camera is beyond the right end (TR, BR). The truth's corners
there are on the top of the frame, which hides the end of the playing area: TR and BR are moved out
by e of the area's width (in the view from above), for a few e, and the photo is read again."""
import json, sys, tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0, "recognizer")
import evaluate, exact

for path in sys.argv[1:]:
    t = json.load(open(path))
    q = np.float64(t["corners_TL_TR_BR_BL"])
    H = exact.homography(np.float64([(0, 0), (1, 0), (1, 1), (0, 1)]), q)
    row = []
    for e in (0.0, 0.02, 0.04, 0.06, 0.08):
        u = dict(t, corners_TL_TR_BR_BL=exact.apply_h(H, np.float64([(0, 0), (1 + e, 0), (1 + e, 1), (0, 1)])).tolist(),
                 image=str((Path(path).parent / t["image"]).resolve()))
        with tempfile.NamedTemporaryFile("w", suffix=".truth.json", dir=Path(path).parent, delete=True) as f:
            f.write(json.dumps(u)); f.flush()
            r = evaluate.run(f.name)
        row.append(f"{e:.2f}:{24 - len(r[2])}")
    print(Path(path).name, " ".join(row))
