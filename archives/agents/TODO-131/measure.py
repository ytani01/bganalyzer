# TODO-131: measure the photo screen on a phone-sized context of the live_view browser.
import json, sys, glob
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("/home/ytani/work/bganalyzer")
OUT = ROOT / "archives/agents/TODO-131"
URL = "http://127.0.0.1:8031/"
photos = sorted(glob.glob(str(ROOT / "samples/*.jpg")))[:5]
JS = """() => {
  const list = document.getElementById('history-list');
  const hist = document.getElementById('history');
  const r = hist.getBoundingClientRect();
  return {
    docScrollHeight: document.documentElement.scrollHeight,
    innerHeight: window.innerHeight,
    listClientHeight: list.clientHeight,
    listScrollHeight: list.scrollHeight,
    liCount: list.querySelectorAll('li').length,
    historyVisible: !hist.hidden,
    historyBottom: r.bottom,
    liFirstTop: list.querySelector('li') ? list.querySelector('li').getBoundingClientRect().top : null,
    liFirstHeight: list.querySelector('li') ? list.querySelector('li').getBoundingClientRect().height : null,
    hdrVersion: document.getElementById('hdr-version').textContent,
    step: document.querySelector('section.step:not([hidden])') ? document.querySelector('section.step:not([hidden])').id : null,
  };
}"""
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = browser.new_context(viewport={"width": 412, "height": 848}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_timeout(1500)
    for i, path in enumerate(photos, 1):
        page.set_input_files("#file", path)
        try:
            page.wait_for_function(
                "n => document.querySelectorAll('#history-list li').length >= n", arg=i, timeout=60000)
        except Exception as e:
            print("wait failed at", i, e)
        page.wait_for_timeout(1500)
        page.goto(URL)   # back to the photo screen (reload)
        page.wait_for_timeout(1500)
        print("after", i, "photo(s):", page.evaluate(JS)["liCount"], flush=True)
    m = page.evaluate(JS)
    print(json.dumps(m, ensure_ascii=False, indent=1))
    page.screenshot(path=str(OUT / "photo-screen.png"))
    ctx.close()
