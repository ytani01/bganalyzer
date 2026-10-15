// The server (analyzer/app.py). Paths are relative ("analyze"), so the app also works under a path
// such as /bg/; ?api=URL points it at another server.
"use strict";

const BgApi = (() => {
  const BASE = (new URLSearchParams(location.search).get("api") || "").replace(/\/$/, "");
  const url = (path) => (BASE ? `${BASE}/${path}` : path);

  async function failure(res) {
    let data = null;
    try { data = await res.json(); } catch (_) { /* not JSON */ }
    const d = data && data.detail;
    return new Error(typeof d === "string" ? d : `HTTP ${res.status}`);
  }

  async function post(path, body, headers) {
    const res = await fetch(url(path), { method: "POST", body, headers });
    if (!res.ok) throw await failure(res);
    try { return await res.json(); } catch (_) { return null; }
  }

  const postJson = (path, obj) => post(path, JSON.stringify(obj), { "content-type": "application/json" });

  // POST asking for the answer in stages (NDJSON lines, {"stage": ...}): onStage(ev) for each stage
  // as it arrives, and the result of the last line ({"stage": "done", "result"}), marked streamed.
  // A server that answers with plain JSON (an older one) gives that JSON, unmarked.
  async function postStages(path, body, onStage) {
    body.append("stream", "true");
    const res = await fetch(url(path), { method: "POST", body });
    if (!res.ok) throw await failure(res);
    const type = res.headers.get("content-type") || "";
    if (!type.includes("ndjson") || !res.body) {
      try { return await res.json(); } catch (_) { return null; }
    }
    const reader = res.body.getReader(), dec = new TextDecoder();
    let buf = "", result = null;
    const take = (line) => {
      if (!line.trim()) return;
      const ev = JSON.parse(line);
      if (ev.stage === "error") throw new Error(typeof ev.detail === "string" ? ev.detail : "読み取りに失敗しました");
      if (ev.stage === "done") result = { ...ev.result, streamed: true };
      else onStage(ev);
    };
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let k;
      while ((k = buf.indexOf("\n")) >= 0) { take(buf.slice(0, k)); buf = buf.slice(k + 1); }
    }
    take(buf + dec.decode());
    if (!result) throw new Error("読み取りの途中で接続が切れました");
    return result;
  }

  // Image px of a sent image -> of the photo (the sent image was the photo scaled by `scale`), for
  // the parts of a geometry (/analyze-photo's, or a stage of the reading or of /find-corners) in px.
  function scaleGeometry(g, scale) {
    const p = ([x, y]) => [x / scale, y / scale];
    const out = { ...g };
    if (g.corners) out.corners = g.corners.map(p);
    if (g.tips) out.tips = g.tips.map(p);
    if (g.checkers) out.checkers = g.checkers.map(([x, y, r, side]) => [x / scale, y / scale, r / scale, side]);
    if (g.counts) out.counts = g.counts.map((c) => ({ ...c, at: p(c.at) }));
    if (g.dice) out.dice = g.dice.map((d) => ({ ...d, quad: d.quad.map(p) }));
    if (g.cube) out.cube = { ...g.cube, quad: g.cube.quad.map(p) };
    if (g.lines) out.lines = g.lines.map((l) => l.map(p));
    if (g.quads) out.quads = g.quads.map((q) => q.map(p));
    return out;
  }

  async function version() {
    const res = await fetch(url("version"));
    return res.ok ? res.json() : null;
  }

  return { post, postJson, postStages, scaleGeometry, version };
})();
