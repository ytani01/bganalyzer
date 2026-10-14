// A photo and its corrected board, written out as a recognizer sample (samples/*.truth.json)
// so the recognizer can be measured and improved on real photos (recognizer/evaluate.py).
// Nothing goes to the server: the user shares the two files themselves.
"use strict";

const BgSample = (() => {
  const CHECKERS = 15;

  // "user-20261014-0932" from a Date (local time)
  function baseName(date) {
    const p = (n) => String(n).padStart(2, "0");
    return `user-${date.getFullYear()}${p(date.getMonth() + 1)}${p(date.getDate())}-${p(date.getHours())}${p(date.getMinutes())}`;
  }

  // The truth.json for one photo. s: {image (file name), corners [[x, y]] TL TR BR BL in the
  // image's pixels, home, bottomColour, board {points, bar_white, bar_black}, dice, cube, read}.
  // read is the board the recognizer gave before the user fixed it (null if not known).
  function truth(s) {
    const b = s.board;
    const onBoard = (sign) => b.points.reduce((t, n) => t + Math.max(sign * n, 0), 0);
    const t = {
      image: s.image,
      note: "Exported from the PWA: the board as corrected by hand on the phone.",
      corners_TL_TR_BR_BL: s.corners.map(([x, y]) => [Math.round(x), Math.round(y)]),
      home: s.home,
      bottom_colour: s.bottomColour,
      points: b.points.slice(),
      bar_white: b.bar_white,
      bar_black: b.bar_black,
      off_white: Math.max(0, CHECKERS - onBoard(1) - b.bar_white),
      off_black: Math.max(0, CHECKERS - onBoard(-1) - b.bar_black),
      dice: s.dice || null,
      // where the cube lies, as evaluate.py compares it. The app has no "no cube": the middle is "centre".
      cube: { at: (s.cube && s.cube.at) || "centre" },
    };
    if (s.cube && s.cube.at !== "centre") t.cube_value = s.cube.value;
    if (s.read) {
      t.read = { points: s.read.points.slice(), bar_white: s.read.bar_white, bar_black: s.read.bar_black };
      t.fixed_points = b.points.map((n, i) => (n !== s.read.points[i] ? i + 1 : 0)).filter(Boolean);
    }
    return t;
  }

  return { baseName, truth };
})();

if (typeof module !== "undefined") module.exports = BgSample;
