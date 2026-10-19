// BG Analyzer PWA: photo -> 4 corners -> recognized board (editable) -> gnubg analysis.
// Colours follow the server: white = the player at the bottom of the photo (手前), black = 奥.
//
// How it fits together: everything the screens show is in `state`. Nothing changes it but
// update(patch), which then runs render(): each part of the page is redrawn from the state when
// what it shows has changed. Event handlers and the flows (reading a photo, analysing) only
// update the state; they never touch the page themselves. The photo history follows the state too.
//
// The other files draw or compute, and know nothing of the state: board.js (the board as data),
// board-view.js (its picture), corners-view.js (the photo with its corners), result.js (the
// result in words), cube.js, moves.js, photo.js, scan.js, history.js, sample.js, api.js.
"use strict";

const APP_VERSION = "0.85.0";   // = __version__ in analyzer/app.py; tells an old cached app.js apart
const UPLOAD_MAX = 2048;      // longest side sent to the server (recognition was checked at this size)
const SEND_AS_IS_MAX = 2560;  // smaller images (screenshots) are sent untouched
const NAME = BgResult.NAME;
const CORNER_NAMES = ["左上", "右上", "右下", "左下"];
const STEPS = ["photo", "corners", "board", "outcome"];
const STEP_TITLES = { photo: "写真の選択", corners: "四隅の調整", board: "盤面の確認/修正", outcome: "解析結果" };
const SHARE_CACHE = "bganalyzer-share";   // same names as in sw.js
const SHARE_KEY = "shared-photo";

const $ = (id) => document.getElementById(id);
const stored = (key, allowed, fallback) => {
  try { const v = localStorage.getItem(key); return allowed.includes(v) ? v : fallback; } catch (_) { return fallback; }
};
const keep = (key, value) => { try { localStorage.setItem(key, value); } catch (_) { /* private mode */ } };
// taken from beside the board (TODO-120): the way this phone last chose, for a new photo
const storedSide = () => ({ sideMode: stored("sideMode", ["on", "off"], "off") === "on",
                            sideFrom: stored("sideFrom", ["right", "left"], "") });
const storedMatch = () => {
  try { return BgCube.fixMatch(JSON.parse(localStorage.getItem("match"))); } catch (_) { return BgCube.fixMatch(null); }
};

// ================================================================ state

const state = {
  step: "photo",
  busy: null,          // {text, scanning, cancel} while waiting for the server (cancel: an AbortController)
  // the photo and where the board is in it
  photo: null,         // {file, bitmap, trimmed}: the chosen photo (EXIF orientation applied); trimmed: cut to the board by the user
  fromPhoto: false,    // the board comes from a photo (else it was set up by hand)
  corners: [],         // [[x, y], ...] in image px, TL TR BR BL
  cornerGuess: "",     // where the corners came from: "finding", "again" (looking again), "found", "default" (a rectangle), "missed", "moved" or "" (tapped)
  cornersMoved: false,
  cornersFixed: [false, false, false, false],   // each corner the user has dragged or tapped in: kept when looking again
  keepCorners: false,  // read with the corners as they are, not fitted to the frame (TODO-084); on once a corner is moved by hand
  // taken from beside the board (TODO-120): the corners are looked for and the board read that way. Kept with
  // each photo; a new photo starts the way this phone last chose (storedSide)
  sideMode: storedSide().sideMode,
  sideFrom: storedSide().sideFrom,   // from the near player's right or left; "" until asked
  edit: null,          // while the photo is being edited (TODO-070): {turn (quarter turns clockwise), angle (degrees, -45..45), rect ([x0, y0, x1, y1] as fractions of the turned photo) or null}
  dragging: false,     // a finger is on the corners
  homePick: "auto",    // the home sent with the photo: "auto" (guess from the checkers) for a new one; "left"/"right" once a tray is tapped (TODO-113), or as kept with a photo picked before
  bottomColour: Number(stored("bottomColour", ["0", "1"], "1")),   // 0 = the darker checkers are 手前's, 1 = the lighter ones (kept on this phone, TODO-113)
  geometry: null,      // where the recognizer found the board: {corners (image px), columns, bar (fractions), photo, from}
  // the board
  board: null,         // {points[24], bar_white, bar_black} (board.js)
  read: null,          // the board as the recognizer read it, before fixes by hand
  home: "right",       // the side 手前's home board is on, as read and drawn
  homeGuess: null,     // how the server guessed home (homePick "auto"): {margin}; null once flipped by hand
  warnings: [],        // the server's notes on the photo (e.g. taken at a steep angle)
  selected: null,      // point index 0..23 or "bar" whose palette is open
  palette: null,       // the palette of colours and counts beside the finger: {at, side, x, y (screen px)}
  paintSide: "white",  // the colour a tap puts on an empty point: the one last put
  undo: [],            // the boards before the latest fixes by hand, the newest last
  // what the analysis is asked
  onRoll: "white",
  dice: [0, 0],        // each 1..6, or 0 while not set
  diceFromPhoto: false,
  cube: BgCube.fromRead(null),   // {at: "centre" | "white" | "black", value, offered} (cube.js)
  cubeFromPhoto: false,
  plies: stored("plies", ["2", "3"], "2"),           // how deep gnubg reads (kept on this phone)
  match: storedMatch(),   // {length (0: money game), white, black, crawford} (cube.js; kept on this phone)
  // the answer
  result: null,        // what /analyze returned
  resultFor: null,     // inputsKey() of what it was worked out for
  resultDice: null,
  sheet: null,         // the settings open beside the part tapped (TODO-113, TODO-150): "match", "cube", "roll" or null
  reanalyzing: false,  // the board fixed on the result screen is being analysed again (TODO-138)
  moveShown: 0,        // the move in the result's list drawn as arrows
  // settings
  photoView: "side",   // the photo on the board screen: "side" (next to the board) or "off"
  autoSpeak: stored("autoSpeak", ["on", "off"], "off") === "on",   // read the result aloud once analysed (kept on this phone, TODO-115)
  collect: stored("collect", ["on", "off"], "on"),   // "on": keep the photo and the fixed board on the server (on unless turned off, TODO-112)
  // where the photo is kept on this phone (history.js)
  historyId: null,
  historyScale: 1,     // image px -> the stored copy's px
};

// Both dice as entered, or null while one is not set.
const diceIn = (s = state) => (s.dice[0] && s.dice[1] ? s.dice.slice() : null);
// A cube just offered (on one side, "ダブルされたところ"): nobody has rolled yet, so dice left in do not count (TODO-086).
const cubeOffered = (s = state) => BgCube.offered(s.cube);
// The dice the analysis uses: both dice, or null while one is not set or the cube is being offered.
const rolled = (s = state) => BgCube.usedDice(s.cube, diceIn(s));
// One die set, the other not: waited on (a double offered uses no dice, so none are half set then)
const halfDie = (s = state) => !cubeOffered(s) && !s.dice[0] !== !s.dice[1];

// What an analysis is worked out from (but its depth): a result fits the board while this is the same.
// (bottomColour: the server's summary names the sides by it)
const inputsKey = (s = state) =>
  s.board && JSON.stringify([s.board.points, s.board.bar_white, s.board.bar_black, s.onRoll, rolled(s), s.cube, s.match, s.bottomColour]);
const resultFits = (s = state) => !!s.result && s.resultFor === inputsKey(s);
const resultStale = (s = state) => !!s.result && (!resultFits(s) || String(s.result.plies) !== s.plies);

function update(patch) {
  // a board from elsewhere (a photo read, a flip): the fixes before it can't be taken back
  if ("board" in patch && !("undo" in patch)) patch = { ...patch, undo: [] };
  if ("step" in patch && patch.step !== state.step) patch = { palette: null, selected: null, edit: null, ...patch };
  Object.assign(state, patch);
  // The cube decides who is on roll: a cube just offered waits on the other side's answer.
  const req = BgCube.request(state.cube, state.onRoll, rolled());
  if (req.on_roll !== state.onRoll) state.onRoll = req.on_roll;
  render();
  persist();
}

// ================================================================ render

// A part of the page: draw(state) runs when key(state) has changed since it last ran.
// key returns undefined to leave the part as it is for now.
const parts = [];
function part(key, draw) { parts.push({ key, draw, last: {} }); }

function render() {
  for (const p of parts) {
    const k = p.key(state);
    if (k === undefined) continue;
    const ks = JSON.stringify(k);
    if (ks === p.last) continue;
    p.last = ks;
    p.draw(state);
  }
}

// Draws a part again even though its inputs look the same (the window was resized).
function redraw(drawFn) { for (const p of parts) if (p.draw === drawFn) p.last = {}; render(); }

// ---- the screen and the header
part((s) => s.step, (s) => {
  const at = STEPS.indexOf(s.step);
  for (const sec of document.querySelectorAll("section.step")) sec.hidden = sec.id !== s.step;
  $(s.step === "corners" ? "corners-match" : "board-match").appendChild($("match"));   // the same inputs on both screens (TODO-093)
  // the board with its edit buttons and the sheets its parts open: on the result screen too, to fix it there (TODO-138)
  const out = s.step === "outcome";
  $(out ? "outcome-board" : "boards").appendChild($("board-pin"));
  for (const k of ["match", "cube", "roll"]) $(out ? "outcome" : "board").appendChild($(`sheet-${k}`));
  for (const sp of document.querySelectorAll("#steps span")) {
    sp.classList.toggle("on", sp.dataset.step === s.step);
    sp.classList.toggle("done", STEPS.indexOf(sp.dataset.step) < at);
  }
  $("back").hidden = s.step === "photo";
  $("title").textContent = STEP_TITLES[s.step];
});

// The bottom bar carries the screen's main action (and reading aloud once there is a result), so it
// can be pressed without scrolling down (TODO-086).
part((s) => [s.step, s.fromPhoto && !!s.board, !!s.result, s.autoSpeak], (s) => {
  $("recognize").hidden = s.step !== "corners";
  $("hdr-reuse").hidden = !(s.step === "corners" && s.fromPhoto && s.board);
  $("analyze").hidden = s.step !== "board";
  $("auto-speak-opt").hidden = s.step !== "board";
  $("auto-speak").checked = s.autoSpeak;
  $("speak").hidden = !(s.step === "outcome" && s.result);
});

// No doubling in the Crawford game: the server refuses a cube on one side then (TODO-066).
const crawfordCube = (s = state) => s.match.crawford && s.cube.at !== "centre";
const CRAWFORD_CUBE = "クロフォードのゲームではダブルできません。キューブを「中央」にするか、「ゲーム」のクロフォードを外してください。";

// What stops the board from being analysed: 「解析する」 is greyed out, with the reasons above it (TODO-116).
const analyzeErrors = (s = state) =>
  s.board ? [...BgBoard.errors(s.board, NAME), ...(crawfordCube(s) ? [CRAWFORD_CUBE] : [])] : [];

// scanning: the reading overlay is drawn on the photo, so the screen is not darkened and the text sits low
part((s) => s.busy, (s) => {
  $("busy").hidden = !s.busy;
  $("busy").classList.toggle("scanning", !!(s.busy && s.busy.scanning));
  $("busy-text").textContent = s.busy ? s.busy.text : "";
  $("busy-cancel").hidden = !(s.busy && s.busy.cancel);
});

// ---- segmented buttons: each shows the state of its name
part((s) => [s.onRoll, s.cube.at, s.collect, s.plies, s.sideFrom], (s) => {
  const value = { onRoll: s.onRoll, cubeAt: s.cube.at,
                  collect: s.collect, plies: s.plies, sideFrom: s.sideFrom };
  for (const seg of document.querySelectorAll(".seg")) {
    for (const b of seg.children) b.classList.toggle("on", b.dataset.value === String(value[seg.dataset.name]));
  }
});

part((s) => s.bottomColour, (s) => {
  // the sides are named by their colour, the lighter 白 (TODO-086): here and in the result's words
  BgResult.setNames(s.bottomColour);
  for (const e of document.querySelectorAll(".nm-white")) e.textContent = NAME.white;
  for (const e of document.querySelectorAll(".nm-black")) e.textContent = NAME.black;
  const [w, b] = s.bottomColour ? ["light", "dark"] : ["dark", "light"];
  const root = document.documentElement.style;
  for (const k of ["chk", "fg", "rim"]) {
    root.setProperty(`--white-${k}`, `var(--${w}-${k})`);
    root.setProperty(`--black-${k}`, `var(--${b}-${k})`);
  }
});

// ---- the corners screen
const cornersView = BgCornersView.create($("photo-canvas"), {
  photo: () => (state.edit ? editPreview() : state.photo && state.photo.bitmap),
  corners: () => (state.edit ? [] : state.corners),
  onTouch: () => stopOverlay("corners"),   // a tap while the search is shown: on to the corners as they are
  onChange: (corners, done, index) => update({ corners, cornersMoved: true, dragging: !done, keepCorners: true,
                                                cornersFixed: state.cornersFixed.map((f, k) => f || k === index) }),
  trimming: () => !!state.edit,
  trimmed: () => {
    const r = state.edit && state.edit.rect, c = r && editPreview();
    return r && [r[0] * c.width, r[1] * c.height, r[2] * c.width, r[3] * c.height];
  },
  onTrim: ([x0, y0, x1, y1]) => {
    const c = editPreview();
    update({ edit: { ...state.edit, rect: [x0 / c.width, y0 / c.height, x1 / c.width, y1 / c.height] } });
  },
});

// The photo as being edited, small enough to turn at once as the slider moves.
let preview = null;   // {photo, small, key, canvas}
function editPreview() {
  const { bitmap } = state.photo, e = state.edit;
  if (!preview || preview.photo !== bitmap) {
    const [iw, ih] = imageSize(bitmap);
    preview = { photo: bitmap, small: scaledCanvas(bitmap, Math.min(1, 1280 / Math.max(iw, ih))) };
  }
  const key = e.turn * 90 + e.angle;
  if (preview.key !== key) Object.assign(preview, { key, canvas: BgPhoto.turn(preview.small, key, null) });
  return preview.canvas;
}

// Not while a finger is on the photo: the text may change height and move the photo under it.
part((s) => (s.dragging ? undefined : [s.corners.length, s.cornerGuess, !!s.edit]), (s) => {
  const n = s.corners.length;
  const fit = "点を動かして盤の内側の四隅に合わせてください。";
  const again = "盤が小さいときは下の「画像を編集」で切り抜いてください。";   // only when the board was not found (TODO-088)
  $("corner-help").innerHTML = s.edit
    ? "角度を直し、盤のまわりをドラッグして囲んでください。四角の角や辺をドラッグすると直せます。"
    : n < 4
    ? `枠の内側の四隅を、手前から見て <b>${n + 1}. ${CORNER_NAMES[n]}</b> の順にタップしてください。`
    : s.cornerGuess === "finding" || s.cornerGuess === "again" ? "盤の四隅を探しています…"
    : s.cornerGuess === "default" || s.cornerGuess === "missed" ? "盤を見つけられませんでした。" + fit + again
    : fit;
  $("recognize").disabled = n < 4 || !!s.edit;
});
part((s) => s.keepCorners, (s) => { $("keep-corners").checked = s.keepCorners; });
// taken from beside (TODO-120): which side is asked only until it is chosen; it can be chosen again
part((s) => [s.sideMode, s.sideFrom], (s) => {
  $("side-mode").checked = s.sideMode;
  $("side-from-row").hidden = !s.sideMode;
  $("side-ask").hidden = !!s.sideFrom;
});
part((s) => s.edit && s.edit.angle, (s) => {
  $("edit-tools").hidden = !s.edit;
  $("turn-tools").hidden = !!s.edit;
  $("corner-tools").hidden = !!s.edit;
  if (!s.edit) return;
  $("edit-angle").value = String(s.edit.angle);
  $("edit-angle-text").textContent = `${s.edit.angle}°`;
});

// The photo is left alone while scan.js draws on it.
const drawCorners = () => cornersView.draw();
part((s) => (s.step !== "corners" || scanning() ? undefined : [photoId(s), s.corners, s.dragging, s.edit]), drawCorners);

// ---- the board screen
part((s) => [s.board, s.fromPhoto, s.warnings, s.home, s.homeGuess, s.bottomColour], (s) => {
  if (!s.board) return;
  // The counts over the board, always (TODO-088, TODO-125): more than 15 in red, fewer read from a photo
  // (borne off, or missed) in yellow, with a ⚠ only then; no checkers at all counts as fewer.
  const { onW, onB } = BgBoard.counts(s.board);
  const cls = (on) => (on > 15 ? "many" : s.fromPhoto && on < 15 ? "few" : "");
  const mark = !onW && !onB ? [["盤に駒がありません", "few"]]
    : [["white", onW], ["black", onB]].map(([side, on]) => [`${NAME[side]} ${on}/15`, cls(on)]);
  const warn = mark.some(([, c]) => c) ? "⚠ " : "";
  $("count-mark").hidden = false;
  $("count-mark").replaceChildren(...mark.map(([text, c], i) =>
    Object.assign(document.createElement("span"), { className: c, textContent: `${i ? "・" : warn}${text}` })));
  // the server's notes on the photo (e.g. taken at a steep angle)
  const warns = s.fromPhoto ? s.warnings : [];
  $("errors").hidden = !warns.length;
  $("errors").textContent = warns.join(" / ");
  // which side 手前's home board was read on, and whether it was guessed
  const side = s.home === "right" ? "右" : "左";
  const g = s.fromPhoto && s.homeGuess;
  const doubtful = !!g && Math.abs(g.margin) < 1;   // only then: the side is said under the board (TODO-086)
  $("home-note").hidden = !doubtful;
  $("home-note").textContent = doubtful ? `ホームの左右を決められず、${side}にしました。違えば盤面図の置き場をタップしてください。` : "";
});

// after the part above: it sets NAME from 手前's colour
part((s) => [s.step, s.board, s.match.crawford, s.cube.at, s.bottomColour], (s) => {
  const errs = s.step === "board" || s.step === "outcome" ? analyzeErrors(s) : [];
  $("analyze").disabled = !!errs.length;
  $("analyze-why").hidden = !errs.length;
  $("analyze-why").textContent = errs.join("\n");
});

// 読み取りの改善 (TODO-112): only for a board read from a photo; saving it on the server only where the
// server keeps them (/version's samples)
let serverKeepsSamples = false;
const drawImprove = (s) => {
  $("collect-opt").hidden = !(serverKeepsSamples && s.fromPhoto);
  $("export-opt").hidden = !s.fromPhoto;
};
part((s) => [s.fromPhoto], drawImprove);

part((s) => [s.undo.length], (s) => {
  $("undo").disabled = !s.undo.length;
});

// The palette: the colour, then the count, of the point (or the bar) held down.
part((s) => [s.palette, s.board, s.onRoll], (s) => {
  const p = s.palette, box = $("palette");
  box.hidden = !p || !s.board;
  if (box.hidden) return;
  const n = BgBoard.countOf(s.board, p.at, p.side);
  $("palette-title").textContent = p.at === "bar" ? "バー" : `ポイント ${BgBoard.number(p.at, s.onRoll)}`;
  for (const b of $("palette-side").children) b.classList.toggle("on", b.dataset.value === p.side);
  for (const b of $("palette-counts").children) b.classList.toggle("on", Number(b.dataset.n) === n);
  // beside the finger, off the point held: on the side with more room, inside the screen
  const w = box.offsetWidth, h = box.offsetHeight, gap = 28;
  const right = p.x < innerWidth / 2;
  const x = Math.max(8, Math.min(innerWidth - w - 8, right ? p.x + gap : p.x - gap - w));
  const y = Math.max(8, Math.min(innerHeight - h - 8, p.y - h / 2));
  box.style.left = `${x}px`;
  box.style.top = `${y}px`;
});

// The pictures of the board: on the board screen (with the photo beside it) and on the result screen.
part((s) => s.board && [s.step, s.board, s.home, s.selected, rolled(s), s.onRoll, s.cube, s.photoView, moveToShow(s),
                        photoId(s), s.corners, s.geometry && s.geometry.corners, s.match], (s) => {
  if (!s.board) return;
  const scene = { board: s.board, home: s.home, selected: s.selected, dice: rolled(s), onRoll: s.onRoll,
                  cube: s.cube, move: moveToShow(s), match: s.match };
  const photo = rectifiedPhoto(s);
  const side = !!photo && s.photoView === "side";
  $("photo-tools").hidden = !photo;
  $("photo-side").checked = s.photoView === "side";
  $("photo-wrap").hidden = !side;
  $("boards").classList.toggle("two", side);
  if (side) BgBoardView.draw($("photo-svg"), { ...scene, photo });   // for looking: taps do nothing (TODO-088)
  // the best move only on the result screen (TODO-092), where the same board is moved to (TODO-138)
  BgBoardView.draw($("board-svg"), { ...scene, move: s.step === "outcome" ? scene.move : null }, select, tapPart);
  placeSheet();   // the part its settings are open for may have moved (the cube to the other side)
});

// ---- a tap on a part around the board picture (TODO-113): the trays flip the home's side, a pip count
// swaps the checkers' owners (the board keeps its colours), the match, the cube and the dice open their sheet
// (the side and the colour are what this photo is read with again, and the colour also the next photo's)
function tapPart(kind) {
  if (kind === "home") {
    const home = state.home === "right" ? "left" : "right";
    setHome(home);
    update({ homePick: home });
  } else if (kind === "colour") {
    editBoard(BgBoard.swapColours);
    keep("bottomColour", state.bottomColour ? "0" : "1");
    update({ bottomColour: state.bottomColour ? 0 : 1 });
  } else update({ sheet: kind });
}
part((s) => [s.sheet, s.step], (s) => {
  for (const k of ["match", "cube", "roll"]) $(`sheet-${k}`).hidden = !((s.step === "board" || s.step === "outcome") && s.sheet === k);
  placeSheet();
});
// Above or below its part, on the side with more room, above the bottom bar, the part itself left in sight (TODO-150).
// Placed again whenever the part or the settings move or change size: a turn of the phone, a scroll, a choice that adds a row.
function placeSheet() {
  const box = state.sheet && $(`sheet-${state.sheet}`);
  const part = box && !box.hidden && document.querySelector(`#board-svg [data-part="${state.sheet}"]`);
  if (!part) return;
  const r = part.getBoundingClientRect(), w = box.offsetWidth, h = box.offsetHeight, gap = 8;
  const bottom = innerHeight - $("actbar").offsetHeight;
  const below = bottom - r.bottom > r.top;
  box.style.left = `${Math.max(8, Math.min(innerWidth - w - 8, (r.left + r.right) / 2 - w / 2))}px`;
  box.style.top = `${Math.max(8, Math.min(bottom - h - 8, below ? r.bottom + gap : r.top - gap - h))}px`;
  // too tall for the screen (a phone on its side): it scrolls itself, else a swipe on it does nothing (TODO-144)
  box.style.touchAction = box.scrollHeight > box.clientHeight ? "pan-y pinch-zoom" : "";
}
addEventListener("resize", placeSheet);
addEventListener("scroll", placeSheet, { passive: true });
const sheetSize = new ResizeObserver(placeSheet);
for (const k of ["match", "cube", "roll"]) sheetSize.observe($(`sheet-${k}`));
for (const b of document.querySelectorAll(".sheet-close")) b.addEventListener("click", () => update({ sheet: null }));
// A value chosen in a sheet is taken at once and closes it, as a count does the palette; the dice once both are set (TODO-150).
// Listened on the sheet, so the choice's own handler has run.
function choseInSheet(e) {
  if (e.type === "click" && !e.target.closest("button[data-value], button[data-n]")) return;
  if (e.currentTarget.id === "sheet-roll" && halfDie()) return;   // one die set, the other still to choose
  update({ sheet: null });
}
for (const k of ["match", "cube", "roll"]) {
  $(`sheet-${k}`).addEventListener("click", choseInSheet);
  $(`sheet-${k}`).addEventListener("change", choseInSheet);
}

// ---- what the analysis is asked
part((s) => [s.dice, s.diceFromPhoto, cubeOffered(s), s.onRoll], (s) => {
  $("dice-row").dataset.side = s.onRoll;   // the faces in the colours of the dice on the board
  // a double offered: no dice yet (TODO-086), but the row stays to choose them, which takes the double back (TODO-150)
  const shown = cubeOffered(s) ? [0, 0] : s.dice;
  for (const [k, id] of [[0, "die1"], [1, "die2"]]) {
    $(id).dataset.value = shown[k] ? String(shown[k]) : "";
    for (const b of $(id).children) b.classList.toggle("on", Number(b.dataset.n) === shown[k]);
  }
  $("dice-note").hidden = !s.diceFromPhoto || cubeOffered(s);
  // with dice in, the side on roll has already rolled: "振った人", not "次に振る人" (TODO-042)
  $("onroll-label").textContent = `${BgResult.rollWho(rolled(s))}人`;
});

// ---- the match (TODO-066): the scores go up to one below its length
part((s) => s.match, (s) => {
  const m = s.match;
  $("match-length").value = String(m.length);
  $("match-score").hidden = !m.length;
  for (const side of ["white", "black"]) {
    const sel = $(`score-${side}`);
    if (sel.options.length !== m.length) {
      sel.replaceChildren(...Array.from({ length: m.length }, (_, k) => new Option(String(k), String(k))));
    }
    sel.value = String(m[side]);
  }
  $("crawford-opt").hidden = !BgCube.canCrawford(m.length, m.white, m.black);
  $("crawford").checked = m.crawford;
});

part((s) => [s.cube, s.cubeFromPhoto, s.onRoll, rolled(s), s.bottomColour], (s) => {
  $("cube-side").hidden = s.cube.at === "centre";
  $("cube-value").value = String(s.cube.value);
  $("cube-offered").checked = s.cube.offered;
  $("cube-note").hidden = !s.cubeFromPhoto;
  const req = BgCube.request(s.cube, s.onRoll, rolled(s));
  const roll = NAME[req.on_roll];
  // only what the settings do not show: who is asked what (TODO-086)
  $("cube-help").textContent = rolled(s) ? ""
    : req.doubled ? `${NAME[req.cube_owner]}の人のテイク／パスを判定します。`
    : req.cube_owner && req.cube_owner !== req.on_roll ? `キューブは${NAME[req.cube_owner]}の人のもの。${roll}の人はダブルできません。`
    : `${roll}の人のダブルを判定します。`;
  $("cube-help").hidden = !$("cube-help").textContent;
});

// ---- the result
part((s) => [s.result, s.resultDice, s.bottomColour], (s) => {
  const box = $("result");
  box.hidden = !s.result;
  if (s.result) box.innerHTML = BgResult.html(s.result, s.resultDice);
});
part((s) => [s.result && s.moveShown], (s) => {
  for (const li of document.querySelectorAll("#result .moves li")) li.classList.toggle("on", Number(li.dataset.k) === s.moveShown);
});
part((s) => [resultStale(s), s.reanalyzing], (s) => {
  $("result").classList.toggle("stale", resultStale(s));
  $("reanalyzing").hidden = !(s.step === "outcome" && resultStale(s));
  $("reanalyzing").textContent = s.reanalyzing ? "盤面が変わったので解析し直しています…" : "盤面が変わりました。直し終わると解析し直します。";
});

// ---- fixed on the result screen (TODO-138): analysed again by itself a moment after the last fix,
// once nothing is half done (the palette open, a die not set while the other is); a sheet left open does not wait (TODO-150)
const REANALYZE_WAIT = 800;   // ms after the last change
let reanalyzeTimer = null;
part((s) => [s.step, resultStale(s) && inputsKey(s), s.plies, !!s.palette, s.busy && 1, analyzeErrors(s).length], (s) => {
  clearTimeout(reanalyzeTimer);
  if (s.step !== "outcome" || !resultStale(s) || s.palette || s.busy || analyzeErrors(s).length || halfDie(s)) return;
  reanalyzeTimer = setTimeout(reanalyze, REANALYZE_WAIT);
});

// The move picked in the result's list (the best one at first) as arrows, while the result fits the board.
function moveToShow(s) {
  const r = s.result;
  if (!r || !r.moves || !r.moves.length || !resultFits(s)) return null;
  const m = r.moves[s.moveShown] || r.moves[0];
  // one arrow per die (the API's steps); results kept from older versions have only the string
  const hops = (m.steps && BgMoves.hops(s.board, r.on_roll, m.steps)) || BgMoves.hops(s.board, r.on_roll, m.move);
  return hops ? { hops, mover: r.on_roll } : null;
}

// ---- the photo of the playing area warped onto the drawn one (photo.js), made once per photo and corners
let photoSerial = 0;
const photoIds = new WeakMap();
function photoId(s) {
  const b = s.photo && s.photo.bitmap;
  if (!b) return 0;
  if (!photoIds.has(b)) photoIds.set(b, ++photoSerial);
  return photoIds.get(b);
}

let rectified = null;   // {key, url}
function rectifiedPhoto(s) {
  if (!s.fromPhoto || !s.photo || s.corners.length !== 4 || !window.BgPhoto) return null;
  // The recognizer's refined corners and columns line the photo up best; they hold for the photo and
  // corners they came from.
  const g0 = s.geometry;
  const g = g0 && g0.photo === photoId(s) && g0.from === JSON.stringify(s.corners) ? g0 : null;
  const key = JSON.stringify([photoId(s), s.corners, g && g.corners]);
  if (rectified && rectified.key === key) return rectified.url;
  let url = null;
  try {
    const { w, h } = BgBoardView.PLAY;
    url = BgPhoto.rectify(s.photo.bitmap, g ? g.corners : s.corners, w * 2, h * 2, g && BgBoardView.columnAnchors(g, 2));
  } catch (err) {
    console.warn("could not show the photo:", err);
  }
  rectified = { key, url };
  return url;
}

// ================================================================ the photo history (history.js)
// Stored on this device only, and kept in step with the state. Failures (no IndexedDB, private
// mode, storage full) never block the app.

const historyRecord = (s) => {
  const k = s.historyScale;
  return { corners: s.corners.map(([x, y]) => [x * k, y * k]), cornerGuess: s.cornerGuess, cornersMoved: s.cornersMoved,
           keepCorners: s.keepCorners, trimmed: s.photo.trimmed, sideMode: s.sideMode, sideFrom: s.sideFrom,
           homePick: s.homePick, home: s.home, homeGuess: s.homeGuess, bottomColour: s.bottomColour,
           onRoll: s.onRoll, dice: diceIn(s), cube: s.cube, board: s.board, read: s.read, warnings: s.warnings };
};

let savedRecord = null;
function persist(force = false) {
  if (!state.historyId || state.dragging) return;
  const record = historyRecord(state);
  const key = JSON.stringify([state.historyId, record]);
  if (key === savedRecord && !force) return;
  savedRecord = key;
  PhotoHistory.update(state.historyId, record).catch(() => {});
}

let thumbUrls = [];
let historyShown = 0;   // bumped to list the photos again
part((s) => (s.step === "photo" ? historyShown : undefined), () => renderHistory());

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
    text.innerHTML = `${BgResult.esc(when)}<span class="sub">${done}</span>`;
    open.append(img, text);
    open.addEventListener("click", () => openHistory(e.id));
    const del = document.createElement("button");
    del.className = "button del";
    del.textContent = "✕";
    del.setAttribute("aria-label", "この写真を履歴から消す");
    del.addEventListener("click", () => forgetPhoto(e.id));
    li.append(open, del);
    ul.append(li);
  }
}

// ================================================================ actions

// The screens, with the phone's back button: one history entry stands for "inside the app", so the
// phone's back comes back here as a popstate instead of leaving the app.
function go(step) {
  if (step !== "photo" && !(history.state && history.state.bg)) history.pushState({ bg: true }, "");
  if (step === "photo") historyShown++;
  if (step !== "outcome") {
    stopSpeaking();   // the stop button is only on the result screen
    if (reanalyzeAbort) reanalyzeAbort.abort();   // a fix on the result screen: analysed on the board screen instead
  }
  update({ step, sheet: null });   // a sheet open on the board screen is closed when it is left (TODO-113)
  if (step === "corners") requestAnimationFrame(() => redraw(drawCorners));   // once the layout has settled
  window.scrollTo(0, 0);
}

const previousStep = () =>
  state.step === "outcome" ? "board" : state.step === "board" && state.fromPhoto ? "corners" : "photo";

// 「最初へ」 only where 戻る does not already lead to the photo screen (TODO-148, TODO-149)
part((s) => [s.step, s.fromPhoto], () => { $("to-start").hidden = previousStep() === "photo"; });

// Back to the photo screen also uses up the history entry, so the next back leaves the app.
function goBack() {
  if (previousStep() === "photo" && history.state && history.state.bg) history.back();
  else go(previousStep());
}

// Straight back to the photo screen from any screen (TODO-148). The history entry is used up as with
// goBack; the popstate it fires finds the photo screen already shown and does nothing.
function goStart() {
  const inApp = history.state && history.state.bg;
  go("photo");
  if (inApp) history.back();
}

async function withBusy(text, work, scanning = false, cancel = null) {
  update({ busy: { text, scanning, cancel } });
  try { return await work(); } finally { update({ busy: null }); }
}

// A tap on a point or the bar of a board picture (board-view.js): put the stack up to the tapped level,
// or empty the point (its number); held down, the palette.
function select(at, { level, side, hold, x, y }) {
  if (closingPalette) return;   // the tap that closed the palette does nothing else
  const b = state.board;
  if (hold) {
    const on = at === "bar" ? side : BgBoard.sideOn(b, at) || state.paintSide;
    update({ selected: at, palette: { at, side: on, x, y } });
    return;
  }
  if (level === 0) { if (at !== "bar") fixBoard(BgBoard.set(b, at, "white", 0)); return; }
  const put = at === "bar" ? side : BgBoard.sideOn(b, at) || state.paintSide;
  fixBoard(BgBoard.tap(b, at, level, put), { paintSide: put });
}

// A fix by hand, which "元に戻す" can take back.
function fixBoard(board, patch = {}) {
  if (JSON.stringify(board) === JSON.stringify(state.board)) { update(patch); return; }
  update({ board, undo: [...state.undo, state.board].slice(-50), ...patch });
}

function closePalette() {
  if (state.palette) update({ palette: null, selected: null });
}
let closingPalette = false;

function editBoard(change) {
  update({ board: change(state.board), read: state.read && change(state.read) });
}

// Who is on roll; a cube just offered lies on the side of the player doubled, so it goes to the other side.
function setOnRoll(side) {
  const offered = BgCube.request(state.cube, state.onRoll, rolled()).doubled;
  update({ onRoll: side, cube: offered ? { ...state.cube, at: BgBoard.other(side) } : state.cube });
}

// A die chosen while a double is offered: the double is cleared, and dice left in from before do not count (TODO-150).
function setDie(k, value) {
  const offered = cubeOffered();
  const dice = offered ? [0, 0] : state.dice.slice();
  dice[k] = Number(value) || 0;
  update({ dice, diceFromPhoto: false, ...(offered && dice[k] ? { cube: { ...state.cube, offered: false }, cubeFromPhoto: false } : {}) });
}

function setCube(patch) {
  update({ cube: { ...state.cube, ...patch }, cubeFromPhoto: false });
}

// The match and its score, from the board screen's settings: kept on this phone (TODO-066).
function setMatch(patch) {
  const match = BgCube.fixMatch({ ...state.match, ...patch });
  keep("match", JSON.stringify(match));
  update({ match });
}

function setResult(result, dice) {
  stopSpeaking();
  update({ result, resultDice: dice || null, resultFor: result ? inputsKey() : null, moveShown: 0 });
}

// A photo, chosen, shared or reopened, with where it was left (or a fresh start).
function startPhoto(file, bitmap, kept, historyId, historyScale) {
  const guess = !kept || !kept.corners || kept.corners.length < 4 || kept.cornerGuess === "finding";
  update({
    photo: { file, bitmap, trimmed: !!(kept && kept.trimmed) }, fromPhoto: true, geometry: null, historyId, historyScale, selected: null,
    corners: guess ? defaultCorners(bitmap) : kept.corners.map((c) => c.slice()),
    // looking again when the app was left: the corners as the user left them
    cornerGuess: guess ? "finding" : kept.cornerGuess === "again" ? "moved" : kept.cornerGuess || "",
    cornersMoved: !!(kept && kept.cornersMoved), keepCorners: !!(kept && kept.keepCorners),
    cornersFixed: [false, false, false, false], edit: null,   // not kept with the photo
    // the way this photo was taken, as kept with it (photos kept before 0.68.0: from the near player's side)
    ...(kept ? { sideMode: !!kept.sideMode, sideFrom: kept.sideFrom || storedSide().sideFrom } : storedSide()),
    // a new photo: guessed by the server (nothing picks it since TODO-113); entries from before 0.6.0 kept only the side picked
    homePick: (kept && (kept.homePick || kept.home)) || "auto",
    home: kept ? kept.home || "right" : state.home,
    homeGuess: kept ? kept.homeGuess || null : state.homeGuess,
    bottomColour: kept ? kept.bottomColour ?? 1 : Number(stored("bottomColour", ["0", "1"], "1")),   // a new photo: the colour kept on this phone
    onRoll: kept ? kept.onRoll || "white" : state.onRoll,
    warnings: (kept && kept.warnings) || [],
    board: (kept && kept.board) || null,
    read: (kept && kept.read) || null,
    dice: (kept && kept.dice) || [0, 0], diceFromPhoto: false,   // the dice of the last position are not this photo's
    cube: (kept && kept.cube) || BgCube.fromRead(null), cubeFromPhoto: false,
  });
  setResult(null);
  persist(true);   // now the most recent
  go("corners");
  if (guess) guessCorners(file, true);
}

async function loadPhoto(file) {
  await withBusy("写真を読み込んでいます…", async () => {
    try {
      const bitmap = await decode(file);
      let id = null, scale = 1;
      try {
        const [w, h] = imageSize(bitmap);
        ({ id, scale } = await PhotoHistory.add(file, bitmap, w, h));
      } catch (_) { /* not stored */ }
      startPhoto(file, bitmap, null, id, scale);
    } catch (err) {
      alert("写真を開けませんでした: " + err.message);
    }
  });
}

async function openHistory(id) {
  await withBusy("写真を読み込んでいます…", async () => {
    try {
      const e = await PhotoHistory.get(id);
      if (!e) { historyShown++; render(); return; }
      startPhoto(e.image, await decode(e.image), e, id, 1);   // the stored copy is now the photo
    } catch (err) {
      alert("写真を開けませんでした: " + err.message);
    }
  });
}

async function forgetPhoto(id) {
  if (!confirm("この写真を履歴から消しますか？")) return;
  if (state.historyId === id) state.historyId = null;
  try { await PhotoHistory.remove(id); } catch (_) { /* already gone */ }
  historyShown++;
  render();
}

// The edited photo (TODO-070) is the photo from now on: what is sent, kept in the history and on the
// Pi. The corners are looked for again in it; the rest (the board read, the settings) stays.
async function applyEdit(e = state.edit) {
  if (!e.turn && !e.angle && !e.rect) { update({ edit: null }); return; }
  search++;   // a search for the corners still running: its answer is the old photo's (nor kept in the history meanwhile)
  await withBusy("画像を作っています…", async () => {
    try {
      const file = new File([await jpeg(BgPhoto.turn(state.photo.bitmap, e.turn * 90 + e.angle, e.rect, UPLOAD_MAX))], "edited.jpg", { type: "image/jpeg" });
      const bitmap = await decode(file);
      const [w, h] = imageSize(bitmap);
      let id = state.historyId, scale = 1;
      try { if (id) scale = await PhotoHistory.replace(id, file, bitmap, w, h); } catch (_) { id = null; /* not stored */ }
      startPhoto(file, bitmap, { ...historyRecord(state), corners: null, cornersMoved: false, keepCorners: false, trimmed: state.photo.trimmed || !!e.rect }, id, scale);
    } catch (err) {
      alert("画像を編集できませんでした: " + err.message);
    }
  });
}

function setUpByHand() {
  update({ fromPhoto: false, read: null, historyId: null, warnings: [], board: BgBoard.start(), selected: null });
  setResult(null);
  go("board");
}

// ================================================================ flows with the server

const imageSize = (b) => [b.width || b.naturalWidth, b.height || b.naturalHeight];

// The rectangle the corners start from while (or if) the board can't be found.
function defaultCorners(bitmap) {
  const [iw, ih] = imageSize(bitmap);
  const mx = iw * 0.1, my = ih * 0.1;
  return [[mx, my], [iw - mx, my], [iw - mx, ih - my], [mx, ih - my]];
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

// The photo as sent: large photos are scaled down (the corners and the answer's pixels with them).
async function uploadImage() {
  const { file, bitmap } = state.photo;
  const [iw, ih] = imageSize(bitmap);
  if (Math.max(iw, ih) <= SEND_AS_IS_MAX) return { blob: file, scale: 1 };
  const scale = Math.min(1, UPLOAD_MAX / Math.max(iw, ih));
  return { blob: await jpeg(scaledCanvas(bitmap, scale)), scale };
}

function scaledCanvas(image, scale) {
  const [iw, ih] = imageSize(image);
  const c = document.createElement("canvas");
  c.width = Math.round(iw * scale);
  c.height = Math.round(ih * scale);
  c.getContext("2d").drawImage(image, 0, 0, c.width, c.height);
  return c;
}

const jpeg = (canvas) => new Promise((res, rej) =>
  canvas.toBlob((b) => (b ? res(b) : rej(new Error("画像が大きすぎます"))), "image/jpeg", 0.92));

// The photo the corners are looked for in: one the user has cut to the board is looked in as a
// whole with the board allowed to fill it (crop = all of it; TODO-070).
async function cornersForm() {
  const { blob, scale } = await uploadImage();
  const fd = new FormData();
  fd.append("image", blob, "board.jpg");
  if (sideSent()) fd.append("side", sideSent());
  if (state.photo.trimmed) {
    const [iw, ih] = imageSize(state.photo.bitmap);
    fd.append("crop", `0,0,${Math.round(iw * scale)},${Math.round(ih * scale)}`);
  }
  return { fd, scale };
}

// What the server finds, shown on the photo as it goes (scan.js), stage by stage: the search for
// the corners, or the reading of the board. One at a time; a tap skips the stages still to come.
let overlay = null;   // {kind: "corners" | "reading", scan}
const scanning = () => !!overlay;

// The overlay of this kind over the photo, or null when it can't run (then the app just waits).
function startOverlay(kind, corners) {
  stopOverlay();
  if (!window.BgScan || state.step !== "corners") return null;
  try {
    const reduced = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
    const scan = BgScan.start($("photo-canvas"), { mode: kind === "corners" ? "corners" : undefined, corners, reduced,
                                                   prepare: () => { cornersView.draw(true); return cornersView.toCanvas; } });
    overlay = { kind, scan };
    return overlay;
  } catch (err) {
    console.warn("no overlay on the photo:", err);
    return null;
  }
}

// Stops the overlay (only one of this kind, if given) and shows the corners again.
function stopOverlay(kind) {
  if (!overlay || (kind && overlay.kind !== kind)) return;
  overlay.scan.stop();
  overlay = null;
  redraw(drawCorners);
}

let search = 0;   // bumped by each search for the corners: only the latest one's answer is taken

// switchSide (a photo just opened): found as taken from beside (TODO-134), the switches are turned that way
// for this photo (not kept on this phone); not when the user has just changed them (cornersAgain).
async function guessCorners(file, switchSide = false) {
  const id = ++search;
  const way = [state.sideMode, state.sideFrom];   // changed by the user meanwhile: theirs stays
  const [iw, ih] = imageSize(state.photo.bitmap);
  const mine = startOverlay("corners", [[0, 0], [iw, 0], [iw, ih], [0, ih]]);   // (the search for the last photo stops)
  let corners = null, side = null;
  try {
    const { fd, scale } = await cornersForm();   // the guess is steadier from the larger image
    const data = await BgApi.postStages("find-corners", fd, (ev) => mine && mine.scan.push(BgApi.scaleGeometry(ev, scale)));
    if (data.corners) corners = data.corners.map(([x, y]) => [x / scale, y / scale]);
    side = data.side || null;
    if (mine && data.streamed && state.photo.file === file) await mine.scan.done();   // every stage shown (or tapped)
  } catch (_) { /* keep the rectangle */ }
  if (overlay === mine) stopOverlay();
  // the user may have moved on to another photo, or started on the corners already
  if (id !== search || state.photo.file !== file || state.cornerGuess !== "finding") return;
  if (state.cornersMoved) update({ cornerGuess: "moved" });
  else if (corners) update({ corners, cornerGuess: "found", ...(switchSide && side && state.sideMode === way[0] && state.sideFrom === way[1] ? { sideMode: true, sideFrom: side } : {}) });
  else update({ cornerGuess: "default" });
  redraw(drawCorners);
}

// Looks again (TODO-068): the corners the user has put in place stay, the others are looked for.
async function findAgain() {
  const id = ++search;
  const { file, bitmap } = state.photo;
  const [iw, ih] = imageSize(bitmap);
  const start = state.corners;   // a new array whenever the user moves one
  const fixed = [0, 1, 2, 3].map((k) => (state.cornersFixed[k] && start[k] ? start[k] : null));
  update({ cornerGuess: "again" });   // not "finding": a photo reopened then keeps the corners the user put
  const mine = startOverlay("corners", [[0, 0], [iw, 0], [iw, ih], [0, ih]]);
  let corners = null;
  try {
    const { fd, scale } = await cornersForm();
    fd.append("fixed", JSON.stringify(fixed.map((p) => p && p.map((v) => +(v * scale).toFixed(1)))));
    const data = await BgApi.postStages("find-corners", fd, (ev) => mine && mine.scan.push(BgApi.scaleGeometry(ev, scale)));
    if (data.corners) corners = data.corners.map(([x, y]) => [x / scale, y / scale]);
    if (mine && data.streamed && state.photo.file === file) await mine.scan.done();
  } catch (_) { /* as not found */ }
  if (overlay === mine) stopOverlay();
  // the user may have moved on to another photo, moved a corner or started reading meanwhile
  if (id !== search || state.photo.file !== file || state.cornerGuess !== "again") return;
  if (state.corners !== start) { update({ cornerGuess: "moved" }); return; }
  // the corners found are rough: read them fitted again
  update({ corners: corners ? corners.map((p, k) => fixed[k] || p) : start, cornerGuess: corners ? "found" : "missed",
           keepCorners: state.keepCorners && !corners });
  redraw(drawCorners);
}

// Taken from beside (TODO-120): "right" or "left" for the server while the mode is on and the side chosen, else null.
const sideSent = () => (state.sideMode && state.sideFrom) || null;

// The corners looked for again, the way the photo is now said to be taken (the mode or its side changed;
// was: sideSent() before). The ones the user put in place stay where they are in the photo, under the name
// they have the new way (BgCornersView.renamed), and the others are looked for; with none put in place,
// all four are looked for afresh.
function cornersAgain(was) {
  if (!state.photo || state.step !== "corners" || state.edit || was === sideSent()) return;
  if (state.corners.length === 4 && state.cornersFixed.some(Boolean)) {
    update({ corners: BgCornersView.renamed(state.corners, was, sideSent()),
             cornersFixed: BgCornersView.renamed(state.cornersFixed, was, sideSent()) });
    findAgain();
    return;
  }
  update({ corners: defaultCorners(state.photo.bitmap), cornerGuess: "finding", cornersMoved: false, keepCorners: false,
           cornersFixed: [false, false, false, false] });
  redraw(drawCorners);
  guessCorners(state.photo.file);
}

// The switch kept on this phone (for the next photo) and with this photo.
function setSideMode(on) {
  const was = sideSent();
  keep("sideMode", on ? "on" : "off");
  update({ sideMode: on });
  cornersAgain(was);   // on for the first time: nothing to send until the side is chosen
}

function setSideFrom(v) {
  const was = sideSent();
  keep("sideFrom", v);
  update({ sideFrom: v });
  cornersAgain(was);
}

// Claude picks the corners (TODO-082): all 4 are replaced. Only on servers that ask Claude (/version).
async function claudeCorners() {
  const id = ++search;   // a search still running is not taken
  const { file } = state.photo;
  const start = state.corners;
  stopOverlay("corners");
  update({ cornerGuess: "again" });
  const cancel = new AbortController();
  let corners = null, error = null;
  try {
    await withBusy("Claude が四隅を選んでいます…", async () => {
      const { blob, scale } = await uploadImage();
      const fd = new FormData();
      fd.append("image", blob, "board.jpg");
      const data = await BgApi.post("claude-corners", fd, undefined, cancel.signal);
      // Claude names them with the near player at the photo's bottom: named as this photo was taken (TODO-120)
      corners = BgCornersView.renamed(data.corners.map(([x, y]) => [x / scale, y / scale]), null, sideSent());
    }, false, cancel);
  } catch (err) {
    if (!cancel.signal.aborted) error = err;
  }
  // as findAgain: another photo, a corner moved or reading started meanwhile
  if (id !== search || state.photo.file !== file || state.cornerGuess !== "again") return;
  if (state.corners !== start || !corners) update({ cornerGuess: "moved" });
  else update({ corners, cornerGuess: "found", cornersFixed: [false, false, false, false], keepCorners: false });   // Claude's, not the user's
  redraw(drawCorners);
  if (error) alert("Claude に選ばせられませんでした: " + error.message);
}

async function recognize() {
  stopOverlay("corners");   // reading now: the corners as they are
  if (state.cornerGuess === "finding" || state.cornerGuess === "again") update({ cornerGuess: "" });   // and a guess coming later does not move them
  $("photo-canvas").scrollIntoView({ block: "nearest" });
  const mine = startOverlay("reading", state.corners.map((p) => p.slice()));
  const skip = () => mine && mine.scan.skip();
  $("busy").addEventListener("click", skip);
  try {
    await withBusy("盤面を読み取っています…", async () => {
      const { blob, scale } = await uploadImage();
      let dice = rolled();
      const cubeByHand = state.cube.at !== "centre";   // else the server uses the cube it reads (if any)
      const req = BgCube.request(state.cube, state.onRoll, dice);
      const fd = new FormData();
      fd.append("image", blob, "board.jpg");
      fd.append("corners", state.corners.flat().map((v) => (v * scale).toFixed(1)).join(","));
      fd.append("home", state.homePick);
      if (state.keepCorners) fd.append("keep_corners", "true");
      if (sideSent()) fd.append("side", sideSent());
      fd.append("bottom_colour", String(state.bottomColour));
      fd.append("on_roll", req.on_roll);
      if (dice) fd.append("dice", dice.join(","));
      if (cubeByHand) {
        fd.append("cube_value", String(req.cube_value));
        fd.append("cube_owner", req.cube_owner);
        fd.append("doubled", String(req.doubled));
      }
      fd.append("plies", state.plies);
      for (const [k, v] of Object.entries(BgCube.matchRequest(state.match))) fd.append(k, String(v));
      const data = await BgApi.postStages("analyze-photo", fd, (ev) => mine && mine.scan.push(BgApi.scaleGeometry(ev, scale)));
      // what was read from the photo goes in as if set by hand (the analysis used it too), marked as read
      const patch = {};
      if (!dice && data.dice_read) {
        dice = data.dice_read;
        Object.assign(patch, { dice: dice.slice(), diceFromPhoto: true });
      }
      if (!cubeByHand && data.cube_read) {
        // in a playing field: the side on roll has just doubled, and the dice wait (TODO-045)
        if (data.cube_read.at === "field" && dice) { dice = null; Object.assign(patch, { dice: [0, 0], diceFromPhoto: false }); }
        Object.assign(patch, { cube: BgCube.fromRead(data.cube_read, state.onRoll), cubeFromPhoto: true });
      }
      // with dice, the cube on a side is owned, not just offered (as the server took it; TODO-086)
      const cube = patch.cube || state.cube;
      if (dice && cubeOffered({ cube })) patch.cube = { ...cube, offered: false };
      if (data.analysis) patch.onRoll = data.analysis.on_roll;
      const g = data.geometry;
      const geometry = g && { ...BgApi.scaleGeometry(g, scale), photo: photoId(state), from: JSON.stringify(state.corners) };
      // the stages still waiting their turn on the photo (a tap skips them). The reading is done only
      // when the last one has been shown, so the text stays "盤面を読み取っています…" till then.
      if (mine) await (data.streamed ? mine.scan.done() : mine.scan.reveal(geometry));
      const rec = data.recognized;
      const board = { points: rec.points, bar_white: rec.bar_white, bar_black: rec.bar_black };
      update({ ...patch, geometry, board, read: BgBoard.copy(board), warnings: data.warnings || [],
               home: data.home || (state.homePick === "auto" ? "right" : state.homePick),
               homeGuess: data.home_guess || null, selected: null });
      go("board");
      setResult(data.analysis, dice);
      // the board was read but not analysed (e.g. a cube read on one side in the Crawford game)
      if (data.analysis_error) alert(crawfordCube() ? CRAWFORD_CUBE : "解析できませんでした: " + data.analysis_error);
    }, !!mine);
  } catch (err) {
    alert("読み取りに失敗しました: " + err.message);
  } finally {
    $("busy").removeEventListener("click", skip);
    if (overlay === mine) stopOverlay();   // the corners again, as before reading
  }
}

async function analyze() {
  if (analyzeErrors().length) return;   // the button is greyed out then
  update({ selected: null });   // done editing
  sendSample();
  if (state.autoSpeak) unlockSpeech();
  // The result on hand still fits the board and settings (e.g. worked out when the photo was read): just show it.
  if (state.result && !resultStale()) { go("outcome"); autoSpeak(); return; }
  const text = state.plies === "3" ? "3手読みで解析しています（しばらくかかります）…" : "解析しています…";
  await withBusy(text, async () => {
    try {
      const dice = rolled();
      setResult(await BgApi.postJson("analyze", analyzeBody(dice)), dice);
      go("outcome");
      autoSpeak();
    } catch (err) {
      alert("解析に失敗しました: " + err.message);
    }
  });
}

function analyzeBody(dice) {
  const body = { board: BgBoard.copy(state.board), plies: Number(state.plies), ...BgCube.request(state.cube, state.onRoll, dice),
                 ...BgCube.matchRequest(state.match), bottom_colour: state.bottomColour };
  if (dice) body.dice = dice;
  return body;
}

// The board fixed on the result screen, analysed again without leaving it (TODO-138). The old result
// stays, greyed out, till the new one is in; fixes made meanwhile are analysed after it.
let reanalyzeAbort = null;
async function reanalyze() {
  if (state.step !== "outcome" || !resultStale() || analyzeErrors().length) return;
  if (reanalyzeAbort) reanalyzeAbort.abort();
  const abort = reanalyzeAbort = new AbortController();
  const key = inputsKey(), dice = rolled();
  update({ reanalyzing: true });
  try {
    const result = await BgApi.postJson("analyze", analyzeBody(dice), abort.signal);
    if (abort.signal.aborted || inputsKey() !== key || state.step !== "outcome") return;   // fixed again meanwhile
    setResult(result, dice);
    sendSample();   // as 「解析する」 does: the board as fixed now
  } catch (err) {
    if (!abort.signal.aborted) alert("解析に失敗しました: " + err.message);
  } finally {
    if (reanalyzeAbort === abort) { reanalyzeAbort = null; update({ reanalyzing: false }); }
  }
}

// ================================================================ a sample for the recognizer (sample.js)
// The photo and the board as fixed by hand, as two files (photo + truth.json) to send to the
// developers so the recognizer can be measured and improved on them; with 「サーバーに保存する」 on (the default, TODO-112), the
// same pair goes to the server each time the board is analysed (POST /samples).

async function sampleOf(name) {
  // the stored copy (the size the app sends anyway) with the corners in its pixels, else the photo itself
  const e = state.historyId && await PhotoHistory.get(state.historyId).catch(() => null);
  const blob = (e && e.image) || state.photo.file;
  const k = e && e.image ? state.historyScale : 1;
  const ext = blob.type === "image/png" ? "png" : "jpg";
  const truth = BgSample.truth({
    image: `${name}.${ext}`, corners: state.corners.map(([x, y]) => [x * k, y * k]),
    home: state.home, bottomColour: state.bottomColour, board: state.board,
    dice: diceIn(), cube: state.cube, read: state.read, side: sideSent(),
  });
  return { blob, ext, truth };
}

// Keep this photo and its board on the server, when the user has turned that on. Never in the way.
async function sendSample() {
  if (!serverKeepsSamples || state.collect !== "on" || !state.fromPhoto || !state.board || !state.historyId) return;
  try {
    const id = state.historyId;
    const { blob, ext, truth } = await sampleOf(`user-${id}`);
    const fd = new FormData();
    fd.append("id", id);
    fd.append("truth", JSON.stringify(truth));
    fd.append("image", blob, `${id}.${ext}`);
    await BgApi.post("samples", fd);
  } catch (_) { /* not kept this time */ }
}

async function exportSample() {
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
        return;
      } catch (err) {
        if (err.name === "AbortError") return;   // closed by the user
        // Chrome on Android refuses a .json (NotAllowedError "Permission denied"): download instead
      }
    }
    for (const f of files) {   // no share sheet (a PC), or it refused: download both
      const a = document.createElement("a");
      a.href = URL.createObjectURL(f);
      a.download = f.name;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 10000);
    }
  } catch (err) {
    alert("書き出せませんでした: " + err.message);
  }
}

// ================================================================ reading the result aloud
// Google Translate's voice through our server (/speech, TODO-111): the same voice on every phone. One
// sentence per request (it takes about 200 characters). When that fails, the rest is read in the
// browser's own voice (Web Speech API), which depends on the phone.

// One Audio for every reading: a phone plays sound only right after a tap, but an element once played
// from a tap may play again later (TODO-115: reading aloud when the analysis comes back seconds later).
const player = new Audio();
let speaking = null;   // the reading going on (a token object), or null
const SILENCE = "data:audio/wav;base64,UklGRnQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YVAAAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgA==";

function toggleSpeaking() {
  if (!state.result) return;
  if (speaking || (window.speechSynthesis && speechSynthesis.speaking)) { stopSpeaking(); return; }
  startSpeaking();
}

function startSpeaking() {
  const sentences = BgResult.speechText(state.result, state.resultDice).split("。").filter((s) => s.trim()).map((s) => s + "。");
  const run = {};
  speaking = run;
  speakLabel(true);
  let k = 0;
  const next = () => {
    if (speaking !== run) return;
    if (k === sentences.length) { stopSpeaking(); return; }
    player.src = BgApi.url("speech?text=" + encodeURIComponent(sentences[k++]));
    player.play().catch(fallback);
  };
  const fallback = () => {
    if (speaking !== run) return;
    speaking = null;
    speakWithBrowser(sentences.slice(k - 1).join(""));
  };
  player.onended = next;
  player.onerror = fallback;
  next();
}

// Called on the tap of 解析する: plays nothing, so the player and the browser's voice may speak once
// the result is in.
function unlockSpeech() {
  stopSpeaking();
  player.src = SILENCE;
  player.play().catch(() => {});
  if (window.speechSynthesis) speechSynthesis.speak(new SpeechSynthesisUtterance(""));
}

const autoSpeak = () => { if (state.autoSpeak && state.result) startSpeaking(); };

function stopSpeaking() {
  if (speaking) { player.onended = player.onerror = null; player.pause(); speaking = null; }
  if (window.speechSynthesis) speechSynthesis.cancel();
  speakLabel(false);
}

function speakWithBrowser(text) {
  const synth = window.speechSynthesis;
  if (!synth) { speakLabel(false); return; }
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "ja-JP";
  const voices = synth.getVoices().filter((v) => /^ja/i.test(v.lang));
  const voice = voices.find((v) => /google/i.test(v.name)) || voices[0];
  if (voice) u.voice = voice;
  u.onend = u.onerror = () => speakLabel(false);
  speakLabel(true);
  synth.speak(u);
}

// The button shows a drawn speaker and a word, not the 🔊 emoji: the emoji looks different on each
// phone and was hard to tell apart. While reading it turns into a stop square and 「止める」.
const SPEAKER_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9h4l5-4v14l-5-4H3z" fill="currentColor"/>' +
  '<path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
const STOP_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="1.5" fill="currentColor"/></svg>';

function speakLabel(on) {
  const btn = $("speak");
  btn.innerHTML = on ? `${STOP_SVG}止める` : `${SPEAKER_SVG}読み上げ`;
  btn.setAttribute("aria-label", on ? "読み上げを止める" : "結果を読み上げる");
  btn.classList.toggle("on", on);
  btn.setAttribute("aria-pressed", on);
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

// ================================================================ events: each only asks for a change

for (const id of ["camera", "file"]) {
  $(id).addEventListener("change", (e) => {
    const file = e.target.files[0];
    e.target.value = "";
    if (file) loadPhoto(file);
  });
}
$("manual").addEventListener("click", setUpByHand);
$("back").addEventListener("click", goBack);
$("to-start").addEventListener("click", goStart);
window.addEventListener("popstate", () => {
  if (state.busy) { history.pushState({ bg: true }, ""); return; }   // wait for the server
  if (state.step !== "photo") go(previousStep());
});

$("corner-reset").addEventListener("click", () => update({ corners: [], cornerGuess: "", cornersFixed: [false, false, false, false] }));
$("keep-corners").addEventListener("change", () => update({ keepCorners: $("keep-corners").checked }));
$("side-mode").addEventListener("change", () => setSideMode($("side-mode").checked));
$("photo-side").addEventListener("change", () => update({ photoView: $("photo-side").checked ? "side" : "off" }));   // a checkbox (TODO-094)
$("edit-start").addEventListener("click", () => { stopOverlay("corners"); update({ edit: { turn: 0, angle: 0, rect: null } }); });
$("edit-cancel").addEventListener("click", () => update({ edit: null }));
$("edit-done").addEventListener("click", () => applyEdit());
// a quarter turn is applied at once (TODO-122)
$("edit-right").addEventListener("click", () => applyEdit({ turn: 1, angle: 0, rect: null }));
$("edit-left").addEventListener("click", () => applyEdit({ turn: 3, angle: 0, rect: null }));
$("edit-angle").addEventListener("input", () => update({ edit: { ...state.edit, angle: Number($("edit-angle").value) } }));
$("find-again").addEventListener("click", findAgain);
$("claude-corners").addEventListener("click", claudeCorners);
$("busy-cancel").addEventListener("click", () => state.busy && state.busy.cancel && state.busy.cancel.abort());
$("recognize").addEventListener("click", recognize);
$("hdr-reuse").addEventListener("click", () => go("board"));
$("to-board").addEventListener("click", () => go("board"));

$("undo").addEventListener("click", () => {
  if (!state.undo.length) return;
  update({ board: state.undo[state.undo.length - 1], undo: state.undo.slice(0, -1), palette: null, selected: null });
});
for (let n = 0; n <= 15; n++) {
  const b = document.createElement("button");
  b.type = "button"; b.dataset.n = String(n); b.textContent = String(n);
  $("palette-counts").appendChild(b);
}
$("palette").addEventListener("click", (e) => {
  const btn = e.target.closest("button"), p = state.palette;
  if (!btn || !p) return;
  if (btn.dataset.value) { update({ palette: { ...p, side: btn.dataset.value } }); return; }
  if (btn.id === "palette-close") { closePalette(); return; }
  if (btn.dataset.n !== undefined) {
    fixBoard(BgBoard.set(state.board, p.at, p.side, Number(btn.dataset.n)), { paintSide: p.side, palette: null, selected: null });
  }
});
// A tap outside the palette closes it (and does nothing else); so does scrolling.
document.addEventListener("pointerdown", (e) => {
  if (!state.palette || $("palette").contains(e.target)) return;
  closingPalette = true;
  closePalette();
}, true);
addEventListener("pointerup", () => setTimeout(() => { closingPalette = false; }));
addEventListener("scroll", closePalette, { passive: true });
// The board was read with the home on the wrong side: mirror it left to right.
function setHome(v) {
  if (v === state.home) return;
  editBoard(BgBoard.mirror);
  update({ home: v, homeGuess: null, selected: null });
}
$("reset-start").addEventListener("click", () => {
  if (confirm("盤面を初期配置に戻しますか？")) fixBoard(BgBoard.start(), { palette: null, selected: null });
});

// The dice: a row of six die faces each, like the palette's counts (TODO-141); the one pressed again clears that die.
for (const [k, id] of [[0, "die1"], [1, "die2"]]) {
  for (let d = 1; d <= 6; d++) {
    const b = document.createElement("button");
    b.type = "button"; b.dataset.n = String(d); b.setAttribute("aria-label", String(d));
    b.innerHTML = `<svg viewBox="0 0 34 34" aria-hidden="true"><rect x="1" y="1" width="32" height="32" rx="6"/>` +
      BgBoardView.PIPS[d].map(([x, y]) => `<circle cx="${17 + x * 9}" cy="${17 + y * 9}" r="3.2"/>`).join("") + "</svg>";
    $(id).appendChild(b);
  }
  $(id).addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) setDie(k, Number(b.dataset.n) === state.dice[k] && !cubeOffered() ? 0 : b.dataset.n);
  });
}
for (const v of BgCube.VALUES) $("cube-value").add(new Option(String(v), String(v)));
$("cube-value").addEventListener("change", () => setCube({ value: Number($("cube-value").value) }));
$("cube-offered").addEventListener("change", () => setCube({ offered: $("cube-offered").checked }));

for (const v of BgCube.MATCH_LENGTHS) $("match-length").add(new Option(v ? `${v} ポイント` : "アンリミテッド", String(v)));
$("match-length").addEventListener("change", () => setMatch({ length: Number($("match-length").value) }));
for (const side of ["white", "black"]) {
  $(`score-${side}`).addEventListener("change", () => setMatch({ [side]: Number($(`score-${side}`).value) }));
}
$("crawford").addEventListener("change", () => setMatch({ crawford: $("crawford").checked }));

const SEGMENTS = {
  sideFrom: setSideFrom,
  onRoll: setOnRoll,
  cubeAt: (v) => setCube({ at: v }),
  collect: (v) => { keep("collect", v); update({ collect: v }); },
  plies: (v) => { keep("plies", v); update({ plies: v }); },
};
for (const seg of document.querySelectorAll(".seg")) {
  seg.addEventListener("click", (e) => {
    const v = e.target.dataset && e.target.dataset.value;
    if (v !== undefined) SEGMENTS[seg.dataset.name](v);
  });
}

$("analyze").addEventListener("click", analyze);
$("auto-speak").addEventListener("change", () => {
  const on = $("auto-speak").checked;
  keep("autoSpeak", on ? "on" : "off");
  update({ autoSpeak: on });
});
$("result").addEventListener("click", (e) => {   // a row of the best moves: its arrows on the board
  const li = e.target.closest(".moves li");
  if (!li) return;
  update({ moveShown: Number(li.dataset.k) });
  $("board-svg").scrollIntoView({ behavior: "smooth", block: "nearest" });
});
speakLabel(false);
$("speak").addEventListener("click", toggleSpeaking);
$("export-sample").addEventListener("click", exportSample);

window.addEventListener("resize", () => redraw(drawCorners));
document.addEventListener("visibilitychange", () => persist());
// The sticky header is as tall as its contents; the board sticks just under it (CSS --hdr-h).
new ResizeObserver(() => {
  document.documentElement.style.setProperty("--hdr-h", document.querySelector("header").offsetHeight + "px");
}).observe(document.querySelector("header"));
// main keeps room under it for the bottom bar (0 while the bar is not shown).
new ResizeObserver(() => {
  document.documentElement.style.setProperty("--bar-h", $("actbar").offsetHeight + "px");
}).observe($("actbar"));

// ================================================================ start

go("photo");
if (window.speechSynthesis) window.speechSynthesis.getVoices();   // Chrome loads the voice list lazily

// "0.40.0" vs "0.39.0" → 1, equal → 0, older → -1 (numbers compared part by part, not as text).
function compareVersions(a, b) {
  const pa = String(a).split(".").map(Number), pb = String(b).split(".").map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const d = (pa[i] || 0) - (pb[i] || 0);
    if (d) return Math.sign(d);
  }
  return 0;
}

// Versions, to tell which build is running (e.g. on the Raspberry Pi), in the header.
$("hdr-version").textContent = `a${APP_VERSION}`;
BgApi.version().then((v) => {
  if (!v) return;
  // The two differ when this device still has an old app.js (reopening fixes it), or when the server
  // was updated with git pull but not restarted, so it still runs the old code (restarting fixes it).
  const cmp = compareVersions(v.analyzer, APP_VERSION);
  const note = cmp > 0 ? `（新しい ${v.analyzer} は開き直すと出ます）`
    : cmp < 0 ? `（サーバーは ${v.analyzer}。再起動が必要）` : "";
  // the note before the commit: on a narrow screen the end is cut off, and the note matters more
  $("hdr-version").textContent = `a${APP_VERSION} · r${v.recognizer}` + note + (v.commit ? ` · ${v.commit}` : "");
  $("hdr-version").classList.toggle("old", cmp !== 0);
  serverKeepsSamples = !!v.samples;
  redraw(drawImprove);
  $("claude-corners").hidden = $("claude-note").hidden = !v.claude;
}).catch(() => {});

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
loadSharedPhoto();

// For checking the app from outside (tools/pi_ui_check.py): the state, and changes made the app's way.
window.BgApp = { get state() { return state; }, update, rolled };
