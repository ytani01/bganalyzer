"""TODO-124: time from loading samples/screen2.jpg to the corners being decided (cornerGuess != finding)."""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = b.contexts[0].new_page()
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_function("window.BgApp && window.BgScan")
    page.evaluate("""() => {
      window.__t = []; const t0 = () => Math.round(performance.now() - window.__start);
      const orig = BgScan.start;
      BgScan.start = function (...a) { const s = orig.apply(this, a); const push = s.push.bind(s);
        s.push = (ev) => { window.__t.push([t0(), 'push:' + (ev.stage || ev.type || JSON.stringify(Object.keys(ev)))]); return push(ev); };
        const done = s.done.bind(s); s.done = () => { window.__t.push([t0(), 'done-wait']); return done().then(r => { window.__t.push([t0(), 'done']); return r; }); };
        return s; };
      let last = BgApp.state.cornerGuess;
      const poll = () => { const g = BgApp.state.cornerGuess; if (g !== last) { window.__t.push([t0(), 'guess:' + g]); last = g; } requestAnimationFrame(poll); };
      poll();
    }""")
    page.evaluate("window.__start = performance.now()")
    page.set_input_files("#file", "samples/screen2.jpg")
    page.wait_for_function("BgApp.state.cornerGuess !== 'finding' && BgApp.state.cornerGuess !== ''", timeout=60000)
    page.wait_for_timeout(300)
    for r in page.evaluate("window.__t"): print(r)
    page.close()
