// The doubling cube on the board screen, and what it asks of the analysis (money game).
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

  // The cube as the recognizer read it (null: none seen, so in the middle).
  function fromRead(read) {
    if (!read || read.at === "centre") return { at: "centre", value: 2, offered: true };
    return { at: read.at, value: VALUES.includes(read.value) ? read.value : 2, offered: true };
  }

  return { VALUES, request, fromRead };
})();

if (typeof module !== "undefined") module.exports = BgCube;
