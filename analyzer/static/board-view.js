// The board picture (SVG), drawn from a scene: what is on the board and around it. It reads
// nothing but the scene, so the board screen, the photo beside it and the result screen are the
// same drawing with different scenes.
//
// scene: {board, home, selected (point index, "bar" or null), photo (an image URL to show in the
// playing area instead of the drawn board and checkers), dice, onRoll, cube {at, value},
// move {hops, mover} (arrows of a best move, BgMoves.hops)}.
"use strict";

const BgBoardView = (() => {
  const SVG = "http://www.w3.org/2000/svg";
  const B = { x0: 20, y0: 24, y1: 416, pw: 48, bar: 40, r: 20, step: 38, tri: 165 };
  const PLAY = { x: B.x0, y: B.y0, w: 12 * B.pw + B.bar, h: B.y1 - B.y0 };   // the playing area
  const BAR_X = B.x0 + 6 * B.pw + B.bar / 2;                                   // the bar's middle
  const RIGHT = B.x0 + 12 * B.pw + B.bar;                                      // the playing area's right edge
  // Rows above and below the board, each on its player's side (奥 above, 手前 below): the tray of
  // borne-off checkers by the home boards, the doubling cube at the other end.
  const ROW = { h: 32, top: -34, bottom: 442 };
  const TRAY = { w: 186 };
  const VIEW = { y: ROW.top - 4, h: ROW.bottom + ROW.h + 4 - (ROW.top - 4) };
  const PIPS = { 1: [[0, 0]], 2: [[-1, -1], [1, 1]], 3: [[-1, -1], [0, 0], [1, 1]],
                 4: [[-1, -1], [1, -1], [-1, 1], [1, 1]], 5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]],
                 6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]] };

  function colX(c) {
    const half = c < 6 ? B.x0 : B.x0 + 6 * B.pw + B.bar;
    return half + (c % 6) * B.pw + B.pw / 2;
  }

  const trayX = (home) => (home === "right" ? RIGHT - TRAY.w : B.x0);
  const rowY = (side) => (side === "black" ? ROW.top : ROW.bottom);

  // Centre of the checker at level k (0 = by the board's edge) of a stack; above 5 they are not drawn.
  // On the bar the stacks start by its middle (clear of its label) and go out, a little closer together.
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

  function draw(svg, scene, onSelect) {
    svg.textContent = "";
    const { board: b, home, photo } = scene;
    svg.setAttribute("viewBox", `0 ${VIEW.y} 660 ${VIEW.h}`);
    el("rect", { x: 0, y: VIEW.y, width: 660, height: VIEW.h, fill: "var(--card)" }, svg);
    el("rect", { x: B.x0 - 6, y: B.y0 - 6, width: RIGHT - B.x0 + 12, height: B.y1 - B.y0 + 12, rx: 6, fill: "var(--frame)" }, svg);
    for (const side of ["white", "black"]) {
      el("rect", { x: trayX(home), y: rowY(side), width: TRAY.w, height: ROW.h, rx: 4, fill: "var(--felt)", stroke: "var(--frame)", "stroke-width": 4 }, svg);
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
    drawBorneOff(svg, b, home);
    if (scene.dice) drawDice(svg, scene.dice, scene.onRoll);
    drawCube(svg, scene.cube, home);
    if (scene.move) drawMove(svg, scene.move, home);
  }

  // Triangles, point numbers, checkers, the selection and a tap area for each point.
  function drawPoints(svg, { board: b, home, selected, photo }, onSelect) {
    const half = (B.y1 - B.y0) / 2;
    for (const top of [true, false]) {
      for (let c = 0; c < 12; c++) {
        const i = BgBoard.pointAt(home, top, c);
        const x = colX(c), h = B.pw / 2;
        const base = top ? B.y0 : B.y1, tip = top ? B.y0 + B.tri : B.y1 - B.tri;
        if (!photo) el("polygon", { points: `${x - h},${base} ${x + h},${base} ${x},${tip}`, fill: c % 2 ? "var(--tri-b)" : "var(--tri-a)" }, svg);
        el("text", { x, y: top ? 16 : 434, class: "num" }, svg).textContent = i + 1;
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
    if (!photo) el("text", { x: BAR_X, y: MID + 5, class: "label" }, svg).textContent = "バー";
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

  // Borne-off checkers as thin slabs on their side in their player's tray, from the board's outer
  // edge inward, with the count.
  function drawBorneOff(svg, b, home) {
    const { offW, offB } = BgBoard.counts(b);
    const wid = 9, step = 10, right = home === "right";
    for (let [side, n] of [["white", offW], ["black", offB]]) {
      if (n <= 0) continue;
      n = Math.min(n, 15);
      const y = rowY(side) + 3;
      for (let k = 0; k < n; k++) {
        const x = right ? RIGHT - 3 - wid - k * step : B.x0 + 3 + k * step;
        el("rect", { x, y, width: wid, height: ROW.h - 6, rx: 2, fill: checkerFill(side), stroke: `var(--${side}-rim)`, "stroke-width": 1.5, "pointer-events": "none" }, svg);
      }
      el("text", { x: right ? RIGHT - n * step - 16 : B.x0 + n * step + 16, y: rowY(side) + ROW.h / 2, class: "off-n", "pointer-events": "none" }, svg)
        .textContent = n;
    }
  }

  // The dice where the side on roll throws them: in its own right-hand field (手前: the right one in
  // the picture, 奥: the left one), in its checker colour.
  function drawDice(svg, dice, side) {
    const size = 34;
    const field = side === "white" ? B.x0 + 6 * B.pw + B.bar : B.x0;
    const cx = field + 3 * B.pw, cy = (B.y0 + B.y1) / 2;
    dice.forEach((d, k) => {
      const x = cx + (k ? 6 : -size - 6), y = cy - size / 2;
      const g = el("g", { class: "die" }, svg);
      el("rect", { x, y, width: size, height: size, rx: 6, fill: `var(--${side}-chk)`, stroke: "#0006", "stroke-width": 1.5 }, g);
      for (const [px, py] of PIPS[d]) {
        el("circle", { cx: x + size / 2 + px * size * 0.27, cy: y + size / 2 + py * size * 0.27, r: size * 0.09, fill: `var(--${side}-fg)` }, g);
      }
    });
  }

  // The doubling cube in its owner's row at the end away from the tray; while nobody owns it, in
  // 手前's row under the bar, showing 64.
  function drawCube(svg, cube, home) {
    const size = 30;
    const x = cube.at === "centre" ? BAR_X - size / 2 : home === "right" ? B.x0 : RIGHT - size;
    const y = rowY(cube.at === "black" ? "black" : "white") + (ROW.h - size) / 2;
    const g = el("g", { class: "die" }, svg);
    el("rect", { x, y, width: size, height: size, rx: 5, fill: "#fafafa", stroke: "#0008", "stroke-width": 1.5 }, g);
    el("text", { x: x + size / 2, y: y + size / 2 + 6, class: "cube-num" }, g).textContent = cube.at === "centre" ? "64" : String(cube.value);
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
      const [x1, y1] = h.to === "off" ? [x0, rowY(mover) + ROW.h / 2] : at(h.to, h.toLevel);
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

  return { PLAY, draw, columnAnchors };
})();
