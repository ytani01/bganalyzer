// BG Analyzer PWA: photo -> 4 corners -> recognized board (editable) -> gnubg analysis.
// Colours follow the server: white = the player at the bottom of the photo (手前), black = 奥.
"use strict";

const APP_VERSION = "0.25.1";   // = __version__ in analyzer/app.py; tells an old cached app.js apart
const API = (new URLSearchParams(location.search).get("api") || "").replace(/\/$/, "");
const UPLOAD_MAX = 2048;      // longest side sent to the server (recognition was checked at this size)
const SEND_AS_IS_MAX = 2560;  // smaller images (screenshots) are sent untouched
const START = [-2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2];
const NAME = { white: "手前", black: "奥" };
const CORNER_NAMES = ["左上", "右上", "右下", "左下"];
const SHARE_CACHE = "bganalyzer-share";   // same names as in sw.js
const SHARE_KEY = "shared-photo";

const $ = (id) => document.getElementById(id);

function storedPlies() {
  try { return localStorage.getItem("plies") === "3" ? "3" : "2"; } catch (_) { return "2"; }
}

function storedCollect() {
  try { return localStorage.getItem("collect") === "on" ? "on" : "off"; } catch (_) { return "off"; }
}

function analysingText() {
  return state.plies === "3" ? "3手読みで解析しています（しばらくかかります）…" : "解析しています…";
}

const state = {
  file: null,        // the chosen File
  bitmap: null,      // decoded image (EXIF orientation applied)
  corners: [],       // [[x, y], ...] in image pixels, TL TR BR BL
  cornerGuess: "",   // the starting corners: "finding", "found", "default" (a rectangle), "moved" or "" (tapped)
  cornersMoved: false,
  homePick: "auto",  // the choice on the corners screen: "auto" (guess from the checkers), "left" or "right"
  home: "right",     // the side the board is read and drawn with
  homeGuess: null,   // how the server guessed home (homePick "auto"): {margin}; null once flipped by hand
  bottomColour: 1,   // 0 = the darker checkers are 手前's, 1 = the lighter ones
  onRoll: "white",
  cubeAt: "centre",  // where the doubling cube lies: "centre", "white" (手前's side) or "black" (cube.js)
  cubeValue: 2,      // the number on it when on a side
  cubeOffered: true, // on a side with no dice: just offered there (take or pass?), not owned
  collect: storedCollect(),   // "on": keep the photo and the fixed board on the server (sendSample)
  plies: storedPlies(),   // how deep gnubg reads: "2" or "3" (kept on this phone)
  fromPhoto: false,
  warnings: [],      // the server's notes on the photo (e.g. taken at a steep angle)
  board: null,       // {points[24], bar_white, bar_black}
  read: null,        // the board as the recognizer read it, before fixes by hand (same layout as board)
  selected: null,    // point index 0..23, or "bar"
  result: null,
  speech: null,      // the result read aloud (speechText) by the header's 🔊 button
  resultKey: null,  // analysisKey() of what the result on screen was worked out for
  moveShown: 0,      // the move in the result's list drawn as arrows on the board
  historyId: null,   // this photo's entry in PhotoHistory (history.js), null if not stored
  historyScale: 1,   // image px -> the stored copy's px
  photoView: "side", // the photo on the board screen: "side" (next to the board) or "off"
  geometry: null,    // where the recognizer found the board: {corners (image px), columns, bar (fractions), bitmap, from}
  rectified: null,   // {bitmap, key, url}: the photo warped onto the board's playing area
};

// ---------------------------------------------------------------- steps
const STEPS = ["photo", "corners", "board", "outcome"];
const STEP_TITLES = { corners: "四隅", board: "盤面・設定", outcome: "結果" };   // the header's title on a phone, where the step list is hidden

// The sticky header is as tall as its contents; the board sticks just under it (CSS --hdr-h).
new ResizeObserver(() => {
  document.documentElement.style.setProperty("--hdr-h", document.querySelector("header").offsetHeight + "px");
}).observe(document.querySelector("header"));
let currentStep = "photo";

function show(step) {
  currentStep = step;
  for (const s of document.querySelectorAll("section.step")) s.hidden = s.id !== step;
  const at = STEPS.indexOf(step);
  for (const s of document.querySelectorAll("#steps span")) {
    s.classList.toggle("on", s.dataset.step === step);
    s.classList.toggle("done", STEPS.indexOf(s.dataset.step) < at);
  }
  $("back").hidden = step === "photo";
  $("title").textContent = step === "photo" ? "BG Analyzer" : STEP_TITLES[step];
  syncHeaderActions();
  // One history entry stands for "inside the app", so the phone's own back button
  // (or gesture) comes back here as a popstate instead of leaving the app.
  if (step !== "photo" && !(history.state && history.state.bg)) history.pushState({ bg: true }, "");
  if (step === "corners") {
    $("to-board").hidden = !(state.fromPhoto && state.board);
    requestAnimationFrame(drawPhoto);
  }
  if (step === "board") $("export-sample").hidden = !(state.fromPhoto && state.board);
  if (step === "board" || step === "outcome") drawBoard();
  if (step === "photo") renderHistory();
  window.scrollTo(0, 0);
}

// The header carries the screen's main action (and reading aloud once there is a result),
// so it can be pressed without scrolling down to the big button.
function syncHeaderActions() {
  $("recognize").hidden = currentStep !== "corners";
  $("analyze").hidden = currentStep !== "board";
  $("speak").hidden = !(currentStep === "outcome" && state.result && window.speechSynthesis);
}
$("speak").addEventListener("click", () => { if (state.speech) toggleSpeaking(state.speech); });

function previousStep() {
  if (currentStep === "outcome") return "board";
  return currentStep === "board" && state.fromPhoto ? "corners" : "photo";
}

// Back to the photo screen also uses up the history entry, so the next back leaves the app.
function goBack() {
  if (previousStep() === "photo" && history.state && history.state.bg) history.back();
  else show(previousStep());
}

$("back").addEventListener("click", goBack);
window.addEventListener("popstate", () => {
  if (!$("busy").hidden) { history.pushState({ bg: true }, ""); return; }   // wait for the server
  if (currentStep !== "photo") show(previousStep());
});

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
    saveHistory();
  });
  sync();
  return sync;
}

// ---------------------------------------------------------------- step 1: photo
for (const id of ["camera", "file"]) {
  $(id).addEventListener("change", (e) => {
    const file = e.target.files[0];
    e.target.value = "";
    if (file) loadPhoto(file);
  });
}

async function loadPhoto(file) {
  busy("写真を読み込んでいます…");
  try {
    state.bitmap = await decode(file);
    state.file = file;
    state.fromPhoto = true;
    state.board = null;
    state.read = null;
    state.warnings = [];
    setDice(null);   // the dice of the last position are not this photo's
    setCube(null);
    setResult(null);
    // start from a rectangle at once, and replace it with the server's guess when that comes
    state.corners = defaultCorners();
    state.cornerGuess = "finding";
    state.cornersMoved = false;
    await addToHistory(file);
    updateCornerUi();
    show("corners");
    guessCorners(file);
  } catch (err) {
    alert("写真を開けませんでした: " + err.message);
  } finally {
    busy();
  }
}

// A photo shared from another app (Android: 共有 → BG Analyzer). sw.js keeps it in a cache on the
// phone and opens ./?shared=1; from there it goes the same way as a chosen photo.
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
  state.read = null;
  state.historyId = null;
  state.warnings = [];
  state.board = { points: START.slice(), bar_white: 0, bar_black: 0 };
  state.selected = null;
  setResult(null);
  $("errors").hidden = true;
  show("board");
});

// ---------------------------------------------------------------- step 2: corners
// The rectangle the corners start from while (or if) the board can't be found.
function defaultCorners() {
  const [iw, ih] = imgSize();
  const mx = iw * 0.1, my = ih * 0.1;
  return [[mx, my], [iw - mx, my], [iw - mx, ih - my], [mx, ih - my]];
}

async function guessCorners(file) {
  let corners = null;
  try {
    const { blob, scale } = await uploadImage();   // the guess is steadier from the larger image
    const fd = new FormData();
    fd.append("image", blob, "board.jpg");
    const data = await post("find-corners", fd);
    if (data.corners) corners = data.corners.map(([x, y]) => [x / scale, y / scale]);
  } catch (_) { /* keep the rectangle */ }
  // the user may have moved on to another photo, or started on the corners already
  if (state.file !== file || state.cornerGuess !== "finding") return;
  if (state.cornersMoved) state.cornerGuess = "moved";
  else if (corners) [state.corners, state.cornerGuess] = [corners, "found"];
  else state.cornerGuess = "default";
  updateCornerUi();
  drawPhoto();
  saveHistory();
}

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
  state.cornersMoved = true;
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
  saveHistory();
}
canvas.addEventListener("pointerup", endDrag);
canvas.addEventListener("pointercancel", endDrag);
window.addEventListener("resize", drawPhoto);

function updateCornerUi() {
  const n = state.corners.length;
  const fit = "点をドラッグして、盤の遊戯面（枠の内側）の四隅 1 左上・2 右上・3 右下・4 左下（手前に座った向き）に合わせてください。";
  $("corner-help").innerHTML = n < 4
    ? `手前に座った向きで、盤の遊戯面（枠の内側）の四隅を <b>${n + 1}. ${CORNER_NAMES[n]}</b> の順にタップしてください（左上→右上→右下→左下）。`
    : state.cornerGuess === "finding" ? "盤の四隅を探しています… " + fit
    : state.cornerGuess === "found" ? "盤の四隅を自動で置きました。ずれていたら" + fit
    : state.cornerGuess === "default" ? "盤を自動で見つけられませんでした。" + fit
    : state.cornerGuess === "moved" ? fit
    : "四隅が決まりました。ホーム側と駒の色を選んで上の「盤面を読み取る」を押してください。";
  $("recognize").disabled = n < 4;
}

$("corner-reset").addEventListener("click", () => {
  state.corners = [];
  state.cornerGuess = "";
  updateCornerUi();
  drawPhoto();
  saveHistory();
});

// Large photos are scaled down before upload; corners are scaled with them.
function uploadImage() {
  const [iw, ih] = imgSize();
  if (Math.max(iw, ih) <= SEND_AS_IS_MAX) return Promise.resolve({ blob: state.file, scale: 1 });
  return shrink(UPLOAD_MAX);
}

async function shrink(maxSide) {
  const [iw, ih] = imgSize();
  const scale = Math.min(1, maxSide / Math.max(iw, ih));
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
    fd.append("home", state.homePick);
    fd.append("bottom_colour", String(state.bottomColour));
    let dice = currentDice();
    const cubeReq = BgCube.request(currentCube(), state.onRoll, dice);
    fd.append("on_roll", cubeReq.on_roll);
    if (dice) fd.append("dice", dice.join(","));
    // a cube set by hand goes with the photo; else the server uses the one it reads (if any)
    const cubeByHand = state.cubeAt !== "centre";
    if (cubeByHand) {
      fd.append("cube_value", String(cubeReq.cube_value));
      fd.append("cube_owner", cubeReq.cube_owner);
      fd.append("doubled", String(cubeReq.doubled));
    }
    fd.append("plies", state.plies);
    const data = await post("analyze-photo", fd);
    if (!dice && data.dice_read) {   // read from the photo (the analysis used them too)
      dice = data.dice_read;
      setDice(dice, true);
    }
    if (!cubeByHand && data.cube_read) setCube(BgCube.fromRead(data.cube_read), true);   // used by the analysis too
    if (data.analysis) setOnRoll(data.analysis.on_roll);
    const rec = data.recognized;
    state.warnings = data.warnings || [];
    const g = data.geometry;
    state.geometry = g && { ...g, corners: g.corners.map(([x, y]) => [x / scale, y / scale]),
                            bitmap: state.bitmap, from: JSON.stringify(state.corners) };
    state.board = { points: rec.points, bar_white: rec.bar_white, bar_black: rec.bar_black };
    state.read = { points: rec.points.slice(), bar_white: rec.bar_white, bar_black: rec.bar_black };
    state.home = data.home || (state.homePick === "auto" ? "right" : state.homePick);
    state.homeGuess = data.home_guess || null;
    state.selected = null;
    saveHistory();
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

// The photo of the playing area (TL TR BR BL corners) warped onto the drawn one, made once per photo and corners.
const PLAY = { x: B.x0, y: B.y0, w: 12 * B.pw + B.bar, h: B.y1 - B.y0 };
function rectifiedPhoto() {
  if (!state.fromPhoto || !state.bitmap || state.corners.length !== 4 || !window.BgPhoto) return null;
  // The recognizer's refined corners and columns line the photo up best; they hold for the photo and corners they came from.
  const g0 = state.geometry;
  const g = g0 && g0.bitmap === state.bitmap && g0.from === JSON.stringify(state.corners) ? g0 : null;
  const key = JSON.stringify([state.corners, g && g.corners]);
  const r = state.rectified;
  if (r && r.bitmap === state.bitmap && r.key === key) return r.url;
  let url = null;
  try {
    url = BgPhoto.rectify(state.bitmap, g ? g.corners : state.corners, PLAY.w * 2, PLAY.h * 2, g && columnAnchors(g, 2));
  } catch (err) {
    console.warn("could not show the photo:", err);
  }
  state.rectified = { bitmap: state.bitmap, key, url };
  return url;
}

// [[x on the drawn playing area * zoom, fraction of the photo's width], ...] through the bar edges and
// the 12 column centres, or just the bar edges if the columns are out of order.
function columnAnchors(g, zoom) {
  const half = 6 * B.pw;
  const bar = [[half * zoom, g.bar[0]], [(half + B.bar) * zoom, g.bar[1]]];
  const cols = (g.columns || []).map((f, c) => [(colX(c) - B.x0) * zoom, f]);
  const ends = (mid) => [[0, 0], ...mid, [PLAY.w * zoom, 1]];
  const increasing = (a) => a.every((p, k) => k === 0 || p[1] > a[k - 1][1]);
  const full = ends([...cols.slice(0, 6), ...bar, ...cols.slice(6)]);
  if (cols.length === 12 && increasing(full)) return full;
  const plain = ends(bar);
  return increasing(plain) ? plain : null;
}

function drawBoard() {
  const photo = rectifiedPhoto();
  const view = photo ? state.photoView : "off";
  $("photo-tools").hidden = !photo;
  $("photo-wrap").hidden = view !== "side";
  $("boards").classList.toggle("two", view === "side");
  if (view === "side") drawBoardOn($("photo-svg"), { photo, checkers: false });
  drawBoardOn($("board-svg"), { photo: null, checkers: true });
  drawBoardOn($("result-svg"), { photo: null, checkers: true });   // the result screen's copy (taps are off there)
  drawCounts();
  drawEditor();
}

// One board picture: the drawn board with the recognized checkers, or the photo with point numbers
// (opts.photo, no checkers). Both pictures share the layout, so a tap selects the same point on either.
function drawBoardOn(svg, opts) {
  svg.textContent = "";
  const b = state.board;
  const xR = B.x0 + 12 * B.pw + B.bar;
  // The picture widens on the home side for the tray of borne-off checkers, and on the other side
  // for the doubling cube's place.
  const vx = -(state.home === "right" ? CUBE.extra : TRAY.extra), vw = 660 + TRAY.extra + CUBE.extra;
  svg.setAttribute("viewBox", `${vx} 0 ${vw} 440`);
  el("rect", { x: vx, y: 0, width: vw, height: 440, fill: "var(--card)" }, svg);
  const fx = Math.min(B.x0, trayX(), cubeX()) - 6, fr = Math.max(xR, trayX() + TRAY.w, cubeX() + CUBE.w) + 6;
  el("rect", { x: fx, y: B.y0 - 6, width: fr - fx, height: B.y1 - B.y0 + 12, rx: 6, fill: "var(--frame)" }, svg);
  el("rect", { x: trayX(), y: B.y0, width: TRAY.w, height: B.y1 - B.y0, fill: "var(--felt)" }, svg);
  if (opts.photo) {
    el("image", { href: opts.photo, x: PLAY.x, y: PLAY.y, width: PLAY.w, height: PLAY.h, preserveAspectRatio: "none" }, svg);
  } else {
    el("rect", { x: B.x0, y: B.y0, width: 6 * B.pw, height: B.y1 - B.y0, fill: "var(--felt)" }, svg);
    el("rect", { x: B.x0 + 6 * B.pw + B.bar, y: B.y0, width: 6 * B.pw, height: B.y1 - B.y0, fill: "var(--felt)" }, svg);
  }

  for (const top of [true, false]) {
    for (let c = 0; c < 12; c++) {
      const i = pointAt(top, c);
      const x = colX(c), h = B.pw / 2;
      const base = top ? B.y0 : B.y1, tip = top ? B.y0 + B.tri : B.y1 - B.tri;
      if (!opts.photo) el("polygon", { points: `${x - h},${base} ${x + h},${base} ${x},${tip}`, fill: c % 2 ? "var(--tri-b)" : "var(--tri-a)" }, svg);
      const lbl = el("text", { x, y: top ? 16 : 434, class: "num" }, svg);
      lbl.textContent = i + 1;
      const n = b.points[i];
      if (n && opts.checkers) drawStack(svg, x, top, Math.abs(n), n > 0 ? "white" : "black");
      if (state.selected === i) {
        el("rect", { x: x - h + 1, y: top ? B.y0 + 1 : B.y0 + (B.y1 - B.y0) / 2 + 1, width: B.pw - 2, height: (B.y1 - B.y0) / 2 - 2, fill: "none", stroke: "var(--sel)", "stroke-width": 3 }, svg);
      }
      const hit = el("rect", { x: x - h, y: top ? B.y0 : B.y0 + (B.y1 - B.y0) / 2, width: B.pw, height: (B.y1 - B.y0) / 2, fill: "transparent", class: "hit" }, svg);
      hit.addEventListener("click", () => select(i));
    }
  }

  // Bar: 奥's checkers in the upper half, 手前's in the lower half.
  const bx = B.x0 + 6 * B.pw + B.bar / 2;
  if (b.bar_black && opts.checkers) drawStack(svg, bx, true, b.bar_black, "black");
  if (b.bar_white && opts.checkers) drawStack(svg, bx, false, b.bar_white, "white");
  if (!opts.photo) {
    const barLbl = el("text", { x: bx, y: (B.y0 + B.y1) / 2 + 5, class: "label" }, svg);
    barLbl.textContent = "バー";
  }
  if (state.selected === "bar") {
    el("rect", { x: bx - B.bar / 2 + 1, y: B.y0 + 1, width: B.bar - 2, height: B.y1 - B.y0 - 2, fill: "none", stroke: "var(--sel)", "stroke-width": 3 }, svg);
  }
  const barHit = el("rect", { x: bx - B.bar / 2, y: B.y0, width: B.bar, height: B.y1 - B.y0, fill: "transparent", class: "hit" }, svg);
  barHit.addEventListener("click", () => select("bar"));
  if (opts.checkers) drawBorneOff(svg);
  if (opts.checkers) drawDice(svg);
  if (opts.checkers) drawCube(svg);
  if (opts.checkers) drawMoveArrows(svg);
}

// The tray of borne-off checkers, outside the frame on the home side as on a real board.
const TRAY = { w: 32, extra: 44 };
function trayX() {
  return state.home === "right" ? B.x0 + 12 * B.pw + B.bar + 12 : B.x0 - 12 - TRAY.w;
}

// Borne-off checkers as thin slabs on their side: 手前's from the bottom, 奥's from the top, with the count.
function drawBorneOff(svg) {
  const { offW, offB } = counts();
  const x = trayX() + 2, w = TRAY.w - 4, hgt = 9, step = 10;
  for (let [side, n] of [["white", offW], ["black", offB]]) {
    if (n <= 0) continue;
    const top = side === "black";
    n = Math.min(n, 15);
    for (let k = 0; k < n; k++) {
      const y = top ? B.y0 + 2 + k * step : B.y1 - 2 - hgt - k * step;
      el("rect", { x, y, width: w, height: hgt, rx: 2, fill: checkerFill(side), stroke: "#555", "stroke-width": 1, "pointer-events": "none" }, svg);
    }
    const t = el("text", { x: trayX() + TRAY.w / 2, y: top ? B.y0 + n * step + 12 : B.y1 - n * step - 12, class: "off-n", "pointer-events": "none" }, svg);
    t.textContent = n;
  }
}

// Column of point index i (0..23) and whether it is in the upper row: the inverse of pointAt.
function columnOf(i) {
  const top = i >= 12;
  if (state.home === "right") return { top, c: top ? i - 12 : 11 - i };
  return { top, c: top ? 23 - i : i };
}

// Centre of the checker at level k (0 = by the board's edge) of a stack, as drawStack places it.
function stackY(top, k) {
  k = Math.min(k, 4);
  return top ? B.y0 + B.r + 1 + k * B.step : B.y1 - B.r - 1 - k * B.step;
}

// Analysis inputs, to tell whether the result on screen still fits the board drawn.
function analysisKey(board, onRoll, dice) {
  return JSON.stringify([board.points, board.bar_white, board.bar_black, onRoll, dice, currentCube()]);
}

// The move picked in the result's list (the best one at first), as arrows on the board.
function drawMoveArrows(svg) {
  const r = state.result;
  if (!r || !r.moves || !r.moves.length || typeof BgMoves === "undefined") return;
  if (state.resultKey !== analysisKey(state.board, state.onRoll, currentDice())) return;   // board changed since
  const m = r.moves[state.moveShown] || r.moves[0];
  const hops = BgMoves.hops(state.board, r.on_roll, m.move);
  if (!hops) return;
  const bx = B.x0 + 6 * B.pw + B.bar / 2;
  const offX = trayX() + TRAY.w / 2;
  const g = el("g", { class: "arrows" }, svg);
  for (const h of hops) {
    let x0, y0;
    if (h.from === "bar") {
      const top = r.on_roll === "black";
      [x0, y0] = [bx, stackY(top, h.fromLevel)];
    } else {
      const { top, c } = columnOf(h.from);
      [x0, y0] = [colX(c), stackY(top, h.fromLevel)];
    }
    let x1, y1;
    if (h.to === "off") {
      [x1, y1] = [offX, y0];
    } else {
      const { top, c } = columnOf(h.to);
      [x1, y1] = [colX(c), stackY(top, h.toLevel)];
    }
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

// The dice entered below the board, where the side on roll throws them: in its own right-hand
// field (手前: the right one in the picture, 奥: the left one), in its checker colour.
const PIPS = { 1: [[0, 0]], 2: [[-1, -1], [1, 1]], 3: [[-1, -1], [0, 0], [1, 1]],
               4: [[-1, -1], [1, -1], [-1, 1], [1, 1]], 5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]],
               6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]] };
function drawDice(svg) {
  const dice = currentDice();
  if (!dice) return;
  const side = state.onRoll, size = 34;
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

// The doubling cube by the board's edge away from the trays (as it lies on a real board): half-way
// up showing 64 while nobody owns it, else at the end of the side it lies on.
const CUBE = { w: 32, extra: 44 };
function cubeX() {
  return state.home === "right" ? B.x0 - 12 - CUBE.w : B.x0 + 12 * B.pw + B.bar + 12;
}

function drawCube(svg) {
  const size = 30, x = cubeX() + (CUBE.w - size) / 2;
  const y = state.cubeAt === "centre" ? (B.y0 + B.y1) / 2 - size / 2 : state.cubeAt === "white" ? B.y1 - size - 2 : B.y0 + 2;
  const g = el("g", { class: "die" }, svg);
  el("rect", { x, y, width: size, height: size, rx: 5, fill: "#fafafa", stroke: "#0008", "stroke-width": 1.5 }, g);
  const t = el("text", { x: x + size / 2, y: y + size / 2 + 6, class: "cube-num" }, g);
  t.textContent = state.cubeAt === "centre" ? "64" : String(state.cubeValue);
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
  drawHomeNote();
}

// Which side the bottom player's home board was read on, and whether it was guessed.
function drawHomeNote() {
  const side = state.home === "right" ? "右" : "左";
  const g = state.fromPhoto && state.homeGuess;
  $("home-note").hidden = !state.fromPhoto;
  $("home-note").textContent = !g ? `手前の人のホームボードは${side}です。`
    : Math.abs(g.margin) < 1 ? `駒の並びからはホームボードの左右を決められなかったので、${side}にしています。逆なら「左右を入れ替える」を押してください。`
    : `駒の並びから、手前の人のホームボードを${side}と推測しました。逆なら「左右を入れ替える」を押してください。`;
}

function select(target) {
  state.selected = state.selected === target ? null : target;
  drawBoard();
}

function drawEditor() {
  const s = state.selected;
  $("editor-buttons").hidden = s === null;
  if (s === null) {
    $("editor-title").textContent = "違う所はポイントやバーをタップして直す（下が手前）";
    return;
  }
  const b = state.board;
  if (s === "bar") {
    $("editor-title").textContent = `バー: 手前 ${b.bar_white} 個、奥 ${b.bar_black} 個`;
  } else {
    const n = b.points[s];
    $("editor-title").textContent = `ポイント ${s + 1}: ` +
      (n === 0 ? "空" : `${n > 0 ? "手前" : "奥"}の駒 ${Math.abs(n)} 個`);
  }
}

$("editor-buttons").addEventListener("click", (e) => {
  const op = e.target.dataset && e.target.dataset.op;
  if (!op || state.selected === null) return;
  if (op === "close") { select(state.selected); return; }
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
  saveHistory();
}

// Swapping colours or sides changes the layout, so the recognizer's reading (state.read) follows.
function swapColours(b) {
  b.points = b.points.map((n) => -n);
  [b.bar_white, b.bar_black] = [b.bar_black, b.bar_white];
}

function mirror(b) {
  b.points = b.points.map((_, i) => b.points[i < 12 ? 11 - i : 35 - i]);
}

$("swap-colours").addEventListener("click", () => {
  swapColours(state.board);
  if (state.read) swapColours(state.read);
  state.bottomColour = 1 - state.bottomColour;
  syncColours();
  boardChanged();
});

// The board was read with the home on the wrong side: mirror it left to right.
$("flip-home").addEventListener("click", () => {
  mirror(state.board);
  if (state.read) mirror(state.read);
  state.home = state.home === "right" ? "left" : "right";
  state.homeGuess = null;
  state.selected = null;
  boardChanged();
});

$("reset-start").addEventListener("click", () => {
  if (!confirm("盤面を初期配置に戻しますか？")) return;
  state.board = { points: START.slice(), bar_white: 0, bar_black: 0 };
  state.selected = null;
  boardChanged();
});

// ---------------------------------------------------------------- analysis
for (const id of ["die1", "die2"]) {
  for (let d = 1; d <= 6; d++) $(id).add(new Option(String(d), String(d)));
  $(id).addEventListener("change", () => {
    if (state.result) $("result").classList.add("stale");
    $("dice-note").hidden = true;
    syncCube();
    if (state.board) drawBoard();
    saveHistory();
  });
}

// ---------------------------------------------------------------- the doubling cube (cube.js)
for (const v of BgCube.VALUES) $("cube-value").add(new Option(String(v), String(v)));

function currentCube() {
  return { at: state.cubeAt, value: state.cubeValue, offered: state.cubeOffered };
}

// cube: {at, value, offered}, or null for the middle. fromPhoto: read from the photo, so say so.
function setCube(cube, fromPhoto = false) {
  const c = cube || BgCube.fromRead(null);
  state.cubeAt = c.at;
  state.cubeValue = c.value;
  state.cubeOffered = c.offered;
  $("cube-note").hidden = !fromPhoto;
  syncCube();
  if (state.board) drawBoard();
}

// What the cube asks of the analysis, and the side on roll that follows from it.
function syncCube() {
  syncCubeAt();
  $("cube-side").hidden = state.cubeAt === "centre";
  $("cube-value").value = String(state.cubeValue);
  $("cube-offered").checked = state.cubeOffered;
  const req = BgCube.request(currentCube(), state.onRoll, currentDice());
  if (req.on_roll !== state.onRoll) setOnRoll(req.on_roll);
  const roll = NAME[req.on_roll];
  $("cube-help").textContent = currentDice()
    ? "ダイスがあるので、最善手を出します。"
    : req.doubled
      ? `${roll}の人が ${req.cube_value} にダブルしたところとして、${NAME[req.cube_owner]}の人がテイクかパスかを判定します。`
      : req.cube_owner && req.cube_owner !== req.on_roll
        ? `キューブは${NAME[req.cube_owner]}の人が持っているので、${roll}の人はダブルできません。`
        : `ダイスが無いので、${roll}の人がダブルすべきかを判定します。`;
}

function cubeChanged() {
  $("cube-note").hidden = true;
  syncCube();
  if (state.result) $("result").classList.add("stale");
  if (state.board) drawBoard();
  saveHistory();
}

$("cube-value").addEventListener("change", () => { state.cubeValue = Number($("cube-value").value); cubeChanged(); });
$("cube-offered").addEventListener("change", () => { state.cubeOffered = $("cube-offered").checked; cubeChanged(); });

function setOnRoll(side) {
  state.onRoll = side;
  syncOnRoll();
}

// fromPhoto: the dice were read from the photo, so say so (the user checks them)
function setDice(dice, fromPhoto = false) {
  $("die1").value = dice ? String(dice[0]) : "";
  $("die2").value = dice ? String(dice[1]) : "";
  $("dice-note").hidden = !fromPhoto;
  if (state.board) drawBoard();
}

function currentDice() {
  const a = $("die1").value, b = $("die2").value;
  return a && b ? [Number(a), Number(b)] : null;
}

$("analyze").addEventListener("click", async () => {
  const errs = boardErrors();
  if (errs.length) { alert(errs.join("\n")); return; }
  if (state.selected !== null) select(state.selected);   // done editing
  sendSample();
  // The result on hand still fits the board and settings (e.g. worked out when the photo was read): just show it.
  if (state.result && !$("result").classList.contains("stale") &&
      state.resultKey === analysisKey(state.board, state.onRoll, currentDice())) {
    show("outcome");
    return;
  }
  busy(analysingText());
  try {
    const dice = currentDice();
    const body = { board: { ...state.board }, plies: Number(state.plies),
                   ...BgCube.request(currentCube(), state.onRoll, dice) };
    if (dice) body.dice = dice;
    const r = await post("analyze", JSON.stringify(body), { "content-type": "application/json" });
    setResult(r, dice);
    show("outcome");
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
  state.resultKey = r ? analysisKey(state.board, state.onRoll, dice || null) : null;   // the board it was worked out for
  state.moveShown = 0;
  if (state.board) drawBoard();   // the best move's arrows, or none
  const box = $("result");
  box.classList.remove("stale");
  box.hidden = !r;
  state.speech = r ? speechText(r, dice) : null;
  syncHeaderActions();
  if (!r) return;
  const pips = r.pips;
  const pipLine = pips.leader
    ? `${NAME[pips.leader]}が ${pips.difference} ピップ リード`
    : "ピップは同じ";
  stopSpeaking();
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
  html += r.cube ? cubeHtml(r.cube) : `<p>${pipLine}。次に振るのは${NAME[r.on_roll]}の人。</p>`;
  if (r.cube) html += `<p>${pipLine}。</p>`;
  if (r.moves) {
    html += `<h2>最善手（${NAME[r.on_roll]}・ダイス ${dice ? dice.join("-") : ""}）</h2>`;
    html += r.moves.length
      ? `<ol class="moves">${r.moves.map((m, k) => `<li data-k="${k}"${k ? "" : ' class="on"'}>${esc(m.move)}<span>エクイティ ${m.equity.toFixed(3)}</span></li>`).join("")}</ol>` +
        `<p class="note">番号は${NAME[r.on_roll]}の人から見たポイント番号です。盤面図の矢印は選んだ手です（行をタップで切り替え）。</p>`
      : "<p>動かせる手がありません。</p>";
  }
  html += `<p class="note">gnubg ${r.plies}手読み。勝率とエクイティはキューブなし${r.cube ? "、キューブの判断はマネーゲーム（ジャコビー・ルールあり）" : ""}。` +
    `Position ID: <code>${esc(r.position_id)}</code></p>`;
  box.innerHTML = html;
  const list = box.querySelector(".moves");
  if (list) list.addEventListener("click", (e) => showMove(list, e.target.closest("li")));
}

// The cube decision: the answer first, then gnubg's cubeful equities (the doubler's, per cube before the double).
function cubeHtml(c) {
  const d = NAME[c.doubler], t = NAME[c.taker];
  const word = c.value > 1 ? "リダブル" : "ダブル";
  const take = c.take ? "テイク" : "パス";
  let html = "<h2>キューブ</h2>";
  if (c.question === "take") {
    html += `<p class="answer">${t}の人は <b>${take}</b></p>`;
    html += `<p>${d}の人の${word}は${c.double ? "正しい" : c.too_good ? "ダブルせずギャモンを狙う方がよい局面" : "早すぎる"}。</p>`;
  } else {
    html += `<p class="answer">${d}の人は <b>${c.double ? `${word}する` : c.too_good ? `${word}しない（ギャモン狙い）` : `${word}しない`}</b></p>`;
    html += `<p>${word}されたら、${t}の人は${take}。</p>`;
  }
  const e = c.equity;
  const row = (name, v) => `<tr><td>${name}</td><td>${v >= 0 ? "+" : ""}${v.toFixed(3)}</td></tr>`;
  html += `<table><tr><th>${d}の人から見て</th><th>エクイティ</th></tr>` +
    row(`${word}しない`, e.no_double) + row(`${word}・テイク`, e.double_take) + row(`${word}・パス`, e.double_pass) +
    `</table><p class="note">gnubg の判断: ${esc(c.proper)}</p>`;
  return html;
}

// A row of the best moves was tapped: show that move's arrows on the board.
function showMove(list, li) {
  if (!li) return;
  state.moveShown = Number(li.dataset.k);
  for (const x of list.children) x.classList.toggle("on", x === li);
  drawBoard();
  $("result-svg").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ---------------------------------------------------------------- reading the result aloud
// The browser's own speech (Web Speech API): free, nothing to set up, and on Android's Chrome
// it is Google's voice. Nothing is sent to our server.
// A short spoken summary, not the numbers: the screen keeps the percentages and pips.
function speechText(r, dice) {
  const parts = [];
  const bestMove = r.moves && dice;   // read first: it is what the player wants to hear
  if (bestMove) {
    const who = `${NAME[r.on_roll]}の人、ダイス ${dice[0]} ${dice[1]}`;
    parts.push(r.moves.length
      ? `${who}の最善手は、${moveToSpeech(r.moves[0].move)}。`
      : `${who}では動かせる手がありません。`);
  }
  if (r.cube) {
    const c = r.cube, word = c.value > 1 ? "リダブル" : "ダブル", take = c.take ? "テイク" : "パス";
    parts.push(c.question === "take"
      ? `${NAME[c.taker]}の人は${take}です。`
      : c.double ? `${NAME[c.doubler]}の人は${word}、${NAME[c.doubler === "white" ? "black" : "white"]}の人は${take}です。`
        : `${NAME[c.doubler]}の人はまだ${word}しません。`);
  }
  if (r.game_over) {
    parts.push(`${NAME[r.favourite]}の勝ちで終局しています。`);
  } else {
    parts.push(standingToSpeech(r));
  }
  if (!bestMove) parts.push(`次に振るのは${NAME[r.on_roll]}の人です。`);
  return parts.join("");
}

// The favourite's winning chance in words; a gammon or a big race lead only when it matters.
function standingToSpeech(r) {
  const fav = r.favourite, p = r.probabilities[fav], pips = r.pips;
  const w = p.win;
  let s = w >= 90 ? `${NAME[fav]}がほぼ勝ちの局面です。`
    : w >= 75 ? `${NAME[fav]}がかなり有利です。`
      : w >= 60 ? `${NAME[fav]}が有利です。`
        : w >= 53 ? `${NAME[fav]}がやや有利です。`
          : "ほぼ互角です。";
  if (w >= 53 && p.gammon >= 25) s += "ギャモン勝ちも十分ありえます。";
  if (pips.leader && pips.difference >= 20) s += `レースは${NAME[pips.leader]}が大きくリードしています。`;
  return s;
}

// "bar/22* 13/8(2) 6/off" -> "バーから22でヒット、13から8を2つ、6から上がり"
function moveToSpeech(move) {
  return move.trim().split(/\s+/).map((step) => {
    const m = step.match(/^(.*?)(?:\((\d+)\))?$/);
    const pts = m[1].split("/").map((x) => {
      const hit = x.endsWith("*");
      const n = x.replace("*", "").toLowerCase();
      return (n === "bar" ? "バー" : n === "off" ? "上がり" : n) + (hit ? "でヒット" : "");
    });
    return pts.join("から") + (m[2] ? `を${m[2]}つ` : "");
  }).join("、");
}

function japaneseVoice() {
  const voices = window.speechSynthesis.getVoices().filter((v) => /^ja/i.test(v.lang));
  return voices.find((v) => /google/i.test(v.name)) || voices[0] || null;
}

function stopSpeaking() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
}

function toggleSpeaking(text) {
  const synth = window.speechSynthesis;
  if (synth.speaking) { synth.cancel(); return; }
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "ja-JP";
  const voice = japaneseVoice();
  if (voice) u.voice = voice;
  const label = (on) => {
    const btn = $("speak");
    btn.textContent = on ? "■" : "🔊";
    btn.classList.toggle("on", on);
    btn.setAttribute("aria-pressed", on);
  };
  u.onstart = () => label(true);
  u.onend = u.onerror = () => label(false);
  synth.speak(u);
}
if (window.speechSynthesis) window.speechSynthesis.getVoices();   // Chrome loads the voice list lazily

$("to-board").addEventListener("click", () => show("board"));

// ---------------------------------------------------------------- recent photos (history.js)
// Stored on this device only. Failures (no IndexedDB, private mode, storage full) never block the app.
async function addToHistory(file) {
  state.historyId = null;
  state.historyScale = 1;
  try {
    const [w, h] = imgSize();
    const { id, scale } = await PhotoHistory.add(file, state.bitmap, w, h);
    state.historyId = id;
    state.historyScale = scale;
  } catch (_) { /* not stored */ }
}

function saveHistory() {
  if (!state.historyId) return;
  const s = state.historyScale;
  PhotoHistory.update(state.historyId, {
    corners: state.corners.map(([x, y]) => [x * s, y * s]),
    cornerGuess: state.cornerGuess,
    cornersMoved: state.cornersMoved,
    homePick: state.homePick,
    home: state.home,
    homeGuess: state.homeGuess,
    bottomColour: state.bottomColour,
    onRoll: state.onRoll,
    dice: currentDice(),
    cube: currentCube(),
    board: state.board,
    read: state.read,
    warnings: state.warnings,
  }).catch(() => {});
}

async function openHistory(id) {
  busy("写真を読み込んでいます…");
  try {
    const e = await PhotoHistory.get(id);
    if (!e) { renderHistory(); return; }
    state.bitmap = await decode(e.image);
    state.file = e.image;
    state.historyId = id;
    state.historyScale = 1;   // the stored copy is now the image
    // corners still being guessed when the photo was left, or never set, are guessed again
    const guess = !e.corners || e.corners.length < 4 || e.cornerGuess === "finding";
    state.corners = guess ? defaultCorners() : e.corners.map((c) => c.slice());
    state.cornerGuess = guess ? "finding" : e.cornerGuess || "";
    state.cornersMoved = !!e.cornersMoved;
    state.homePick = e.homePick || e.home || "auto";   // entries from before 0.6.0 kept only the side picked
    state.home = e.home || "right";
    state.homeGuess = e.homeGuess || null;
    state.bottomColour = e.bottomColour ?? 1;
    state.onRoll = e.onRoll || "white";
    state.fromPhoto = true;
    state.warnings = e.warnings || [];
    state.board = e.board || null;
    state.read = e.read || null;
    state.selected = null;
    setDice(e.dice);
    setCube(e.cube || null);
    syncHomePick();
    syncColours();
    syncOnRoll();
    setResult(null);
    updateCornerUi();
    saveHistory();   // now the most recent
    show("corners");   // from before reading the board; the board read before is one button away
    if (guess) guessCorners(e.image);
  } catch (err) {
    alert("写真を開けませんでした: " + err.message);
  } finally {
    busy();
  }
}

let thumbUrls = [];
async function renderHistory() {
  let entries = [];
  try { entries = await PhotoHistory.list(); } catch (_) { /* no IndexedDB */ }
  thumbUrls.forEach((u) => URL.revokeObjectURL(u));
  thumbUrls = [];
  const ul = $("history-list");
  ul.textContent = "";
  $("history").hidden = !entries.length;
  for (const e of entries) {
    const li = document.createElement("li");
    const open = document.createElement("button");
    open.className = "open";
    const img = document.createElement("img");
    img.alt = "";
    img.src = URL.createObjectURL(e.thumb);
    thumbUrls.push(img.src);
    const text = document.createElement("span");
    const when = new Date(e.time).toLocaleString("ja-JP", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
    const done = e.board ? "盤面の読み取りまで" : e.cornersMoved ? "四隅を合わせたところまで" : "写真を選んだところまで";
    text.innerHTML = `${esc(when)}<span class="sub">${done}</span>`;
    open.append(img, text);
    open.addEventListener("click", () => openHistory(e.id));
    const del = document.createElement("button");
    del.className = "button del";
    del.textContent = "✕";
    del.setAttribute("aria-label", "この写真を履歴から消す");
    del.addEventListener("click", async () => {
      if (!confirm("この写真を履歴から消しますか？")) return;
      if (state.historyId === e.id) state.historyId = null;
      try { await PhotoHistory.remove(e.id); } catch (_) { /* already gone */ }
      renderHistory();
    });
    li.append(open, del);
    ul.append(li);
  }
}

// ---------------------------------------------------------------- a sample for the recognizer (sample.js)
// The photo and the board as fixed by hand, as two files (photo + truth.json) to send to the
// developers so the recognizer can be measured and improved on them; with 「Pi に残す」 on, the
// same pair goes to the server each time the board is analysed (POST /samples).
async function sampleOf(name) {
  // the stored copy (the size the app sends anyway) with the corners in its pixels, else the photo itself
  const e = state.historyId && await PhotoHistory.get(state.historyId).catch(() => null);
  const blob = (e && e.image) || state.file;
  const s = e && e.image ? state.historyScale : 1;
  const ext = blob.type === "image/png" ? "png" : "jpg";
  const truth = BgSample.truth({
    image: `${name}.${ext}`,
    corners: state.corners.map(([x, y]) => [x * s, y * s]),
    home: state.home, bottomColour: state.bottomColour, board: state.board,
    dice: currentDice(), cube: currentCube(), read: state.read,
  });
  return { blob, ext, truth };
}

// Keep this photo and its board on the server, when the user has turned that on. Never in the way.
async function sendSample() {
  if (state.collect !== "on" || !state.fromPhoto || !state.board || !state.historyId) return;
  try {
    const { blob, ext, truth } = await sampleOf(`user-${state.historyId}`);
    const fd = new FormData();
    fd.append("id", state.historyId);
    fd.append("truth", JSON.stringify(truth));
    fd.append("image", blob, `${state.historyId}.${ext}`);
    await post("samples", fd);
  } catch (_) { /* not kept this time */ }
}

$("export-sample").addEventListener("click", async () => {
  try {
    const name = BgSample.baseName(new Date());
    const { blob, ext, truth } = await sampleOf(name);
    const files = [
      new File([blob], `${name}.${ext}`, { type: blob.type || "image/jpeg" }),
      new File([JSON.stringify(truth) + "\n"], `${name}.truth.json`, { type: "application/json" }),
    ];
    if (navigator.canShare && navigator.canShare({ files })) {
      try {
        await navigator.share({ files, title: "BG Analyzer のサンプル" });
      } catch (err) {
        if (err.name !== "AbortError") throw err;
      }
      return;
    }
    for (const f of files) {   // no share sheet (a PC): download both
      const a = document.createElement("a");
      a.href = URL.createObjectURL(f);
      a.download = f.name;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 10000);
    }
  } catch (err) {
    alert("書き出せませんでした: " + err.message);
  }
});

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

const syncHomePick = initSeg("homePick");
const syncBottomColour = initSeg("bottomColour", syncColours);
// A cube just offered lies on the side of the player doubled, so the other one is on roll.
function cubeFollowsTurn() {
  if (BgCube.request(currentCube(), state.onRoll, currentDice()).doubled) {
    state.cubeAt = state.onRoll === "white" ? "black" : "white";
    syncCube();
  }
}
const syncOnRoll = initSeg("onRoll", () => {
  cubeFollowsTurn();
  if (state.result) $("result").classList.add("stale");
  if (state.board) drawBoard();   // the dice move to the other side
});
const syncCubeAt = initSeg("cubeAt", cubeChanged);
// The other side to roll; with a result on screen, analyse again for the new side at once.
$("flip-turn").addEventListener("click", () => {
  state.onRoll = state.onRoll === "white" ? "black" : "white";
  syncOnRoll();
  cubeFollowsTurn();
  if (state.board) drawBoard();
  saveHistory();
  if (state.result) $("analyze").click();
});
initSeg("photoView", drawBoard);
initSeg("collect", () => {
  try { localStorage.setItem("collect", state.collect); } catch (_) { /* private mode */ }
});
initSeg("plies", () => {
  try { localStorage.setItem("plies", state.plies); } catch (_) { /* private mode */ }
  if (state.result) $("result").classList.add("stale");
});
syncColours();
syncCube();
updateCornerUi();
show("photo");

// Versions, to tell which build is running (e.g. on the Raspberry Pi): small in the header, in full in the footer.
$("hdr-version").textContent = `v${APP_VERSION}`;
fetch(API ? `${API}/version` : "version")
  .then((res) => (res.ok ? res.json() : null))
  .then((v) => {
    if (!v) return;
    const old = v.analyzer !== APP_VERSION;   // an old app.js still cached on this device
    $("hdr-version").textContent = `v${APP_VERSION} · r${v.recognizer}` + (old ? `（新しい ${v.analyzer} は開き直すと出ます）` : "");
    $("hdr-version").classList.toggle("old", old);
    $("collect-opt").hidden = $("collect-note").hidden = !v.samples;
    $("version").textContent = `analyzer ${v.analyzer} · recognizer ${v.recognizer}` +
      (v.commit ? ` · ${v.commit}` : "") +
      (v.analyzer !== APP_VERSION ? `（画面は ${APP_VERSION}。開き直すと新しくなります）` : "");
  })
  .catch(() => {});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}

loadSharedPhoto();
