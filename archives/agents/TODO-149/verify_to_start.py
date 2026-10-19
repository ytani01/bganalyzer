import sys
from playwright.sync_api import sync_playwright
URL="http://127.0.0.1:8011/"
SAMPLE=sys.argv[1]
def st(p,l):
    t=p.inner_text("#title"); v=p.is_visible("#to-start")
    print(f"{l}: title={t!r} to-start_visible={v}"); return t,v
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path="/usr/bin/chromium")
    def fresh():
        c=b.new_context(viewport={"width":390,"height":844}); p=c.new_page()
        p.goto("about:blank"); p.goto(URL); p.wait_for_selector("#title"); return p
    p=fresh(); st(p,"1 photo (expect hidden)")
    p.set_input_files("#file",SAMPLE); p.wait_for_function("document.querySelector('#title').innerText!='写真の選択'",timeout=30000); p.wait_for_timeout(500)
    st(p,"2 corners (expect hidden)")
    p.click("#recognize")
    p.wait_for_function("document.querySelector('#title').innerText!='四隅の調整'",timeout=90000); p.wait_for_timeout(500)
    st(p,"3 board from photo (expect visible)")
    p=fresh(); p.click("#manual"); p.wait_for_timeout(500); st(p,"4 manual board (expect hidden)")
    p.click("#analyze"); p.wait_for_function("document.querySelector('#title').innerText!='盤面の確認/修正'",timeout=90000); p.wait_for_timeout(500)
    st(p,"5 result (expect visible)")
    p.click("#back"); p.wait_for_timeout(500); st(p,"6 back to manual board (expect hidden)")
    b.close()
