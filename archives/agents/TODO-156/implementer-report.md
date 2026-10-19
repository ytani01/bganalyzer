# TODO-156 implementer 報告

## 変更点
- `analyzer/static/board-view.js`: `drawCube` で、`BgCube.offered(cube)` のとき、キューブを列の端でなく、ダブルされた人（`cube.at`）の側の盤面の中央（`drawDice` と同じ場所）に描く。`fieldCx` を足し、`drawDice` と共用。ダブルされていないとき（持ち主あり・中央）の描き方、`cube` のタップ（`tapPart`）、Crawford の描き方は変えていない。
- `analyzer/app.py`・`analyzer/static/app.js`: analyzer を 0.87.0 → 0.88.0。
- `TODO.md`: 実装と版の 2 項目にチェック（ローカルの行は未チェック）。

## 確かめたこと
- `uv run pytest analyzer/test_pwa.py -q` → 32 passed。
- live_view のブラウザ（CDP 9222）で、この作業ツリーのサーバー（8156）を開き、`BgBoardView.draw` を home=right で 3 通り呼んで `g.die` の位置を読んだ。
  - 黒がダブルされた（白が振る）: ダイス `?` は右の場 x=452,498、キューブ 4 は左の場 x=144,y=200（盤の中央の高さ）。
  - 白がダブルされた（黒が振る）: ダイス `?` は左の場 x=124,170、キューブ 4 は右の場 x=472,y=200。
  - ダブルされていない（白が持ち主）: キューブ 4 は列の端 x=658,y=382（従来どおり）。
- 画像での確認は verifier に任せた（私は数値のみ）。

## 判断が要る点
- 「倍にした値」: 解析側（`analysis.py` の `doubled`）では、ダブルされたところの `cube.value` は倍にした後の値（「showing the new value」）。そこで `cube.value` をそのまま描いた（さらに 2 倍はしていない）。写真から読む値（`fromRead`）も盤の上の数字そのまま。TODO の意図が「持ち主のキューブの値の 2 倍」なら、ここは違う。
- ダブルされたところで `onPart`（盤面の画面）のとき `drawDice` は `?` を描く（従来どおり、振る人＝ダブルした人の場）。ダブルされた人の場とは別の場なので重ならない。

## 範囲外で気づいたこと
- なし。文書（`rg 'ダブルされた' 'キューブ' *.md`）に古くなる記述は無かった。

## 追記: ダブル中の「?」ダイスを消す（ユーザー決定 2026-10-19）
- `analyzer/static/board-view.js` の `draw`: `BgCube.offered(scene.cube)` が真なら `drawDice` を呼ばない（`scene.dice` があっても出さない）。ダブルしていないときの「?」とそのタップ（ダイスの設定）は従来どおり。`drawCube` のコメントも合わせた。
- `analyzer/README.md`（ダイスの絵の説明、盤からの設定の説明）と `TODO.md` の TODO-156 の節に決定を書き足した。
- 足りるか: 足りる。ダイスの設定（`sheet-roll`）を開く入口は盤のダイスのタップだけだが、ダブル中は次に振る人がキューブで決まる（`app.js` の `setOnRoll` 周辺）ので設定する必要がなく、ダイスを入れたいときはキューブのタップ → 「ダブルされたところ」を外すと「?」が戻る。ダイスの目を選ぶとダブルが外れる動き（TODO-150）の入口が盤から無くなるだけ。
- 確かめたこと: `uv run pytest analyzer/test_pwa.py -q`→ 32 passed。描画位置の数値: ダブル中は `g.die` がキューブ 1 つだけ（「?」なし）、ダブルしていないときは「?」2 つとキューブ（列の端）のまま。
