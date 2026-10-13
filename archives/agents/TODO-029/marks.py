"""Per sample: candidates reaching _ink, and the seen ranking under MAX_MARKS 4 and 8."""
import glob, sys, numpy as np
sys.path.insert(0, "recognizer")
import cube, evaluate
log = []
orig = cube._ink
def ink(gray, body):
    r = orig(gray, body); log.append((body["x"], body["y"], body["side"], *r)); return r
cube._ink = ink
def rank(lim):
    found = [c for c in log if 0.04 <= c[3] <= 0.4 and 1 <= c[4] <= lim]
    out = []
    for b in sorted(found, key=lambda c: -c[2]):
        if any(np.hypot(b[0]-o[0], b[1]-o[1]) < 0.6*o[2] for o, _, _ in out): continue
        seen = [o for o in found if np.hypot(b[0]-o[0], b[1]-o[1]) < 0.5*b[2]]
        out.append((b, len(seen), sorted(o[4] for o in seen)))
    out.sort(key=lambda c: -c[1])
    return [(round(b[0]), round(b[1]), n, m) for b, n, m in out[:3]]
for f in sorted(glob.glob("samples/*.truth.json") + glob.glob("samples/external/*.truth.json")):
    for app in (False, True):
        log.clear()
        res = evaluate.run(f, app=app)
        print(f.split("/")[-1], "app" if app else "raw", "answer", res[-1][0], "truth", res[-1][1],
              "| m4", rank(4), "| m8", rank(8), flush=True)
