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

  // A button of the editor (op: "w+", "w-", "b+", "b-" or "clear") on a point (0..23) or "bar".
  function edit(b, at, op) {
    const out = copy(b);
    if (at === "bar") {
      if (op === "w+") out.bar_white++;
      if (op === "w-") out.bar_white = Math.max(0, out.bar_white - 1);
      if (op === "b+") out.bar_black++;
      if (op === "b-") out.bar_black = Math.max(0, out.bar_black - 1);
      if (op === "clear") out.bar_white = out.bar_black = 0;
      return out;
    }
    let n = out.points[at];
    if (op === "w+") n = Math.max(n, 0) + 1;
    if (op === "w-" && n > 0) n--;
    if (op === "b+") n = Math.min(n, 0) - 1;
    if (op === "b-" && n < 0) n++;
    if (op === "clear") n = 0;
    out.points[at] = n;
    return out;
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

  return { START, other, start, copy, counts, errors, swapColours, mirror, edit, pointAt, columnOf };
})();

if (typeof module !== "undefined") module.exports = BgBoard;
