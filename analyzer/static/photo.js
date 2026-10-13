// The photo on the board screen: the quad tapped in step 2, warped onto the drawn board's playing area
// so each point of the photo sits where the same point is drawn. Runs in the browser only; nothing is sent.
// Also loaded by Node in the tests (module.exports).
"use strict";

(function (root) {
  // 3x3 homography (row-major, h[8] = 1) that maps each src[k] = [x, y] to dst[k].
  function homography(src, dst) {
    const A = [], b = [];
    for (let k = 0; k < 4; k++) {
      const [x, y] = src[k], [u, v] = dst[k];
      A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
      A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
    }
    return solve(A, b).concat(1);
  }

  // Gaussian elimination with partial pivoting.
  function solve(A, b) {
    const n = b.length;
    const M = A.map((row, i) => row.concat(b[i]));
    for (let c = 0; c < n; c++) {
      let p = c;
      for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
      if (Math.abs(M[p][c]) < 1e-12) throw new Error("the corners do not make a quadrilateral");
      [M[c], M[p]] = [M[p], M[c]];
      for (let r = 0; r < n; r++) {
        if (r === c) continue;
        const f = M[r][c] / M[c][c];
        for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k];
      }
    }
    return M.map((row, i) => row[n] / row[i]);
  }

  function apply(h, x, y) {
    const w = h[6] * x + h[7] * y + h[8];
    return [(h[0] * x + h[1] * y + h[2]) / w, (h[3] * x + h[4] * y + h[5]) / w];
  }

  // Piecewise-linear y(x) through anchors [[x, y], ...] sorted by x (straight beyond the ends).
  function interp(anchors, x) {
    let k = 1;
    while (k < anchors.length - 1 && x > anchors[k][0]) k++;
    const [x0, y0] = anchors[k - 1], [x1, y1] = anchors[k];
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
  }

  // Output RGBA pixels (dw x dh): each output pixel (u, v) is sampled bilinearly from src
  // (RGBA, sw x sh) at apply(h, mapX(u + .5), v + .5). Outside the source is left black.
  function warp(src, sw, sh, h, dw, dh, mapX) {
    const out = new Uint8ClampedArray(dw * dh * 4);
    const mx = new Float64Array(dw);
    for (let u = 0; u < dw; u++) mx[u] = mapX ? mapX(u + 0.5) : u + 0.5;
    for (let v = 0; v < dh; v++) {
      for (let u = 0; u < dw; u++) {
        const o = (v * dw + u) * 4;
        out[o + 3] = 255;
        let [x, y] = apply(h, mx[u], v + 0.5);
        x -= 0.5; y -= 0.5;
        if (!(x >= 0 && y >= 0 && x <= sw - 1 && y <= sh - 1)) continue;
        const x0 = Math.max(0, Math.min(Math.floor(x), sw - 2)), y0 = Math.max(0, Math.min(Math.floor(y), sh - 2));
        const x1 = Math.min(x0 + 1, sw - 1), y1 = Math.min(y0 + 1, sh - 1);
        const fx = x - x0, fy = y - y0;
        const i00 = (y0 * sw + x0) * 4, i10 = (y0 * sw + x1) * 4, i01 = (y1 * sw + x0) * 4, i11 = (y1 * sw + x1) * 4;
        for (let c = 0; c < 3; c++) {
          const top = src[i00 + c] + (src[i10 + c] - src[i00 + c]) * fx;
          const bot = src[i01 + c] + (src[i11 + c] - src[i01 + c]) * fx;
          out[o + c] = top + (bot - top) * fy;
        }
      }
    }
    return out;
  }

  // Data URL of the rectified playing area, w x h pixels. corners: TL TR BR BL in image pixels.
  // columns (optional): [[x, f], ...] put the photo's column at fraction f of its width (0..1) at output x,
  // so the photo's points line up with the drawn ones even where the real bar is wider or narrower.
  function rectify(image, corners, w, h, columns) {
    const iw = image.width || image.naturalWidth, ih = image.height || image.naturalHeight;
    // Sample from a copy no larger than needed: a 12 MP photo would cost ~50 MB of pixels.
    const s = Math.min(1, 2048 / Math.max(iw, ih));
    const sw = Math.round(iw * s), sh = Math.round(ih * s);
    const sc = document.createElement("canvas");
    sc.width = sw; sc.height = sh;
    const sctx = sc.getContext("2d");
    sctx.drawImage(image, 0, 0, sw, sh);
    const src = sctx.getImageData(0, 0, sw, sh).data;
    const hm = homography([[0, 0], [w, 0], [w, h], [0, h]], corners.map(([x, y]) => [x * s, y * s]));
    const dc = document.createElement("canvas");
    dc.width = w; dc.height = h;
    const dctx = dc.getContext("2d");
    const img = dctx.createImageData(w, h);
    const mapX = columns && columns.length >= 2 ? (x) => interp(columns, x) * w : null;
    img.data.set(warp(src, sw, sh, hm, w, h, mapX));
    dctx.putImageData(img, 0, 0);
    return dc.toDataURL("image/jpeg", 0.88);
  }

  const api = { homography, apply, interp, warp, rectify };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.BgPhoto = api;
})(this);
