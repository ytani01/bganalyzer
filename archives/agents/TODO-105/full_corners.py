# check_corners for every sample (plain and --app) with the corners.py in the working tree; saved for comparing
import glob, json, sys, time
sys.path.insert(0, "recognizer")
import check_corners
out, t0 = {}, time.perf_counter()
for f in sorted(glob.glob("samples/*.truth.json")):
    for app in (False, True):
        out[f"{f} {'app' if app else ''}"] = check_corners.measure(f, app)[0]
out["seconds"] = time.perf_counter() - t0
json.dump(out, open(sys.argv[1], "w"), indent=0)
