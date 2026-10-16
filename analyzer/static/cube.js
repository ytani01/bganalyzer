// The doubling cube on the board screen, and what it asks of the analysis; also the match it is played in.
// The cube is where it lies: "centre" (nobody owns it, showing 64), or on 手前's ("white") or
// 奥's ("black") side showing value. With no dice on the board, a cube on one side is taken to
// have just been offered to that side (offered: true): the other side doubled, and the question
// is take or pass. Otherwise the side owns it, and the question is whether the side on roll doubles.
"use strict";

const BgCube = (() => {
  const VALUES = [2, 4, 8, 16, 32, 64];
  const other = (side) => (side === "white" ? "black" : "white");

  // The fields of an /analyze request for this cube, with the side on roll (which a double decides).
  function request(cube, onRoll, dice) {
    if (!cube || cube.at === "centre") {
      return { on_roll: onRoll, cube_value: 1, cube_owner: null, doubled: false };
    }
    if (!dice && cube.offered) {
      return { on_roll: other(cube.at), cube_value: cube.value, cube_owner: cube.at, doubled: true };
    }
    return { on_roll: onRoll, cube_value: cube.value, cube_owner: cube.at, doubled: false };
  }

  // The cube as the recognizer read it (null: none seen, so in the middle). "field": it lies in a
  // playing field, so onRoll has just doubled and it is offered to the other side (TODO-045).
  // Its number is the one read (TODO-025), else 2.
  function fromRead(read, onRoll) {
    if (!read || read.at === "centre") return { at: "centre", value: 2, offered: true };
    const value = VALUES.includes(read.value) ? read.value : 2;
    if (read.at === "field") return { at: other(onRoll || "white"), value, offered: true };
    return { at: read.at, value, offered: true };
  }

  // The match (TODO-066): {length (0: a money game), white, black (the scores), crawford}, made whole:
  // a length the app offers, scores below it, and the Crawford game only when just one side is 1 away.
  const MATCH_LENGTHS = Array.from({ length: 26 }, (_, k) => k);
  function fixMatch(m) {
    m = m || {};
    const length = MATCH_LENGTHS.includes(Number(m.length)) ? Number(m.length) : 0;
    const score = (v) => Math.min(Math.max(Math.trunc(Number(v)) || 0, 0), Math.max(length - 1, 0));
    const white = score(m.white), black = score(m.black);
    return { length, white, black, crawford: !!m.crawford && canCrawford(length, white, black) };
  }
  const canCrawford = (length, white, black) => length > 0 && (white === length - 1) !== (black === length - 1);

  // The fields of an /analyze (or /analyze-photo) request for the match (made whole by fixMatch).
  function matchRequest(m) {
    return { match_length: m.length, score_white: m.white, score_black: m.black, crawford: m.crawford };
  }

  return { VALUES, request, fromRead, MATCH_LENGTHS, fixMatch, canCrawford, matchRequest };
})();

if (typeof module !== "undefined") module.exports = BgCube;
