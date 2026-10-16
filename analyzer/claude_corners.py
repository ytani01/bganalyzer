"""POST /claude-corners: the playing area's corners as Claude sees them, for photos the guess misses (TODO-082).

Off unless BG_CLAUDE is set to the claude command (a path: the systemd user unit's PATH has no
~/.local/bin). The photo goes to Anthropic only when the user presses the button. One at a time, killed
after a while or when the app gives up. There is no limit on how many in a row: the app is public, so
anyone can use up the owner's Claude limits, one after another (the owner decided so, 2026-10-17).
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import math
import os
import re
import signal
import tempfile
import time

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

TIMEOUT = 60        # seconds; a reply took 7-9 s when tried
LONG_SIDE = 1568    # larger images are scaled down by the API anyway
PROMPT = ("This photo shows a backgammon board. Give the four corners of the playing area "
          "(both fields and the bar, inside the frame), as seen by the player at the bottom of the photo: "
          "top-left, top-right, bottom-right, bottom-left. Pixel coordinates in this image "
          "({w}x{h}). First, for each corner in turn, say in one line what you see there and where it is. "
          "Then end with one line of JSON: {{\"corners\": [[x,y],[x,y],[x,y],[x,y]]}}")
CORNERS = re.compile(r'\{\s*"corners"\s*:')

router = APIRouter()
log = logging.getLogger("uvicorn.error")
_running = False


def claude_command() -> str | None:
    return os.environ.get("BG_CLAUDE") or None


def _message(img) -> tuple[str, float]:
    """The stream-json user message (the image and the prompt), and the scale the image was sent at."""
    s = min(1, LONG_SIDE / max(img.shape[:2]))
    small = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img
    h, w = small.shape[:2]
    b64 = base64.b64encode(cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 90])[1]).decode()
    msg = {"type": "user", "message": {"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
        {"type": "text", "text": PROMPT.format(w=w, h=h)}]}}
    return json.dumps(msg) + "\n", s


def _corners(stdout: bytes) -> list:
    """The last {"corners": ...} in the result line's text, as 4 [x, y] (raises if there is none)."""
    lines = [json.loads(line) for line in stdout.decode(errors="replace").splitlines() if line.startswith("{")]
    text = [r for r in lines if r.get("type") == "result"][-1]["result"]
    start = [m.start() for m in CORNERS.finditer(text)][-1]
    c = json.JSONDecoder().raw_decode(text[start:])[0]["corners"]
    c = [[float(x), float(y)] for x, y in c]
    assert len(c) == 4 and all(math.isfinite(v) for p in c for v in p)   # NaN can't be sent back as JSON
    return c


async def _kill(proc):
    # the group, even when claude itself has ended: its children may still be there (holding stdout)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    await proc.wait()


@router.post("/claude-corners")
async def claude_corners(request: Request, image: UploadFile = File(...)):
    """corners (TL, TR, BR, BL) in the sent image's pixels, kept inside it."""
    global _running
    cmd = claude_command()
    if cmd is None:
        raise HTTPException(404, "this server does not ask Claude")
    if _running:
        raise HTTPException(429, "Claude is busy with another photo")
    _running = True
    try:
        img = cv2.imdecode(np.frombuffer(await image.read(), np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(422, "could not decode image")
        h, w = img.shape[:2]
        msg, s = _message(img)
        model = os.environ.get("BG_CLAUDE_MODEL") or "claude-sonnet-5-5"
        log.info("claude-corners: asking %s (%dx%d)", model, w, h)
        t = time.monotonic()
        with tempfile.TemporaryDirectory() as cwd:   # nothing for it to read
            try:
                proc = await asyncio.create_subprocess_exec(
                    cmd, "-p", "--model", model, "--input-format", "stream-json", "--output-format", "stream-json",
                    "--verbose", "--tools", "", "--no-session-persistence", "--setting-sources", "", "--effort", "high",
                    stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                    cwd=cwd, start_new_session=True)
            except OSError as e:   # BG_CLAUDE is a wrong path, or not executable
                log.warning("claude-corners: could not start %s: %s", cmd, e.strerror)
                raise HTTPException(502, f"could not start claude: {e.strerror}") from e
            try:
                reply = asyncio.ensure_future(proc.communicate(msg.encode()))
                while not (await asyncio.wait({reply}, timeout=0.5))[0]:
                    if await request.is_disconnected():
                        log.info("claude-corners: cancelled after %.0f s", time.monotonic() - t)
                        raise HTTPException(499, "cancelled")
                    if time.monotonic() - t > TIMEOUT:
                        log.warning("claude-corners: no answer in %d s", TIMEOUT)
                        raise HTTPException(504, f"Claude did not answer in {TIMEOUT} s")
                stdout, _ = reply.result()
            finally:
                reply.cancel()
                await _kill(proc)
        dt = time.monotonic() - t
        if proc.returncode != 0:
            log.warning("claude-corners: claude exited with %d after %.0f s", proc.returncode, dt)
            raise HTTPException(502, f"claude exited with {proc.returncode}")
        try:
            c = _corners(stdout)
        except Exception as e:
            log.warning("claude-corners: no corners in the answer after %.0f s", dt)
            raise HTTPException(502, "could not read the corners in Claude's answer") from e
        log.info("claude-corners: done in %.0f s", dt)
        return {"corners": [[min(max(x / s, 0), w), min(max(y / s, 0), h)] for x, y in c], "width": w, "height": h}
    finally:
        _running = False
