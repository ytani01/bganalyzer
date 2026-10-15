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

const APP_VERSION = "0.40.2";   // = __version__ in analyzer/app.py; tells an old cached app.js apart
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

// ================================================================ state

const state = {
  step: "photo",
  busy: null,          // {text, scanning} while waiting for the server
  // the photo and where the board is in it
  photo: null,         // {file, bitmap}: the chosen photo (EXIF orientation applied)
  fromPhoto: false,    // the board comes from a photo (else it was set up by hand)
  corners: [],         // [[x, y], ...] in image px, TL TR BR BL
  cornerGuess: "",     // where the corners came from: "finding", "found", "default" (a rectangle), "moved" or "" (tapped)
  cornersMoved: false,
  dragging: false,     // a finger is on the corners
  homePick: "auto",    // the choice on the corners screen: "auto" (guess from the checkers), "left" or "right"
  bottomColour: 1,     // 0 = the darker checkers are 手前's, 1 = the lighter ones
  geometry: null,      // where the recognizer found the board: {corners (image px), columns, bar (fractions), photo, from}
  // the board
  board: null,         // {points[24], bar_white, bar_black} (board.js)
  read: null,          // the board as the recognizer read it, before fixes by hand
  home: "right",       // the side 手前's home board is on, as read and drawn
  homeGuess: null,     // how the server guessed home (homePick "auto"): {margin}; null once flipped by hand
  warnings: [],        // the server's notes on the photo (e.g. taken at a steep angle)
  selected: null,      // point index 0..23 or "bar" being edited
  // what the analysis is asked
  onRoll: "white",
  dice: [0, 0],        // each 1..6, or 0 while not set
  diceFromPhoto: false,
  cube: BgCube.fromRead(null),   // {at: "centre" | "white" | "black", value, offered} (cube.js)
  cubeFromPhoto: false,
  plies: stored("plies", ["2", "3"], "2"),           // how deep gnubg reads (kept on this phone)
  // the answer
  result: null,        // what /analyze returned
  resultFor: null,     // inputsKey() of what it was worked out for
  resultDice: null,
  moveShown: 0,        // the move in the result's list drawn as arrows
  // settings
  photoView: "side",   // the photo on the board screen: "side" (next to the board) or "off"
  collect: stored("collect", ["on", "off"], "off"),  // "on": keep the photo and the fixed board on the server
  // where the photo is kept on this phone (history.js)
  historyId: null,
  historyScale: 1,     // image px -> the stored copy's px
};

// Both dice, or null while one is not set.
const rolled = (s = state) => (s.dice[0] && s.dice[1] ? s.dice.slice() : null);

// What an analysis is worked out from (but its depth): a result fits the board while this is the same.
const inputsKey = (s = state) =>
  s.board && JSON.stringify([s.board.points, s.board.bar_white, s.board.bar_black, s.onRoll, rolled(s), s.cube]);
const resultFits = (s = state) => !!s.result && s.resultFor === inputsKey(s);
const resultStale = (s = state) => !!s.result && (!resultFits(s) || String(s.result.plies) !== s.plies);

function update(patch) {
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
  for (const sp of document.querySelectorAll("#steps span")) {
    sp.classList.toggle("on", sp.dataset.step === s.step);
    sp.classList.toggle("done", STEPS.indexOf(sp.dataset.step) < at);
  }
  $("back").hidden = s.step === "photo";
  $("title").textContent = STEP_TITLES[s.step];
});

// The header carries the screen's main action (and reading aloud once there is a result), so it
// can be pressed without scrolling down to the big button.
part((s) => [s.step, s.fromPhoto && !!s.board, !!s.result], (s) => {
  $("recognize").hidden = s.step !== "corners";
  $("hdr-reuse").hidden = !(s.step === "corners" && s.fromPhoto && s.board);
  $("analyze").hidden = s.step !== "board";
  $("speak").hidden = !(s.step === "outcome" && s.result && window.speechSynthesis);
});

// scanning: the reading overlay is drawn on the photo, so the screen is not darkened and the text sits low
part((s) => s.busy, (s) => {
  $("busy").hidden = !s.busy;
  $("busy").classList.toggle("scanning", !!(s.busy && s.busy.scanning));
  $("busy-text").textContent = s.busy ? s.busy.text : "";
});

// ---- segmented buttons: each shows the state of its name
part((s) => [s.homePick, s.bottomColour, s.onRoll, s.cube.at, s.photoView, s.collect, s.plies], (s) => {
  const value = { homePick: s.homePick, bottomColour: s.bottomColour, onRoll: s.onRoll, cubeAt: s.cube.at,
                  photoView: s.photoView, collect: s.collect, plies: s.plies };
  for (const seg of document.querySelectorAll(".seg")) {
    for (const b of seg.children) b.classList.toggle("on", b.dataset.value === String(value[seg.dataset.name]));
  }
});

part((s) => s.bottomColour, (s) => {
  const light = "#f3efe4", dark = "#3a2a4a";
  const root = document.documentElement.style;
  root.setProperty("--white-chk", s.bottomColour ? light : dark);
  root.setProperty("--black-chk", s.bottomColour ? dark : light);
  root.setProperty("--white-fg", s.bottomColour ? "#222" : "#fff");
  root.setProperty("--black-fg", s.bottomColour ? "#fff" : "#222");
});

// ---- the corners screen
const cornersView = BgCornersView.create($("photo-canvas"), {
  photo: () => state.photo && state.photo.bitmap,
  corners: () => state.corners,
  onTouch: () => stopOverlay("corners"),   // a tap while the search is shown: on to the corners as they are
  onChange: (corners, done) => update({ corners, cornersMoved: true, dragging: !done }),
});

// Not while a finger is on the photo: the text may change height and move the photo under it.
part((s) => (s.dragging ? undefined : [s.corners.length, s.cornerGuess]), (s) => {
  const n = s.corners.length;
  const fit = "点をドラッグして、盤の遊戯面（枠の内側）の四隅 1 左上・2 右上・3 右下・4 左下（手前に座った向き）に合わせてください。";
  $("corner-help").innerHTML = n < 4
    ? `手前に座った向きで、盤の遊戯面（枠の内側）の四隅を <b>${n + 1}. ${CORNER_NAMES[n]}</b> の順にタップしてください（左上→右上→右下→左下）。`
    : s.cornerGuess === "finding" ? "盤の四隅を探しています… " + fit
    : s.cornerGuess === "found" ? "盤の四隅を自動で置きました。ずれていたら" + fit
    : s.cornerGuess === "default" ? "盤を自動で見つけられませんでした。" + fit
    : s.cornerGuess === "moved" ? fit
    : "四隅が決まりました。ホーム側と駒の色を選んで上の「盤面を読み取る」を押してください。";
  $("recognize").disabled = n < 4;
});

// The photo is left alone while scan.js draws on it.
const drawCorners = () => cornersView.draw();
part((s) => (s.step !== "corners" || scanning() ? undefined : [photoId(s), s.corners, s.dragging]), drawCorners);

// ---- the board screen
part((s) => [s.board, s.fromPhoto, s.warnings, s.home, s.homeGuess], (s) => {
  if (!s.board) return;
  const { onW, onB, offW, offB } = BgBoard.counts(s.board);
  const line = (name, on, off) =>
    `<span${on > 15 ? ' class="bad"' : ""}>${name}: 盤上とバー ${on} 個・上がり ${Math.max(off, 0)} 個</span>`;
  $("counts").innerHTML = line("手前", onW, offW) + "<br>" + line("奥", onB, offB) +
    '<br><span class="note">上がった駒は 15 − 盤上 − バー として数えます。読み取りで駒を見落とすと、その分が上がった扱いになります。</span>';
  const errs = BgBoard.errors(s.board);
  if (!errs.length && s.fromPhoto && (offW > 0 || offB > 0)) {
    errs.push(`上がった駒が 手前 ${offW} 個・奥 ${offB} 個 の扱いです。駒の見落としがないか確かめてください。`);
  }
  if (s.fromPhoto) errs.unshift(...s.warnings);
  $("errors").hidden = !errs.length;
  $("errors").textContent = errs.join(" / ");
  // which side 手前's home board was read on, and whether it was guessed
  const side = s.home === "right" ? "右" : "左";
  const g = s.fromPhoto && s.homeGuess;
  $("home-note").hidden = !s.fromPhoto;
  $("home-note").textContent = !g ? `手前の人のホームボードは${side}です。`
    : Math.abs(g.margin) < 1 ? `駒の並びからはホームボードの左右を決められなかったので、${side}にしています。逆なら「左右を入れ替える」を押してください。`
    : `駒の並びから、手前の人のホームボードを${side}と推測しました。逆なら「左右を入れ替える」を押してください。`;
  $("export-sample").hidden = !s.fromPhoto;
});

part((s) => [s.selected, s.board], (s) => {
  const at = s.selected, b = s.board;
  $("editor-buttons").hidden = at === null;
  $("editor-title").textContent = at === null ? "違う所はポイントやバーをタップして直す（下が手前）"
    : at === "bar" ? `バー: 手前 ${b.bar_white} 個、奥 ${b.bar_black} 個`
    : `ポイント ${at + 1}: ` + (b.points[at] === 0 ? "空" : `${b.points[at] > 0 ? "手前" : "奥"}の駒 ${Math.abs(b.points[at])} 個`);
});

// The pictures of the board: on the board screen (with the photo beside it) and on the result screen.
part((s) => s.board && [s.board, s.home, s.selected, rolled(s), s.onRoll, s.cube, s.photoView, moveToShow(s),
                        photoId(s), s.corners, s.geometry && s.geometry.corners], (s) => {
  if (!s.board) return;
  const scene = { board: s.board, home: s.home, selected: s.selected, dice: rolled(s), onRoll: s.onRoll,
                  cube: s.cube, move: moveToShow(s) };
  const photo = rectifiedPhoto(s);
  const side = !!photo && s.photoView === "side";
  $("photo-tools").hidden = !photo;
  $("photo-wrap").hidden = !side;
  $("boards").classList.toggle("two", side);
  if (side) BgBoardView.draw($("photo-svg"), { ...scene, photo }, select);
  BgBoardView.draw($("board-svg"), scene, select);
  BgBoardView.draw($("result-svg"), scene, select);   // the result screen's copy (taps are off there by CSS)
});

// ---- what the analysis is asked
part((s) => [s.dice, s.diceFromPhoto], (s) => {
  $("die1").value = s.dice[0] ? String(s.dice[0]) : "";
  $("die2").value = s.dice[1] ? String(s.dice[1]) : "";
  $("dice-note").hidden = !s.diceFromPhoto;
  // with dice in, the side on roll has already rolled: "振った人", not "次に振る人" (TODO-042)
  $("onroll-label").textContent = `${BgResult.rollWho(rolled(s))}人`;
});

part((s) => [s.cube, s.cubeFromPhoto, s.onRoll, rolled(s)], (s) => {
  $("cube-side").hidden = s.cube.at === "centre";
  $("cube-value").value = String(s.cube.value);
  $("cube-offered").checked = s.cube.offered;
  $("cube-note").hidden = !s.cubeFromPhoto;
  const req = BgCube.request(s.cube, s.onRoll, rolled(s));
  const roll = NAME[req.on_roll];
  $("cube-help").textContent = rolled(s)
    ? "ダイスがあるので、最善手を出します。"
    : req.doubled
      ? `${roll}の人が ${req.cube_value} にダブルしたところとして、${NAME[req.cube_owner]}の人がテイクかパスかを判定します。`
      : req.cube_owner && req.cube_owner !== req.on_roll
        ? `キューブは${NAME[req.cube_owner]}の人が持っているので、${roll}の人はダブルできません。`
        : `ダイスが無いので、${roll}の人がダブルすべきかを判定します。`;
});

// ---- the result
part((s) => [s.result, s.resultDice], (s) => {
  const box = $("result");
  box.hidden = !s.result;
  if (s.result) box.innerHTML = BgResult.html(s.result, s.resultDice);
});
part((s) => [s.result && s.moveShown], (s) => {
  for (const li of document.querySelectorAll("#result .moves li")) li.classList.toggle("on", Number(li.dataset.k) === s.moveShown);
});
part((s) => resultStale(s), (s) => $("result").classList.toggle("stale", resultStale(s)));

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
           homePick: s.homePick, home: s.home, homeGuess: s.homeGuess, bottomColour: s.bottomColour,
           onRoll: s.onRoll, dice: rolled(s), cube: s.cube, board: s.board, read: s.read, warnings: s.warnings };
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
  update({ step });
  if (step === "corners") requestAnimationFrame(() => redraw(drawCorners));   // once the layout has settled
  window.scrollTo(0, 0);
}

const previousStep = () =>
  state.step === "outcome" ? "board" : state.step === "board" && state.fromPhoto ? "corners" : "photo";

// Back to the photo screen also uses up the history entry, so the next back leaves the app.
function goBack() {
  if (previousStep() === "photo" && history.state && history.state.bg) history.back();
  else go(previousStep());
}

async function withBusy(text, work, scanning = false) {
  update({ busy: { text, scanning } });
  try { return await work(); } finally { update({ busy: null }); }
}

function select(at) {
  update({ selected: state.selected === at ? null : at });
}

function editBoard(change) {
  update({ board: change(state.board), read: state.read && change(state.read) });
}

// Who is on roll; a cube just offered lies on the side of the player doubled, so it goes to the other side.
function setOnRoll(side) {
  const offered = BgCube.request(state.cube, state.onRoll, rolled()).doubled;
  update({ onRoll: side, cube: offered ? { ...state.cube, at: BgBoard.other(side) } : state.cube });
}

function setDie(k, value) {
  const dice = state.dice.slice();
  dice[k] = Number(value) || 0;
  update({ dice, diceFromPhoto: false });
}

function setCube(patch) {
  update({ cube: { ...state.cube, ...patch }, cubeFromPhoto: false });
}

function setResult(result, dice) {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  update({ result, resultDice: dice || null, resultFor: result ? inputsKey() : null, moveShown: 0 });
}

// A photo, chosen, shared or reopened, with where it was left (or a fresh start).
function startPhoto(file, bitmap, kept, historyId, historyScale) {
  const guess = !kept || !kept.corners || kept.corners.length < 4 || kept.cornerGuess === "finding";
  update({
    photo: { file, bitmap }, fromPhoto: true, geometry: null, historyId, historyScale, selected: null,
    corners: guess ? defaultCorners(bitmap) : kept.corners.map((c) => c.slice()),
    cornerGuess: guess ? "finding" : kept.cornerGuess || "",
    cornersMoved: !!(kept && kept.cornersMoved),
    // entries from before 0.6.0 kept only the side picked
    homePick: (kept && (kept.homePick || kept.home)) || (kept ? "auto" : state.homePick),
    home: kept ? kept.home || "right" : state.home,
    homeGuess: kept ? kept.homeGuess || null : state.homeGuess,
    bottomColour: kept ? kept.bottomColour ?? 1 : state.bottomColour,
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
  if (guess) guessCorners(file);
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
  const c = document.createElement("canvas");
  c.width = Math.round(iw * scale);
  c.height = Math.round(ih * scale);
  c.getContext("2d").drawImage(bitmap, 0, 0, c.width, c.height);
  return { blob: await new Promise((res) => c.toBlob(res, "image/jpeg", 0.92)), scale };
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

async function guessCorners(file) {
  const [iw, ih] = imageSize(state.photo.bitmap);
  const mine = startOverlay("corners", [[0, 0], [iw, 0], [iw, ih], [0, ih]]);   // (the search for the last photo stops)
  let corners = null;
  try {
    const { blob, scale } = await uploadImage();   // the guess is steadier from the larger image
    const fd = new FormData();
    fd.append("image", blob, "board.jpg");
    const data = await BgApi.postStages("find-corners", fd, (ev) => mine && mine.scan.push(BgApi.scaleGeometry(ev, scale)));
    if (data.corners) corners = data.corners.map(([x, y]) => [x / scale, y / scale]);
    if (mine && data.streamed && state.photo.file === file) await mine.scan.done();   // every stage shown (or tapped)
  } catch (_) { /* keep the rectangle */ }
  if (overlay === mine) stopOverlay();
  // the user may have moved on to another photo, or started on the corners already
  if (state.photo.file !== file || state.cornerGuess !== "finding") return;
  if (state.cornersMoved) update({ cornerGuess: "moved" });
  else if (corners) update({ corners, cornerGuess: "found" });
  else update({ cornerGuess: "default" });
  redraw(drawCorners);
}

async function recognize() {
  stopOverlay("corners");   // reading now: the corners as they are
  if (state.cornerGuess === "finding") update({ cornerGuess: "" });   // and a guess coming later does not move them
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
      fd.append("bottom_colour", String(state.bottomColour));
      fd.append("on_roll", req.on_roll);
      if (dice) fd.append("dice", dice.join(","));
      if (cubeByHand) {
        fd.append("cube_value", String(req.cube_value));
        fd.append("cube_owner", req.cube_owner);
        fd.append("doubled", String(req.doubled));
      }
      fd.append("plies", state.plies);
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
    }, !!mine);
  } catch (err) {
    alert("読み取りに失敗しました: " + err.message);
  } finally {
    $("busy").removeEventListener("click", skip);
    if (overlay === mine) stopOverlay();   // the corners again, as before reading
  }
}

async function analyze() {
  const errs = BgBoard.errors(state.board);
  if (errs.length) { alert(errs.join("\n")); return; }
  update({ selected: null });   // done editing
  sendSample();
  // The result on hand still fits the board and settings (e.g. worked out when the photo was read): just show it.
  if (state.result && !resultStale()) { go("outcome"); return; }
  const text = state.plies === "3" ? "3手読みで解析しています（しばらくかかります）…" : "解析しています…";
  await withBusy(text, async () => {
    try {
      const dice = rolled();
      const body = { board: BgBoard.copy(state.board), plies: Number(state.plies), ...BgCube.request(state.cube, state.onRoll, dice) };
      if (dice) body.dice = dice;
      setResult(await BgApi.postJson("analyze", body), dice);
      go("outcome");
    } catch (err) {
      alert("解析に失敗しました: " + err.message);
    }
  });
}

// ================================================================ a sample for the recognizer (sample.js)
// The photo and the board as fixed by hand, as two files (photo + truth.json) to send to the
// developers so the recognizer can be measured and improved on them; with 「Pi に残す」 on, the
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
    dice: rolled(), cube: state.cube, read: state.read,
  });
  return { blob, ext, truth };
}

// Keep this photo and its board on the server, when the user has turned that on. Never in the way.
async function sendSample() {
  if (state.collect !== "on" || !state.fromPhoto || !state.board || !state.historyId) return;
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
// The browser's own speech (Web Speech API): free, nothing to set up, and on Android's Chrome it is
// Google's voice. Nothing is sent to our server.

function toggleSpeaking() {
  const synth = window.speechSynthesis;
  if (!synth || !state.result) return;
  if (synth.speaking) { synth.cancel(); return; }
  const u = new SpeechSynthesisUtterance(BgResult.speechText(state.result, state.resultDice));
  u.lang = "ja-JP";
  const voices = synth.getVoices().filter((v) => /^ja/i.test(v.lang));
  const voice = voices.find((v) => /google/i.test(v.name)) || voices[0];
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
window.addEventListener("popstate", () => {
  if (state.busy) { history.pushState({ bg: true }, ""); return; }   // wait for the server
  if (state.step !== "photo") go(previousStep());
});

$("corner-reset").addEventListener("click", () => update({ corners: [], cornerGuess: "" }));
$("recognize").addEventListener("click", recognize);
$("hdr-reuse").addEventListener("click", () => go("board"));
$("to-board").addEventListener("click", () => go("board"));

$("editor-buttons").addEventListener("click", (e) => {
  const op = e.target.dataset && e.target.dataset.op;
  const at = state.selected;
  if (!op || at === null) return;
  if (op === "close") update({ selected: null });
  else update({ board: BgBoard.edit(state.board, at, op) });
});
$("swap-colours").addEventListener("click", () => {
  editBoard(BgBoard.swapColours);
  update({ bottomColour: 1 - state.bottomColour });
});
// The board was read with the home on the wrong side: mirror it left to right.
$("flip-home").addEventListener("click", () => {
  editBoard(BgBoard.mirror);
  update({ home: state.home === "right" ? "left" : "right", homeGuess: null, selected: null });
});
$("reset-start").addEventListener("click", () => {
  if (confirm("盤面を初期配置に戻しますか？")) update({ board: BgBoard.start(), selected: null });
});

for (const [k, id] of [[0, "die1"], [1, "die2"]]) {
  for (let d = 1; d <= 6; d++) $(id).add(new Option(String(d), String(d)));
  $(id).addEventListener("change", () => setDie(k, $(id).value));
}
for (const v of BgCube.VALUES) $("cube-value").add(new Option(String(v), String(v)));
$("cube-value").addEventListener("change", () => setCube({ value: Number($("cube-value").value) }));
$("cube-offered").addEventListener("change", () => setCube({ offered: $("cube-offered").checked }));
// The other side to roll; with a result on screen, analyse again for the new side at once.
$("flip-turn").addEventListener("click", () => {
  setOnRoll(BgBoard.other(state.onRoll));
  if (state.result) analyze();
});

const SEGMENTS = {
  homePick: (v) => update({ homePick: v }),
  bottomColour: (v) => update({ bottomColour: Number(v) }),
  onRoll: setOnRoll,
  cubeAt: (v) => setCube({ at: v }),
  photoView: (v) => update({ photoView: v }),
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
$("result").addEventListener("click", (e) => {   // a row of the best moves: its arrows on the board
  const li = e.target.closest(".moves li");
  if (!li) return;
  update({ moveShown: Number(li.dataset.k) });
  $("result-svg").scrollIntoView({ behavior: "smooth", block: "nearest" });
});
$("speak").addEventListener("click", toggleSpeaking);
$("export-sample").addEventListener("click", exportSample);

window.addEventListener("resize", () => redraw(drawCorners));
document.addEventListener("visibilitychange", () => persist());
// The sticky header is as tall as its contents; the board sticks just under it (CSS --hdr-h).
new ResizeObserver(() => {
  document.documentElement.style.setProperty("--hdr-h", document.querySelector("header").offsetHeight + "px");
}).observe(document.querySelector("header"));

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

// Versions, to tell which build is running (e.g. on the Raspberry Pi): small in the header, in full in the footer.
$("hdr-version").textContent = `v${APP_VERSION}`;
BgApi.version().then((v) => {
  if (!v) return;
  // The two differ when this device still has an old app.js (reopening fixes it), or when the server
  // was updated with git pull but not restarted, so it still runs the old code (restarting fixes it).
  const cmp = compareVersions(v.analyzer, APP_VERSION);
  const hdrNote = cmp > 0 ? `（新しい ${v.analyzer} は開き直すと出ます）`
    : cmp < 0 ? `（サーバーは ${v.analyzer}。再起動が必要）` : "";
  const footNote = cmp > 0 ? `（画面は ${APP_VERSION}。開き直すと新しくなります）`
    : cmp < 0 ? `（画面は ${APP_VERSION}。サーバーを立ち上げ直すと揃います）` : "";
  $("hdr-version").textContent = `v${APP_VERSION} · r${v.recognizer}` + hdrNote;
  $("hdr-version").classList.toggle("old", cmp !== 0);
  $("collect-opt").hidden = $("collect-note").hidden = !v.samples;
  $("version").textContent = `analyzer ${v.analyzer} · recognizer ${v.recognizer}` +
    (v.commit ? ` · ${v.commit}` : "") + footNote;
}).catch(() => {});

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
loadSharedPhoto();

// For checking the app from outside (tools/pi_ui_check.py): the state, and changes made the app's way.
window.BgApp = { get state() { return state; }, update, rolled };
