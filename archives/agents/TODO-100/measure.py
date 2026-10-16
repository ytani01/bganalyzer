"""TODO-100 の実測: screen1（ダイス 4-2、マネーゲーム）を読み取って解析し、Luck の文と読み上げを記録する。

    uv run -q --no-project --with playwright python archives/agents/TODO-100/measure.py

ローカルホスト（http://127.0.0.1:8000/）の PWA を headless Chromium で 1 回だけ操作する。コードは変えない。
値は page.evaluate でまとめて読み出し、判定は Python 側で行う。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from playwright.sync_api import sync_playwright  # noqa: E402
import pi_ui_check as u  # noqa: E402

# 結果の画面の Luck の行と最善手の見出し、読み上げ（window.__spoken）を読み出す
READ_JS = """
() => ({
  luckLines: [...document.querySelectorAll('p')].map(p => p.textContent.trim()).filter(t => t.startsWith('Luck')),
  moveHeadings: [...document.querySelectorAll('h2')].map(h => h.textContent.trim()).filter(t => t.startsWith('最善手')),
  rolled: BgApp.rolled(),
  luck: BgApp.state.result ? BgApp.state.result.luck : null,
  spoken: window.__spoken,
})
"""

results = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=u.CHROMIUM)
    page = u.open_app(b)
    truth = u.read_photo(page)
    results["truth_home"] = truth["home"]
    results["dice_read"] = page.evaluate("BgApp.rolled()")
    results["match_state"] = page.evaluate("BgApp.state.match")
    u.show_outcome(page)
    page.wait_for_timeout(300)
    results["screen"] = page.evaluate(READ_JS)
    page.click("#speak")
    page.wait_for_timeout(300)
    spoken = page.evaluate("window.__spoken")
    results["spoken"] = spoken
    results["spoken_joined"] = " ".join(spoken)
    results["alerts"] = page.alerts
    b.close()

text = " ".join(results["spoken"])
luck = results["screen"]["luckLines"]
results["checks"] = {
    "luck_line_is_ordinary": bool(luck) and luck[0].endswith("・ふつうの目"),
    "spoken_has_no_目です": "目です" not in text,
    "spoken_has_best_move": "最善手は、" in text,
    "spoken_count": len(results["spoken"]),
}
print(json.dumps(results, ensure_ascii=False, indent=1))
