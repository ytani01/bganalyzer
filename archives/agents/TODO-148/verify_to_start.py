import sys
from playwright.sync_api import sync_playwright
URL="http://127.0.0.1:8011/"
SAMPLE=sys.argv[1]
def st(p,l):
    t=p.inner_text("#title"); v=p.is_visible("#to-start")
    print(f"{l}: title={t!r} to-start_visible={v} url={p.url}"); return t,v
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path="/usr/bin/chromium")
    def fresh():
        c=b.new_context(viewport={"width":390,"height":844}); p=c.new_page()
        p.goto("about:blank"); p.goto(URL); p.wait_for_selector("#title"); return p
    p=fresh(); st(p,"a photo")
    # b
    p.set_input_files("#file",SAMPLE); p.wait_for_function("document.querySelector('#title').innerText!='写真の選択'",timeout=30000)
    st(p,"b corners")
    bb=p.locator("#back").bounding_box(); ts=p.locator("#to-start").bounding_box(); print("back",bb,"to-start",ts,"right_of_back",ts["x"]>=bb["x"]+bb["width"])
    p.click("#to-start"); st(p,"b after click")
    p.go_back(); p.wait_for_timeout(500); print("b after go_back url=",p.url)
    # c
    p=fresh(); p.click("#manual"); p.wait_for_timeout(500); st(p,"c board")
    p.click("#to-start"); st(p,"c after click")
    p.go_back(); p.wait_for_timeout(500); print("c after go_back url=",p.url)
    # d
    p=fresh(); p.click("#manual"); p.wait_for_timeout(500); st(p,"d board")
    p.click("#analyze"); p.wait_for_selector("#to-start:visible",timeout=5000)
    p.wait_for_function("document.querySelector('#title').innerText!='盤面'",timeout=90000); p.wait_for_timeout(500)
    st(p,"d result")
    p.click("#to-start"); st(p,"d after click")
    p.go_back(); p.wait_for_timeout(500); print("d after go_back url=",p.url)
    b.close()
