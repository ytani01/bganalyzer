"""TODO-066 verifier. Server: uv run uvicorn app:app --app-dir analyzer --port 8765
Run: uv run -q --no-project --with playwright python archives/agents/TODO-066/verify.py"""
import json, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
URL = "http://127.0.0.1:8765/"
START = "4HPwATDgc/ABMA"   # initial position id


def post(path, body):
    req = urllib.request.Request(URL + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def fields(r):
    import re
    b = r.post_data_buffer or b""
    if b"form-data" in b[:400]:
        return {k.decode(): v.decode() for k, v in re.findall(rb'name="(match_length|score_white|score_black|crawford)"\r?\n\r?\n([^\r\n]*)', b)}
    return b.decode()[:400]


def api():
    base = {"position_id": START}
    for name, extra in [("money", {}), ("7pt 3-5", dict(match_length=7, score_white=3, score_black=5)),
                        ("crawford 6-4", dict(match_length=7, score_white=6, score_black=4, crawford=True)),
                        ("score>=length 7", dict(match_length=7, score_white=7, score_black=0)),
                        ("crawford, no N-1", dict(match_length=7, score_white=3, score_black=4, crawford=True))]:
        s, d = post("analyze", {**base, **extra})
        if s != 200:
            print("API", name, s, str(d)[:200]); continue
        print("API", name, s, "equity", d.get("equity"), "cube", json.dumps(d.get("cube"), ensure_ascii=False)[:200],
              "match", d.get("match"), "| summary:", d.get("summary_ja", "")[:90])
    # same with dice, 2 numbers, to see equity changes
    for name, extra in [("money", {}), ("7pt 3-5", dict(match_length=7, score_white=3, score_black=5))]:
        s, d = post("analyze", {**base, "dice": [3, 1], **extra})
        print("API dice 3-1", name, s, d.get("equity"), (d.get("moves") or [{}])[0] if s == 200 else d)


def pwa():
    from playwright.sync_api import sync_playwright
    truth = json.loads((ROOT / "samples/screen1.truth.json").read_text())
    synth = json.loads((ROOT / "samples/synth-cube-photo2-16.truth.json").read_text())
    out = {}
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/usr/bin/chromium")
        ctx = br.new_context(viewport={"width": 390, "height": 844}, service_workers="block", reduced_motion="reduce")
        ctx.add_init_script("""window.__fd = []; const f = window.fetch; window.fetch = (u, o) => {
          if (o && o.body instanceof FormData) window.__fd.push([String(u), [...o.body.entries()].filter(([k]) => /match|score|crawford|cube|doubled/.test(k)).map(([k, v]) => k + "=" + v).join("&")]);
          return f(u, o); };""")
        page = ctx.new_page()
        alerts, reqs = [], []
        page.on("dialog", lambda d: (alerts.append(d.message), d.dismiss()))
        page.on("request", lambda r: reqs.append((r.url.rsplit("/", 1)[-1], fields(r))) if r.method == "POST" else None)
        page.goto(URL)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        W = 180000
        busy = lambda: page.wait_for_function("document.getElementById('busy').hidden", timeout=W)  # noqa: E731
        state = lambda: page.evaluate("""() => { const v = (id) => document.getElementById(id);
          const vis = (id) => !!v(id) && !v(id).closest('[hidden]');
          return {step: [...document.querySelectorAll('section.step')].filter(s => !s.hidden).map(s => s.id),
            visible: vis('match-length'), len: v('match-length').value, w: v('score-white').value, b: v('score-black').value,
            scoreShown: vis('score-white'), crawfordShown: vis('crawford'), crawford: v('crawford').checked,
            ls: localStorage.getItem('match')}; }""")
        page.select_option("#match-length", "7")
        page.select_option("#score-white", "3"); page.select_option("#score-black", "5")
        out["photo screen"] = state()
        page.set_input_files("#file", str(ROOT / "samples" / truth["image"]))
        page.wait_for_function("!document.getElementById('corners').hidden && document.getElementById('busy').hidden", timeout=W)
        page.wait_for_function("!/探しています/.test(document.getElementById('corner-help').textContent)", timeout=W)
        out["corners screen"] = state()
        page.click(f'.seg[data-name="homePick"] [data-value="{truth["home"]}"]')
        page.click(f'.seg[data-name="bottomColour"] [data-value="{truth["bottom_colour"]}"]')
        reqs.clear()
        page.click("#recognize")
        page.wait_for_function("!document.getElementById('board').hidden && document.getElementById('busy').hidden", timeout=W)
        out["recognize requests"] = reqs
        out["analyze-photo form"] = page.evaluate("window.__fd")
        out["board screen"] = state()
        # photo request's form fields
        reqs.clear()
        page.click("#analyze"); page.wait_for_function("!document.getElementById('outcome').hidden && document.getElementById('busy').hidden", timeout=W)
        out["outcome screen"] = state()
        out["analyze request"] = [(u, d) for u, d in reqs]
        out["result text (7pt 3-5)"] = page.inner_text("#result")[:300]
        page.screenshot(path=str(ROOT / "archives/agents/TODO-066/outcome.png"), full_page=True)
        out["match bbox"] = page.evaluate("""() => { const r = document.getElementById('match').getBoundingClientRect();
          const kids = [...document.querySelectorAll('#match select, #match label')].filter(e => e.offsetParent)
            .map(e => { const b = e.getBoundingClientRect(); return [e.id || e.textContent.trim(), Math.round(b.x), Math.round(b.y), Math.round(b.right), Math.round(b.bottom)]; });
          return {box: [r.x, r.y, r.right, r.bottom].map(Math.round), vw: innerWidth, scrollW: document.documentElement.scrollWidth, kids}; }""")
        # change on outcome -> reanalyze
        reqs.clear()
        page.select_option("#score-white", "4"); busy()
        page.wait_for_timeout(1500); busy()
        out["change on outcome: requests"] = [(u, d) for u, d in reqs]
        out["change on outcome: result text"] = page.inner_text("#result")[:200]
        # reload
        page.reload(); page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        out["after reload"] = state()
        # back to money
        page.select_option("#match-length", "0")
        out["money"] = state()
        page.reload(); page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        out["money after reload"] = state()
        # crawford + one-sided cube photo
        page.select_option("#match-length", "7")
        page.select_option("#score-white", "6"); page.select_option("#score-black", "4")
        if not page.is_checked("#crawford"):
            page.check("#crawford")
        out["crawford set"] = state()
        page.goto(URL); page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        alerts.clear(); reqs.clear()
        page.set_input_files("#file", str(ROOT / "samples" / synth["image"]))
        page.wait_for_function("!document.getElementById('corners').hidden && document.getElementById('busy').hidden", timeout=W)
        page.wait_for_function("!/探しています/.test(document.getElementById('corner-help').textContent)", timeout=W)
        page.click(f'.seg[data-name="homePick"] [data-value="{synth["home"]}"]')
        page.click(f'.seg[data-name="bottomColour"] [data-value="{synth["bottom_colour"]}"]')
        page.click("#recognize")
        page.wait_for_function("!document.getElementById('board').hidden && document.getElementById('busy').hidden", timeout=W)
        page.wait_for_timeout(800)
        out["crawford+cube: state"] = state()
        out["crawford+cube: photo form"] = page.evaluate("window.__fd")
        out["crawford+cube: alerts"] = list(alerts)
        out["crawford+cube: cube read"] = page.evaluate("() => [document.getElementById('cube-value').value, document.getElementById('cube-side').hidden]")
        br.close()
    for k, v in out.items():
        print("PWA", k, "=", json.dumps(v, ensure_ascii=False))


if __name__ == "__main__":
    api()
    pwa()
