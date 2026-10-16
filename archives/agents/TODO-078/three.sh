# TODO-078: corner error on the photos looked at (photo5, the photo before painting, commons-rollup-oblique, commons-tavli-red-white)
uv run python archives/agents/TODO-078/score.py "$1" | rg "truth \d"
cd recognizer && uv run python check_corners.py ../samples/photo5.truth.json ../samples/commons-rollup-oblique.truth.json ../samples/commons-tavli-red-white.truth.json | rg -v "^$"
