"""TODO-099 の実測: マッチの札と行を盤の絵（#board-svg と #result-svg）で読み出し、読み上げを記録する。

    uv run -q --no-project --with playwright python archives/agents/TODO-099/measure.py

ローカルホスト（http://127.0.0.1:8000/）の PWA を、スマホの代わりに headless Chromium で操作する。
コードは変えない。値は page.evaluate でまとめて読み出し、判定は Python 側で行う。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from playwright.sync_api import sync_playwright  # noqa: E402
import pi_ui_check as u  # noqa: E402

# 盤の絵の部品を読み出す（すべて SVG の user 座標。getBBox の値）
SCENE_JS = """
(sel) => {
  const svg = document.querySelector(sel);
  const bb = (e) => { const b = e.getBBox(); return {x: b.x, y: b.y, w: b.width, h: b.height}; };
  const next = (e) => (e.nextElementSibling ? e.nextElementSibling.textContent : null);
  return {
    viewBox: svg.getAttribute('viewBox'),
    dotTexts: [...svg.querySelectorAll('text')].map(t => t.textContent).filter(s => s.includes('点')),
    matchN: [...svg.querySelectorAll('.match-n')].map(t => ({text: t.textContent, bb: bb(t)})),
    cards: [...svg.querySelectorAll('rect[width="56"]')].map(r => ({text: next(r), bb: bb(r)})),
    pips: [...svg.querySelectorAll('rect[width="96"]')].map(r => ({text: next(r), bb: bb(r)})),
    trays: [...svg.querySelectorAll('rect[width="186"]')].map(r => bb(r)),
    cubes: [...svg.querySelectorAll('g.die')].filter(g => g.querySelector('.cube-num'))
      .map(g => ({text: g.querySelector('.cube-num').textContent, bb: bb(g)})),
  };
}
"""

SPEECH_CHECK = "window.__spoken"


def inter(a, b):
    """Overlap with positive area (touching edges do not count)."""
    return (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
            and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"])


def overlaps(scene):
    """Each score card against the cubes, the PIP cards and the trays."""
    found = []
    for c in scene["cards"]:
        for kind, items in (("cube", scene["cubes"]), ("pip", scene["pips"]), ("tray", [{"bb": t} for t in scene["trays"]])):
            for it in items:
                if inter(c["bb"], it["bb"]):
                    found.append((c["text"], kind, it.get("text")))
    return found


def summarize(scene):
    cx = lambda e: round(e["bb"]["x"] + e["bb"]["w"] / 2, 1)
    return {
        "viewBox": scene["viewBox"],
        "dotTexts": scene["dotTexts"],
        "matchN": [(m["text"], round(m["bb"]["x"], 1), round(m["bb"]["w"], 1), cx(m)) for m in scene["matchN"]],
        "cards": [(c["text"], {k: round(v, 1) for k, v in c["bb"].items()}) for c in scene["cards"]],
        "cubes": [(c["text"], {k: round(v, 1) for k, v in c["bb"].items()}) for c in scene["cubes"]],
        "pips": [(p["text"], {k: round(v, 1) for k, v in p["bb"].items()}) for p in scene["pips"]],
        "trays": [{k: round(v, 1) for k, v in t.items()} for t in scene["trays"]],
        "overlaps": overlaps(scene),
    }


def scene(page, sel):
    return page.evaluate(SCENE_JS, sel)


MATCH = {"length": 7, "white": 6, "black": 3, "crawford": True}
CUBE = {"at": "black", "value": 2}
results = {}

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=u.CHROMIUM)

    # 2: マネーゲーム
    page = u.open_app(b)
    truth = u.read_photo(page)
    results["truth_home"] = truth["home"]
    page.evaluate("BgApp.update({ match: BgCube.fixMatch(null) })")
    page.wait_for_timeout(300)
    results["item2_money"] = summarize(scene(page, "#board-svg"))
    results["item2_alerts"] = page.alerts
    page.close()

    # 3 と 4: 7 点マッチ（クロフォード）、home を実際の側と逆にする
    page = u.open_app(b)
    u.read_photo(page)
    page.evaluate("o => BgApp.update({ match: BgCube.fixMatch(o.match), cube: o.cube })", {"match": MATCH, "cube": CUBE})
    page.wait_for_timeout(300)
    results["item3_home"] = summarize(scene(page, "#board-svg"))
    other = "left" if truth["home"] == "right" else "right"
    page.evaluate("h => BgApp.update({ home: h })", other)
    page.wait_for_timeout(300)
    results["item4_home_other"] = summarize(scene(page, "#board-svg"))
    results["item4_home_other_value"] = other
    results["item3_alerts"] = page.alerts
    page.close()

    # 5: 同じ条件で解析し、結果の盤と読み上げ
    page = u.open_app(b)
    u.read_photo(page)
    # cube {black, 2} は解析で「クロフォードではダブルできません」と断られたので、中央のキューブで測る
    page.evaluate("o => BgApp.update({ match: BgCube.fixMatch(o.match), cube: o.cube })", {"match": MATCH, "cube": {"at": "centre", "value": 1}})
    try:
        u.show_outcome(page)
    except Exception as e:   # 解析が出なかったときは、その時の画面を記録して終える
        results["item5_error"] = str(e).splitlines()[0]
        results["item5_alerts"] = page.alerts
        results["item5_state"] = page.evaluate("""() => ({
            outcomeHidden: document.querySelector('#outcome').hidden,
            busy: document.querySelector('#busy').hidden,
            status: [...document.querySelectorAll('[role=status],.status,#status,#error,.error')].map(e => e.textContent.trim()).filter(Boolean),
            result: !!BgApp.state.result,
            match: BgApp.state.match,
            cube: BgApp.state.cube,
        })""")
        print(json.dumps(results, ensure_ascii=False, indent=1))
        b.close()
        sys.exit(1)
    page.wait_for_timeout(300)
    results["item5_result"] = summarize(scene(page, "#result-svg"))
    page.click("#speak")
    page.wait_for_timeout(300)
    spoken = page.evaluate(SPEECH_CHECK)
    results["item5_spoken"] = spoken
    results["item5_alerts"] = page.alerts
    results["item5_has_match_word"] = [s for s in spoken if "ポイントマッチ" in s or "点" in s]
    page.close()

    b.close()

print(json.dumps(results, ensure_ascii=False, indent=1))
