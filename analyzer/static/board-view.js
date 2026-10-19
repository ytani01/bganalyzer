// The board picture (SVG), drawn from a scene: what is on the board and around it. It reads
// nothing but the scene, so the board screen, the photo beside it and the result screen are the
// same drawing with different scenes.
//
// scene: {board, home, selected (point index, "bar" or null), photo (an image URL to show in the
// playing area instead of the drawn board and checkers), dice, onRoll, cube {at, value},
// move {hops, mover} (arrows of a best move, BgMoves.hops), match {length (0: a money game), white,
// black, crawford} (BgCube.fixMatch)}.
// onPart (the board screen only): called with "home" (a tray), "colour" (a pip count), "match", "cube"
// or "roll" (the dice) when that part is tapped. With it, the match line is there in a money game too
// ("アンリミテッド") and the dice before a roll as dashed "?" (TODO-113).
"use strict";

const BgBoardView = (() => {
  const SVG = "http://www.w3.org/2000/svg";
  const B = { x0: 20, y0: 24, y1: 416, pw: 48, bar: 40, r: 20, step: 38, tri: 165 };
  const PLAY = { x: B.x0, y: B.y0, w: 12 * B.pw + B.bar, h: B.y1 - B.y0 };   // the playing area
  const BAR_X = B.x0 + 6 * B.pw + B.bar / 2;                                   // the bar's middle
  const RIGHT = B.x0 + 12 * B.pw + B.bar;                                      // the playing area's right edge
  // The column beside the board on the home side (TODO-151, TODO-152, TODO-155), top to bottom: 奥's pip count, the cube
  // 奥 owns, 奥's tray of borne-off checkers, 奥's score, the cube in the middle, 手前's score, 手前's tray, the cube
  // 手前 owns, 手前's pip count. 3 apart. The pip counts stick out above and below the board's frame.
  const COL = { w: 56, gap: 8, y0: B.y0 - 6, y1: B.y1 + 6, score: 32, tray: 101, cube: 40, pip: 40, pad: 3 };
  const VIEW = { y: COL.y0 - COL.pad - COL.pip - 4, h: (COL.y1 - COL.y0) + 2 * (COL.pad + COL.pip + 4) };
  const MATCH_H = 26;   // the line above 奥's row for the match, only in a match (TODO-099)
  const PIPS = { 1: [[0, 0]], 2: [[-1, -1], [1, 1]], 3: [[-1, -1], [0, 0], [1, 1]],
                 4: [[-1, -1], [1, -1], [-1, 1], [1, 1]], 5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]],
                 6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]] };

  function colX(c) {
    const half = c < 6 ? B.x0 : B.x0 + 6 * B.pw + B.bar;
    return half + (c % 6) * B.pw + B.pw / 2;
  }

  const sideX = (home) => (home === "right" ? RIGHT + 6 + COL.gap : B.x0 - 6 - COL.gap - COL.w);
  const trayY = (side) => (side === "black" ? COL.y0 + COL.cube + COL.pad : COL.y1 - COL.cube - COL.pad - COL.tray);
  const scoreY = (side) => (side === "black" ? trayY("black") + COL.tray + COL.pad : trayY("white") - COL.pad - COL.score);
  const cubeY = (at) => (at === "black" ? COL.y0 : at === "white" ? COL.y1 - COL.cube : scoreY("black") + COL.score + COL.pad);
  const pipY = (side) => (side === "black" ? COL.y0 - COL.pad - COL.pip : COL.y1 + COL.pad);

  // Centre of the checker at level k (0 = by the board's edge) of a stack; above 5 they are not drawn.
  // On the bar the stacks start a little off its middle and go out, a little closer together.
  const MID = (B.y0 + B.y1) / 2, BAR_GAP = 9, BAR_STEP = 36;
  function stackY(top, k, bar) {
    k = Math.min(k, 4);
    if (bar) return top ? MID - BAR_GAP - B.r - k * BAR_STEP : MID + BAR_GAP + B.r + k * BAR_STEP;
    return top ? B.y0 + B.r + 1 + k * B.step : B.y1 - B.r - 1 - k * B.step;
  }

  function el(name, attrs, parent) {
    const e = document.createElementNS(SVG, name);
    for (const k in attrs) {
      // CSS variables only work through style, not presentation attributes
      if (String(attrs[k]).startsWith("var(")) e.style.setProperty(k, attrs[k]);
      else e.setAttribute(k, attrs[k]);
    }
    if (parent) parent.appendChild(e);
    return e;
  }

  const checkerFill = (side) => (side === "white" ? "var(--white-chk)" : "var(--black-chk)");

  // A part around the board that onPart is called for when tapped.
  function tapPart(e, kind, onPart) {
    if (onPart) {
      e.classList.add("tap");
      e.dataset.part = kind;
      e.addEventListener("click", () => onPart(kind));
    }
    return e;
  }

  function draw(svg, scene, onSelect, onPart) {
    svg.textContent = "";
    const { board: b, home, photo } = scene;
    const match = scene.match && (scene.match.length || onPart) ? scene.match : null;
    const y0 = VIEW.y - (match ? MATCH_H : 0), h = VIEW.h + (match ? MATCH_H : 0);
    const x0 = home === "right" ? 0 : -COL.w - COL.gap, w = 660 + COL.w + COL.gap;
    svg.setAttribute("viewBox", `${x0} ${y0} ${w} ${h}`);
    el("rect", { x: x0, y: y0, width: w, height: h, fill: "var(--card)" }, svg);
    if (match) drawMatch(svg, match, home, y0, onPart);
    el("rect", { x: B.x0 - 6, y: B.y0 - 6, width: RIGHT - B.x0 + 12, height: B.y1 - B.y0 + 12, rx: 6, fill: "var(--frame)" }, svg);
    for (const side of ["white", "black"]) {
      tapPart(el("rect", { x: sideX(home), y: trayY(side), width: COL.w, height: COL.tray, rx: 4, fill: "var(--felt)", stroke: "var(--frame)", "stroke-width": 4 }, svg), "home", onPart);
    }
    if (photo) {
      el("image", { href: photo, x: PLAY.x, y: PLAY.y, width: PLAY.w, height: PLAY.h, preserveAspectRatio: "none" }, svg);
    } else {
      el("rect", { x: B.x0, y: B.y0, width: 6 * B.pw, height: B.y1 - B.y0, fill: "var(--felt)" }, svg);
      el("rect", { x: B.x0 + 6 * B.pw + B.bar, y: B.y0, width: 6 * B.pw, height: B.y1 - B.y0, fill: "var(--felt)" }, svg);
    }
    drawPoints(svg, scene, onSelect);
    drawBar(svg, scene, onSelect);
    if (photo) return;   // the photo shows the checkers itself
    if (scene.onRoll) drawWay(svg, scene.onRoll, home);
    drawBorneOff(svg, b, home);
    drawPips(svg, b, home, onPart);
    if (scene.dice || onPart) drawDice(svg, scene.dice, scene.onRoll, onPart);
    drawCube(svg, scene.cube, home, onPart, scene.match);
    if (scene.move) drawMove(svg, scene.move, home);
  }

  // Triangles, point numbers, checkers, the selection and a tap area for each point.
  function drawPoints(svg, { board: b, home, selected, photo, onRoll }, onSelect) {
    const half = (B.y1 - B.y0) / 2;
    for (const top of [true, false]) {
      for (let c = 0; c < 12; c++) {
        const i = BgBoard.pointAt(home, top, c);
        const x = colX(c), h = B.pw / 2;
        const base = top ? B.y0 : B.y1, tip = top ? B.y0 + B.tri : B.y1 - B.tri;
        if (!photo) el("polygon", { points: `${x - h},${base} ${x + h},${base} ${x},${tip}`, fill: c % 2 ? "var(--tri-b)" : "var(--tri-a)" }, svg);
        el("text", { x, y: top ? 16 : 434, class: "num" }, svg).textContent = BgBoard.number(i, onRoll);
        const n = b.points[i];
        if (n && !photo) drawStack(svg, x, top, Math.abs(n), n > 0 ? "white" : "black");
        if (selected === i) {
          el("rect", { x: x - h + 1, y: top ? B.y0 + 1 : B.y0 + half + 1, width: B.pw - 2, height: half - 2, fill: "none", stroke: "var(--sel)", "stroke-width": 3 }, svg);
        }
        if (!onSelect) continue;
        bindTap(el("rect", { x: x - h, y: top ? B.y0 : B.y0 + half, width: B.pw, height: half, fill: "transparent", class: "hit" }, svg),
                svg, i, top, null, onSelect);
        // the point's number, by the board's edge: a tap there empties the point
        bindTap(el("rect", { x: x - h, y: top ? 0 : B.y1, width: B.pw, height: top ? B.y0 : 440 - B.y1, fill: "transparent", class: "hit-num" }, svg),
                svg, i, top, null, onSelect, 0);
      }
    }
  }

  // The bar: 手前's checkers in the upper half, 奥's in the lower half (each stack from the middle).
  function drawBar(svg, { board: b, selected, photo }, onSelect) {
    if (b.bar_black && !photo) drawStack(svg, BAR_X, false, b.bar_black, "black", true);
    if (b.bar_white && !photo) drawStack(svg, BAR_X, true, b.bar_white, "white", true);
    if (selected === "bar") {
      el("rect", { x: BAR_X - B.bar / 2 + 1, y: B.y0 + 1, width: B.bar - 2, height: B.y1 - B.y0 - 2, fill: "none", stroke: "var(--sel)", "stroke-width": 3 }, svg);
    }
    if (!onSelect) return;
    const half = (B.y1 - B.y0) / 2;
    for (const top of [true, false]) {   // 手前's half above, 奥's below
      bindTap(el("rect", { x: BAR_X - B.bar / 2, y: top ? B.y0 : B.y0 + half, width: B.bar, height: half, fill: "transparent", class: "hit" }, svg),
              svg, "bar", top, top ? "white" : "black", onSelect);
    }
  }

  // A tap area of a point or of the bar's half. onSelect(at, {level, side, hold, x, y}) on lifting the finger
  // (hold false; level 1..5 from the board's edge, from the middle on the bar, or `fixedLevel`), or once the finger has stayed put for
  // HOLD_MS, or on a right click (hold true). x, y: where on the screen. A finger that moves is scrolling.
  const HOLD_MS = 450, SLOP = 10;
  function bindTap(rect, svg, at, top, side, onSelect, fixedLevel) {
    let down = null, timer = null;
    const cancel = () => { clearTimeout(timer); timer = null; down = null; };
    const levelAt = (cx, cy) => {
      if (fixedLevel !== undefined) return fixedLevel;
      const m = svg.getScreenCTM();
      const y = m ? new DOMPoint(cx, cy).matrixTransform(m.inverse()).y : 0;
      const k = at === "bar" ? ((top ? MID - y : y - MID) - BAR_GAP) / BAR_STEP : (top ? y - B.y0 : B.y1 - y) / B.step;
      return Math.max(1, Math.min(5, Math.floor(k) + 1));
    };
    const fire = (hold, cx, cy) => onSelect(at, { level: levelAt(cx, cy), side, hold, x: cx, y: cy });
    rect.addEventListener("pointerdown", (e) => {
      if (e.button) return;
      down = [e.clientX, e.clientY];
      timer = setTimeout(() => { const [cx, cy] = down; cancel(); fire(true, cx, cy); }, HOLD_MS);
    });
    rect.addEventListener("pointermove", (e) => {
      if (down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) > SLOP) cancel();
    });
    rect.addEventListener("pointerup", (e) => {
      if (!down) return;
      const [cx, cy] = down;
      cancel();
      fire(false, cx, cy);
      e.preventDefault();
    });
    rect.addEventListener("pointercancel", cancel);
    rect.addEventListener("pointerleave", cancel);
    rect.addEventListener("contextmenu", (e) => { e.preventDefault(); cancel(); fire(true, e.clientX, e.clientY); });
  }

  // Up to 5 checkers of a stack from the board's edge (the bar's middle), the count on the last when there are more.
  function drawStack(svg, x, top, n, side, bar) {
    const shown = Math.min(n, 5);
    for (let k = 0; k < shown; k++) {
      const y = stackY(top, k, bar);
      el("circle", { cx: x, cy: y, r: B.r, fill: checkerFill(side), stroke: `var(--${side}-rim)`, "stroke-width": 2.5, "pointer-events": "none" }, svg);
      if (k === shown - 1 && n > 5) {
        el("text", { x, y, class: "stack-n", fill: `var(--${side}-fg)`, "pointer-events": "none" }, svg).textContent = n;
      }
    }
  }

  // Borne-off checkers as thin slabs in their player's tray, from the board's outer edge (奥: the top,
  // 手前: the bottom) toward the middle, with the count.
  function drawBorneOff(svg, b, home) {
    const { offW, offB } = BgBoard.counts(b);
    const hgt = 4, step = 5, x = sideX(home) + 6;
    for (let [side, n] of [["white", offW], ["black", offB]]) {
      if (n <= 0) continue;
      n = Math.min(n, 15);
      const top = side === "black", edge = top ? trayY(side) + 4 : trayY(side) + COL.tray - 4;
      for (let k = 0; k < n; k++) {
        const y = top ? edge + k * step : edge - hgt - k * step;
        el("rect", { x, y, width: COL.w - 12, height: hgt, rx: 1.5, fill: checkerFill(side), stroke: `var(--${side}-rim)`, "stroke-width": 1, "pointer-events": "none" }, svg);
      }
      el("text", { x: x + (COL.w - 12) / 2, y: top ? edge + n * step + 10 : edge - n * step - 10, class: "off-n", "pointer-events": "none" }, svg)
        .textContent = n;
    }
  }

  // Each side's pip count at its end of the column, outside the cube, on a plate of its checker colour: "PIP" over the number (TODO-090, TODO-155).
  function drawPips(svg, b, home, onPart) {
    const pips = BgBoard.pips(b), x = sideX(home);
    for (const side of ["white", "black"]) {
      const y = pipY(side);
      const g = tapPart(el("g", {}, svg), "colour", onPart);
      el("rect", { x, y, width: COL.w, height: COL.pip, rx: 6, fill: checkerFill(side), stroke: `var(--${side}-rim)`, "stroke-width": 2, "pointer-events": "none" }, g);
      el("text", { x: x + COL.w / 2, y: y + 12, class: "pip-l", fill: `var(--${side}-fg)`, "pointer-events": "none" }, g).textContent = "PIP";
      el("text", { x: x + COL.w / 2, y: y + 28, class: "pip-n", fill: `var(--${side}-fg)`, "pointer-events": "none" }, g).textContent = String(pips[side]);
    }
  }

  // The match on a line of its own above 奥's row, and each side's score as a grey square-cornered card with a black number in the middle of the column (TODO-099, TODO-152, TODO-155).
  function drawMatch(svg, m, home, y0, onPart) {
    tapPart(el("text", { x: BAR_X, y: y0 + MATCH_H / 2 + 2, class: "match-n", "pointer-events": "none" }, svg), "match", onPart).textContent =
      (m.length ? `${m.length} ポイントマッチ` + (m.crawford ? "（クロフォード）" : "") : "アンリミテッド") + (onPart ? " ▾" : "");
    if (!m.length) return;
    const x = sideX(home);
    for (const side of ["white", "black"]) {
      const y = scoreY(side);
      const g = tapPart(el("g", {}, svg), "match", onPart);
      el("rect", { x, y, width: COL.w, height: COL.score, fill: "#c4c4c4", stroke: "#0008", "stroke-width": 1.5, "pointer-events": "none" }, g);
      el("text", { x: x + COL.w / 2, y: y + COL.score / 2, class: "score-n", "pointer-events": "none" }, g).textContent = String(m[side]);
    }
  }

  // The dice where the side on roll throws them: in its own right-hand field (手前: the right one in
  // the picture, 奥: the left one), in its checker colour. No dice (before a roll): dashed, with "?".
  function drawDice(svg, dice, side, onPart) {
    const size = 34;
    const field = side === "white" ? B.x0 + 6 * B.pw + B.bar : B.x0;
    const cx = field + 3 * B.pw, cy = (B.y0 + B.y1) / 2;
    (dice || [0, 0]).forEach((d, k) => {
      const x = cx + (k ? 6 : -size - 6), y = cy - size / 2;
      const g = tapPart(el("g", { class: "die" }, svg), "roll", onPart);
      if (!d) {
        el("rect", { x, y, width: size, height: size, rx: 6, fill: `var(--${side}-chk)`, "fill-opacity": 0.25, stroke: "#0006", "stroke-width": 1.5, "stroke-dasharray": "4 3" }, g);
        el("text", { x: x + size / 2, y: y + size / 2 + 7, class: "die-q" }, g).textContent = "?";
        return;
      }
      el("rect", { x, y, width: size, height: size, rx: 6, fill: `var(--${side}-chk)`, stroke: "#0006", "stroke-width": 1.5 }, g);
      for (const [px, py] of PIPS[d]) {
        el("circle", { cx: x + size / 2 + px * size * 0.27, cy: y + size / 2 + py * size * 0.27, r: size * 0.09, fill: `var(--${side}-fg)` }, g);
      }
    });
  }

  // The doubling cube in the column, at its owner's end; while nobody owns it, in the middle, showing 64.
  // In the Crawford game it says "Crawford" instead of a number (TODO-152).
  function drawCube(svg, cube, home, onPart, match) {
    const size = COL.cube;
    const x = sideX(home) + (COL.w - size) / 2, y = cubeY(cube.at);
    const g = tapPart(el("g", { class: "die" }, svg), "cube", onPart);
    el("rect", { x, y, width: size, height: size, rx: 5, fill: "#fafafa", stroke: "#0008", "stroke-width": 1.5 }, g);
    const crawford = match && match.length > 0 && match.crawford;
    if (crawford) {   // two lines, "Craw" over "ford", to fit the cube
      ["Craw", "ford"].forEach((t, k) => el("text", { x: x + size / 2, y: y + size / 2 + (k ? 8 : -8), class: "cube-crawford" }, g).textContent = t);
      return;
    }
    el("text", { x: x + size / 2, y: y + size / 2 + 7.5, class: "cube-num" }, g).textContent = cube.at === "centre" ? "64" : String(cube.value);
  }

  // The way the side on roll goes, as a see-through U across the middle of the board (over the
  // checkers, under the dice): from its farthest point along its far row, round at the end away from home, and back
  // along its near row to home (TODO-092). 手前's far row is the upper one, 奥's the lower one.
  function drawWay(svg, side, home) {
    const r = 42, yTop = MID - r, yBot = MID + r;
    const right = home === "right";
    const inset = 82, xHome = right ? RIGHT - inset : B.x0 + inset, xTurn = right ? B.x0 + inset + r : RIGHT - inset - r;
    const [y0, y1] = side === "white" ? [yTop, yBot] : [yBot, yTop];
    const dir = right ? 1 : -1, head = 20;
    const sweep = (y0 < y1) === right ? 0 : 1;
    const d = `M${xHome},${y0} H${xTurn} A${r},${r} 0 0 ${sweep} ${xTurn},${y1} H${xHome - dir * head}`;
    const tip = `${xHome},${y1} ${xHome - dir * head},${y1 - 13} ${xHome - dir * head},${y1 + 13}`;
    const g = el("g", { class: "way", opacity: 0.6 }, svg);
    el("path", { d, fill: "none", stroke: `var(--${side}-rim)`, "stroke-width": 12, "stroke-linecap": "round" }, g);
    el("polygon", { points: tip, fill: `var(--${side}-rim)`, stroke: `var(--${side}-rim)`, "stroke-width": 4, "stroke-linejoin": "round" }, g);
    el("path", { d, fill: "none", stroke: checkerFill(side), "stroke-width": 8, "stroke-linecap": "round" }, g);
    el("polygon", { points: tip, fill: checkerFill(side) }, g);
  }

  // A move as arrows, one per die, with a red ring where a checker is hit.
  function drawMove(svg, { hops, mover }, home) {
    const at = (p, level) => {
      if (p === "bar") return [BAR_X, stackY(mover === "white", level, true)];
      const { top, c } = BgBoard.columnOf(home, p);
      return [colX(c), stackY(top, level)];
    };
    const g = el("g", { class: "arrows" }, svg);
    for (const h of hops) {
      const [x0, y0] = at(h.from, h.fromLevel);
      // off: to the tray's edge facing the board, clear of the count in its middle
      const [x1, y1] = h.to === "off" ? [sideX(home) + (home === "right" ? 0 : COL.w), trayY(mover) + COL.tray / 2] : at(h.to, h.toLevel);
      drawArrow(g, x0, y0, x1, y1);
      if (h.hit) el("circle", { cx: x1, cy: y1, r: B.r, fill: "none", stroke: "#e53935", "stroke-width": 3 }, g);
    }
  }

  // A gently curved arrow (bent toward the middle of the board, off the checkers in between).
  function drawArrow(g, x0, y0, x1, y1) {
    const dx = x1 - x0, dy = y1 - y0, len = Math.hypot(dx, dy);
    if (len < 1) return;
    let px = -dy / len, py = dx / len;
    const mx = (x0 + x1) / 2, my = (y0 + y1) / 2, cy = (B.y0 + B.y1) / 2;
    if (py * (cy - my) < 0 || (Math.abs(py) < 0.1 && px * (330 - mx) < 0)) { px = -px; py = -py; }
    const bend = Math.min(40, len * 0.2);
    const qx = mx + px * bend, qy = my + py * bend;
    const tx = x1 - qx, ty = y1 - qy, tl = Math.hypot(tx, ty) || 1;
    const ux = tx / tl, uy = ty / tl, head = 14;
    const ex = x1 - ux * head, ey = y1 - uy * head;   // the line stops where the head starts
    const d = `M${x0},${y0} Q${qx},${qy} ${ex},${ey}`;
    el("path", { d, fill: "none", stroke: "#000", "stroke-opacity": 0.45, "stroke-width": 8, "stroke-linecap": "round" }, g);
    el("path", { d, fill: "none", stroke: "var(--sel)", "stroke-width": 4, "stroke-linecap": "round" }, g);
    el("circle", { cx: x0, cy: y0, r: 5, fill: "var(--sel)", stroke: "#0008", "stroke-width": 1.5 }, g);
    const w = 8;
    el("polygon", { points: `${x1},${y1} ${ex - uy * w},${ey + ux * w} ${ex + uy * w},${ey - ux * w}`,
                    fill: "var(--sel)", stroke: "#0008", "stroke-width": 1.5 }, g);
  }

  // Where the photo's columns are, for warping the photo onto the drawn playing area (photo.js):
  // [[x on the drawn playing area * zoom, fraction of the photo's width], ...] through the bar edges
  // and the 12 column centres, or just the bar edges if the columns are out of order.
  function columnAnchors(geometry, zoom) {
    const half = 6 * B.pw;
    const bar = [[half * zoom, geometry.bar[0]], [(half + B.bar) * zoom, geometry.bar[1]]];
    const cols = (geometry.columns || []).map((f, c) => [(colX(c) - B.x0) * zoom, f]);
    const ends = (mid) => [[0, 0], ...mid, [PLAY.w * zoom, 1]];
    const increasing = (a) => a.every((p, k) => k === 0 || p[1] > a[k - 1][1]);
    const full = ends([...cols.slice(0, 6), ...bar, ...cols.slice(6)]);
    if (cols.length === 12 && increasing(full)) return full;
    const plain = ends(bar);
    return increasing(plain) ? plain : null;
  }

  return { PLAY, PIPS, draw, columnAnchors };
})();
