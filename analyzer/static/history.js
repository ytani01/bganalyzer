// Recent photos, kept only on this device (IndexedDB) so one can be picked again later.
// Nothing here goes to the server. Each entry holds the photo (shrunk), a thumbnail, and
// what was chosen for it (corners, home side, colours, the corrected board), newest first.
"use strict";

const PhotoHistory = (() => {
  const DB_NAME = "bganalyzer", STORE = "photos";
  const KEEP = 3;            // older entries are deleted automatically
  const MAX_SIDE = 2048;     // the size the app sends to the server anyway (UPLOAD_MAX)
  const KEEP_AS_IS = { side: 2560, bytes: 1.5e6 };  // small files (screenshots) are stored untouched
  const THUMB_SIDE = 192;

  // Scale that fits w x h within max on its longest side (never enlarges).
  function fitScale(w, h, max) {
    return Math.min(1, max / Math.max(w, h));
  }

  // Ids of the entries beyond the newest `keep`.
  function idsToDrop(entries, keep = KEEP) {
    return entries.slice().sort((a, b) => b.time - a.time).slice(keep).map((e) => e.id);
  }

  let dbPromise = null;
  function db() {
    if (!dbPromise) {
      dbPromise = new Promise((resolve, reject) => {
        if (!self.indexedDB) { reject(new Error("IndexedDB がありません")); return; }
        const req = indexedDB.open(DB_NAME, 1);
        req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: "id" });
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });
      dbPromise.catch(() => { dbPromise = null; });
    }
    return dbPromise;
  }

  async function run(mode, fn) {
    const d = await db();
    return new Promise((resolve, reject) => {
      const tx = d.transaction(STORE, mode);
      const req = fn(tx.objectStore(STORE));
      tx.oncomplete = () => resolve(req && req.result);
      tx.onerror = tx.onabort = () => reject(tx.error);
    });
  }

  function toBlob(image, w, h, scale, quality) {
    const c = document.createElement("canvas");
    c.width = Math.max(1, Math.round(w * scale));
    c.height = Math.max(1, Math.round(h * scale));
    c.getContext("2d").drawImage(image, 0, 0, c.width, c.height);
    return new Promise((res, rej) => c.toBlob((b) => (b ? res(b) : rej(new Error("画像を作れません"))), "image/jpeg", quality));
  }

  async function list() {
    const all = await run("readonly", (s) => s.getAll());
    return (all || []).sort((a, b) => b.time - a.time);
  }

  // Store a newly opened photo. Returns {id, scale}: scale converts the image's pixels
  // to the stored copy's (corners are saved in the stored copy's pixels).
  async function add(file, image, w, h) {
    let blob = file, scale = 1;
    if (Math.max(w, h) > KEEP_AS_IS.side || file.size > KEEP_AS_IS.bytes) {
      scale = fitScale(w, h, MAX_SIDE);
      blob = await toBlob(image, w, h, scale, 0.9);
    }
    const thumb = await toBlob(image, w, h, fitScale(w, h, THUMB_SIDE), 0.7);
    const entry = { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, time: Date.now(), image: blob, thumb };
    await run("readwrite", (s) => s.put(entry));
    const drop = idsToDrop(await list());
    if (drop.length) await run("readwrite", (s) => { drop.forEach((id) => s.delete(id)); });
    return { id: entry.id, scale };
  }

  // Merge fields (corners, board, ...) into an entry; it also becomes the most recent.
  async function update(id, fields) {
    const entry = await run("readonly", (s) => s.get(id));
    if (!entry) return;
    await run("readwrite", (s) => s.put({ ...entry, ...fields, time: Date.now() }));
  }

  const get = (id) => run("readonly", (s) => s.get(id));
  const remove = (id) => run("readwrite", (s) => s.delete(id));

  return { KEEP, fitScale, idsToDrop, list, add, update, get, remove };
})();

if (typeof module !== "undefined") module.exports = PhotoHistory;
