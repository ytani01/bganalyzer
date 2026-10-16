"""GNU Backgammon (the gnubg Python package), run in a helper process.

The gnubg extension crashes when evaluating (1-ply and up) on any thread but the main one, and
web servers call handlers from worker threads. So gnubg runs on the main thread of one spawned
helper process; this also serialises calls. analysis.py turns what this returns into the API's
answer.

Positions are gnubg position ids, seen from the player on roll. A board is (opponent, player).
"""
from __future__ import annotations

import ctypes
import multiprocessing
import os
import re
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

_pool: ProcessPoolExecutor | None = None


def evaluate(pid: str, plies: int, dice, max_moves: int, cube=None, match=None):
    """In the helper: (win, win gammon, win backgammon, lose gammon, lose backgammon, equity) for the
    player on roll, cubeless, then

    - with cube = (value, owner): gnubg's cube decision before the roll (_cube_hint), or None when
      there is none; else None,
    - with dice: the best max_moves plays [{"move", "steps", "equity"}, ...]; else None,
    - with dice: the roll's luck (_luck); else None.

    match: None for a money game, else (length, (score of the player on roll, the opponent's),
    crawford, the cube's number)."""
    return _call(_engine, pid, plies, dice, max_moves, cube, match)


def shutdown() -> None:
    """Stop the gnubg helper. Call on server exit, or it outlives the server."""
    global _pool
    if _pool is not None:
        _pool.shutdown()
        _pool = None


def _call(fn, *args):
    global _pool
    for attempt in range(2):
        if _pool is None:
            _pool = ProcessPoolExecutor(1, mp_context=multiprocessing.get_context("spawn"))
        try:
            return _pool.submit(fn, *args).result(timeout=60)
        except BrokenProcessPool:
            _pool = None   # helper died: start a fresh one and retry once
            if attempt:
                raise


# ---------------------------------------------------------------- in the helper process

def _cube_infos(gnubg, match):
    """gnubg's cube info for the player on roll, and for the opponent (who is on roll after a play)."""
    if match is None:
        # money game, said in full: gnubg.cube_info() alone follows the session, which _cube_hint
        # may have left in a match
        money = gnubg.cube_info(1, -1, 0, 0, (0, 0), 0, 0)
        return money, money
    length, (me, opp), crawford, value = match   # the owner does not change a cubeless evaluation
    return (gnubg.cube_info(value, -1, 0, length, (me, opp), int(crawford), 0),
            gnubg.cube_info(value, -1, 0, length, (opp, me), int(crawford), 0))


def _engine(pid: str, plies: int, dice, max_moves: int, cube=None, match=None):
    import gnubg
    board = gnubg.position_from_id(pid)   # (opponent, player on roll)
    ctx = gnubg.eval_context(0, plies)    # cubeless
    ci, ci_opp = _cube_infos(gnubg, match)
    probs = gnubg.evaluate(board, ci, ctx)
    hint = None if cube is None else _cube_hint(gnubg, pid, plies, *cube, match=match)
    moves = None
    if dice is not None:
        found = gnubg.find_best_moves(board, ci, ctx, tuple(dice))
        tuples = _complete_moves(gnubg, board, ctx, tuple(dice), found, max_moves, ci_opp)
        # steps: one [from, to] per die, as gnubg plays them (points by the side on roll,
        # 25 = bar, 0 = off), so "22/15" can be drawn through the point it passes
        moves = [{"move": gnubg.move_tuple_to_string(t, board),
                  "steps": [[t[k], t[k + 1]] for k in range(0, len(t), 2)],
                  "equity": round(m["score"], 3)} for t, m in zip(tuples, found)]
    return probs, hint, moves, None if dice is None else _luck(gnubg, board, min(plies, 1), ci, ci_opp, tuple(dice))


def _luck(gnubg, board, plies, ci, ci_opp, dice) -> float:
    """The roll's luck for the player on roll, as gnubg reckons it (cubeless; TODO-098): the best play's
    equity with these dice less the average over the 21 rolls. At most 1-ply: 21 searches at 2-ply
    take over a second."""
    ctx = gnubg.eval_context(0, plies)

    def best(d):
        found = gnubg.find_best_moves(board, ci, ctx, d)
        # no legal play: the board stays and the opponent rolls
        return found[0]["score"] if found else -gnubg.evaluate((board[1], board[0]), ci_opp, ctx)[5]

    rolls = [(a, b) for a in range(1, 7) for b in range(a, 7)]
    mean = sum(best(r) * (1 if r[0] == r[1] else 2) for r in rolls) / 36
    return best(tuple(sorted(dice))) - mean


# The Python module has no call for a cube decision (gnubg.hint() refuses cube hints, and
# evaluate() gives only the cubeless equity), so it is asked as gnubg's own "hint" command
# about a game set up in the helper, and the printed answer is read.
_session_ready = False
_in_match = False   # the helper's gnubg session is a match (set up by the last call), not money


def _gnubg_output(gnubg, command: str) -> str:
    """What a gnubg command prints (from C, so stdout is caught at the file descriptor)."""
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


def _cube_hint(gnubg, pid: str, plies: int, value: int, owner: int, match=None):
    """gnubg's cube decision for the player on roll (before rolling), in a money game or the match
    (as in evaluate; its cube is not used here).

    owner: -1 centred, 0 the player on roll, 1 the opponent. Returns the cubeful equities
    for the player on roll (in units of the cube as it is) and gnubg's proper action, or None
    when the player on roll cannot double (also in the Crawford game)."""
    global _session_ready, _in_match
    if not _session_ready:
        for c in ("set threads 1", "set sound enable off", "set display off", "set confirm new off",
                  "set player 0 human", "set player 1 human", "set beavers 0", "new game"):
            _gnubg_output(gnubg, c)
        _session_ready = True
    if match is not None:
        # set up afresh each time. A score 1 away is taken by gnubg as post-Crawford unless told
        # otherwise; "set crawford" is refused (harmlessly) when no one is 1 away.
        length, (me, opp), crawford = match[:3]
        for c in (f"new match {length}", f"set score {me} {opp}", f"set crawford {'on' if crawford else 'off'}"):
            _gnubg_output(gnubg, c)
        _in_match = True
    elif _in_match:
        _gnubg_output(gnubg, "new session")   # back to money ("new game" would go on with the match)
        _in_match = False
    for c in ("set turn 0", f"set board {pid}", f"set cube value {value}",
              "set cube centre" if owner < 0 else f"set cube owner {owner}",
              f"set evaluation cubedecision evaluation plies {plies}"):
        _gnubg_output(gnubg, c)
    return _parse_cube_hint(_gnubg_output(gnubg, "hint"))


_CUBE_LINES = (("no (?:re)?double", "no_double"), ("(?:re)?double, pass", "double_pass"),
               ("(?:re)?double, take", "double_take"))


def _parse_cube_hint(text: str):
    """Read gnubg's printed cube analysis:

        Cubeful equities:
        1. No double           +0.098
        2. Double, pass        +1.000  (+0.902)
        3. Double, take        -0.171  (-0.269)
        Proper cube action: No double, take (23.0%)
    """
    eq = {}
    for name, key in _CUBE_LINES:
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


def _play(board, steps):
    """board after the steps [from, to, from, to, ...] (a gnubg move tuple)."""
    b = tuple(map(tuple, board))
    for k in range(0, len(steps), 2):
        b = _step(b, steps[k], steps[k + 1])
    return b


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


def _complete_moves(gnubg, board, ctx, dice, found, count, ci_opp) -> list[tuple]:
    """The move tuples of the first count of gnubg's find_best_moves, made whole.

    gnubg's tuple stops at the first checker borne off: 3-1 gives (3,) for both
    "3/off 1/off" and "3/off 3/2". Such a play is found again among the legal
    plays: one that can follow the steps we do have, scoring what gnubg scored
    (ci_opp: the cube info find_best_moves used, from the opponent's side).
    """
    tuples = [tuple(m["move"]) for m in found]
    if all(len(t) % 2 == 0 for t in tuples[:count]):
        return tuples[:count]
    plays = _legal_plays(board, dice)
    taken = {_play(board, t) for t in tuples if len(t) % 2 == 0}   # the plays whose tuples are whole
    tuples = tuples[:count]
    # index -> the board after the steps we have, and the step that was cut: a checker borne off
    open_ = {n: _step(_play(board, t[:-1]), t[-1], 0) for n, t in enumerate(tuples) if len(t) % 2}
    out = list(tuples)
    scores: dict = {}

    def gap(n, a):                        # how far the play leading to a is from gnubg's score
        if a not in scores:
            scores[a] = -gnubg.evaluate((a[1], a[0]), ci_opp, ctx)[5]
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
