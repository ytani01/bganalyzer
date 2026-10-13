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
__version__ = "0.22.1"

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
    # The doubling cube (money game). Without dice, the answer has the cube decision.
    cube_value: int = 1
    cube_owner: str | None = None   # white, black or null (in the middle)
    doubled: bool = False           # on_roll has just doubled to cube_value: take or pass?


def _board_to_position(b: Board) -> Position:
    pos = Position(points=list(b.points), bar_white=b.bar_white, bar_black=b.bar_black)
    w, bl = pos.counts()
    pos.off_white = 15 - w if b.off_white is None else b.off_white
    pos.off_black = 15 - bl if b.off_black is None else b.off_black
    return pos


def _run(pos: Position, on_roll: str, plies: int, dice, **cube) -> dict:
    try:
        r = analyze(pos, on_roll, plies=plies, dice=dice, **cube)
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
    return _run(pos, req.on_roll, req.plies, req.dice,
                cube_value=req.cube_value, cube_owner=req.cube_owner, doubled=req.doubled)


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
    home: str = Form("right", description="left, right or auto (guessed from the checkers)"),
    bottom_colour: int = Form(0),
    on_roll: str = Form("white"),
    plies: int = Form(DEFAULT_PLIES),
    dice: str | None = Form(None, description="e.g. 3,1; without it, the dice read from the photo (if any)"),
    cube_value: int | None = Form(None, description="without it, the cube read from the photo (if any)"),
    cube_owner: str | None = Form(None, description="white or black; empty: in the middle"),
    doubled: bool = Form(False),
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
    if home not in ("left", "right", "auto"):
        raise HTTPException(422, "home must be left, right or auto")
    pos, info = recognize(img, list(zip(c[0::2], c[1::2])), home=home, bottom_colour=bottom_colour)
    warnings = [WARNINGS[w] for w in info.get("warnings", [])]
    errors = pos.validate()
    # geometry: where the recognizer found the board and its columns (image pixels of the sent image),
    # so the app can line the photo up with the read board.
    # dice_read: the two dice lying in the fields, when the recognizer is sure of them (else null)
    # cube_read: where the doubling cube lies, {"at": "centre" | "white" | "black"} (its number is not read), or null
    read = info["dice"]["values"]
    cube = info.get("cube")
    cube_read = cube and {"at": cube["at"]}
    out = {"recognized": pos.to_dict(), "home": info["home"], "home_guess": info["home_guess"], "errors": errors, "warnings": warnings, "geometry": info.get("geometry"),
           "dice_read": read, "cube_read": cube_read}
    if errors:
        # Let the app show the read board for manual correction.
        return out | {"analysis": None}
    d = d or (tuple(read) if read else None)
    if cube_value is None:
        cube_value, cube_owner, doubled = 1, None, False
        if cube_read and cube_read["at"] != "centre":
            # a cube on one side shows 2 or more (2 when unread); with no dice, it has just been offered there
            cube_value, cube_owner, doubled = 2, cube_read["at"], d is None
            if doubled:
                on_roll = "black" if cube_owner == "white" else "white"
    return out | {"analysis": _run(pos, on_roll, plies, d,
                                   cube_value=cube_value, cube_owner=cube_owner or None, doubled=doubled)}


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
class AppFiles(StaticFiles):
    """The PWA's files, which the browser must check for a newer copy each time.

    Without Cache-Control, browsers keep a file for a while on their own guess (a share
    of its age), so after an update the phone can run the old app.js against the new API."""

    def file_response(self, *args, **kwargs):
        res = super().file_response(*args, **kwargs)
        res.headers["Cache-Control"] = "no-cache"
        return res


app.mount("/", AppFiles(directory=Path(__file__).resolve().parent / "static", html=True), name="pwa")
