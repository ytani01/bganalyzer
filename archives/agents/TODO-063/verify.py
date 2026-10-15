"""TODO-063 確認: 版・配色・バーのタップ・手前の色の入れ替え・画面を 1 回ずつ確かめる。
実行: uv run -q --no-project --with playwright python archives/agents/TODO-063/verify.py
サーバーは http://127.0.0.1:8031/ で起動している前提。コードは変えない。
"""
import json, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("/home/ytani/work/bganalyzer/archives/agents/TODO-063")
URL = "http://127.0.0.1:8031/"
BAR_X = 328.0   # B.x0 + 6*B.pw + B.bar/2 = 20 + 288 + 20
MID = 220.0     # (y0 + y1) / 2 = (24 + 416) / 2
WAIT = 30000

# style.css の値（computed は rgb 表記）
EXPECT = {
    "felt": "rgb(47, 107, 79)",
    "tri-a": "rgb(201, 143, 74)",
    "tri-b": "rgb(163, 58, 44)",
    "light": ("rgb(255, 253, 246)", "rgb(51, 51, 51)"),
    "dark": ("rgb(28, 28, 28)", "rgb(216, 216, 216)"),
}

READ = """() => {
  const svg = document.querySelector('#board-svg');
  const cs = (e) => { const s = getComputedStyle(e); return [s.fill, s.stroke]; };
  const circles = [...svg.querySelectorAll('circle')].map((e) => {
    const [fill, stroke] = cs(e);
    return {cx: +e.getAttribute('cx'), cy: +e.getAttribute('cy'), fill, stroke};
  });
  const polys = [...svg.querySelectorAll('polygon')].map((e) => cs(e)[0]);
  const rects = [...svg.querySelectorAll('rect')].map((e) => cs(e)[0]);
  return {circles, polys, rects};
}"""


def read(page):
    return page.evaluate(READ)


def summarise_colours(data):
    pairs = {}
    for c in data["circles"]:
        key = f'{c["fill"]} / {c["stroke"]}'
        pairs[key] = pairs.get(key, 0) + 1
    polys = {}
    for f in data["polys"]:
        polys[f] = polys.get(f, 0) + 1
    felt = sum(1 for f in data["rects"] if f == EXPECT["felt"])
    return {"circles (fill / stroke: count)": pairs, "polygon fills: count": polys,
            "rects with felt fill": felt, "rects total": len(data["rects"])}


def bar_checkers(data):
    white = sorted([c for c in data["circles"] if c["cx"] == BAR_X and c["cy"] < MID], key=lambda c: -c["cy"])
    black = sorted([c for c in data["circles"] if c["cx"] == BAR_X and c["cy"] > MID], key=lambda c: c["cy"])
    return white, black


def tap(page, k, level):
    """tools/ui_snapshot.py の Run.tap と同じ位置の決め方。"""
    hit = page.locator("#board-svg .hit").nth(k)
    top = k < 12 or k == 24
    f = (level - 0.5) * 38 / 196
    if k >= 24:
        f, top = (9 + (level - 0.5) * 36) / 196, not top
    box = hit.bounding_box()
    hit.click(position={"x": box["width"] / 2, "y": box["height"] * (f if top else 1 - f)})
    page.wait_for_function("document.getElementById('busy').hidden", timeout=WAIT)


def main():
    res = {}
    # 1. 版
    with urllib.request.urlopen(URL + "version", timeout=10) as r:
        res["version_api"] = json.load(r)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/usr/bin/chromium")
        ctx = br.new_context(viewport={"width": 412, "height": 915})
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        page.goto(URL)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        res["header_version"] = page.inner_text("#hdr-version").strip()

        page.click("#manual")
        page.wait_for_function("document.getElementById('busy').hidden", timeout=WAIT)
        page.wait_for_selector("#board-svg .hit")

        # 2. 色（初期の盤）
        d0 = read(page)
        res["2_colours_before"] = summarise_colours(d0)
        w0, b0 = bar_checkers(d0)
        res["bar_before"] = {"white": len(w0), "black": len(b0)}

        # 3. バーのタップ: 上半分(k=24) level 2 → 手前 2 個、下半分(k=25) level 1 → 奥 1 個
        tap(page, 24, 2)
        d1 = read(page)
        w1, b1 = bar_checkers(d1)
        res["3_bar_white_after_level2"] = {"count": len(w1), "cy": [c["cy"] for c in w1],
                                          "fill_stroke": [[c["fill"], c["stroke"]] for c in w1]}
        tap(page, 25, 1)
        d2 = read(page)
        w2, b2 = bar_checkers(d2)
        res["3_bar_black_after_level1"] = {"count": len(b2), "cy": [c["cy"] for c in b2],
                                          "fill_stroke": [[c["fill"], c["stroke"]] for c in b2]}
        res["3_bar_white_still"] = {"count": len(w2), "cy": [c["cy"] for c in w2]}
        res["3_bar_text_stack_n"] = page.evaluate(
            "() => [...document.querySelectorAll('#board-svg .stack-n')].map((e) => e.textContent)")

        br.close()

    # 4. 手前の色の入れ替え: bottomColour の設定は四隅の画面にしか無いので、写真を読ませて盤を出す
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/usr/bin/chromium")
        ctx = br.new_context(viewport={"width": 412, "height": 915})
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        page.goto(URL)
        page.wait_for_function("document.querySelector('#hdr-version').textContent.trim() !== ''")
        page.set_input_files("#file", str(Path("/home/ytani/work/bganalyzer/samples/screen1.png")))
        page.wait_for_function("!document.getElementById('corners').hidden && document.getElementById('busy').hidden", timeout=WAIT)
        page.wait_for_function("!/探しています/.test(document.getElementById('corner-help').textContent)", timeout=WAIT)
        page.locator('.seg[data-name="homePick"] [data-value="left"]').click()
        page.locator('.seg[data-name="bottomColour"] [data-value="1"]').click()
        page.click("#recognize")
        page.wait_for_function("!document.getElementById('board').hidden && document.getElementById('busy').hidden", timeout=WAIT)
        page.wait_for_selector("#board-svg .hit")
        page.locator('.seg[data-name="photoView"] [data-value="off"]').click() if page.locator('.seg[data-name="photoView"]').count() else None
        page.wait_for_function("document.getElementById('busy').hidden", timeout=WAIT)
        tap(page, 24, 2)
        tap(page, 25, 1)
        dA = read(page)
        wA, bA = bar_checkers(dA)
        res["4_colours_before_swap"] = summarise_colours(dA)
        res["4_bar_before_swap"] = {"white": [[c["fill"], c["stroke"]] for c in wA], "black": [[c["fill"], c["stroke"]] for c in bA]}
        # 盤の画面から四隅の画面へ戻り、手前の色を入れ替えて、もう一度盤を開く
        page.click("#back")
        page.wait_for_function("!document.getElementById('corners').hidden && document.getElementById('busy').hidden", timeout=WAIT)
        seg = page.locator('.seg[data-name="bottomColour"]')
        cur = seg.locator(".on").get_attribute("data-value")
        values = seg.locator("[data-value]").evaluate_all("els => els.map((e) => e.dataset.value)")
        other = [v for v in values if v != cur][0]
        res["4_seg"] = {"current": cur, "clicked": other}
        seg.locator(f'[data-value="{other}"]').click()
        page.click("#to-board")
        page.wait_for_function("!document.getElementById('board').hidden && document.getElementById('busy').hidden", timeout=WAIT)
        page.wait_for_selector("#board-svg .hit")
        dB = read(page)
        wB, bB = bar_checkers(dB)
        res["4_colours_after_swap"] = summarise_colours(dB)
        res["4_bar_after_swap"] = {"white": [[c["fill"], c["stroke"]] for c in wB], "black": [[c["fill"], c["stroke"]] for c in bB]}

        # 5. 画面（バーに駒がある状態）
        page.screenshot(path=str(OUT / "board.png"))
        br.close()

    # 照合
    checks = {}
    for name, d in (("manual_before_swap", d2), ("photo_before_swap", dA), ("photo_after_swap", dB)):
        allowed = {EXPECT["light"], EXPECT["dark"]}
        checks[f"circles_{name}_are_light_or_dark"] = all((c["fill"], c["stroke"]) in allowed for c in d["circles"])
        checks[f"polys_{name}_are_tri_a_or_b"] = all(f in (EXPECT["tri-a"], EXPECT["tri-b"]) for f in d["polys"])
    checks["bar_white_before_is_light"] = (w2[0]["fill"], w2[0]["stroke"]) == EXPECT["light"]
    checks["bar_black_before_is_dark"] = (b2[0]["fill"], b2[0]["stroke"]) == EXPECT["dark"]
    checks["swap_white_bar_light_to_dark"] = (wA[0]["fill"], wA[0]["stroke"]) == EXPECT["light"] and (wB[0]["fill"], wB[0]["stroke"]) == EXPECT["dark"]
    checks["swap_black_bar_dark_to_light"] = (bA[0]["fill"], bA[0]["stroke"]) == EXPECT["dark"] and (bB[0]["fill"], bB[0]["stroke"]) == EXPECT["light"]
    res["checks"] = checks
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
