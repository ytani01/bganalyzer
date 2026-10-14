// The reading overlay: while the server reads the board, the board's outline, triangles and bar are
// drawn over the photo in perspective (from the four corners) with a sweeping scan line; when the
// answer comes, the outline moves to where the recognizer fitted it and the triangle tips and checkers
// it found appear on the photo. Drawing only: nothing here changes what is read.
// Also loaded by Node in the tests (module.exports): layout() and lines() need no DOM.
"use strict";

(function (root) {
  const P = root.BgPhoto || (typeof require !== "undefined" ? require("./photo.js") : null);
  const TRI_DEPTH = 0.44;   // triangle length / board height (as recognizer/board.py)
  const BAR = 0.16;         // bar width / field width, before the recognizer has measured it

  // Columns (centres) and bar edges as fractions of the playing area's width, and a point's width.
  // geom: the recognizer's {columns, bar} or nothing (the usual board).
  function layout(geom) {
    if (geom && geom.columns && geom.columns.length === 12 && geom.bar) {
      const cols = geom.columns.slice();
      const pw = ((cols[5] - cols[0]) + (cols[11] - cols[6])) / 10;
      return { cols, bar: geom.bar.slice(), pw };
    }
    const a = 1 / (2 + BAR), pw = a / 6;
    const cols = [];
    for (let c = 0; c < 12; c++) cols.push(c < 6 ? (c + 0.5) * pw : a + a * BAR + (c - 6 + 0.5) * pw);
    return { cols, bar: [a, a + a * BAR], pw };
  }

  // The board's lines in image pixels: corners TL TR BR BL of the playing area, lay from layout().
  // Straight lines stay straight in perspective, so mapping the ends is enough.
  function lines(corners, lay) {
    const h = P.homography([[0, 0], [1, 0], [1, 1], [0, 1]], corners);
    const at = (u, v) => P.apply(h, u, v);
    const half = lay.pw / 2;
    const tris = [];
    for (let c = 0; c < 12; c++) {
      const x = lay.cols[c];
      tris.push([at(x - half, 0), at(x, TRI_DEPTH), at(x + half, 0)]);        // top row
      tris.push([at(x - half, 1), at(x, 1 - TRI_DEPTH), at(x + half, 1)]);    // bottom row
    }
    return {
      quad: [at(0, 0), at(1, 0), at(1, 1), at(0, 1)],
      mid: [at(0, 0.5), at(1, 0.5)],
      bar: lay.bar.map((u) => [at(u, 0), at(u, 1)]),
      tris,
      sweep: (u) => [at(u, 0), at(u, 1)],
    };
  }

  const lerp = (a, b, f) => a + (b - a) * f;
  const lerpPts = (A, B, f) => A.map(([x, y], k) => [lerp(x, B[k][0], f), lerp(y, B[k][1], f)]);
  const clamp01 = (x) => Math.max(0, Math.min(1, x));
  const ease = (x) => 1 - Math.pow(1 - clamp01(x), 3);

  const CYAN = "79, 227, 255", GREEN = "125, 255, 154";
  const STAGES = ["枠を合わせています", "三角形を探しています", "駒を探しています", "駒の色を分けています"];

  // Starts the overlay on canvas. opts:
  //   prepare(): draws the bare photo on the canvas and returns toCanvas([x, y]) (image px -> CSS px)
  //   corners: TL TR BR BL in image px; reduced: draw once, without movement
  // Returns {reveal(geom) -> Promise (resolves when shown or tapped), stop()}.
  function start(canvas, opts) {
    const ctx = canvas.getContext("2d");
    const dpr = () => canvas.width / (canvas.clientWidth || canvas.width);
    let snap = null, toCanvas = null, size = "";
    function base() {
      const s = canvas.width + "x" + canvas.height;
      if (!snap || s !== size) {
        toCanvas = opts.prepare();
        snap = document.createElement("canvas");
        snap.width = canvas.width; snap.height = canvas.height;
        snap.getContext("2d").drawImage(canvas, 0, 0);
        size = canvas.width + "x" + canvas.height;
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.drawImage(snap, 0, 0);
      const d = dpr();
      ctx.setTransform(d, 0, 0, d, 0, 0);
      ctx.fillStyle = "rgba(0, 12, 24, .38)";
      ctx.fillRect(0, 0, canvas.width / d, canvas.height / d);
    }

    const guess = lines(opts.corners, layout(null));
    let raf = 0, stopped = false, t0 = performance.now();
    let reveal = null;   // {t0, from, to, geom, done}

    const cp = (p) => toCanvas(p);
    function path(pts, close) {
      ctx.beginPath();
      pts.forEach((p, k) => { const [x, y] = cp(p); k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
      if (close) ctx.closePath();
    }
    function glow(rgb, a, w, blur) {
      ctx.strokeStyle = `rgba(${rgb}, ${a})`;
      ctx.lineWidth = w;
      ctx.shadowColor = `rgba(${rgb}, ${Math.min(1, a + 0.2)})`;
      ctx.shadowBlur = blur;
    }

    // The board's lines, each part shown from 0 to 1 by p.
    function drawBoard(L, rgb, p) {
      ctx.save();
      // outline, drawn round from the top-left corner
      const per = clamp01(p.quad);
      if (per > 0) {
        const q = L.quad.concat([L.quad[0]]);
        const len = [];
        for (let k = 0; k < 4; k++) len.push(Math.hypot(...cp(q[k + 1]).map((v, i) => v - cp(q[k])[i])));
        const total = len.reduce((a, b) => a + b, 0);
        let left = per * total;
        ctx.beginPath();
        let [x, y] = cp(q[0]);
        ctx.moveTo(x, y);
        for (let k = 0; k < 4 && left > 0; k++) {
          const f = Math.min(1, left / len[k]);
          const [x1, y1] = cp(q[k + 1]);
          ctx.lineTo(x + (x1 - x) * f, y + (y1 - y) * f);
          left -= len[k];
          [x, y] = [x1, y1];
        }
        glow(rgb, 0.95, 2.2, 12);
        ctx.stroke();
      }
      // triangles one by one, left to right along the top, then the bottom
      const order = [...L.tris.keys()].sort((i, j) => (i % 2) - (j % 2) || i - j);
      order.forEach((i, n) => {
        const f = clamp01(p.tris * 26 - n);
        if (f <= 0) return;
        path(L.tris[i], true);
        ctx.fillStyle = `rgba(${rgb}, ${0.07 * f})`;
        ctx.shadowBlur = 0;
        ctx.fill();
        glow(rgb, 0.75 * f, 1.2, 6);
        ctx.stroke();
      });
      // the middle line and the bar
      const fb = clamp01(p.bar);
      if (fb > 0) {
        ctx.setLineDash([6, 6]);
        path(L.mid);
        glow(rgb, 0.5 * fb, 1, 0);
        ctx.stroke();
        ctx.setLineDash([]);
        for (const e of L.bar) { path(e); glow(rgb, 0.9 * fb, 1.6, 8); ctx.stroke(); }
      }
      ctx.restore();
    }

    // corner brackets that breathe
    function drawCorners(L, rgb, t) {
      const s = 14 + 3 * Math.sin(t / 220);
      ctx.save();
      glow(rgb, 0.95, 2.5, 10);
      L.quad.forEach((p, k) => {
        const [x, y] = cp(p);
        const sx = k === 0 || k === 3 ? 1 : -1, sy = k < 2 ? 1 : -1;
        ctx.beginPath();
        ctx.moveTo(x + sx * s, y); ctx.lineTo(x, y); ctx.lineTo(x, y + sy * s);
        ctx.stroke();
      });
      ctx.restore();
    }

    function drawSweep(L, rgb, u) {
      ctx.save();
      for (let k = 0; k < 10; k++) {   // a fading trail behind the line
        const v = u - k * 0.006;
        if (v < 0) break;
        path(L.sweep(v));
        glow(rgb, k ? 0.28 * (1 - k / 10) : 1, k ? 3 : 2, k ? 0 : 18);
        ctx.stroke();
      }
      ctx.restore();
    }

    function label(text, rgb) {
      const d = dpr(), w = canvas.width / d, h = canvas.height / d;
      ctx.save();
      ctx.font = "bold 13px ui-monospace, Menlo, monospace";
      const tw = ctx.measureText(text).width;
      ctx.fillStyle = "rgba(0, 0, 0, .55)";
      ctx.fillRect(10, h - 34, tw + 20, 24);
      ctx.fillStyle = `rgb(${rgb})`;
      ctx.shadowColor = `rgb(${rgb})`;
      ctx.shadowBlur = 6;
      ctx.textBaseline = "middle";
      ctx.fillText(text, 20, h - 22);
      ctx.restore();
      return w;
    }

    function frameWaiting(t) {
      drawBoard(guess, CYAN, { quad: t / 500, tris: (t - 300) / 1000, bar: (t - 900) / 500 });
      drawCorners(guess, CYAN, t);
      if (opts.reduced) { label("▶ 盤面を読み取っています", CYAN); return; }   // a still picture
      if (t > 1300) drawSweep(guess, CYAN, ((t - 1300) % 1500) / 1500);
      const k = Math.min(STAGES.length - 1, Math.floor(t / 1300));
      const dots = ".".repeat(1 + Math.floor(t / 300) % 3);
      label("▶ " + STAGES[k] + dots, CYAN);
    }

    function frameReveal(t) {
      const r = reveal;
      const f = ease(t / 380);
      const L = lines(lerpPts(r.fromCorners, r.geom.corners, f), {
        cols: r.from.cols.map((c, i) => lerp(c, r.to.cols[i], f)),
        bar: r.from.bar.map((b, i) => lerp(b, r.to.bar[i], f)),
        pw: lerp(r.from.pw, r.to.pw, f),
      });
      const rgb = f < 1 ? CYAN : GREEN;
      drawBoard(L, rgb, { quad: 1, tris: 1, bar: 1 });
      drawCorners(L, rgb, t);
      ctx.save();
      // triangle tips: small crosshairs
      (r.geom.tips || []).forEach(([x, y], n) => {
        const a = clamp01((t - 380 - n * 12) / 120);
        if (a <= 0) return;
        const [cx, cy] = cp([x, y]);
        glow(GREEN, a, 1.5, 6);
        ctx.beginPath();
        ctx.moveTo(cx - 6, cy); ctx.lineTo(cx + 6, cy); ctx.moveTo(cx, cy - 6); ctx.lineTo(cx, cy + 6);
        ctx.stroke();
      });
      // checkers: rings that pop in, left to right
      const ck = r.checkers;
      ck.forEach(([x, y, rad, side], n) => {
        const a = clamp01((t - 520 - n * (700 / Math.max(ck.length, 1))) / 160);
        if (a <= 0) return;
        const [cx, cy] = cp([x, y]);
        const [ex] = cp([x + rad, y]);
        const rr = Math.max(4, Math.abs(ex - cx)) * (1 + 0.35 * (1 - ease(a)));
        const rgb2 = side === "white" ? "255, 255, 255" : "255, 176, 0";
        ctx.beginPath();
        ctx.arc(cx, cy, rr, 0, 2 * Math.PI);
        ctx.fillStyle = `rgba(${rgb2}, ${0.16 * a})`;
        ctx.shadowBlur = 0;
        ctx.fill();
        glow(rgb2, a, 2, 10);
        ctx.stroke();
      });
      ctx.restore();
      const counted = Math.min(ck.length, Math.max(0, Math.floor((t - 520) / (700 / Math.max(ck.length, 1)))));
      label(t < 520 ? "▶ 枠と列を合わせ直しました" : `▶ 駒の候補 ${counted} 個`, GREEN);
      if (t > r.duration && !r.done) { r.done = true; r.resolve(); }
    }

    function frame(now) {
      if (stopped) return;
      if (!canvas.isConnected || canvas.offsetParent === null) { raf = requestAnimationFrame(frame); return; }
      base();
      if (reveal) frameReveal(now - reveal.t0);
      else frameWaiting(opts.reduced ? 1e9 : now - t0);
      if (opts.reduced && !reveal) return;   // one still picture is enough
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);

    return {
      // Show what the recognizer found (geometry from /analyze-photo, corners in this image's px).
      reveal(geom) {
        if (stopped || !geom || !geom.corners || opts.reduced) return Promise.resolve();
        const checkers = (geom.checkers || []).slice().sort((a, b) => a[0] - b[0]);
        return new Promise((resolve) => {
          reveal = { t0: performance.now(), geom, checkers, fromCorners: opts.corners,
                     from: layout(null), to: layout(geom), duration: 1500, resolve, done: false };
          cancelAnimationFrame(raf);
          raf = requestAnimationFrame(frame);
        });
      },
      // Skip the rest of the reveal (a tap).
      skip() { if (reveal && !reveal.done) { reveal.done = true; reveal.resolve(); } },
      stop() { stopped = true; cancelAnimationFrame(raf); },
    };
  }

  const api = { layout, lines, start, TRI_DEPTH };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.BgScan = api;
})(this);
