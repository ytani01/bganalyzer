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


def evaluate(pid: str, plies: int, dice, max_moves: int, cube=None):
    """In the helper: (win, win gammon, win backgammon, lose gammon, lose backgammon, equity) for the
    player on roll, cubeless, and then

    - with cube = (value, owner): gnubg's cube decision (_cube_hint), or None when there is none,
    - else with dice: the best max_moves plays [{"move", "steps", "equity"}, ...],
    - else None."""
    return _call(_engine, pid, plies, dice, max_moves, cube)


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
        # steps: one [from, to] per die, as gnubg plays them (points by the side on roll,
        # 25 = bar, 0 = off), so "22/15" can be drawn through the point it passes
        moves = [{"move": gnubg.move_tuple_to_string(t, board),
                  "steps": [[t[k], t[k + 1]] for k in range(0, len(t), 2)],
                  "equity": round(m["score"], 3)} for t, m in zip(tuples, found)]
    return probs, moves


# The Python module has no call for a cube decision (gnubg.hint() refuses cube hints, and
# evaluate() gives only the cubeless equity), so it is asked as gnubg's own "hint" command
# about a money game set up in the helper, and the printed answer is read.
_session_ready = False


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
    taken = {_play(board, t) for t in tuples if len(t) % 2 == 0}   # the plays whose tuples are whole
    tuples = tuples[:count]
    # index -> the board after the steps we have, and the step that was cut: a checker borne off
    open_ = {n: _step(_play(board, t[:-1]), t[-1], 0) for n, t in enumerate(tuples) if len(t) % 2}
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
