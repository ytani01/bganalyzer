import json
from playwright.sync_api import sync_playwright
out = {}
def vis(p, sel): return p.evaluate("s=>{const e=document.querySelector(s);return !!e&&!e.hidden&&e.getClientRects().length>0}", sel)
def box(p, sel): return p.evaluate("s=>{const r=document.querySelector(s).getBoundingClientRect();return {top:r.top,bottom:r.bottom,left:r.left,right:r.right}}", sel)
def st(p): return p.evaluate("()=>({home:BgApp.state.home,bc:BgApp.state.bottomColour,sheet:BgApp.state.sheet,step:BgApp.state.step,match:BgApp.state.match,cube:BgApp.state.cube,dice:BgApp.state.dice,onRoll:BgApp.state.onRoll})")
def sheets(p): return {k: vis(p, "#sheet-"+k) for k in ("match","cube","roll")}
def tap(p, kind): p.locator(f'#board-svg [data-part="{kind}"]').first.click()
with sync_playwright() as pw:
    b = pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
    p = b.contexts[0].pages[0]
    out["initial"] = st(p); out["ls"] = p.evaluate("()=>({...localStorage})")
    p.reload(); p.wait_for_function("document.querySelector('#hdr-version').textContent.trim()!==''")
    out["version"] = p.inner_text("#hdr-version")
    p.click("#manual"); p.wait_for_function("BgApp.state.step==='board'")
    out["start"] = st(p)
    out["parts"] = p.evaluate("()=>[...document.querySelectorAll('#board-svg [data-part]')].map(e=>e.dataset.part)")
    # 1 home / colour
    h0 = st(p)["home"]; svg0 = p.inner_html("#board-svg")
    tap(p,"home"); out["home"] = [h0, st(p)["home"], svg0 != p.inner_html("#board-svg")]
    tap(p,"home"); out["home_back"] = st(p)["home"]
    c0 = st(p)["bc"]; tap(p,"colour"); out["colour"] = [c0, st(p)["bc"]]
    tap(p,"colour"); out["colour_back"] = st(p)["bc"]
    # sheets
    for k in ("match","cube","roll"):
        tap(p,k); out["sheet_"+k] = sheets(p)
        if k=="match":
            p.select_option("#match-length","5"); out["match_after"] = [st(p)["match"], p.text_content("#board-svg")[:200]]
            out["sheet_bottom_vs_actbar"] = [box(p,"#sheet-match")["bottom"], box(p,"#actbar")["top"]]
            out["analyze_enabled"] = p.evaluate("()=>{const e=document.querySelector('#analyze');return {disabled:e.disabled}}")
            out["analyze_clickable"] = p.evaluate("()=>{const r=document.querySelector('#analyze').getBoundingClientRect();const e=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return e===document.querySelector('#analyze')||document.querySelector('#analyze').contains(e)}")
            p.select_option("#match-length","0")
        if k=="cube":
            p.click('#sheet-cube [data-name=cubeAt] [data-value=white]'); out["cube_after"] = [st(p)["cube"], p.text_content("#board-svg")[:100]]
            p.click('#sheet-cube [data-name=cubeAt] [data-value=centre]')
        if k=="roll":
            p.select_option("#die1","3"); p.select_option("#die2","5"); out["dice_after"] = [st(p)["dice"], p.text_content("#board-svg")[:100]]
            p.select_option("#die1",""); p.select_option("#die2","")
        p.locator(f"#sheet-{k} .sheet-close").click(); out["closed_"+k] = sheets(p)
    # 3 leave with sheet open
    tap(p,"cube"); p.click("#back"); p.wait_for_function("BgApp.state.step!=='board'")
    out["left"] = [st(p)["step"], st(p)["sheet"]]
    p.click("#manual"); p.wait_for_function("BgApp.state.step==='board'")
    out["returned"] = [st(p)["sheet"], sheets(p)]
    # 4 unlimited + empty dice
    out["unlimited_text"] = "アンリミテッド" in p.text_content("#board-svg")
    out["dice_q"] = p.evaluate("()=>[...document.querySelectorAll('#board-svg .die-q')].length")
    out["dashed"] = p.evaluate("()=>[...document.querySelectorAll('#board-svg .die-q')].map(e=>e.textContent)")
    # 5 persistence
    c0 = st(p)["bc"]; tap(p,"colour"); c1 = st(p)["bc"]
    p.reload(); p.wait_for_function("document.querySelector('#hdr-version').textContent.trim()!==''")
    p.click("#manual"); p.wait_for_function("BgApp.state.step==='board'")
    out["persist"] = [c0, c1, st(p)["bc"]]
    if st(p)["bc"] != c0: tap(p,"colour")
    out["persist_restored"] = st(p)["bc"]
    # 6
    out["result_parts"] = p.evaluate("()=>document.querySelectorAll('#result-svg [data-part], #photo-svg [data-part]').length")
    out["home_pick_board_screen"] = p.evaluate("()=>!!document.querySelector('#home-pick')")
    out["home_pick_all_dom"] = p.evaluate("()=>document.querySelectorAll('#home-pick').length")
    print(json.dumps(out, ensure_ascii=False, indent=1))
