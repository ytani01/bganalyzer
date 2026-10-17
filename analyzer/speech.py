"""GET /speech: a piece of the spoken summary in Google Translate's voice, so that every phone reads it in
the same voice (TODO-111). The browser's own voice depends on the phone, and a PC's Chromium has none.

translate_tts is not an official API: it may stop or refuse at any time, and the app then reads with the
browser's own voice. Only the text goes to Google (never a photo). It takes about 200 characters at a
time, so the app sends one sentence (up to 。) per request.
"""
from __future__ import annotations

import logging
import urllib.parse
import urllib.request

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

TTS_URL = "https://translate.google.com/translate_tts"
TEXT_MAX = 200

router = APIRouter()
log = logging.getLogger("uvicorn.error")


@router.get("/speech")
def speech(text: str = Query(..., min_length=1, max_length=TEXT_MAX, description="one sentence of the spoken summary")):
    url = TTS_URL + "?" + urllib.parse.urlencode({"ie": "UTF-8", "tl": "ja", "client": "tw-ob", "q": text})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            audio = r.read()
    except OSError as e:   # refused, changed or unreachable: the app falls back to the browser's voice
        log.warning("translate_tts failed: %s", e)
        raise HTTPException(502, f"translate_tts: {e}") from e
    return Response(audio, media_type="audio/mpeg", headers={"Cache-Control": "max-age=86400"})
