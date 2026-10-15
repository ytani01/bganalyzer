// The board as data: {points[24], bar_white, bar_black}, as the server has it. points[i] is the
// point i+1 seen by 手前 ("white"): > 0 手前's checkers, < 0 奥's. Pure functions; nothing here
// touches the page.
"use strict";

const BgBoard = (() => {
  const START = [-2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2];
  const other = (side) => (side === "white" ? "black" : "white");

  function start() {
    return { points: START.slice(), bar_white: 0, bar_black: 0 };
  }

  function copy(b) {
    return b && { points: b.points.slice(), bar_white: b.bar_white, bar_black: b.bar_black };
  }

  // Checkers on the board and the bar, and borne off (15 less those), for each side.
  function counts(b) {
    const onW = b.points.reduce((s, n) => s + Math.max(n, 0), 0) + b.bar_white;
    const onB = b.points.reduce((s, n) => s + Math.max(-n, 0), 0) + b.bar_black;
    return { onW, onB, offW: 15 - onW, offB: 15 - onB };
  }

  // What stops the board from being analysed.
  function errors(b) {
    const { onW, onB } = counts(b);
    const errs = [];
    if (onW > 15) errs.push(`手前の駒が ${onW} 個あります（15個まで）`);
    if (onB > 15) errs.push(`奥の駒が ${onB} 個あります（15個まで）`);
    if (onW === 0 && onB === 0) errs.push("盤に駒がありません");
    return errs;
  }

  // The two colours the other way round.
  function swapColours(b) {
    return { points: b.points.map((n) => -n), bar_white: b.bar_black, bar_black: b.bar_white };
  }

  // Left and right the other way round (the home board read on the wrong side).
  function mirror(b) {
    return { ...copy(b), points: b.points.map((_, i) => b.points[i < 12 ? 11 - i : 35 - i]) };
  }

  const LEVELS = 5;   // checkers drawn in a stack; the 5th level of a taller stack carries the count

  // The checkers of `side` on a point (0..23) or on the bar, and the side whose checkers are on a point.
  function countOf(b, at, side) {
    if (at === "bar") return side === "white" ? b.bar_white : b.bar_black;
    const n = b.points[at];
    return side === "white" ? Math.max(n, 0) : Math.max(-n, 0);
  }
  const sideOn = (b, at) => (b.points[at] > 0 ? "white" : b.points[at] < 0 ? "black" : null);

  // n checkers of `side` on a point (the other side's go) or on the bar (the other side's stay).
  function set(b, at, side, n) {
    const out = copy(b);
    n = Math.max(0, Math.min(15, n));
    if (at === "bar") out[side === "white" ? "bar_white" : "bar_black"] = n;
    else out.points[at] = side === "white" ? n : -n;
    return out;
  }

  // A tap at `level` (1..5 from the board's edge, from the middle on the bar) of a point or of the bar's half of `side`: the stack
  // up to there; on its top checker one fewer; on the 5th level of a stack of 5 or more one more.
  // An empty point takes `side` (the colour last put); a point with checkers keeps theirs.
  function tap(b, at, level, side) {
    if (at !== "bar") side = sideOn(b, at) || side;
    const n = countOf(b, at, side);
    level = Math.max(1, Math.min(LEVELS, level));
    if (level === LEVELS && n >= LEVELS) return set(b, at, side, n + 1);
    return set(b, at, side, level === n ? n - 1 : level);
  }

  // Column (0..11, left to right) of a row -> point index (0..23), as 手前 sees the board with the
  // home board on `home` ("left" or "right"); and back.
  function pointAt(home, top, c) {
    if (home === "right") return top ? 12 + c : 11 - c;
    return top ? 23 - c : c;
  }

  function columnOf(home, i) {
    const top = i >= 12;
    if (home === "right") return { top, c: top ? i - 12 : 11 - i };
    return { top, c: top ? 23 - i : i };
  }

  return { START, LEVELS, other, start, copy, counts, errors, swapColours, mirror, countOf, sideOn, set, tap,
           pointAt, columnOf };
})();

if (typeof module !== "undefined") module.exports = BgBoard;
