"""HTTP API for position analysis (step 2) and the PWA (step 3, static/ served at /).

Run: uvicorn app:app --app-dir analyzer

Do not run with --reload or several workers: the gnubg extension is not fork-safe.
"""
from __future__ import annotations

import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from analysis import (DEFAULT_PLIES, MAX_PLIES, Position, analyze, parse_position, shutdown,
                      summary_ja)

# The analyzer's version (this API, analysis.py and the PWA in static/). Bump it when analyzer/
# changes; the recognizer has its own in recognizer/board.py. How to bump: CLAUDE.md.
__version__ = "0.5.0"

REPO = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(_app):
    yield
    shutdown()   # uvicorn re-raises SIGTERM after this, so atexit hooks never run


app = FastAPI(title="bganalyzer", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Board(BaseModel):
    """Recognizer convention: points[i] = White's point i+1, >0 White, <0 Black."""
    points: list[int] = Field(min_length=24, max_length=24)
    bar_white: int = 0
    bar_black: int = 0
    off_white: int | None = None   # default: whatever makes 15
    off_black: int | None = None


class AnalyzeRequest(BaseModel):
    position_id: str | None = None
    board: Board | None = None
    on_roll: str = "white"
    plies: int = Field(DEFAULT_PLIES, ge=0, le=MAX_PLIES)
    dice: tuple[int, int] | None = None


def _board_to_position(b: Board) -> Position:
    pos = Position(points=list(b.points), bar_white=b.bar_white, bar_black=b.bar_black)
    w, bl = pos.counts()
    pos.off_white = 15 - w if b.off_white is None else b.off_white
    pos.off_black = 15 - bl if b.off_black is None else b.off_black
    return pos


def _run(pos: Position, on_roll: str, plies: int, dice) -> dict:
    try:
        r = analyze(pos, on_roll, plies=plies, dice=dice)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    r["board"] = {k: v for k, v in pos.to_dict().items() if k in
                  ("points", "bar_white", "bar_black", "off_white", "off_black")}
    r["summary"] = summary_ja(r)
    return r


@app.get("/health")
def health():
    return {"ok": True}


def git_commit(git_dir: Path = REPO / ".git") -> str | None:
    """Short id of the checked-out commit, read from the files (git itself may not be installed).

    The Docker image carries only .git/HEAD and the refs for this (see .dockerignore).
    """
    try:
        head = (git_dir / "HEAD").read_text().strip()
        if head.startswith("ref: "):
            ref = head[5:]
            loose = git_dir / ref
            if loose.is_file():
                head = loose.read_text().strip()
            else:
                packed = (git_dir / "packed-refs").read_text().splitlines()
                head = next(line.split()[0] for line in packed if line.endswith(" " + ref))
        return head[:7] if len(head) >= 7 else None
    except (OSError, StopIteration):
        return None


@app.get("/version")
def version():
    from board import __version__ as recognizer_version

    return {"analyzer": __version__, "recognizer": recognizer_version, "commit": git_commit()}


@app.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    if (req.position_id is None) == (req.board is None):
        raise HTTPException(422, "give exactly one of position_id or board")
    if req.position_id is not None:
        try:
            pos = parse_position(req.position_id, req.on_roll)
        except Exception as e:
            raise HTTPException(422, f"invalid position id: {req.position_id}") from e
    else:
        pos = _board_to_position(req.board)
    return _run(pos, req.on_roll, req.plies, req.dice)


@app.post("/find-corners")
async def find_corners_endpoint(image: UploadFile = File(...)):
    """A first guess at the playing area's corners (TL, TR, BR, BL), for the app to show
    before the user adjusts them. corners is null when no board was found."""
    from corners import find_corners  # recognizer (OpenCV); imported lazily

    img = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(422, "could not decode image")
    return {"corners": find_corners(img), "width": img.shape[1], "height": img.shape[0]}


@app.post("/analyze-photo")
async def analyze_photo(
    image: UploadFile = File(...),
    corners: str = Form(..., description="x1,y1,...,x4,y4: TL,TR,BR,BL of the playing area"),
    home: str = Form("right"),
    bottom_colour: int = Form(0),
    on_roll: str = Form("white"),
    plies: int = Form(DEFAULT_PLIES),
    dice: str | None = Form(None, description="e.g. 3,1"),
):
    from board import recognize  # recognizer (OpenCV); imported lazily

    img = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(422, "could not decode image")
    try:
        c = [float(v) for v in corners.split(",")]
        assert len(c) == 8
        d = tuple(int(v) for v in dice.split(",")) if dice else None
    except Exception as e:
        raise HTTPException(422, "corners must be 8 numbers, dice two numbers") from e
    if home not in ("left", "right"):
        raise HTTPException(422, "home must be left or right")
    pos, info = recognize(img, list(zip(c[0::2], c[1::2])), home=home, bottom_colour=bottom_colour)
    warnings = [WARNINGS[w] for w in info.get("warnings", [])]
    errors = pos.validate()
    # geometry: where the recognizer found the board and its columns (image pixels of the sent image),
    # so the app can line the photo up with the read board.
    out = {"recognized": pos.to_dict(), "errors": errors, "warnings": warnings, "geometry": info.get("geometry")}
    if errors:
        # Let the app show the read board for manual correction.
        return out | {"analysis": None}
    return out | {"analysis": _run(pos, on_roll, plies, d)}


@app.post("/share-target")
def share_target():
    # Android's share sheet posts photos here (manifest share_target); sw.js normally answers on
    # the phone. This only runs before the service worker is up: don't read or keep the photo,
    # just open the app ("./" keeps the /bg/ prefix the proxy strips).
    return RedirectResponse("./?shared=none", status_code=303)


# What the recognizer's warnings mean for the person holding the phone.
WARNINGS = {
    "oblique": "斜めから撮った写真なので、読み間違いが多いかもしれません。盤の真上から撮り直すと正確に読めます。",
}


# The PWA. Mounted last so the API routes above take precedence.
mimetypes.add_type("application/manifest+json", ".webmanifest")   # unknown before Python 3.13
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent / "static", html=True), name="pwa")
