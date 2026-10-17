#!/bin/sh
# TODO-120: the corner search (proto_corners.py, slopes up to 1.0) and the reading with the truth's corners (evaluate.py),
# on the photos taken from beside the board. usage: sh archives/agents/TODO-120/measure.sh <dir of the *.truth.json>
d=${1:-/tmp/claude-649/-home-ytani-work-bganalyzer/707b7369-3499-4f3f-bd74-f14e97c6c2ef/scratchpad/raw}
set -- "$d"/photo5-raw.truth.json "$d"/photo6-raw.truth.json "$d"/user-1792239246813-2hhe5o.truth.json "$d"/user-1792237981068-xqv7k9.truth.json "$d"/user-1792239782228-mghnwm.truth.json "$d"/user-1792239974939-ri4m9g.truth.json
timeout 900 uv run python archives/agents/TODO-120/proto_corners.py --wide "$@" < /dev/null
timeout 900 uv run python recognizer/evaluate.py "$@" < /dev/null | rg "points correct" -
