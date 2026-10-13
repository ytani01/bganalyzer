// A best move as gnubg writes it ("bar/22* 13/8(2) 6/off"), turned into the hops a checker makes,
// so the board picture can draw them as arrows. Points are numbered by the side on roll (1..24),
// "bar" is 25 and "off" is 0, as in gnubg's move string.
"use strict";

const BgMoves = (() => {
  // "24/18/13 6/4*(2)" -> [{from: 24, to: 18, hit: false}, {from: 18, to: 13, ...}, {from: 6, to: 4, hit: true} x 2]
  function parse(move) {
    const hops = [];
    for (const part of String(move).trim().split(/\s+/)) {
      if (!part) continue;
      const m = part.match(/^(.*?)(?:\((\d+)\))?$/);
      const pts = m[1].split("/").map((x) => ({
        n: /^bar$/i.test(x.replace("*", "")) ? 25 : /^off$/i.test(x.replace("*", "")) ? 0 : Number(x.replace("*", "")),
        hit: x.endsWith("*"),
      }));
      if (pts.length < 2 || pts.some((p) => !Number.isInteger(p.n) || p.n < 0 || p.n > 25)) return null;
      const one = [];
      for (let k = 1; k < pts.length; k++) one.push({ from: pts[k - 1].n, to: pts[k].n, hit: pts[k].hit });
      for (let c = 0; c < (m[2] ? Number(m[2]) : 1); c++) hops.push(...one);
    }
    return hops;
  }

  // The hops of a move played on board ({points, bar_white, bar_black}; points[i] is point i+1 seen
  // from 手前, + for white) by side ("white" or "black"), in board terms:
  // [{from: i | "bar", to: i | "off", fromLevel, toLevel, hit}], where a level is the place in the
  // stack (0 = the checker at the edge of the board) the checker leaves from or lands on.
  // null when the move does not fit the board.
  function hops(board, side, move) {
    const list = parse(move);
    if (!list) return null;
    const sign = side === "white" ? 1 : -1;
    const pts = board.points.slice();
    const bar = { white: board.bar_white || 0, black: board.bar_black || 0 };
    const other = side === "white" ? "black" : "white";
    const index = (n) => (side === "white" ? n - 1 : 24 - n);   // the mover's point n -> points[] index
    const out = [];
    for (const h of list) {
      let from, fromLevel;
      if (h.from === 25) {
        if (bar[side] < 1) return null;
        from = "bar";
        fromLevel = --bar[side];
      } else {
        from = index(h.from);
        if (from < 0 || from > 23 || pts[from] * sign < 1) return null;
        fromLevel = Math.abs(pts[from]) - 1;
        pts[from] -= sign;
      }
      let to, toLevel = 0, hit = false;
      if (h.to === 0) {
        to = "off";
      } else {
        to = index(h.to);
        if (to < 0 || to > 23) return null;
        if (pts[to] * sign === -1) {        // a blot is hit and goes to the bar
          pts[to] = 0;
          bar[other]++;
          hit = true;
        } else if (pts[to] * sign < 0) {
          return null;
        }
        toLevel = Math.abs(pts[to]);
        pts[to] += sign;
      }
      out.push({ from, to, fromLevel, toLevel, hit });
    }
    return out;
  }

  return { parse, hops };
})();

if (typeof module !== "undefined") module.exports = BgMoves;
