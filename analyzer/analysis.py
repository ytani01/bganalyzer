"""Analyse a backgammon position with GNU Backgammon (gnubg Python package).

All results are reported from both sides' point of view using the recognizer's
convention: White = the player at the bottom of the photo, Black = the other.
"""
from __future__ import annotations

import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recognizer"))
from position import Position  # noqa: E402

DEFAULT_PLIES = 2   # 2-ply: gnubg's usual analysis strength, ~30 ms per position
MAX_PLIES = 3
SIDES = ("white", "black")

# The gnubg extension crashes when evaluating (1-ply and up) on any thread but
# the main one, and web servers call handlers from worker threads. So gnubg runs
# on the main thread of one spawned helper process; this also serialises calls.
_pool: ProcessPoolExecutor | None = None


def _engine(pid: str, plies: int, dice, max_moves: int):
    import gnubg
    board = gnubg.position_from_id(pid)   # (opponent, player on roll)
    ctx = gnubg.eval_context(0, plies)    # cubeless
    probs = gnubg.evaluate(board, gnubg.cube_info(), ctx)
    moves = None
    if dice is not None:
        found = gnubg.find_best_moves(board, gnubg.cube_info(), ctx, tuple(dice))
        moves = [{"move": gnubg.move_tuple_to_string(m["move"], board),
                  "equity": round(m["score"], 3)} for m in found[:max_moves]]
    return probs, moves


def _call_engine(*args):
    global _pool
    for attempt in range(2):
        if _pool is None:
            _pool = ProcessPoolExecutor(1, mp_context=multiprocessing.get_context("spawn"))
        try:
            return _pool.submit(_engine, *args).result(timeout=60)
        except BrokenProcessPool:
            _pool = None   # helper died: start a fresh one and retry once
            if attempt:
                raise


def other(side: str) -> str:
    return "black" if side == "white" else "white"


def parse_position(pid: str, on_roll: str) -> Position:
    pos = Position.from_position_id(pid, on_roll)
    if pos.position_id(on_roll) != pid.rstrip("="):
        raise ValueError(f"invalid position id: {pid}")
    return pos


def _check(pos: Position) -> None:
    if any(n < 0 for n in (pos.bar_white, pos.bar_black, pos.off_white, pos.off_black)):
        raise ValueError("bar and off counts must not be negative")
    w, b = pos.counts()
    if w != 15 or b != 15:
        raise ValueError(f"each side needs 15 checkers (white {w}, black {b})")


def analyze(pos: Position, on_roll: str = "white", *, plies: int = DEFAULT_PLIES,
            dice: tuple[int, int] | None = None, max_moves: int = 5) -> dict:
    """Win/gammon/backgammon chances, equity and pip counts for `pos`.

    `on_roll` is the side about to roll. With `dice`, also returns the best
    checker plays for that roll.
    """
    if on_roll not in SIDES:
        raise ValueError("on_roll must be 'white' or 'black'")
    if not 0 <= plies <= MAX_PLIES:
        raise ValueError(f"plies must be 0..{MAX_PLIES}")
    if dice is not None and (len(dice) != 2 or not all(1 <= d <= 6 for d in dice)):
        raise ValueError("dice must be two numbers 1..6")
    _check(pos)

    pid = pos.position_id(on_roll)
    pw, pb = pos.pips()
    result = {
        "position_id": pid,
        "on_roll": on_roll,
        "pips": {"white": pw, "black": pb,
                 "leader": "white" if pw < pb else "black" if pb < pw else None,
                 "difference": abs(pw - pb)},
        "plies": plies,
    }

    winner = "white" if pos.off_white == 15 else "black" if pos.off_black == 15 else None
    if winner:
        result.update(game_over=True, favourite=winner,
                      probabilities=None, equity=None, moves=None)
        return result

    (win, wg, wbg, lg, lbg, equity), moves = _call_engine(
        pid, plies, None if dice is None else tuple(dice), max_moves)

    def pct(x: float) -> float:
        return round(100 * x, 1)

    mover = {"win": pct(win), "gammon": pct(wg), "backgammon": pct(wbg)}
    opponent = {"win": pct(1 - win), "gammon": pct(lg), "backgammon": pct(lbg)}
    result.update(
        game_over=False,
        probabilities={on_roll: mover, other(on_roll): opponent},
        # Cubeless money equity for the side on roll (+1 = sure single win).
        equity={on_roll: round(equity, 3), other(on_roll): round(-equity, 3)},
        favourite=on_roll if equity > 0 else other(on_roll),
        moves=moves,
    )
    return result


def summary_ja(r: dict) -> str:
    """One-line Japanese summary for display."""
    name = {"white": "手前", "black": "奥"}
    if r["game_over"]:
        return f"{name[r['favourite']]}の勝ちで終局しています。"
    p = r["probabilities"]
    fav = r["favourite"]
    return (f"{name[fav]}が有利: 勝率 {p[fav]['win']}%（ギャモン {p[fav]['gammon']}%）、"
            f"ピップ 手前 {r['pips']['white']} / 奥 {r['pips']['black']}")
