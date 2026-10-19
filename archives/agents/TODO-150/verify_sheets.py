from playwright.sync_api import sync_playwright
URL="http://127.0.0.1:8011/"
R="""(sel)=>{const e=document.querySelector(sel);if(!e||e.hidden)return null;const r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom].map(x=>Math.round(x*10)/10)}"""
def rect(p,s): return p.evaluate(R,s)
def ov(a,b): return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
def tap(p,k):
    pr=p.evaluate(R,f'#board-svg [data-part="{k}"]'); p.mouse.click((pr[0]+pr[2])/2,(pr[1]+pr[3])/2); p.wait_for_timeout(400)
def check(p,k,label):
    pr=rect(p,f'#board-svg [data-part="{k}"]'); sh=rect(p,f"#sheet-{k}")
    if not sh: print(label,k,"SHEET HIDDEN","part",pr); return
    W,H=p.evaluate("[innerWidth,innerHeight]"); ab=p.evaluate("document.querySelector('#actbar').offsetHeight")
    gap=pr[1]-sh[3] if sh[3]<=pr[1] else sh[1]-pr[3]
    ok=(not ov(pr,sh)) and gap<=20 and gap>=0 and sh[0]>=0 and sh[2]<=W and sh[1]>=0 and sh[3]<=H-ab
    print(label,k,"OK" if ok else "NG","part",pr,"sheet",sh,"gap",round(gap,1),"limit",(W,H-ab))
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path="/usr/bin/chromium")
    def fresh():
        c=b.new_context(viewport={"width":390,"height":844}); p=c.new_page()
        p.goto(URL); p.evaluate("localStorage.setItem('collect','off')"); p.goto(URL); p.wait_for_selector("#manual"); p.click("#manual"); p.wait_for_timeout(500); return p
    p=fresh(); p.click("#analyze")
    p.wait_for_function("document.querySelector('#title').innerText!='盤面の確認/修正'",timeout=90000); p.wait_for_timeout(800)
    print("title",p.inner_text("#title"))
    for k in ["match","cube","roll"]:
        tap(p,k); check(p,k,"a"); 
        if k=="roll": p.screenshot(path="archives/agents/TODO-150/roll-outcome.png")
        p.click(f"#sheet-{k} .sheet-close"); p.wait_for_timeout(300)
    p=fresh(); tap(p,"cube")
    for v in ["white","black"]:
        p.click(f'#sheet-cube [data-name="cubeAt"] [data-value="{v}"]'); p.wait_for_timeout(500)
        pr=rect(p,'#board-svg [data-part="cube"]'); sh=rect(p,"#sheet-cube")
        print("b",v,"overlap" if ov(pr,sh) else "no-overlap","part",pr,"sheet",sh)
    b.close()
