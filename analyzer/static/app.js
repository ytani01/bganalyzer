// BG Analyzer PWA: photo -> 4 corners -> recognized board (editable) -> gnubg analysis.
// Colours follow the server: white = the player at the bottom of the photo (手前), black = 奥.
"use strict";

const API = (new URLSearchParams(location.search).get("api") || "").replace(/\/$/, "");
const UPLOAD_MAX = 2048;      // longest side sent to the server (recognition was checked at this size)
const SEND_AS_IS_MAX = 2560;  // smaller images (screenshots) are sent untouched
const START = [-2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2];
const NAME = { white: "手前", black: "奥" };
const CORNER_NAMES = ["左上", "右上", "右下", "左下"];
const SHARE_CACHE = "bganalyzer-share";   // same names as in sw.js
const SHARE_KEY = "shared-photo";

const $ = (id) => document.getElementById(id);

const state = {
  file: null,        // the chosen File
  bitmap: null,      // decoded image (EXIF orientation applied)
  corners: [],       // [[x, y], ...] in image pixels, TL TR BR BL
  home: "right",
  bottomColour: 1,   // 0 = the darker checkers are 手前's, 1 = the lighter ones
  onRoll: "white",
  fromPhoto: false,
  warnings: [],      // the server's notes on the photo (e.g. taken at a steep angle)
  board: null,       // {points[24], bar_white, bar_black}
  selected: null,    // point index 0..23, or "bar"
  result: null,
};

// ---------------------------------------------------------------- steps
function show(step) {
  for (const s of document.querySelectorAll("section.step")) s.hidden = s.id !== step;
  for (const s of document.querySelectorAll("#steps span")) s.classList.toggle("on", s.dataset.step === step);
  if (step === "corners") requestAnimationFrame(drawPhoto);
  if (step === "board") drawBoard();
  window.scrollTo(0, 0);
}

function busy(text) {
  $("busy").hidden = !text;
  $("busy-text").textContent = text || "";
}

// ---------------------------------------------------------------- segmented buttons
function initSeg(name, onChange) {
  const seg = document.querySelector(`.seg[data-name="${name}"]`);
  const sync = () => {
    for (const b of seg.children) b.classList.toggle("on", b.dataset.value === String(state[name]));
  };
  seg.addEventListener("click", (e) => {
    const v = e.target.dataset && e.target.dataset.value;
    if (v === undefined) return;
    state[name] = name === "bottomColour" ? Number(v) : v;
    sync();
    if (onChange) onChange();
  });
  sync();
  return sync;
}

// ---------------------------------------------------------------- step 1: photo
$("file").addEventListener("change", (e) => {
  const file = e.target.files[0];
  e.target.value = "";
  if (file) loadPhoto(file);
});

async function loadPhoto(file) {
  busy("写真を読み込んでいます…");
  try {
    state.bitmap = await decode(file);
    state.file = file;
    state.corners = [];
    state.fromPhoto = true;
    updateCornerUi();
    show("corners");
  } catch (err) {
    alert("写真を開けませんでした: " + err.message);
  } finally {
    busy();
  }
}

// A photo shared from another app (Android: 共有 → BG Analyzer). sw.js keeps it in a cache on the
// phone and opens ./?shared=1; it is not sent to the server until 盤面を読み取る, as usual.
async function loadSharedPhoto() {
  const params = new URLSearchParams(location.search);
  const shared = params.get("shared");
  if (shared === null) return;
  params.delete("shared");
  const rest = params.toString();
  history.replaceState(null, "", location.pathname + (rest ? "?" + rest : ""));
  if (shared === "none") {   // the service worker was not running yet, so the photo did not arrive
    alert("共有された写真を受け取れませんでした。もう一度共有するか、「写真を撮る / 選ぶ」から選んでください。");
    return;
  }
  try {
    const cache = await caches.open(SHARE_CACHE);
    const res = await cache.match(SHARE_KEY);
    if (!res) return;
    await cache.delete(SHARE_KEY);
    const blob = await res.blob();
    const name = decodeURIComponent(res.headers.get("X-File-Name") || "shared.jpg");
    loadPhoto(new File([blob], name, { type: blob.type }));
  } catch (err) {
    alert("共有された写真を開けませんでした: " + err.message);
  }
}

async function decode(file) {
  if (window.createImageBitmap) {
    try { return await createImageBitmap(file, { imageOrientation: "from-image" }); } catch (_) { /* fall back */ }
  }
  const url = URL.createObjectURL(file);
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    return img;
  } finally {
    URL.revokeObjectURL(url);
  }
}

$("manual").addEventListener("click", () => {
  state.fromPhoto = false;
  state.warnings = [];
  state.board = { points: START.slice(), bar_white: 0, bar_black: 0 };
  state.selected = null;
  setResult(null);
  $("errors").hidden = true;
  show("board");
});

// ---------------------------------------------------------------- step 2: corners
const canvas = $("photo-canvas");
let view = null;   // {scale, ox, oy} image px -> canvas css px
let drag = null;   // {index, pointerId}
let loupeAt = null;

function imgSize() {
  const b = state.bitmap;
  return [b.width || b.naturalWidth, b.height || b.naturalHeight];
}

function drawPhoto() {
  if (!state.bitmap || $("corners").hidden) return;
  const [iw, ih] = imgSize();
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
  ctx.drawImage(state.bitmap, view.ox, view.oy, iw * scale, ih * scale);

  const pts = state.corners.map(toCanvas);
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
  if (loupeAt) drawLoupe(ctx, loupeAt, cw);
}

// Magnified view of the area under the finger, drawn in the opposite top corner.
function drawLoupe(ctx, [ix, iy], cw) {
  const size = 120, zoom = 3;
  const src = size / (view.scale * zoom);
  const [cx] = toCanvas([ix, iy]);
  const x0 = cx < cw / 2 ? cw - size - 8 : 8, y0 = 8;
  ctx.save();
  ctx.beginPath();
  ctx.rect(x0, y0, size, size);
  ctx.clip();
  ctx.fillStyle = "#000";
  ctx.fillRect(x0, y0, size, size);
  ctx.drawImage(state.bitmap, ix - src / 2, iy - src / 2, src, src, x0, y0, size, size);
  ctx.restore();
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 2;
  ctx.strokeRect(x0, y0, size, size);
  ctx.beginPath();
  ctx.moveTo(x0 + size / 2, y0 + size / 2 - 12); ctx.lineTo(x0 + size / 2, y0 + size / 2 + 12);
  ctx.moveTo(x0 + size / 2 - 12, y0 + size / 2); ctx.lineTo(x0 + size / 2 + 12, y0 + size / 2);
  ctx.strokeStyle = "#ffcc33";
  ctx.stroke();
}

const toCanvas = ([x, y]) => [view.ox + x * view.scale, view.oy + y * view.scale];

function toImage(e) {
  const r = canvas.getBoundingClientRect();
  const [iw, ih] = imgSize();
  const x = (e.clientX - r.left - view.ox) / view.scale;
  const y = (e.clientY - r.top - view.oy) / view.scale;
  return [Math.min(Math.max(x, 0), iw - 1), Math.min(Math.max(y, 0), ih - 1)];
}

canvas.addEventListener("pointerdown", (e) => {
  if (!view) return;
  const r = canvas.getBoundingClientRect();
  const px = e.clientX - r.left, py = e.clientY - r.top;
  let index = state.corners.findIndex((c) => {
    const [x, y] = toCanvas(c);
    return Math.hypot(x - px, y - py) < 28;
  });
  if (index < 0) {
    if (state.corners.length >= 4) return;
    state.corners.push(toImage(e));
    index = state.corners.length - 1;
  }
  drag = { index, pointerId: e.pointerId };
  canvas.setPointerCapture(e.pointerId);
  loupeAt = state.corners[index];
  drawPhoto();
  e.preventDefault();
});

canvas.addEventListener("pointermove", (e) => {
  if (!drag || e.pointerId !== drag.pointerId) return;
  state.corners[drag.index] = toImage(e);
  loupeAt = state.corners[drag.index];
  drawPhoto();
});

function endDrag(e) {
  if (!drag || e.pointerId !== drag.pointerId) return;
  drag = null;
  loupeAt = null;
  updateCornerUi();   // after the finger is up: the text above may change height and move the canvas
  drawPhoto();
}
canvas.addEventListener("pointerup", endDrag);
canvas.addEventListener("pointercancel", endDrag);
window.addEventListener("resize", drawPhoto);

function updateCornerUi() {
  const n = state.corners.length;
  $("corner-help").innerHTML = n < 4
    ? `手前に座った向きで、盤の遊戯面（枠の内側）の四隅を <b>${n + 1}. ${CORNER_NAMES[n]}</b> の順にタップしてください（左上→右上→右下→左下）。`
    : "四隅が決まりました。ホーム側と駒の色を選んで「盤面を読み取る」を押してください。";
  $("recognize").disabled = n < 4;
}

$("corner-reset").addEventListener("click", () => {
  state.corners = [];
  updateCornerUi();
  drawPhoto();
});
$("back-photo").addEventListener("click", () => show("photo"));

// Large photos are scaled down before upload; corners are scaled with them.
async function uploadImage() {
  const [iw, ih] = imgSize();
  if (Math.max(iw, ih) <= SEND_AS_IS_MAX) return { blob: state.file, scale: 1 };
  const scale = UPLOAD_MAX / Math.max(iw, ih);
  const c = document.createElement("canvas");
  c.width = Math.round(iw * scale);
  c.height = Math.round(ih * scale);
  c.getContext("2d").drawImage(state.bitmap, 0, 0, c.width, c.height);
  const blob = await new Promise((res) => c.toBlob(res, "image/jpeg", 0.92));
  return { blob, scale };
}

$("recognize").addEventListener("click", async () => {
  busy("盤面を読み取っています…");
  try {
    const { blob, scale } = await uploadImage();
    const fd = new FormData();
    fd.append("image", blob, "board.jpg");
    fd.append("corners", state.corners.flat().map((v) => (v * scale).toFixed(1)).join(","));
    fd.append("home", state.home);
    fd.append("bottom_colour", String(state.bottomColour));
    fd.append("on_roll", state.onRoll);
    const dice = currentDice();
    if (dice) fd.append("dice", dice.join(","));
    const data = await post("analyze-photo", fd);
    const rec = data.recognized;
    state.warnings = data.warnings || [];
    state.board = { points: rec.points, bar_white: rec.bar_white, bar_black: rec.bar_black };
    state.selected = null;
    show("board");
    setResult(data.analysis, dice);
  } catch (err) {
    alert("読み取りに失敗しました: " + err.message);
  } finally {
    busy();
  }
});

// ---------------------------------------------------------------- step 3: board
const SVG = "http://www.w3.org/2000/svg";
const B = { x0: 20, y0: 24, y1: 416, pw: 48, bar: 40, r: 20, step: 38, tri: 165 };

function colX(c) {
  const half = c < 6 ? B.x0 : B.x0 + 6 * B.pw + B.bar;
  return half + (c % 6) * B.pw + B.pw / 2;
}

// Column (0..11, left to right) of each row -> point index (0..23) as the bottom player sees the board.
function pointAt(top, c) {
  if (state.home === "right") return top ? 12 + c : 11 - c;
  return top ? 23 - c : c;
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

function checkerFill(side) {
  return side === "white" ? "var(--white-chk)" : "var(--black-chk)";
}

function drawStack(svg, x, top, n, side) {
  const shown = Math.min(n, 5);
  for (let k = 0; k < shown; k++) {
    const y = top ? B.y0 + B.r + 1 + k * B.step : B.y1 - B.r - 1 - k * B.step;
    el("circle", { cx: x, cy: y, r: B.r, fill: checkerFill(side), stroke: "#555", "stroke-width": 1.5, "pointer-events": "none" }, svg);
    if (k === shown - 1 && n > 5) {
      const t = el("text", { x, y, class: "stack-n", fill: `var(--${side}-fg)`, "pointer-events": "none" }, svg);
      t.textContent = n;
    }
  }
}

function drawBoard() {
  const svg = $("board-svg");
  svg.textContent = "";
  const b = state.board;
  const xR = B.x0 + 12 * B.pw + B.bar;
  el("rect", { x: 0, y: 0, width: 660, height: 440, fill: "var(--card)" }, svg);
  el("rect", { x: B.x0 - 6, y: B.y0 - 6, width: xR - B.x0 + 12, height: B.y1 - B.y0 + 12, rx: 6, fill: "var(--frame)" }, svg);
  el("rect", { x: B.x0, y: B.y0, width: 6 * B.pw, height: B.y1 - B.y0, fill: "var(--felt)" }, svg);
  el("rect", { x: B.x0 + 6 * B.pw + B.bar, y: B.y0, width: 6 * B.pw, height: B.y1 - B.y0, fill: "var(--felt)" }, svg);

  for (const top of [true, false]) {
    for (let c = 0; c < 12; c++) {
      const i = pointAt(top, c);
      const x = colX(c), h = B.pw / 2;
      const base = top ? B.y0 : B.y1, tip = top ? B.y0 + B.tri : B.y1 - B.tri;
      el("polygon", { points: `${x - h},${base} ${x + h},${base} ${x},${tip}`, fill: c % 2 ? "var(--tri-b)" : "var(--tri-a)" }, svg);
      const lbl = el("text", { x, y: top ? 16 : 434, class: "num" }, svg);
      lbl.textContent = i + 1;
      const n = b.points[i];
      if (n) drawStack(svg, x, top, Math.abs(n), n > 0 ? "white" : "black");
      if (state.selected === i) {
        el("rect", { x: x - h + 1, y: top ? B.y0 + 1 : B.y0 + (B.y1 - B.y0) / 2 + 1, width: B.pw - 2, height: (B.y1 - B.y0) / 2 - 2, fill: "none", stroke: "var(--sel)", "stroke-width": 3 }, svg);
      }
      const hit = el("rect", { x: x - h, y: top ? B.y0 : B.y0 + (B.y1 - B.y0) / 2, width: B.pw, height: (B.y1 - B.y0) / 2, fill: "transparent", class: "hit" }, svg);
      hit.addEventListener("click", () => select(i));
    }
  }

  // Bar: 奥's checkers in the upper half, 手前's in the lower half.
  const bx = B.x0 + 6 * B.pw + B.bar / 2;
  if (b.bar_black) drawStack(svg, bx, true, b.bar_black, "black");
  if (b.bar_white) drawStack(svg, bx, false, b.bar_white, "white");
  const barLbl = el("text", { x: bx, y: (B.y0 + B.y1) / 2 + 5, class: "label" }, svg);
  barLbl.textContent = "バー";
  if (state.selected === "bar") {
    el("rect", { x: bx - B.bar / 2 + 1, y: B.y0 + 1, width: B.bar - 2, height: B.y1 - B.y0 - 2, fill: "none", stroke: "var(--sel)", "stroke-width": 3 }, svg);
  }
  const barHit = el("rect", { x: bx - B.bar / 2, y: B.y0, width: B.bar, height: B.y1 - B.y0, fill: "transparent", class: "hit" }, svg);
  barHit.addEventListener("click", () => select("bar"));

  drawCounts();
  drawEditor();
}

function counts() {
  const b = state.board;
  const onW = b.points.reduce((s, n) => s + Math.max(n, 0), 0) + b.bar_white;
  const onB = b.points.reduce((s, n) => s + Math.max(-n, 0), 0) + b.bar_black;
  return { onW, onB, offW: 15 - onW, offB: 15 - onB };
}

function boardErrors() {
  const { onW, onB } = counts();
  const errs = [];
  if (onW > 15) errs.push(`手前の駒が ${onW} 個あります（15個まで）`);
  if (onB > 15) errs.push(`奥の駒が ${onB} 個あります（15個まで）`);
  if (onW === 0 && onB === 0) errs.push("盤に駒がありません");
  return errs;
}

function drawCounts() {
  const { onW, onB, offW, offB } = counts();
  const part = (name, on, off) => {
    const bad = on > 15 ? ' class="bad"' : "";
    return `<span${bad}>${name}: 盤上とバー ${on} 個・上がり ${Math.max(off, 0)} 個</span>`;
  };
  $("counts").innerHTML = part("手前", onW, offW) + "<br>" + part("奥", onB, offB) +
    '<br><span class="note">上がった駒は 15 − 盤上 − バー として数えます。読み取りで駒を見落とすと、その分が上がった扱いになります。</span>';
  const errs = boardErrors();
  if (!errs.length && state.fromPhoto && (offW > 0 || offB > 0)) {
    errs.push(`上がった駒が 手前 ${offW} 個・奥 ${offB} 個 の扱いです。駒の見落としがないか確かめてください。`);
  }
  if (state.fromPhoto) errs.unshift(...state.warnings);
  $("errors").hidden = !errs.length;
  $("errors").textContent = errs.join(" / ");
}

function select(target) {
  state.selected = state.selected === target ? null : target;
  drawBoard();
}

function drawEditor() {
  const s = state.selected;
  $("editor-buttons").hidden = s === null;
  if (s === null) {
    $("editor-title").textContent = "ポイントかバーをタップすると駒の数を直せます";
    return;
  }
  const b = state.board;
  if (s === "bar") {
    $("editor-title").textContent = `バー: 手前 ${b.bar_white} 個、奥 ${b.bar_black} 個`;
  } else {
    const n = b.points[s];
    $("editor-title").textContent = `ポイント ${s + 1}（手前から見た番号）: ` +
      (n === 0 ? "空" : `${n > 0 ? "手前" : "奥"}の駒 ${Math.abs(n)} 個`);
  }
}

$("editor-buttons").addEventListener("click", (e) => {
  const op = e.target.dataset && e.target.dataset.op;
  if (!op || state.selected === null) return;
  const b = state.board, s = state.selected;
  if (s === "bar") {
    if (op === "w+") b.bar_white++;
    if (op === "w-") b.bar_white = Math.max(0, b.bar_white - 1);
    if (op === "b+") b.bar_black++;
    if (op === "b-") b.bar_black = Math.max(0, b.bar_black - 1);
    if (op === "clear") b.bar_white = b.bar_black = 0;
  } else {
    let n = b.points[s];
    if (op === "w+") n = Math.max(n, 0) + 1;
    if (op === "w-" && n > 0) n--;
    if (op === "b+") n = Math.min(n, 0) - 1;
    if (op === "b-" && n < 0) n++;
    if (op === "clear") n = 0;
    b.points[s] = n;
  }
  boardChanged();
});

function boardChanged() {
  if (state.result) $("result").classList.add("stale");
  drawBoard();
}

$("swap-colours").addEventListener("click", () => {
  const b = state.board;
  b.points = b.points.map((n) => -n);
  [b.bar_white, b.bar_black] = [b.bar_black, b.bar_white];
  state.bottomColour = 1 - state.bottomColour;
  syncColours();
  boardChanged();
});

// The board was read with the home on the wrong side: mirror it left to right.
$("flip-home").addEventListener("click", () => {
  const b = state.board;
  b.points = b.points.map((_, i) => b.points[i < 12 ? 11 - i : 35 - i]);
  state.home = state.home === "right" ? "left" : "right";
  syncHome();
  state.selected = null;
  boardChanged();
});

$("reset-start").addEventListener("click", () => {
  if (!confirm("盤面を初期配置に戻しますか？")) return;
  state.board = { points: START.slice(), bar_white: 0, bar_black: 0 };
  state.selected = null;
  boardChanged();
});

$("back-corners").addEventListener("click", () => show(state.fromPhoto ? "corners" : "photo"));

// ---------------------------------------------------------------- analysis
for (const id of ["die1", "die2"]) {
  for (let d = 1; d <= 6; d++) $(id).add(new Option(String(d), String(d)));
  $(id).addEventListener("change", () => state.result && $("result").classList.add("stale"));
}

function currentDice() {
  const a = $("die1").value, b = $("die2").value;
  return a && b ? [Number(a), Number(b)] : null;
}

$("analyze").addEventListener("click", async () => {
  const errs = boardErrors();
  if (errs.length) { alert(errs.join("\n")); return; }
  busy("解析しています…");
  try {
    const body = { board: { ...state.board }, on_roll: state.onRoll };
    const dice = currentDice();
    if (dice) body.dice = dice;
    const r = await post("analyze", JSON.stringify(body), { "content-type": "application/json" });
    setResult(r, dice);
    $("result").scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    alert("解析に失敗しました: " + err.message);
  } finally {
    busy();
  }
});

// path is relative ("analyze"), so the app also works under a path such as /bg/.
async function post(path, body, headers) {
  const res = await fetch(API ? `${API}/${path}` : path, { method: "POST", body, headers });
  let data = null;
  try { data = await res.json(); } catch (_) { /* not JSON */ }
  if (!res.ok) {
    const d = data && data.detail;
    throw new Error(typeof d === "string" ? d : `HTTP ${res.status}`);
  }
  return data;
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function setResult(r, dice) {
  state.result = r;
  const box = $("result");
  box.classList.remove("stale");
  box.hidden = !r;
  if (!r) return;
  const pips = r.pips;
  const pipLine = pips.leader
    ? `${NAME[pips.leader]}が ${pips.difference} ピップ リード`
    : "ピップは同じ";
  let html = `<h2>${esc(r.summary)}</h2>`;
  if (!r.game_over) {
    const p = r.probabilities;
    const w = p.white.win, bl = p.black.win;
    html += `<div class="winbar"><div class="w" style="width:${w}%">手前 ${w}%</div>` +
      `<div class="b" style="width:${bl}%">奥 ${bl}%</div></div>`;
    html += `<table><tr><th></th><th>手前</th><th>奥</th></tr>` +
      `<tr><td>勝率</td><td>${w}%</td><td>${bl}%</td></tr>` +
      `<tr><td>うちギャモン勝ち</td><td>${p.white.gammon}%</td><td>${p.black.gammon}%</td></tr>` +
      `<tr><td>うちバックギャモン勝ち</td><td>${p.white.backgammon}%</td><td>${p.black.backgammon}%</td></tr>` +
      `<tr><td>エクイティ</td><td>${r.equity.white.toFixed(3)}</td><td>${r.equity.black.toFixed(3)}</td></tr>` +
      `<tr><td>ピップ数</td><td>${pips.white}</td><td>${pips.black}</td></tr></table>`;
  }
  html += `<p>${pipLine}。次に振るのは${NAME[r.on_roll]}の人。</p>`;
  if (r.moves) {
    html += `<h2>最善手（${NAME[r.on_roll]}・ダイス ${dice ? dice.join("-") : ""}）</h2>`;
    html += r.moves.length
      ? `<ol class="moves">${r.moves.map((m) => `<li>${esc(m.move)}<span>エクイティ ${m.equity.toFixed(3)}</span></li>`).join("")}</ol>` +
        `<p class="note">番号は${NAME[r.on_roll]}の人から見たポイント番号です。</p>`
      : "<p>動かせる手がありません。</p>";
  }
  html += `<p class="note">gnubg ${r.plies}手読み・キューブなし。Position ID: <code>${esc(r.position_id)}</code></p>`;
  box.innerHTML = html;
}

// ---------------------------------------------------------------- colours & init
function syncColours() {
  const light = "#f3efe4", dark = "#3a2a4a";
  const root = document.documentElement.style;
  root.setProperty("--white-chk", state.bottomColour ? light : dark);
  root.setProperty("--black-chk", state.bottomColour ? dark : light);
  root.setProperty("--white-fg", state.bottomColour ? "#222" : "#fff");
  root.setProperty("--black-fg", state.bottomColour ? "#fff" : "#222");
  syncBottomColour();
}

const syncHome = initSeg("home");
const syncBottomColour = initSeg("bottomColour", syncColours);
initSeg("onRoll", () => state.result && $("result").classList.add("stale"));
syncColours();
updateCornerUi();
show("photo");

// Server versions in the footer, to tell which build is running (e.g. on the Raspberry Pi).
fetch(API ? `${API}/version` : "version")
  .then((res) => (res.ok ? res.json() : null))
  .then((v) => {
    if (!v) return;
    $("version").textContent = `analyzer ${v.analyzer} · recognizer ${v.recognizer}` +
      (v.commit ? ` · ${v.commit}` : "");
  })
  .catch(() => {});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}

loadSharedPhoto();
