from playwright.sync_api import sync_playwright
URL="http://127.0.0.1:8011/"
def vis(p,s): return p.is_visible(s)
def S(p): return p.evaluate("JSON.stringify({sheet:BgApp.state.sheet,dice:BgApp.state.dice,cube:BgApp.state.cube})")
def tap(p,k):
    pr=p.evaluate(f"(()=>{{const r=document.querySelector('#board-svg [data-part=\"{k}\"]').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]}})()"); p.mouse.click(*pr); p.wait_for_timeout(300)
def die(p,n,i): p.click(f"#die{n} button >> nth={i}"); p.wait_for_timeout(300)
def open_(p,k): 
    if not vis(p,f"#sheet-{k}"): tap(p,k)
    assert vis(p,f"#sheet-{k}"),k
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path="/usr/bin/chromium")
    def fresh():
        c=b.new_context(viewport={"width":390,"height":844}); p=c.new_page()
        p.goto(URL); p.evaluate("localStorage.setItem('collect','off')"); p.goto(URL); p.wait_for_selector("#manual"); p.click("#manual"); p.wait_for_timeout(500); return p
    print("die buttons per die:",fresh().locator("#die1 button").count())
    p=fresh()
    tap(p,"cube"); p.click('#sheet-cube [data-value="black"]'); p.wait_for_timeout(300); print("a cube black -> sheet-cube visible:",vis(p,"#sheet-cube"))
    tap(p,"match"); n=p.locator("#match-length option").count(); p.select_option("#match-length",index=2); p.wait_for_timeout(300); print("a match length -> visible:",vis(p,"#sheet-match"),"options",n)
    tap(p,"roll"); die(p,1,3); print("a die1 -> visible:",vis(p,"#sheet-roll"),S(p)); die(p,2,1); print("a die2 -> visible:",vis(p,"#sheet-roll"),S(p))
    # b
    p=fresh(); tap(p,"roll"); die(p,1,3); print("b half:",S(p),"open",vis(p,"#sheet-roll"))
    p.click("#sheet-roll .sheet-close"); p.wait_for_timeout(300)
    tap(p,"cube"); p.click('#sheet-cube [data-value="centre"]'); p.wait_for_timeout(300); print("b centre -> cube visible:",vis(p,"#sheet-cube"))
    # c
    p=fresh(); tap(p,"cube"); p.click('#sheet-cube [data-value="white"]'); p.wait_for_timeout(300)
    print("c white: sheet-cube",vis(p,"#sheet-cube"),"offered",p.is_checked("#cube-offered"),"cube-side",vis(p,"#cube-side"))
    tap(p,"roll"); print("c roll open:",vis(p,"#sheet-roll"),"dice-row",vis(p,"#dice-row"),"die1 visible",vis(p,"#die1"),S(p))
    print("c selected buttons:",p.evaluate("[...document.querySelectorAll('#die1 button,#die2 button')].filter(e=>e.classList.contains('on')||e.getAttribute('aria-pressed')=='true'||e.classList.contains('active')).length"))
    die(p,1,2); print("c die1 -> offered",p.is_checked("#cube-offered"),"open",vis(p,"#sheet-roll"),S(p))
    die(p,2,4); print("c die2 -> open",vis(p,"#sheet-roll"),S(p))
    # d
    p=fresh(); p.click("#analyze"); p.wait_for_function("document.querySelector('#title').innerText!='盤面の確認/修正'",timeout=90000); p.wait_for_timeout(800)
    before=p.inner_text("#result") if p.query_selector("#result") else p.inner_text("main")
    tap(p,"roll"); die(p,1,0); print("d die1 open",vis(p,"#sheet-roll"))
    die(p,2,1); print("d die2 open",vis(p,"#sheet-roll"),S(p))
    seen=False
    for _ in range(200):
        if vis(p,"#reanalyzing"): seen=True; break
        p.wait_for_timeout(50)
    print("d #reanalyzing appeared:",seen,p.inner_text("#reanalyzing") if seen else "")
    try: p.wait_for_selector("#reanalyzing",state="hidden",timeout=90000); print("d reanalyzing gone")
    except Exception as e: print("d still shown",e)
    after=p.inner_text("#result") if p.query_selector("#result") else p.inner_text("main")
    print("d result changed:",before!=after, "| title",p.inner_text("#title"))
    print("d dice now",S(p))
    b.close()
