# find_corners_any for every sample: which way it took (None = the normal search) and the score; to a JSON file
# usage: uv run python side_choice.py <recognizer dir> <out.json>
import glob, json, os, sys
sys.path.insert(0, sys.argv[1])
import cv2
import side
out = {}
for f in sorted(glob.glob("samples/*.truth.json")):
    t = json.load(open(f))
    img = cv2.imread(os.path.join("samples", t["image"]))
    q, way = side.find_corners_any(img)
    out[os.path.basename(f)] = [way, round(side._score(img, q), 3)]
json.dump(out, open(sys.argv[2], "w"), indent=0)
