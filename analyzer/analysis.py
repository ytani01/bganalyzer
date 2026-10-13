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


def _engine(pid: str, plies: int, dice, max_moves: int, cube=None):
    import gnubg
    board = gnubg.position_from_id(pid)   # (opponent, player on roll)
    ctx = gnubg.eval_context(0, plies)    # cubeless
    probs = gnubg.evaluate(board, gnubg.cube_info(), ctx)
    if cube is not None:
        return probs, _cube_hint(gnubg, pid, plies, *cube)
    moves = None
    if dice is not None:
        found = gnubg.find_best_moves(board, gnubg.cube_info(), ctx, tuple(dice))
        tuples = _complete_moves(gnubg, board, ctx, tuple(dice), found, max_moves)
        moves = [{"move": gnubg.move_tuple_to_string(t, board),
                  "equity": round(m["score"], 3)} for t, m in zip(tuples, found)]
    return probs, moves


# The Python module has no call for a cube decision (gnubg.hint() refuses cube hints, and
# evaluate() gives only the cubeless equity), so it is asked as gnubg's own "hint" command
# about a money game set up in the helper, and the printed answer is read.
_session_ready = False


def _gnubg_output(gnubg, command: str) -> str:
    """What a gnubg command prints (from C, so stdout is caught at the file descriptor)."""
    import ctypes
    import os
    import tempfile

    libc = ctypes.CDLL(None)
    sys.stdout.flush()
    saved = os.dup(1)
    with tempfile.TemporaryFile() as f:
        os.dup2(f.fileno(), 1)
        try:
            gnubg.command(command)
        finally:
            libc.fflush(None)
            os.dup2(saved, 1)
            os.close(saved)
        f.seek(0)
        return f.read().decode(errors="replace")


def _cube_hint(gnubg, pid: str, plies: int, value: int, owner: int):
    """gnubg's cube decision for the player on roll (before rolling), money game.

    owner: -1 centred, 0 the player on roll, 1 the opponent. Returns the cubeful equities
    for the player on roll (in units of the cube as it is) and gnubg's proper action, or None
    when the player on roll cannot double."""
    global _session_ready
    if not _session_ready:
        for c in ("set threads 1", "set sound enable off", "set display off", "set confirm new off",
                  "set player 0 human", "set player 1 human", "set beavers 0", "new game"):
            _gnubg_output(gnubg, c)
        _session_ready = True
    for c in ("set turn 0", f"set board {pid}", f"set cube value {value}",
              "set cube centre" if owner < 0 else f"set cube owner {owner}",
              f"set evaluation cubedecision evaluation plies {plies}"):
        _gnubg_output(gnubg, c)
    return _parse_cube_hint(_gnubg_output(gnubg, "hint"))


def _parse_cube_hint(text: str):
    """Read gnubg's printed cube analysis:

        Cubeful equities:
        1. No double           +0.098
        2. Double, pass        +1.000  (+0.902)
        3. Double, take        -0.171  (-0.269)
        Proper cube action: No double, take (23.0%)
    """
    import re

    eq = {}
    for name, key in (("no (?:re)?double", "no_double"), ("(?:re)?double, pass", "double_pass"),
                      ("(?:re)?double, take", "double_take")):
        m = re.search(rf"^\s*\d\.\s+{name}\s+([+-]?\d+\.\d+)", text, re.I | re.M)
        if m:
            eq[key] = float(m.group(1))
    m = re.search(r"^Proper cube action:\s*(.+?)\s*$", text, re.M)
    if len(eq) < 3 or not m:
        return None
    return {"equity": eq, "proper": m.group(1)}


# A play is a list of (from, to) steps, numbered as gnubg does from the side of the
# player on roll: 1-24 the points, 25 the bar, 0 off. A board is (opponent, player).

def _step(board, src, dst):
    opp, me = list(board[0]), list(board[1])
    me[src - 1] -= 1
    if dst:
        me[dst - 1] += 1
        if opp[24 - dst] == 1:            # a blot: hit it onto the bar
            opp[24 - dst] = 0
            opp[24] += 1
    return tuple(opp), tuple(me)


def _legal_plays(board, dice) -> dict:
    """Every legal play for the roll, one per resulting board: {board: steps}."""
    d1, d2 = dice
    orders = [(d1,) * 4] if d1 == d2 else [(d1, d2), (d2, d1)]
    found: dict = {}   # resulting board -> (steps, dice used)

    def sources(me, d):
        if me[24]:
            return [(25, 25 - d)]
        home = not any(me[6:25])
        out = []
        for i in range(24):
            if me[i]:
                if i - d >= 0:
                    out.append((i + 1, i + 1 - d))
                elif home and (i - d == -1 or not any(me[i + 1:6])):
                    out.append((i + 1, 0))
        return out

    def walk(b, rest, steps, used):
        moved = False
        if rest:
            for src, dst in sources(b[1], rest[0]):
                if dst and b[0][24 - dst] >= 2:
                    continue              # the point is made
                moved = True
                walk(_step(b, src, dst), rest[1:], steps + [(src, dst)], used + [rest[0]])
        if not moved:
            found.setdefault(b, (steps, used))

    for order in orders:
        walk(tuple(map(tuple, board)), order, [], [])
    most = max(len(s) for s, _ in found.values())
    plays = {b: (s, u) for b, (s, u) in found.items() if len(s) == most}
    if most == 1 and d1 != d2 and any(u == [max(dice)] for _, u in plays.values()):
        plays = {b: v for b, v in plays.items() if v[1] == [max(dice)]}   # must use the larger die
    return {b: s for b, (s, _) in plays.items()}


def _below(a, b) -> bool:
    """Can the player's checkers on board a still move on to board b?"""
    ca = cb = 0
    for i in range(24, -1, -1):
        ca, cb = ca + a[1][i], cb + b[1][i]
        if cb > ca:
            return False
    return True


def _complete_moves(gnubg, board, ctx, dice, found, count) -> list[tuple]:
    """The move tuples of the first count of gnubg's find_best_moves, made whole.

    gnubg's tuple stops at the first checker borne off: 3-1 gives (3,) for both
    "3/off 1/off" and "3/off 3/2". Such a play is found again among the legal
    plays: one that can follow the steps we do have, scoring what gnubg scored.
    """
    tuples = [tuple(m["move"]) for m in found]
    if all(len(t) % 2 == 0 for t in tuples[:count]):
        return tuples[:count]
    plays = _legal_plays(board, dice)
    taken = set()                         # the plays whose tuples are whole
    for t in tuples:
        if len(t) % 2 == 0:
            b = tuple(map(tuple, board))
            for k in range(0, len(t), 2):
                b = _step(b, t[k], t[k + 1])
            taken.add(b)
    tuples = tuples[:count]
    open_ = {}                            # index -> the board after the steps we have
    for n, t in enumerate(tuples):
        if len(t) % 2:
            b = tuple(map(tuple, board))
            for k in range(0, len(t) - 1, 2):
                b = _step(b, t[k], t[k + 1])
            open_[n] = _step(b, t[-1], 0)     # the step that was cut: a checker borne off
    out = list(tuples)
    scores: dict = {}

    def gap(n, a):                        # how far the play leading to a is from gnubg's score
        if a not in scores:
            scores[a] = -gnubg.evaluate((a[1], a[0]), gnubg.cube_info(), ctx)[5]
        return round(abs(found[n]["score"] - scores[a]), 6)

    # The steps we have can lead to several plays, and the board after them can even be
    # another play's end ("5/off 1/off" cut to "5/off" = "5/4 4/off"), so go by the score:
    # match each cut move to a play gnubg scored the same, then to any play that fits.
    cands = {n: [a for a in plays if a not in taken and _below(b, a)] for n, b in open_.items()}
    if any(len(c) > 1 for c in cands.values()):
        cands = {n: sorted(c, key=lambda a: (gap(n, a), a != open_[n])) for n, c in cands.items()}
    owner: dict = {}                      # play -> the cut move it is given to

    def give(n, edges, seen):             # Kuhn's augmenting path
        for a in edges(n):
            if a not in seen:
                seen.add(a)
                if a not in owner or give(owner[a], edges, seen):
                    owner[a] = n
                    return True
        return False

    for edges in (lambda n: [a for a in cands[n] if gap(n, a) <= 1e-5], lambda n: cands[n]):
        for n in cands:
            if n not in owner.values():
                give(n, edges, set())
    for a, n in owner.items():
        out[n] = tuple(x for step in plays[a] for x in step)
    return out


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


def shutdown() -> None:
    """Stop the gnubg helper. Call on server exit, or it outlives the server."""
    global _pool
    if _pool is not None:
        _pool.shutdown()
        _pool = None


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


CUBE_VALUES = (1, 2, 4, 8, 16, 32, 64)


def analyze(pos: Position, on_roll: str = "white", *, plies: int = DEFAULT_PLIES,
            dice: tuple[int, int] | None = None, max_moves: int = 5,
            cube_value: int = 1, cube_owner: str | None = None, doubled: bool = False) -> dict:
    """Win/gammon/backgammon chances, equity and pip counts for `pos`.

    `on_roll` is the side about to roll. With `dice`, also returns the best
    checker plays for that roll. Without dice, also returns the cube decision (money game):
    whether `on_roll` should double, and whether the other side should take. The cube shows
    `cube_value` and is owned by `cube_owner` (None: in the middle). `doubled`: `on_roll` has
    just doubled, and the cube (showing the new value) waits on the other side's take or pass.
    """
    if on_roll not in SIDES:
        raise ValueError("on_roll must be 'white' or 'black'")
    if not 0 <= plies <= MAX_PLIES:
        raise ValueError(f"plies must be 0..{MAX_PLIES}")
    if dice is not None and (len(dice) != 2 or not all(1 <= d <= 6 for d in dice)):
        raise ValueError("dice must be two numbers 1..6")
    if cube_value not in CUBE_VALUES:
        raise ValueError(f"cube_value must be one of {CUBE_VALUES}")
    if cube_owner not in (None, *SIDES):
        raise ValueError("cube_owner must be 'white', 'black' or null (in the middle)")
    if (cube_value == 1) != (cube_owner is None) and not doubled:
        raise ValueError("a cube showing 1 is in the middle; a doubled cube has an owner")
    if doubled:
        if dice is not None:
            raise ValueError("no dice while a double waits on take or pass")
        if cube_value == 1 or cube_owner == on_roll:
            raise ValueError("a doubled cube shows 2 or more and lies on the side of the player doubled")
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
                      probabilities=None, equity=None, moves=None, cube=None)
        return result

    # The cube question: the cube as it was before on_roll's (possible) double.
    ask = None
    if doubled:
        before = cube_value // 2
        ask = (before, -1 if before == 1 else 0)
    elif dice is None and cube_owner in (None, on_roll):
        ask = (cube_value, -1 if cube_owner is None else 0)
    (win, wg, wbg, lg, lbg, equity), found = _call_engine(
        pid, plies, None if dice is None else tuple(dice), max_moves, ask)
    moves = found if ask is None else None
    cube = _cube_result(found, on_roll, ask[0], doubled) if ask and found else None

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
        cube=cube,
    )
    return result


def _cube_result(hint: dict, doubler: str, value: int, doubled: bool) -> dict:
    """The cube decision in the app's terms, from gnubg's: should the doubler double, and should
    the other side take. Equities are the doubler's, in units of the cube before the double."""
    proper = hint["proper"].lower()
    too_good = proper.startswith("too good")
    return {
        "question": "take" if doubled else "double",
        "doubler": doubler,
        "taker": other(doubler),
        "value": value,                  # the cube before the double
        "equity": hint["equity"],
        "double": proper.startswith(("double", "redouble")),
        "too_good": too_good,            # better to play on for a gammon than to cash
        "take": "take" in proper or "beaver" in proper,
        "proper": hint["proper"],        # gnubg's words, e.g. "No double, take (23.0%)"
    }


def summary_ja(r: dict) -> str:
    """One-line Japanese summary for display."""
    name = {"white": "手前", "black": "奥"}
    if r["game_over"]:
        return f"{name[r['favourite']]}の勝ちで終局しています。"
    p = r["probabilities"]
    fav = r["favourite"]
    text = (f"{name[fav]}が有利: 勝率 {p[fav]['win']}%（ギャモン {p[fav]['gammon']}%）、"
            f"ピップ 手前 {r['pips']['white']} / 奥 {r['pips']['black']}")
    if r.get("cube"):
        text += "。" + cube_summary_ja(r["cube"])
    return text


def cube_summary_ja(c: dict) -> str:
    """The cube decision in one Japanese sentence."""
    name = {"white": "手前", "black": "奥"}
    d, t = name[c["doubler"]], name[c["taker"]]
    word = "リダブル" if c["value"] > 1 else "ダブル"
    take = "テイク" if c["take"] else "パス"
    if c["question"] == "take":
        why = ("ダブルは正しい" if c["double"] else
               "本当はダブルせずギャモンを狙う局面" if c["too_good"] else "ダブルは早すぎる")
        return f"{t}は{take}（{d}の{why}）"
    if c["double"]:
        return f"{d}は{word}すべき、{t}は{take}"
    if c["too_good"]:
        return f"{d}は{word}せずギャモンを狙う（{word}されたら{t}は{take}）"
    return f"{d}はまだ{word}しない（{word}されたら{t}は{take}）"
