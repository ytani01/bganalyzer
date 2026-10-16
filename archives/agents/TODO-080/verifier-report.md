# TODO-080 verifier 報告

## 結果
- 8010 で uvicorn 起動（PID 383898）、確認後に kill 済み（pgrep で残りなしを確認）。8000 は触っていない。
- `uv run pytest analyzer/test_pwa.py`: 18 passed（終了コード 0 と読む。出力末尾 "18 passed"）。
- `ui_snapshot.py record ... manual`: 最後まで通った（"37 snapshots"、rc=0）。"home left" の段が記録されている（JSON 内に文字列あり）。
- 変更ファイル（main との差分）: TODO.md, analyzer/README.md, analyzer/app.py（0.47.0）, analyzer/static/app.js（APP_VERSION 0.47.0）, analyzer/static/index.html, recognizer/README.md, tools/ui_snapshot.py。未追跡: archives/agents/TODO-080/。いずれも項目の範囲と読める（recognizer/README.md の中身は見ていない）。

## 画面3の操作（Playwright, /usr/bin/chromium, 390x844, 手入力の初期配置）
読み取り手段: state はモジュール内なので #board-svg のラベル（text）と circle の座標、`.seg[data-name="home"] .on`。
- a 最初: .on = right。ラベル 上段 13..24 が x=44..612 の左→右、下段 12..1。circle 30 個。
- b 同じ側（right）を押す: svg の innerHTML が a と完全一致、.on = right。変化なし。
- c 反対側（left）を押す: .on = left。ラベルが逆（上段 24..13、下段 1..12）。**駒の circle の x 分布は a と同一**（x=44:10, 236:6, 372:10, 612:4）。
- d right を押し直す: svg innerHTML が a と完全一致、.on = right。
- 画面2: 「自動/左/右」（homePick）のボタンは DOM に 3 つ残っている（画面3では非表示）。

## 食い違いに見えるもの（実害は未確認）
- c で「駒の見た目の位置は左右反転」は確認できなかった。ポイント番号の付き方は逆になったが、circle の位置は a と同じだった。初期配置が左右対称で、鏡写しにしても見た目の駒の位置が変わらないためと推測（推測。非対称な盤面では確かめていない）。
- 手入力の流れでは home-note は hidden のため、文言は読めていない。写真由来の流れ（文言の「手前のホーム」への変更）は確かめていない。
