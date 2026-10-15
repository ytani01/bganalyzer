// The photo on the corners screen, with the four corners of the playing area to drag into place.
// A loupe magnifies the area under the finger. The view keeps only what a drag needs; the corners
// themselves belong to the app, which hears of every change through onChange.
//
//   const view = BgCornersView.create(canvas, {
//     photo: () => bitmap,               // the image (EXIF orientation applied)
//     corners: () => [[x, y], ...],      // image px, TL TR BR BL (up to 4 while they are tapped in)
//     onTouch(),                         // a finger came down (before anything moves)
//     onChange(corners, done),           // the corners moved; done: the finger is up
//   });
//   view.draw();      // the photo and the corners; view.draw(true): the photo alone (for scan.js)
//   view.toCanvas;    // image px -> canvas css px, as last drawn
"use strict";

const BgCornersView = (() => {
  const GRAB = 28;   // css px from a corner that still picks it up

  function create(canvas, app) {
    let view = null;   // {scale, ox, oy}: image px -> canvas css px
    let drag = null;   // {index, pointerId}
    let loupeAt = null;

    const size = () => { const b = app.photo(); return [b.width || b.naturalWidth, b.height || b.naturalHeight]; };
    const toCanvas = ([x, y]) => [view.ox + x * view.scale, view.oy + y * view.scale];

    function toImage(e) {
      const r = canvas.getBoundingClientRect();
      const [iw, ih] = size();
      const x = (e.clientX - r.left - view.ox) / view.scale;
      const y = (e.clientY - r.top - view.oy) / view.scale;
      return [Math.min(Math.max(x, 0), iw - 1), Math.min(Math.max(y, 0), ih - 1)];
    }

    function draw(bare) {
      const photo = app.photo();
      if (!photo || !canvas.offsetParent) return;   // no photo, or not on screen
      const [iw, ih] = size();
      const cw = canvas.parentElement.clientWidth;
      const ch = Math.min(window.innerHeight * 0.68, cw * ih / iw);
      const dpr = window.devicePixelRatio || 1;
      canvas.style.height = ch + "px";
      canvas.width = Math.round(cw * dpr);
      canvas.height = Math.round(ch * dpr);
      const scale = Math.min(cw / iw, ch / ih);
      view = { scale, ox: (cw - iw * scale) / 2, oy: (ch - ih * scale) / 2 };
      const ctx = canvas.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = "#000";
      ctx.fillRect(0, 0, cw, ch);
      ctx.drawImage(photo, view.ox, view.oy, iw * scale, ih * scale);
      if (bare === true) return;   // the reading overlay (scan.js) draws on the photo alone

      const pts = app.corners().map(toCanvas);
      if (pts.length > 1) {
        ctx.beginPath();
        pts.forEach(([x, y], k) => (k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
        if (pts.length === 4) ctx.closePath();
        ctx.strokeStyle = "#ffcc33";
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      pts.forEach(([x, y], k) => {
        ctx.beginPath();
        ctx.arc(x, y, 11, 0, 2 * Math.PI);
        ctx.fillStyle = "rgba(255, 204, 51, .85)";
        ctx.fill();
        ctx.fillStyle = "#000";
        ctx.font = "bold 13px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(k + 1), x, y);
      });
      if (loupeAt) drawLoupe(ctx, photo, loupeAt, cw);
    }

    // Magnified view of the area under the finger, drawn in the opposite top corner.
    function drawLoupe(ctx, photo, [ix, iy], cw) {
      const side = 120, zoom = 3;
      const src = side / (view.scale * zoom);
      const [cx] = toCanvas([ix, iy]);
      const x0 = cx < cw / 2 ? cw - side - 8 : 8, y0 = 8;
      ctx.save();
      ctx.beginPath();
      ctx.rect(x0, y0, side, side);
      ctx.clip();
      ctx.fillStyle = "#000";
      ctx.fillRect(x0, y0, side, side);
      ctx.drawImage(photo, ix - src / 2, iy - src / 2, src, src, x0, y0, side, side);
      ctx.restore();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 2;
      ctx.strokeRect(x0, y0, side, side);
      ctx.beginPath();
      ctx.moveTo(x0 + side / 2, y0 + side / 2 - 12); ctx.lineTo(x0 + side / 2, y0 + side / 2 + 12);
      ctx.moveTo(x0 + side / 2 - 12, y0 + side / 2); ctx.lineTo(x0 + side / 2 + 12, y0 + side / 2);
      ctx.strokeStyle = "#ffcc33";
      ctx.stroke();
    }

    // A finger on a corner picks it up; elsewhere it adds the next one while there are fewer than 4.
    canvas.addEventListener("pointerdown", (e) => {
      app.onTouch();
      if (!view) return;
      const r = canvas.getBoundingClientRect();
      const px = e.clientX - r.left, py = e.clientY - r.top;
      const corners = app.corners().map((c) => c.slice());
      let index = corners.findIndex((c) => {
        const [x, y] = toCanvas(c);
        return Math.hypot(x - px, y - py) < GRAB;
      });
      if (index < 0) {
        if (corners.length >= 4) return;
        corners.push(toImage(e));
        index = corners.length - 1;
      }
      drag = { index, pointerId: e.pointerId };
      canvas.setPointerCapture(e.pointerId);
      loupeAt = corners[index];
      app.onChange(corners, false);
      e.preventDefault();
    });

    canvas.addEventListener("pointermove", (e) => {
      if (!drag || e.pointerId !== drag.pointerId) return;
      const corners = app.corners().map((c) => c.slice());
      corners[drag.index] = loupeAt = toImage(e);
      app.onChange(corners, false);
    });

    function release(e) {
      if (!drag || e.pointerId !== drag.pointerId) return;
      drag = loupeAt = null;
      app.onChange(app.corners(), true);
    }
    canvas.addEventListener("pointerup", release);
    canvas.addEventListener("pointercancel", release);

    return { draw, toCanvas: (p) => toCanvas(p) };
  }

  return { create };
})();
