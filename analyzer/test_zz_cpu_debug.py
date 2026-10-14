# TEMPORARY (TODO-028): where do x86_64 and the Pi part? Prints hashes of each step, then fails.
import hashlib, json, sys
from pathlib import Path
import cv2, numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recognizer"))
import corners


def h(a):
    return hashlib.md5(np.ascontiguousarray(a).tobytes()).hexdigest()[:10]


def test_debug_hashes():
    samples = Path(__file__).resolve().parent.parent / "samples"
    out = []
    for name in ("commons-tavli-red-brown", "commons-dark-homeleft", "photo2", "commons-travel-case", "commons-case-dice"):
        t = json.loads((samples / f"{name}.truth.json").read_text())
        img = cv2.imread(str(samples / t["image"]))
        small, _ = corners.shrink(img)
        blur = cv2.GaussianBlur(small, (0, 0), 1.5)
        lab = cv2.cvtColor(blur, cv2.COLOR_BGR2Lab)
        tris = corners.find_triangles(small)
        v = corners.find_v_shapes(small)
        rows = corners._rows(tris)
        out.append(f"{name} img={h(img)} small={h(small)} blur={h(blur)} lab={h(lab)} "
                   f"tris={len(tris)}:{h(np.array([np.concatenate([a, b, [c]]) for a, b, c in tris]).round(3))} "
                   f"v={len(v)} rows={rows is not None} quad={corners.guess(small).round(2).tolist()}")
    print("\n".join(out))
    assert False, "\n".join(out)
