"""Request bodies of the HTTP API (app.py, samples.py)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from analysis import DEFAULT_PLIES, MAX_PLIES


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
