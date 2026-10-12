"""HTTP API for position analysis (step 2) and the PWA (step 3, static/ served at /).

Run: uvicorn app:app --app-dir analyzer

Do not run with --reload or several workers: the gnubg extension is not fork-safe.
"""
from __future__ import annotations

import mimetypes
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from analysis import DEFAULT_PLIES, MAX_PLIES, Position, analyze, parse_position, summary_ja

app = FastAPI(title="bganalyzer")
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
    errors = pos.validate()
    if errors:
        # Let the app show the read board for manual correction.
        return {"recognized": pos.to_dict(), "errors": errors, "analysis": None}
    return {"recognized": pos.to_dict(), "errors": [], "analysis": _run(pos, on_roll, plies, d)}


# The PWA. Mounted last so the API routes above take precedence.
mimetypes.add_type("application/manifest+json", ".webmanifest")   # unknown before Python 3.13
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent / "static", html=True), name="pwa")
