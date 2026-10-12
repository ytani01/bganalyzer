"""Backgammon position model, gnubg Position ID encoding and pip counts.

Board convention (from White's point of view, White sits at the bottom of the photo):
  points[i] = count on White's point i+1 (i = 0..23).
  >0 = White checkers, <0 = Black checkers.
  White moves 24 -> 1 (home board = points 1..6, bottom right).
  Black's point number for index i is 24 - i.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass, field, asdict

START = [0] * 24
START[5], START[7], START[12], START[23] = 5, 3, 5, 2
START[18], START[16], START[11], START[0] = -5, -3, -5, -2


@dataclass
class Position:
    points: list[int] = field(default_factory=lambda: [0] * 24)
    bar_white: int = 0
    bar_black: int = 0
    off_white: int = 0
    off_black: int = 0

    @classmethod
    def start(cls) -> "Position":
        return cls(points=list(START))

    def counts(self) -> tuple[int, int]:
        w = sum(n for n in self.points if n > 0) + self.bar_white + self.off_white
        b = -sum(n for n in self.points if n < 0) + self.bar_black + self.off_black
        return w, b

    def validate(self) -> list[str]:
        errs = []
        w, b = self.counts()
        if w != 15:
            errs.append(f"White has {w} checkers (expected 15)")
        if b != 15:
            errs.append(f"Black has {b} checkers (expected 15)")
        return errs

    def pips(self) -> tuple[int, int]:
        w = sum((i + 1) * n for i, n in enumerate(self.points) if n > 0) + 25 * self.bar_white
        b = sum((24 - i) * -n for i, n in enumerate(self.points) if n < 0) + 25 * self.bar_black
        return w, b

    # --- gnubg Position ID -------------------------------------------------
    def _player_arrays(self) -> tuple[list[int], list[int]]:
        """25-entry arrays (own points 1..24 then bar) for White and Black."""
        white = [max(self.points[i], 0) for i in range(24)] + [self.bar_white]
        black = [max(-self.points[23 - i], 0) for i in range(24)] + [self.bar_black]
        return white, black

    def position_id(self, on_roll: str = "white") -> str | None:
        """gnubg Position ID. The player on roll is encoded first."""
        white, black = self._player_arrays()
        if sum(white) > 15 or sum(black) > 15:
            return None
        first, second = (white, black) if on_roll == "white" else (black, white)
        bits = []
        for arr in (second, first):  # gnubg: opponent (anBoard[0]) first, then player on roll
            for n in arr:
                bits += [1] * n + [0]
        bits += [0] * (80 - len(bits))
        data = bytearray(10)
        for k, bit in enumerate(bits):
            if bit:
                data[k // 8] |= 1 << (k % 8)
        return base64.b64encode(bytes(data)).decode().rstrip("=")

    @classmethod
    def from_position_id(cls, pid: str, on_roll: str = "white") -> "Position":
        data = base64.b64decode(pid + "==")
        bits = [(data[k // 8] >> (k % 8)) & 1 for k in range(80)]
        arrs, cur, n = [], [], 0
        for bit in bits:
            if len(arrs) == 2:
                break
            if bit:
                n += 1
            else:
                cur.append(n)
                n = 0
                if len(cur) == 25:
                    arrs.append(cur)
                    cur = []
        second, first = arrs
        white, black = (first, second) if on_roll == "white" else (second, first)
        p = cls()
        for i in range(24):
            if white[i]:
                p.points[i] = white[i]
            if black[23 - i]:
                p.points[i] = -black[23 - i]
        p.bar_white, p.bar_black = white[24], black[24]
        p.off_white = 15 - sum(white)
        p.off_black = 15 - sum(black)
        return p

    def to_dict(self) -> dict:
        d = asdict(self)
        d["pips"] = dict(zip(("white", "black"), self.pips()))
        d["position_id_white_on_roll"] = self.position_id("white")
        d["position_id_black_on_roll"] = self.position_id("black")
        d["errors"] = self.validate()
        return d

    def ascii(self) -> str:
        def cell(n):
            return "  ." if n == 0 else (f"{n:>2}W" if n > 0 else f"{-n:>2}B")
        top = "".join(cell(self.points[i]) for i in range(12, 18)) + " |" + \
              "".join(cell(self.points[i]) for i in range(18, 24))
        bot = "".join(cell(self.points[i]) for i in range(11, 5, -1)) + " |" + \
              "".join(cell(self.points[i]) for i in range(5, -1, -1))
        pw, pb = self.pips()
        return (f" 13 14 15 16 17 18   19 20 21 22 23 24\n{top}\n{bot}\n"
                f" 12 11 10  9  8  7    6  5  4  3  2  1\n"
                f"bar W{self.bar_white} B{self.bar_black}  off W{self.off_white} B{self.off_black}"
                f"  pips W{pw} B{pb}")
