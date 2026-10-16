"""HTTP API for position analysis (step 2) and the PWA (step 3, static/ served at /).

Run: uvicorn app:app --app-dir analyzer

Do not run with --reload or several workers: the gnubg extension is not fork-safe.
"""
from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from analysis import DEFAULT_PLIES, Position, analyze, other, parse_position, shutdown, summary_ja
from models import AnalyzeRequest, Board
from samples import router as samples_router, samples_dir

# The analyzer's version (this API, the modules beside it and the PWA in static/). Bump it when analyzer/
# changes; the recognizer has its own in recognizer/board.py. How to bump: CLAUDE.md.
__version__ = "0.44.0"

REPO = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(_app):
    yield
    shutdown()   # uvicorn re-raises SIGTERM after this, so atexit hooks never run


app = FastAPI(title="bganalyzer", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(samples_router)
log = logging.getLogger("uvicorn.error")   # uvicorn's access log has the status but not why


@app.exception_handler(HTTPException)
async def log_http_error(request: Request, exc: HTTPException):
    if 400 <= exc.status_code < 500:
        # %r: a detail can quote what was sent (a position id); keep it on one line
        log.warning("%s %s -> %d: %r", request.method, request.url.path, exc.status_code, exc.detail)
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def log_validation_error(request: Request, exc: RequestValidationError):
    # only where and what, not the input: it can be the photo or the form's values
    why = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    log.warning("%s %s -> 422: %s", request.method, request.url.path, why)
    return await request_validation_exception_handler(request, exc)


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
    """Short id of the checked-out commit, read from the files (git itself may not be installed)."""
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

    # samples: whether this server keeps photos sent to /samples (the app shows its switch only then)
    return {"analyzer": __version__, "recognizer": recognizer_version, "commit": git_commit(),
            "samples": samples_dir() is not None}


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
async def find_corners_endpoint(
    image: UploadFile = File(...),
    stream: bool = Form(False, description="answer as NDJSON lines: each stage of the search as it is done, then the result"),
    fixed: str | None = Form(None, description='JSON [TL, TR, BR, BL], each [x, y] the user has put in place or null: kept as they are'),
    crop: str | None = Form(None, description="x0,y0,x1,y1: look only in this part of the photo"),
):
    """A guess at the playing area's corners (TL, TR, BR, BL), for the app to show before the user
    adjusts them, or again after (fixed, crop). corners is null when no board was found."""
    from corners import find_corners  # recognizer (OpenCV); imported lazily

    img = await _decode(image)
    try:
        f = json.loads(fixed) if fixed else None
        assert f is None or (isinstance(f, list) and len(f) == 4)
        f = f and [None if p is None else [float(v) for v in p] for p in f]
        assert f is None or all(p is None or len(p) == 2 for p in f)
        c = tuple(float(v) for v in crop.split(",")) if crop else None
        assert c is None or len(c) == 4
    except Exception as e:
        raise HTTPException(422, "fixed must be 4 of [x, y] or null, crop 4 numbers") from e
    size = {"width": img.shape[1], "height": img.shape[0]}
    if stream:
        return _stream(lambda progress: {"corners": find_corners(img, progress, fixed=f, crop=c)} | size)
    return {"corners": find_corners(img, fixed=f, crop=c)} | size


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
    stream: bool = Form(False, description="answer as NDJSON lines: each stage of the reading as it is done, then the result"),
):
    from board import recognize  # recognizer (OpenCV); imported lazily

    img = await _decode(image)
    try:
        c = [float(v) for v in corners.split(",")]
        assert len(c) == 8
        d = tuple(int(v) for v in dice.split(",")) if dice else None
    except Exception as e:
        raise HTTPException(422, "corners must be 8 numbers, dice two numbers") from e
    if home not in ("left", "right", "auto"):
        raise HTTPException(422, "home must be left, right or auto")
    pts = list(zip(c[0::2], c[1::2]))

    def work(progress=None):
        pos, info = recognize(img, pts, home=home, bottom_colour=bottom_colour, progress=progress)
        return _photo_result(pos, info, d, on_roll, plies, cube_value, cube_owner, doubled)
    return _stream(work) if stream else work()


async def _decode(image: UploadFile):
    """The uploaded photo as a BGR image."""
    img = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(422, "could not decode image")
    return img


def _stream(work) -> StreamingResponse:
    """The answer as NDJSON lines (_stream_stages), sent as soon as each is written."""
    return StreamingResponse(_stream_stages(work), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


async def _stream_stages(work):
    """Runs work(progress) in a thread and yields NDJSON lines: {"stage": ..., ...} for each stage the
    recognizer reports, then {"stage": "done", "result": what the endpoint returns}, or
    {"stage": "error", "detail": ...} (the status is already 200 by then)."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def progress(stage, data):
        loop.call_soon_threadsafe(queue.put_nowait, {"stage": stage, **data})

    def line(obj):
        return json.dumps(obj, ensure_ascii=False) + "\n"

    job = loop.run_in_executor(None, work, progress)
    while True:
        getter = asyncio.ensure_future(queue.get())
        done, _ = await asyncio.wait({getter, job}, return_when=asyncio.FIRST_COMPLETED)
        if getter in done:
            yield line(getter.result())
            continue
        getter.cancel()
        break
    while not queue.empty():   # stages reported just before the end (put before the job finished)
        yield line(queue.get_nowait())
    try:
        yield line({"stage": "done", "result": job.result()})
    except HTTPException as e:
        log.warning("analyze-photo (stream): %s", e.detail)
        yield line({"stage": "error", "detail": e.detail})
    except Exception as e:   # noqa: BLE001 - the client must hear of it; the status is already sent
        log.exception("analyze-photo (stream) failed")
        yield line({"stage": "error", "detail": str(e) or type(e).__name__})


# What the recognizer's warnings mean for the person holding the phone.
WARNINGS = {
    "oblique": "斜めから撮った写真なので、読み間違いが多いかもしれません。盤の真上から撮り直すと正確に読めます。",
}


def _photo_result(pos, info, d, on_roll, plies, cube_value, cube_owner, doubled) -> dict:
    """What /analyze-photo returns for the read board: the board, what was read and the analysis."""
    warnings = [WARNINGS[w] for w in info.get("warnings", [])]
    errors = pos.validate()
    # geometry: where the recognizer found the board and its columns (image pixels of the sent image),
    # so the app can line the photo up with the read board.
    # dice_read: the two dice lying in the fields, when the recognizer is sure of them (else null)
    # cube_read: where the doubling cube lies and the number on it, {"at": "centre" | "white" | "black" | "field",
    # "value": 2 .. 64 or null (not read with confidence; always null in the centre, where it means 1)}, or null
    read = info["dice"]["values"]
    cube = info.get("cube")
    cube_read = cube and {"at": cube["at"], "value": None if cube["at"] == "centre" else cube.get("value")}
    # a cube in a playing field (TODO-045): the side on roll has just doubled (to the number read, else 2),
    # and the other side takes or passes. Dice on the board (read or sent) are left out: no one rolls before the answer.
    field_double = cube_value is None and bool(cube_read) and cube_read["at"] == "field"
    if field_double:
        read, d = None, None
    out = {"recognized": pos.to_dict(), "home": info["home"], "home_guess": info["home_guess"], "errors": errors, "warnings": warnings, "geometry": info.get("geometry"),
           "dice_read": read, "cube_read": cube_read}
    if errors:
        # Let the app show the read board for manual correction.
        return out | {"analysis": None}
    if not d and read:
        d = tuple(read)
        # dice in the photo: someone has rolled, so no double waits on take or pass (TODO-033).
        # A cube offered by hand stays where it was set: its side has taken and owns it, and the
        # player who doubled (on_roll, as sent) rolls these dice.
        doubled = False
    if cube_value is None:
        cube_value, cube_owner, doubled = 1, None, False
        shown = cube_read and cube_read["value"] or 2   # the number read (TODO-025), else 2
        if field_double:
            cube_value, cube_owner, doubled = shown, other(on_roll), True
        elif cube_read and cube_read["at"] != "centre":
            # a cube on one side shows 2 or more; with no dice, it has just been offered there
            cube_value, cube_owner, doubled = shown, cube_read["at"], d is None
            if doubled:
                on_roll = other(cube_owner)
    return out | {"analysis": _run(pos, on_roll, plies, d,
                                   cube_value=cube_value, cube_owner=cube_owner or None, doubled=doubled)}


@app.post("/share-target")
def share_target():
    # Android's share sheet posts photos here (manifest share_target); sw.js normally answers on
    # the phone. This only runs before the service worker is up: don't read or keep the photo,
    # just open the app ("./" keeps the /bg/ prefix the proxy strips).
    return RedirectResponse("./?shared=none", status_code=303)


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
