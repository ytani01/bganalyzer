"""TODO-123 check. BG_CDP=http://127.0.0.1:9222 uv run -q --no-project --with playwright python this.py"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8001/"
IMG = "/home/ytani/work/bganalyzer/samples/collected-2aunci.jpg"
JS = """ids => Object.fromEntries(ids.map(i => { const e = document.querySelector(i); const r = e.getBoundingClientRect();
  return [i, {top: +r.top.toFixed(1), left: +r.left.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1), right: +r.right.toFixed(1)}] }))"""

def rows(page, ids, label):
    d = page.evaluate(JS, ids)
    print(label)
    for k, v in d.items(): print("  ", k, v)
    tops = {v["top"] for v in d.values()}
    print("  -> distinct tops:", sorted(tops), "SAME ROW" if len(tops) == 1 else "DIFFERENT ROWS")

def game(page, label):
    ids = ["#match-length", "#score-white", "#score-black"]
    for n in ("3", "25", "0"):
        page.select_option("#match-length", n)
        page.wait_for_timeout(200)
        t = page.evaluate("(()=>{const e=document.querySelector('#match-length');return [e.selectedOptions[0].text,e.scrollWidth,e.clientWidth]})()")
        print("  select text/scrollW/clientW:", t)
        if n == "0":
            print("  score hidden:", page.evaluate("document.querySelector('#match-score').hidden"))
            rows(page, ["#match-length"], label + " 長さ=アンリミテッド")
            continue
        rows(page, ids, label + " 長さ=" + n + " 0-0")
        page.select_option("#score-white", str(int(n) - 1))
        page.wait_for_timeout(200)
        print("  crawford hidden:", page.evaluate("document.querySelector('#crawford-opt').hidden"))
        rows(page, ids + ["#crawford-opt"], label + " 長さ=" + n + " 白=" + str(int(n) - 1))
        print("  vw", page.evaluate("document.documentElement.clientWidth"), "scrollW", page.evaluate("document.documentElement.scrollWidth"))
        page.select_option("#score-white", "0")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(os.environ["BG_CDP"])
    page = browser.contexts[0].new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(URL)
    page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
    print("4. version:", page.evaluate("document.querySelector('#hdr-version').textContent.trim()"))
    page.set_input_files("#file", IMG)
    page.wait_for_function("BgApp.state.cornerGuess !== 'finding' && BgApp.state.cornerGuess !== ''", timeout=60000)
    page.wait_for_timeout(500)
    print("viewport", page.evaluate("innerWidth"), "step", page.evaluate("BgApp.state.step"))
    rows(page, ["#edit-left", "#edit-right", "#edit-start"], "1. 回転の行")
    print("claude hidden:", page.evaluate("document.querySelector('#claude-corners').hidden"))
    rows(page, ["#corner-reset", "#find-again"], "2a. 四隅の行 (Claude 非表示)")
    page.evaluate("document.querySelector('#claude-corners').hidden = false")
    print("button texts:", page.evaluate("['#corner-reset','#find-again','#claude-corners'].map(i=>document.querySelector(i).textContent)"))
    rows(page, ["#corner-reset", "#find-again", "#claude-corners"], "2b. 四隅の行 (Claude の hidden を外す)")
    page.evaluate("document.querySelector('#claude-corners').hidden = true")
    game(page, "3a. 四隅の画面")
    page.click("#recognize")
    page.wait_for_function("BgApp.state.step === 'board'", timeout=90000)
    page.wait_for_timeout(500)
    game(page, "3b. 盤面の画面")
    page.close()
