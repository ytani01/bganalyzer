"""Analyse a backgammon position with GNU Backgammon (run by engine.py).

All results are reported from both sides' point of view using the recognizer's
convention: White = the player at the bottom of the photo, Black = the other.
"""
from __future__ import annotations

import sys
from pathlib import Path

from engine import evaluate, shutdown  # noqa: F401  shutdown: app.py stops the gnubg helper through this module

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "recognizer"))
from position import Position  # noqa: E402

DEFAULT_PLIES = 2   # 2-ply: gnubg's usual analysis strength, ~30 ms per position
MAX_PLIES = 3
SIDES = ("white", "black")


def names_ja(white_light: bool = True) -> dict:
    """The sides in Japanese by their checkers' colour, as drawn: the lighter ones are 白 (TODO-086)."""
    return {"white": "白", "black": "黒"} if white_light else {"white": "黒", "black": "白"}


NAME_JA = names_ja()
CUBE_VALUES = (1, 2, 4, 8, 16, 32, 64)
MAX_MATCH = 64   # gnubg plays matches up to 64 points


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
            dice: tuple[int, int] | None = None, max_moves: int = 5,
            cube_value: int = 1, cube_owner: str | None = None, doubled: bool = False,
            match_length: int = 0, score_white: int = 0, score_black: int = 0, crawford: bool = False) -> dict:
    """Win/gammon/backgammon chances, equity and pip counts for `pos`.

    `on_roll` is the side about to roll. With `dice`, also returns the best
    checker plays for that roll. Also returns the cube decision before the roll (with dice, only
    when `on_roll` should have doubled: TODO-096): whether `on_roll` should double, and whether
    the other side should take. The cube shows
    `cube_value` and is owned by `cube_owner` (None: in the middle). `doubled`: `on_roll` has
    just doubled, and the cube (showing the new value) waits on the other side's take or pass.
    `match_length` 0 is a money game (Jacoby rule); else a match to that many points with the
    sides' scores and whether this is the Crawford game (no doubling).
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
    if not 0 <= match_length <= MAX_MATCH:
        raise ValueError(f"match_length must be 0 (money) .. {MAX_MATCH}")
    score = {"white": score_white, "black": score_black}
    if match_length == 0:
        if score_white or score_black or crawford:
            raise ValueError("a money game has no score and no Crawford game")
    else:
        if not all(0 <= v < match_length for v in score.values()):
            raise ValueError("each score must be 0 .. match_length - 1")
        away1 = [v == match_length - 1 for v in score.values()]
        if crawford and sum(away1) != 1:
            raise ValueError("the Crawford game needs one side (only) 1 point from winning the match")
        if crawford and cube_value != 1:
            # app.js looks for "Crawford" here: a reading that took the Crawford game off says nothing (TODO-153)
            raise ValueError("no doubling in the Crawford game: the cube stays at 1 in the middle")
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
        "match": {"length": match_length, "score": score, "crawford": crawford} if match_length else None,
    }

    winner = "white" if pos.off_white == 15 else "black" if pos.off_black == 15 else None
    if winner:
        result.update(game_over=True, favourite=winner,
                      probabilities=None, equity=None, moves=None, cube=None, luck=None)
        return result

    # The cube question: the cube as it was before on_roll's (possible) double.
    ask = None
    if doubled:
        before = cube_value // 2
        ask = (before, -1 if before == 1 else 0)
    elif cube_owner in (None, on_roll):
        ask = (cube_value, -1 if cube_owner is None else 0)
    # the match, from on_roll's side, with the cube's number for the evaluation (before a double)
    match = None
    if match_length:
        match = (match_length, (score[on_roll], score[other(on_roll)]), crawford, ask[0] if ask else cube_value)
    (win, wg, wbg, lg, lbg, equity), hint, moves, luck = evaluate(
        pid, plies, None if dice is None else tuple(dice), max_moves, ask, match)
    cube = _cube_result(hint, on_roll, ask[0], doubled, dice is not None) if hint else None
    if cube and dice is not None and not cube["double"]:
        cube = None   # with dice, only when on_roll should have doubled before rolling (TODO-096)

    def pct(x: float) -> float:
        return round(100 * x, 1)

    mover = {"win": pct(win), "gammon": pct(wg), "backgammon": pct(wbg)}
    opponent = {"win": pct(1 - win), "gammon": pct(lg), "backgammon": pct(lbg)}
    result.update(
        game_over=False,
        probabilities={on_roll: mover, other(on_roll): opponent},
        # Cubeless equity for the side on roll (+1 = sure single win; in a match, gnubg's money-like
        # equity from the match winning chances).
        equity={on_roll: round(equity, 3), other(on_roll): round(-equity, 3)},
        # money: by the equity, as before; a match: by the chance to win this game (the match equity
        # can favour the side less likely to win it)
        favourite=on_roll if (win > 0.5 if match_length else equity > 0) else other(on_roll),
        moves=moves,
        cube=cube,
        luck=None if luck is None else round(luck, 3),   # the roll's luck for on_roll (TODO-098)
    )
    return result


def _cube_result(hint: dict, doubler: str, value: int, doubled: bool, rolled: bool = False) -> dict:
    """The cube decision in the app's terms, from gnubg's: should the doubler double, and should
    the other side take. Equities are the doubler's, in units of the cube before the double."""
    proper = hint["proper"].lower()
    too_good = proper.startswith("too good")
    optional = proper.startswith("optional")   # "Optional double, take": doubling or not is the same
    return {
        "question": "take" if doubled else "double",
        "doubler": doubler,
        "taker": other(doubler),
        "value": value,                  # the cube before the double
        "equity": hint["equity"],
        "double": proper.startswith(("double", "redouble")),
        "too_good": too_good,            # better to play on for a gammon than to cash
        "optional": optional,            # double or not, either is right (seen in matches)
        "take": "take" in proper or "beaver" in proper,
        "proper": hint["proper"],        # gnubg's words, e.g. "No double, take (23.0%)"
        "rolled": rolled,                # the dice are in: should the doubler have doubled before rolling
    }


def summary_ja(r: dict, name: dict = NAME_JA) -> str:
    """One-line Japanese summary for display (name: names_ja)."""
    if r["game_over"]:
        return f"{name[r['favourite']]}の勝ちで終局しています。"
    p = r["probabilities"]
    fav = r["favourite"]
    text = (match_ja(r["match"], name) + "。" if r.get("match") else "") + (f"{name[fav]}が有利: 勝率 {p[fav]['win']}%（ギャモン {p[fav]['gammon']}%）、"
            f"ピップ {name['white']} {r['pips']['white']} / {name['black']} {r['pips']['black']}")
    if r.get("cube"):
        text += "。" + cube_summary_ja(r["cube"], name)
    return text


def cube_summary_ja(c: dict, name: dict = NAME_JA) -> str:
    """The cube decision in one Japanese sentence."""
    d, t = name[c["doubler"]], name[c["taker"]]
    word = "リダブル" if c["value"] > 1 else "ダブル"
    take = "テイク" if c["take"] else "パス"
    if c["question"] == "take":
        why = ("ダブルは正しい" if c["double"] else f"{word}はしてもしなくてもよい" if c.get("optional") else
               "本当はダブルせずギャモンを狙う局面" if c["too_good"] else "ダブルは早すぎる")
        return f"{t}は{take}（{d}の{why}）"
    if c.get("rolled"):
        d = f"振る前、{d}"
    if c["double"]:
        return f"{d}は{word}すべき、{t}は{take}"
    if c.get("optional"):
        return f"{d}は{word}してもしなくてもよい（{word}されたら{t}は{take}）"
    if c["too_good"]:
        return f"{d}は{word}せずギャモンを狙う（{word}されたら{t}は{take}）"
    return f"{d}はまだ{word}しない（{word}されたら{t}は{take}）"


def match_ja(m: dict, name: dict = NAME_JA) -> str:
    """The match in Japanese, e.g. "7 ポイントマッチ 白 3 対 黒 5（クロフォード）"."""
    return (f"{m['length']} ポイントマッチ {name['white']} {m['score']['white']} 対 {name['black']} {m['score']['black']}"
            + ("（クロフォード）" if m["crawford"] else ""))
