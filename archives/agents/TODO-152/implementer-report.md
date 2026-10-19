# TODO-152 implementer report

## 変更
- `analyzer/static/board-view.js`: COL を score 32 / cube 28 / pad 3 に。`trayY`（端はキューブ分あける）、新設 `scoreY`、`cubeY`（奥持ち=COL.y0、手前持ち=COL.y1-cube、中央=奥スコアの下）。`drawMatch` は白地の 32×32 の札に数字だけ。`drawCube` は第5引数 `match` を受け、`length>0 && crawford` で `Crawford`（textLength=24、spacingAndGlyphs）。先頭近くと2関数のコメントを更新。
- `analyzer/static/style.css`: `.score-n`（20px 太字）、`.cube-crawford`（7px 太字）を追加。
- `analyzer/app.py`、`analyzer/static/app.js`: 0.85.0。
- `analyzer/static/sw.js`: CACHE v59 -> v60（TODO-089 の盤の見た目の変更 PR が同じく上げていたため）。
- `TODO.md`: TODO-152 の 1 つ目にチェック。

## 測った値（getBBox。viewBox 座標、ホームが右／左、キューブは奥・中央・手前、Crawford あり／なし、アンリミテッド）
列は y 18..422、x 650..706（右）。奥トレイ 49..168、手前トレイ 272..391、スコア札 171..203 と 237..269（x 662..694）、
キューブ 18..46 / 206..234 / 394..422（x 664..692）。間は全部 3。Crawford の字は 24×8 でキューブ内（x 666..690、y 216..224）。
アンリミテッドはスコア札なし。左ホームは x が -50 に移るだけで y は同じ。はみ出し・重なりなし。
`uv run pytest analyzer/test_pwa.py`: 31 passed。
測定は board.js と board-view.js を単独ページに読み込んで実行（実アプリ・BG_CDP は未使用）。

## 懸念
- Crawford の字は 7px 相当とかなり小さい（textLength で幅を詰めている）。見た目は未評価。
- タップの実機確認（`- [ ] ローカル:`）は未実施。
