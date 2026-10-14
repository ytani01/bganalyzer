// The overlays on the photo while the server works, stage by stage:
// - the search for the corners (mode "corners", after a photo is loaded): a scan line across the
//   photo, then the straight edges found across and upright, the quadrilaterals compared and the corners;
// - the reading: the board's outline, triangles and bar drawn in perspective from the four corners
//   with a scan line, then the frame fitted (each round), the triangle tips, the checkers, the
//   counts, the dice and the cube.
// Each stage the server reports is queued and shown for its STAGE_MS in turn; the work is over when
// the last one has been shown. Drawing only: nothing here changes what is found or read.
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
  // How long each stage stays on screen (ms), by the stage's name as the server sends it.
  // Change a number here to make that stage shorter or longer; a stage not listed gets DEFAULT_STAGE_MS.
  const DEFAULT_STAGE_MS = 1000;
  const STAGE_MS = {
    // the search for the corners, after a photo is loaded (/find-corners)
    edges: 1000,       // 横の縁（奥と手前）の候補の直線
    uprights: 1000,    // 縦の縁（左右）の候補の直線
    candidates: 1000,  // 盤らしい四角形の候補を比べる
    corners: 1000,     // 四隅が決まる
    // the reading (/analyze-photo)
    fit: 1000,         // 四隅の合わせ直し（枠の線で 2 回、三角形の並びで 2 回。1 回ごとに）
    board: 1000,       // 枠と列（段階を流さないサーバーのとき）
    tips: 1000,        // 三角形の先
    checkers: 1000,    // 駒の円
    counts: 1000,      // ポイントごとの数
    dice: 1000,        // ダイス
    cube: 1000,        // キューブ
  };
  const stageMs = (stage) => (stage in STAGE_MS ? STAGE_MS[stage] : DEFAULT_STAGE_MS);

  // Starts the overlay on canvas. opts:
  //   prepare(): draws the bare photo on the canvas and returns toCanvas([x, y]) (image px -> CSS px)
  //   corners: TL TR BR BL in image px; reduced: still pictures, without movement
  // Returns {push(stage event), done() -> Promise (resolves when every stage has been shown or the
  // reading was tapped), reveal(geom) (the stages from a whole geometry, then done()), skip(), stop()}.
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

    const CORNERS = opts.mode === "corners";   // the search for the corners (/find-corners), not the reading
    const guess = lines(opts.corners, layout(null));
    let raf = 0, stopped = false, t0 = performance.now();

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

    function frameWaiting(t) {
      if (CORNERS) {   // nothing known yet: a scan line across the whole photo
        if (!opts.reduced) drawSweep(guess, CYAN, (t % 1500) / 1500);
        return;
      }
      drawBoard(guess, CYAN, { quad: t / 500, tris: (t - 300) / 1000, bar: (t - 900) / 500 });
      drawCorners(guess, CYAN, t);
      if (opts.reduced) return;   // a still picture
      if (t > 1300) drawSweep(guess, CYAN, ((t - 1300) % 1500) / 1500);
    }

    // ---- the stages, as the server reports them, each shown for its STAGE_MS in turn ----
    const FIT = 380;   // the frame moving to where it was fitted
    const AMBER = "255, 176, 0", WHITE = "255, 255, 255", MAGENTA = "255, 102, 230";
    const YELLOW = "255, 230, 80", BLUE = "90, 170, 255", ORANGE = "255, 120, 70";

    // The search for the corners: the edges found across the photo, the upright ones, the
    // quadrilaterals compared and the corners, each drawn over the ones before (which fade).
    function segment([a, b], rgb, alpha, grow, width) {
      const [x0, y0] = cp(a), [x1, y1] = cp(b);
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x0 + (x1 - x0) * grow, y0 + (y1 - y0) * grow);
      glow(rgb, alpha, width, 10);
      ctx.stroke();
    }
    function frameCornerStages(now) {
      const at = (k) => seen[k] && { d: seen[k].data, t: now - seen[k].t0, here: cur && cur.stage === k };
      ctx.save();
      const ed = at("edges");
      if (ed) (ed.d.lines || []).forEach((l, n) =>
        segment(l, ORANGE, ed.here ? 1 : 0.4, intro(ed.t - n * 0.08 * stageMs("edges"), 0.4 * stageMs("edges")), 2));
      const up = at("uprights");
      if (up) {
        const list = up.d.lines || [], step = 0.5 * stageMs("uprights") / Math.max(list.length, 1);
        list.forEach((l, n) => segment(l, BLUE, up.here ? 1 : 0.4, intro(up.t - n * step, 0.3 * stageMs("uprights")), 2));
      }
      const ca = at("candidates");
      if (ca) {   // the best last, so it is drawn on top; each one in turn while the stage is on
        const list = (ca.d.quads || []).slice().reverse(), step = 0.6 * stageMs("candidates") / Math.max(list.length, 1);
        list.forEach((q, n) => {
          const a = intro(ca.t - n * step, 150);
          if (a <= 0) return;
          const best = n === list.length - 1;
          path(q, true);
          glow(YELLOW, a * (ca.here ? (best ? 1 : 0.5) : 0.3), best ? 2.4 : 1.2, best ? 10 : 0);
          ctx.stroke();
        });
      }
      const co = at("corners");
      if (co && co.d.corners) {
        const a = intro(co.t, 300);
        const L = lines(co.d.corners, layout(null));
        drawBoard(L, GREEN, { quad: a, tris: 0, bar: 0 });
        if (a >= 1) drawCorners(L, GREEN, co.t);
      }
      ctx.restore();
    }
    const queue = [];            // stages received, not shown yet
    let cur = null;              // the stage on screen: {stage, data, t0}
    let finished = false, skipped = false, onDone = null;
    const seen = {};             // what has been shown so far, by stage: {data, t0}
    let frameFrom = null, frameTo = null, frameT0 = 0;   // the frame moving: {corners, lay}

    const intro = (t, dur) => (opts.reduced ? 1 : clamp01(t / dur));
    const frameOf = (d) => ({ corners: d.corners, lay: layout(d) });

    function next(now) {
      if (queue.length && (!cur || now - cur.t0 >= stageMs(cur.stage))) {
        cur = queue.shift();
        cur.t0 = now;
        seen[cur.stage] = { data: cur.data, t0: now };
        if (!CORNERS && cur.data.corners) {   // fit, board, checkers: the frame (and maybe the columns) found
          frameFrom = frameTo ? currentFrame(now) : { corners: opts.corners, lay: layout(null) };
          frameTo = frameOf(cur.data);
          frameT0 = now;
        }
      }
      if (onDone && finished && (skipped || (!queue.length && (!cur || now - cur.t0 >= stageMs(cur.stage))))) {
        const f = onDone; onDone = null; f();
      }
    }

    function currentFrame(now) {
      const f = opts.reduced ? 1 : ease((now - frameT0) / FIT);
      return {
        corners: lerpPts(frameFrom.corners, frameTo.corners, f),
        lay: { cols: frameFrom.lay.cols.map((c, i) => lerp(c, frameTo.lay.cols[i], f)),
               bar: frameFrom.lay.bar.map((b, i) => lerp(b, frameTo.lay.bar[i], f)),
               pw: lerp(frameFrom.lay.pw, frameTo.lay.pw, f) },
        moving: f < 1,
      };
    }

    // A square found on the photo (a die or the cube), closing in from around it, with text above it.
    function drawSquare(quad, rgb, a, text) {
      const pts = quad.map(cp);
      const cx = pts.reduce((s, p) => s + p[0], 0) / 4, cy = pts.reduce((s, p) => s + p[1], 0) / 4;
      const g = 1 + 0.5 * (1 - ease(a));
      ctx.beginPath();
      pts.forEach(([x, y], k) => {
        const X = cx + (x - cx) * g, Y = cy + (y - cy) * g;
        k ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y);
      });
      ctx.closePath();
      ctx.fillStyle = `rgba(${rgb}, ${0.18 * a})`;
      ctx.shadowBlur = 0;
      ctx.fill();
      glow(rgb, a, 2.4, 12);
      ctx.stroke();
      if (text) tag(text, cx, Math.min(...pts.map((p) => p[1])) - 4, rgb, a, "bottom");
    }

    function tag(text, x, y, rgb, a, baseline) {
      ctx.font = "bold 15px ui-monospace, Menlo, monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = baseline || "middle";
      ctx.fillStyle = `rgba(${rgb}, ${a})`;
      ctx.shadowColor = "rgba(0, 0, 0, .95)";
      ctx.shadowBlur = 5;
      ctx.fillText(text, x, y);
    }

    function frameStages(now) {
      if (CORNERS) { frameCornerStages(now); return; }
      const F = currentFrame(now);
      const L = lines(F.corners, F.lay);
      const rgb = F.moving ? CYAN : GREEN;
      drawBoard(L, rgb, { quad: 1, tris: 1, bar: 1 });
      drawCorners(L, rgb, now - frameT0);
      ctx.save();
      const at = (k) => seen[k] && { d: seen[k].data, t: now - seen[k].t0, here: cur && cur.stage === k };
      const tips = at("tips");
      if (tips) (tips.d.tips || []).forEach(([x, y], n) => {   // triangle tips: small crosshairs
        const a = opts.reduced ? 1 : clamp01((tips.t - n * 20) / 120);
        if (a <= 0) return;
        const [cx, cy] = cp([x, y]);
        glow(GREEN, a, 1.5, 6);
        ctx.beginPath();
        ctx.moveTo(cx - 6, cy); ctx.lineTo(cx + 6, cy); ctx.moveTo(cx, cy - 6); ctx.lineTo(cx, cy + 6);
        ctx.stroke();
      });
      const ck = at("checkers");
      if (ck) {   // checkers: rings that pop in, left to right; fainter once the counts are up
        const list = ck.d.sorted || (ck.d.sorted = (ck.d.checkers || []).slice().sort((a, b) => a[0] - b[0]));
        const step = 0.6 * stageMs("checkers") / Math.max(list.length, 1), dim = ck.here ? 1 : 0.45;
        list.forEach(([x, y, rad, side], n) => {
          const a = opts.reduced ? 1 : clamp01((ck.t - n * step) / 160);
          if (a <= 0) return;
          const [cx, cy] = cp([x, y]);
          const [ex] = cp([x + rad, y]);
          const rr = Math.max(4, Math.abs(ex - cx)) * (1 + 0.35 * (1 - ease(a)));
          const c = side === "white" ? WHITE : AMBER;
          ctx.beginPath();
          ctx.arc(cx, cy, rr, 0, 2 * Math.PI);
          ctx.fillStyle = `rgba(${c}, ${0.16 * a * dim})`;
          ctx.shadowBlur = 0;
          ctx.fill();
          glow(c, a * dim, 2, 10 * dim);
          ctx.stroke();
        });
      }
      const cn = at("counts");
      if (cn) (cn.d.counts || []).forEach((c, n) => {   // the number counted by each point
        const a = intro(cn.t - n * 25, 180);
        if (a <= 0) return;
        const [x, y] = cp(c.at);
        tag(String(c.n), x, y, c.side === "white" ? WHITE : AMBER, a);
      });
      const di = at("dice");
      if (di) (di.d.dice || []).forEach((d, n) => {
        const a = intro(di.t - n * 120, 200);
        if (a > 0) drawSquare(d.quad, CYAN, a, String(d.value));
      });
      const cu = at("cube");
      if (cu && cu.d.cube) {
        const a = intro(cu.t, 200);
        if (a > 0) drawSquare(cu.d.cube.quad, MAGENTA, a);
      }
      ctx.restore();
    }

    function frame(now) {
      if (stopped) return;
      raf = requestAnimationFrame(frame);
      next(now);
      if (!canvas.isConnected || canvas.offsetParent === null) return;
      base();
      if (cur) frameStages(now);
      else frameWaiting(opts.reduced ? 1e9 : now - t0);
    }
    raf = requestAnimationFrame(frame);

    const STAGE_NAMES = CORNERS ? ["edges", "uprights", "candidates", "corners"]
                                : ["fit", "board", "tips", "checkers", "counts", "dice", "cube"];
    return {
      // A stage the recognizer has finished ({stage, ...} as /analyze-photo streams it, in this
      // image's px): shown for its STAGE_MS once the ones before it have had theirs.
      push(ev) {
        if (stopped || !ev || !STAGE_NAMES.includes(ev.stage)) return;
        const { stage, ...data } = ev;
        queue.push({ stage, data });
      },
      // No more stages will come. Resolves once every stage has been shown (or the reading was tapped).
      done() {
        finished = true;
        if (stopped) return Promise.resolve();
        return new Promise((resolve) => { onDone = resolve; });
      },
      // Show the stages from a whole geometry (a server that does not stream), then done().
      reveal(geom) {
        if (geom && geom.corners) {
          const frame = { corners: geom.corners, columns: geom.columns, bar: geom.bar };
          this.push({ stage: "board", ...frame });
          this.push({ stage: "tips", tips: geom.tips || [] });
          this.push({ stage: "checkers", ...frame, checkers: geom.checkers || [] });
          if (geom.counts) this.push({ stage: "counts", counts: geom.counts });
          this.push({ stage: "dice", dice: geom.dice || [] });
          this.push({ stage: "cube", cube: geom.cube || null });
        }
        return this.done();
      },
      // The stage on screen now (its name), or null before the first one.
      stage() { return cur ? cur.stage : null; },
      // Skip the rest (a tap): done() resolves as soon as the result is in.
      skip() { skipped = true; },
      stop() {
        stopped = true; cancelAnimationFrame(raf);
        if (onDone) { const f = onDone; onDone = null; f(); }
      },
    };
  }

  const api = { layout, lines, start, TRI_DEPTH, STAGE_MS, DEFAULT_STAGE_MS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.BgScan = api;
})(this);
