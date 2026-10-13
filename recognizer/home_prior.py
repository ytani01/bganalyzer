"""Learn where checkers usually stand, to guess which side the bottom player's home board is on.

A photo shows the board but not which way the players move: the same checkers read with the
home on the other side give a mirrored position, which is legal too. Real positions are not
symmetric that way (points like the 6, 8 and 13 fill up, the 7 and 12 less), so the more
likely of the two tells the side.

Run this once to make home_prior.json from gnubg self-play (gnubg is in the dev environment):
    uv run python recognizer/home_prior.py
"""
import json
import random
from pathlib import Path

CLIP = 5   # counts above this are lumped together
OUT = Path(__file__).resolve().parent / "home_prior.json"
# How much likelier (log) the chosen side must be. Below this the guess is a coin toss: keep the default.
# On gnubg self-play, a margin of 1 or more covers 99% of positions and is right 99% of the time
# even with 8 of the 24 points misread (README「ホームボードの推測」).
MIN_MARGIN = 1.0

_logp = None


def mirror(points):
    """The same checkers read with the home on the other side."""
    return [points[11 - i] if i < 12 else points[35 - i] for i in range(24)]


def log_likelihood(points):
    global _logp
    if _logp is None:
        _logp = json.loads(OUT.read_text())["logp"]
    return sum(_logp[i][state(n)] for i, n in enumerate(points))


def guess(points, default="right"):
    """points: White's points read with the home on the right. Returns (home, margin): the side
    whose reading is likelier, and by how much (log); `default` when it is too close to call."""
    margin = log_likelihood(points) - log_likelihood(mirror(points))
    if abs(margin) < MIN_MARGIN:
        return default, margin
    return ("right" if margin > 0 else "left"), margin


def _apply(board, move):
    """board = (opponent, player) 25-arrays (index 24 = bar), move = gnubg move tuple."""
    opp, me = list(board[0]), list(board[1])
    move = tuple(move) + (0,) * (len(move) % 2)   # gnubg leaves out a trailing 0 (= borne off)
    for f, t in zip(move[0::2], move[1::2]):
        if f < 0:
            break
        me[f - 1] -= 1
        if t > 0:
            me[t - 1] += 1
            if opp[24 - t] == 1:   # hit: the blot goes to the bar
                opp[24 - t] = 0
                opp[24] += 1
    return opp, me


def _points(board):
    """White (on roll) = board[1]: signed counts on White's points 1..24."""
    opp, me = board
    return [me[i] - opp[23 - i] for i in range(24)]


def selfplay(games, seed=0):
    import gnubg
    rnd = random.Random(seed)
    ctx = gnubg.eval_context(0, 0)
    start = gnubg.position_from_id("4HPwATDgc/ABMA")
    out = []
    for _ in range(games):
        board = start
        for _ in range(400):
            d = (rnd.randint(1, 6), rnd.randint(1, 6))
            moves = gnubg.find_best_moves(board, gnubg.cube_info(), ctx, d)
            if moves:
                # people don't always play the best move: sometimes take one of the next few
                k = 0 if rnd.random() < 0.7 else rnd.randrange(min(4, len(moves)))
                board = _apply(board, moves[k]["move"])
                out.append(_points(board))   # the player who just moved, as White
            board = board[::-1]
            if sum(board[0][:25]) == 0 or sum(board[1][:25]) == 0:
                break
    return out


def state(n):
    return max(-CLIP, min(CLIP, n)) + CLIP


def learn(positions):
    counts = [[1.0] * (2 * CLIP + 1) for _ in range(24)]   # add-one smoothing
    for pts in positions:
        for i, n in enumerate(pts):
            counts[i][state(n)] += 1
    import math
    return [[round(math.log(c / sum(row)), 3) for c in row] for row in counts]


if __name__ == "__main__":
    pos = selfplay(4000)
    OUT.write_text(json.dumps({"clip": CLIP, "positions": len(pos), "logp": learn(pos)}) + "\n")
    print(f"{len(pos)} positions -> {OUT.name}")
