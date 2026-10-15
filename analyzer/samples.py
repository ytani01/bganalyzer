"""POST /samples: photos with their corrected boards, kept to measure and improve the recognizer (TODO-030).

Off unless BG_SAMPLES_DIR is set (bganalyzer.service sets it), and the app sends them only when the user
turns it on. Each photo is one id: a later send replaces the earlier one. When enough new pairs have
come, they are measured again in a child process (recognizer/collected.py).
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

import analysis  # noqa: F401  puts recognizer/ on sys.path
import collected   # recognizer/collected.py
from models import Board

RECOGNIZER = Path(__file__).resolve().parent.parent / "recognizer"
SAMPLE_ID = re.compile(r"^[A-Za-z0-9-]{1,64}$")
SAMPLE_TYPES = {"image/jpeg": "jpg", "image/png": "png"}
SAMPLE_MAX_BYTES = 20_000_000
SAMPLE_MAX_COUNT = 1000   # the app is public (Funnel): don't let anyone fill the Pi's disk

router = APIRouter()
log = logging.getLogger("uvicorn.error")


def samples_dir() -> Path | None:
    d = os.environ.get("BG_SAMPLES_DIR")
    return Path(d) if d else None


@router.post("/samples")
async def save_sample(
    id: str = Form(..., description="the photo's id on the phone (letters, digits and -)"),
    truth: str = Form(..., description="the truth.json (sample.js)"),
    image: UploadFile = File(...),
):
    d = samples_dir()
    if d is None:
        raise HTTPException(404, "this server does not keep samples")
    if not SAMPLE_ID.match(id):
        raise HTTPException(422, "bad id")
    ext = SAMPLE_TYPES.get(image.content_type or "")
    if ext is None:
        raise HTTPException(422, "image must be JPEG or PNG")
    data = await image.read(SAMPLE_MAX_BYTES + 1)
    if len(data) > SAMPLE_MAX_BYTES:
        raise HTTPException(413, "image too large")
    try:
        t = json.loads(truth)
        Board(points=t["points"], bar_white=t["bar_white"], bar_black=t["bar_black"])
        assert len(t["corners_TL_TR_BR_BL"]) == 4 and t["home"] in ("left", "right")
    except Exception as e:
        raise HTTPException(422, "bad truth") from e
    name = f"user-{id}"
    t["image"] = f"{name}.{ext}"
    d.mkdir(parents=True, exist_ok=True)
    if not (d / f"{name}.truth.json").exists() and sum(1 for _ in d.glob("*.truth.json")) >= SAMPLE_MAX_COUNT:
        raise HTTPException(507, "the sample folder is full")
    for old in d.glob(f"{name}.*"):   # a PNG sent before a JPEG of the same photo, etc.
        old.unlink()
    (d / t["image"]).write_bytes(data)
    (d / f"{name}.truth.json").write_text(json.dumps(t, ensure_ascii=False) + "\n")
    measure_collected(d)
    return {"saved": name}


_measuring: subprocess.Popen | None = None


def measure_collected(d: Path) -> None:
    """When enough new pairs came, measure them again in a child process (recognizer/collected.py)."""
    global _measuring
    if (_measuring and _measuring.poll() is None) or len(collected.new_pairs(d)) < collected.NEW:
        return
    try:   # at the lowest priority: the API it was started from comes first; why it failed goes to measure.log
        with open(d / "measure.log", "w") as err:
            _measuring = subprocess.Popen(["nice", "-n", "19", sys.executable, str(RECOGNIZER / "collected.py"), str(d)],
                                          stdout=subprocess.DEVNULL, stderr=err)
    except OSError as e:   # the pair is saved: not measuring this time is no reason to fail the request
        log.warning("could not measure collected/ again: %r", e)
