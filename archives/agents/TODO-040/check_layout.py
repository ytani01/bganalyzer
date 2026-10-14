import json, sys
from playwright.sync_api import sync_playwright
URL = "http://localhost:8765/index.html"
JS = """() => {
 const r = e => { const b = e.getBoundingClientRect(); return {x:b.x,y:b.y,w:b.width,h:b.height}; };
 const tips = document.querySelector('#photo details.tips');
 const pick = document.querySelector('#photo .pick');
 const kids = [...pick.children].filter(e => e.tagName === 'BUTTON' || e.tagName === 'LABEL' || e.tagName==='A').map(e => ({tag:e.tagName,id:e.id,text:e.textContent.trim(),...r(e),sw:e.scrollWidth,cw:e.clientWidth,sh:e.scrollHeight,ch:e.clientHeight}));
 return {tipsBottom: tips.getBoundingClientRect().bottom, pickTop: pick.getBoundingClientRect().top,
  pickChildren:[...pick.children].map(e=>e.tagName+'#'+e.id), kids,
  docSW: document.documentElement.scrollWidth, vw: innerWidth};
}"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/chromium")
    for w, h in [(390, 844), (1024, 768)]:
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(URL); pg.wait_for_timeout(500)
        print(w, json.dumps(pg.evaluate(JS), ensure_ascii=False, indent=1))
        pg.screenshot(path=f"archives/agents/TODO-040/photo-{w}.png")
        if w == 390:
            pg.click("#manual"); pg.wait_for_timeout(300)
            print("board visible:", pg.evaluate("() => !document.querySelector('#board').hidden && getComputedStyle(document.querySelector('#board')).display"),
                  "photo hidden:", pg.evaluate("() => document.querySelector('#photo').hidden"))
    b.close()
