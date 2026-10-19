// Offline shell: cache the app files; API calls always go to the network.
const CACHE = "bganalyzer-v61";
const SHARE_CACHE = "bganalyzer-share";   // a photo shared from another app, until app.js picks it up
const SHARE_KEY = "shared-photo";
const SHELL = ["./", "index.html", "style.css", "app.js", "board.js", "board-view.js", "corners-view.js", "api.js", "photo.js", "scan.js", "history.js", "moves.js", "cube.js", "sample.js", "result.js", "manifest.webmanifest", "icon.svg", "icon-192.png", "icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL.map((u) => new Request(u, { cache: "no-cache" })))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE && k !== SHARE_CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// Network first so a new version shows up at once; the cache is the fallback when offline.
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method === "POST" && url.href === new URL("share-target", self.registration.scope).href) {
    e.respondWith(receiveShare(e.request));
    return;
  }
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  // the spoken sentences (TODO-111): one per request, not kept (they would pile up, and offline the
  // fallback below would answer with another sentence's voice)
  if (url.href.startsWith(new URL("speech", self.registration.scope).href)) return;
  // no-cache: ask the server even when the browser's own cache thinks its copy is fresh
  e.respondWith(fetch(e.request, { cache: "no-cache" })
    .then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); }
      return res;
    })
    .catch(() => caches.match(e.request, { ignoreSearch: true })));
});

// Android's share sheet (manifest share_target) posts the photo here. Keep it on the phone and
// open the app, which loads it like a picked photo; the server never sees this request.
async function receiveShare(request) {
  try {
    const file = (await request.formData()).get("photo");
    if (file && typeof file !== "string") {
      const cache = await caches.open(SHARE_CACHE);
      await cache.put(SHARE_KEY, new Response(file, { headers: {
        "Content-Type": file.type || "image/jpeg",
        "X-File-Name": encodeURIComponent(file.name || "shared.jpg"),
      } }));
    }
  } catch (_) { /* the app opens without a photo */ }
  return Response.redirect(new URL("./?shared=1", self.registration.scope).href, 303);
}
