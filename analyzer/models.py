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
    # The doubling cube. The answer has the cube decision before the roll (with dice, only when a double was due).
    cube_value: int = 1
    cube_owner: str | None = None   # white, black or null (in the middle)
    doubled: bool = False           # on_roll has just doubled to cube_value: take or pass?
    # The match: length 0 = money game. Scores are White's and Black's; crawford: no doubling this game.
    match_length: int = 0
    score_white: int = 0
    score_black: int = 0
    crawford: bool = False
    # Which checkers are White's (the player at the bottom): 1 the lighter, 0 the darker. Only for the
    # words: the lighter side is called 白 (TODO-086). Without it, White is 白.
    bottom_colour: int | None = None
