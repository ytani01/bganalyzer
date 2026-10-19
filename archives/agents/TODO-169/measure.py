import json, urllib.request
from playwright.sync_api import sync_playwright
B="http://127.0.0.1:8023/"
def post(body):
    rq=urllib.request.Request(B+"analyze",json.dumps(body).encode(),{"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(rq,timeout=60))
base={"position_id":"4HPwATDgc/ABMA","on_roll":"white"}
cases={"dice":(post({**base,"dice":[3,1]}),[3,1]),"nodice":(post(base),None)}
JS="""([r,d])=>{const box=document.createElement('div');box.id='result';box.className='result';box.innerHTML=BgResult.html(r,d);document.body.prepend(box);
const rect=e=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height].map(v=>Math.round(v*10)/10)};
const hs=[...box.querySelectorAll('h3')].map(h=>({text:h.textContent,rect:rect(h),fs:getComputedStyle(h).fontSize,color:getComputedStyle(h).color,next:h.nextElementSibling.tagName+'.'+h.nextElementSibling.className,nextRect:rect(h.nextElementSibling),prev:h.previousElementSibling&&h.previousElementSibling.tagName,prevRect:h.previousElementSibling&&rect(h.previousElementSibling),sw:h.scrollWidth,cw:h.clientWidth}));
return {h2:[...box.querySelectorAll('h2')].map(e=>e.textContent),h3:hs,box:rect(box),docW:document.documentElement.scrollWidth}}"""
with sync_playwright() as p:
    br=p.chromium.launch(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
    for k,(r,d) in cases.items():
        pg=br.new_page(viewport={"width":390,"height":844})
        pg.goto(B); pg.wait_for_function("typeof BgResult!=='undefined'")
        out=pg.evaluate(JS,[r,d]); print(k,json.dumps(out,ensure_ascii=False,indent=1))
        if k=="dice":
            pg.locator("#result").first.screenshot(path="archives/agents/TODO-169/result-dice.png")
    br.close()
